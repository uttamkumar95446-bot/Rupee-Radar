"""AI-powered transaction categorization service.

Uses Groq LLM as primary categorizer with rule-based keyword fallback.
Hybrid mode: uses LLM when confident, falls back to rules for re-check.

Architecture alignment: §7 AI/ML Integration, §9 Category Keyword Map.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

from backend.core.categories import ALL_CATEGORIES, CATEGORY_KEYWORDS
from backend.core.config import settings
from backend.models.schemas import Transaction
from backend.services.rate_limiter import estimate_tokens, get_limiter

logger = logging.getLogger(__name__)

# Maximum transactions per LLM batch
BATCH_SIZE = 15

# Confidence thresholds
HIGH_CONFIDENCE = 0.9  # Use LLM result as-is
MEDIUM_CONFIDENCE = 0.5  # Re-check with rules
LOW_CONFIDENCE = 0.0  # Use rules exclusively


def categorize_by_keywords(description: str) -> Tuple[str, float, Optional[str]]:
    """Categorize a single transaction description using keyword matching.

    Args:
        description: Transaction description text.

    Returns:
        Tuple of (category, confidence, merchant_override).
        confidence is 0.7 for keyword match, 0.0 for "Other" fallback.
    """
    if not description:
        return "Other", 0.0, None

    desc_lower = description.lower()

    best_category = "Other"
    best_confidence = 0.0
    best_merchant: Optional[str] = None

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_lower:
                # Longer keyword match = higher confidence
                keyword_ratio = len(keyword) / max(len(desc_lower), 1)
                confidence = min(0.7, 0.4 + keyword_ratio * 0.3)

                if confidence > best_confidence:
                    best_category = category
                    best_confidence = confidence
                    # Use the matched keyword as merchant hint
                    best_merchant = keyword.title()

    return best_category, best_confidence, best_merchant


def _build_categorization_prompt(transactions: List[Transaction]) -> List[Dict]:
    """Build the LLM prompt for batch transaction categorization.

    Args:
        transactions: List of transactions to categorize.

    Returns:
        List of message dicts for the Groq API.
    """
    system_prompt = (
        "You are a financial transaction categorizer for Indian bank statements. "
        f"Classify each transaction into exactly one category: {', '.join(ALL_CATEGORIES)}. "
        "Also clean/standardize the description and extract the merchant name.\n\n"
        "Rules:\n"
        "- Food: restaurants, food delivery, groceries, cafes\n"
        "- Travel: cabs, flights, trains, fuel, parking, tolls\n"
        "- Shopping: online shopping, malls, retail stores\n"
        "- Bills: utilities, phone, internet, recharges, taxes\n"
        "- EMI: loan payments, equated monthly installments\n"
        "- Subscriptions: Netflix, Spotify, Prime, memberships\n"
        "- Salary: salary credits, payroll\n"
        "- Rent: rent payments, rental agreements\n"
        "- Investments: SIP, mutual funds, stocks, PPF, NPS\n"
        "- Other: anything that doesn't fit above\n\n"
        "Return a JSON array of objects with fields: "
        '"original", "cleaned", "category", "merchant", "confidence".\n\n'
        "Example:\n"
        '[{"original": "SWIGGY*12345 MUMBAI", "cleaned": "Swiggy Order", '
        '"category": "Food", "merchant": "Swiggy", "confidence": 0.95}]\n\n'
        "CRITICAL: Return ONLY valid JSON. No markdown, no code blocks, no extra text."
    )

    user_content_lines = ["Categorize these transactions:"]
    for i, txn in enumerate(transactions, 1):
        user_content_lines.append(
            f'{i}. Date: {txn.date}, Description: "{txn.original_description}", '
            f'Amount: ₹{txn.amount:.2f}, Type: {txn.txn_type}'
        )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "\n".join(user_content_lines)},
    ]


def _parse_llm_response(response_text: str) -> List[Optional[Dict]]:
    """Parse the LLM JSON response into structured results.

    Handles variations: code blocks, trailing commas, extra text.

    Args:
        response_text: Raw response text from the LLM.

    Returns:
        List of parsed dicts or None for failed items.
    """
    import json

    # Strip markdown code blocks if present
    text = response_text.strip()
    if "```json" in text:
        text = text.split("```json")[1]
        if "```" in text:
            text = text.split("```")[0]
    elif "```" in text:
        text = text.split("```")[1]
        if "```" in text:
            text = text.split("```")[0]

    text = text.strip()

    # Try to find JSON array in the response
    array_start = text.find("[")
    array_end = text.rfind("]")
    if array_start >= 0 and array_end > array_start:
        text = text[array_start : array_end + 1]

    if not text:
        logger.warning("Empty LLM response after cleaning.")
        return []

    try:
        results = json.loads(text)
        if not isinstance(results, list):
            logger.warning(f"LLM response is not a list: {type(results)}")
            return []
        return results
    except json.JSONDecodeError:
        # Try to fix common JSON issues
        try:
            # Replace single quotes with double quotes
            fixed = text.replace("'", '"')
            # Remove trailing commas before closing brackets
            fixed = re.sub(r",\s*]", "]", fixed)
            fixed = re.sub(r",\s*}", "}", fixed)
            results = json.loads(fixed)
            if isinstance(results, list):
                return results
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            return []

    return []


def _call_llm(messages: List[Dict]) -> Optional[str]:
    """Call the configured LLM API with the given messages.

    Respects the LLM_PROVIDER setting: groq, openai, or local.
    Enforces rate limits: max 30 requests/minute, 100K tokens/day.

    Args:
        messages: List of message dicts for the chat API.

    Returns:
        Response text content, or None on failure.
    """
    provider = settings.LLM_PROVIDER

    if provider in ("groq", "openai"):
        limiter = get_limiter()

        # Check API key
        if provider == "groq" and not settings.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY not configured. Skipping Groq LLM call.")
            return None
        if provider == "openai" and not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured. Skipping OpenAI LLM call.")
            return None

        # Estimate tokens for this request
        estimated_tokens = estimate_tokens(messages)

        # Check daily token budget
        if not limiter.check_budget(estimated_tokens):
            logger.warning(
                f"Daily token budget exceeded ({limiter.tokens_remaining} remaining, "
                f"~{estimated_tokens} needed). Falling back to rules."
            )
            return None

        # Respect request-per-minute rate limit
        limiter.wait_if_needed()

        try:
            if provider == "groq":
                import groq
                client = groq.Groq(
                    api_key=settings.GROQ_API_KEY,
                    timeout=settings.AI_TIMEOUT_SECONDS,
                    max_retries=2,
                )
                response = client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
            else:  # openai
                from openai import OpenAI
                client = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    timeout=settings.AI_TIMEOUT_SECONDS,
                    max_retries=2,
                )
                response = client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content

            # Record token usage (use estimate if usage info not available from response)
            limiter.record_usage(estimated_tokens)
            return content

        except Exception as e:
            logger.error(f"{provider.upper()} API call failed: {e}")
            return None

    else:  # local
        logger.info("LLM_PROVIDER=local. No cloud LLM call attempted.")
        return None


def categorize_transactions(
    transactions: List[Transaction],
    force_rules_only: bool = False,
) -> Tuple[List[Transaction], List[str]]:
    """Categorize a list of transactions using AI (Groq/OpenAI) + rule fallback.

    Implements hybrid approach per architecture §7:
    - LLM when confidence > 0.9 -> use LLM result
    - 0.5-0.9 -> re-check with rules, use higher confidence result
    - < 0.5 or force_rules_only -> use rules exclusively

    Respects LLM_PROVIDER setting (groq, openai, local).

    Args:
        transactions: List of cleaned but uncategorized transactions.
        force_rules_only: If True, skip LLM and use only keyword rules.

    Returns:
        Tuple of (categorized_transactions, warnings).
    """
    if not transactions:
        return [], []

    warnings: List[str] = []
    categorized: List[Transaction] = []
    llm_results: Dict[int, Dict] = {}

    # Step 1: Determine if LLM should be used
    provider = settings.LLM_PROVIDER
    llm_configured = (
        (provider == "groq" and bool(settings.GROQ_API_KEY)) or
        (provider == "openai" and bool(settings.OPENAI_API_KEY)) or
        (provider == "local")
    )
    use_llm = not force_rules_only and llm_configured and provider != "local"

    if use_llm:
        # Process in batches
        for batch_start in range(0, len(transactions), BATCH_SIZE):
            batch = transactions[batch_start:batch_start + BATCH_SIZE]
            messages = _build_categorization_prompt(batch)

            logger.info(
                f"Calling Groq LLM for batch "
                f"({batch_start + 1}-{batch_start + len(batch)} of {len(transactions)})..."
            )

            response_text = _call_llm(messages)
            if response_text:
                results = _parse_llm_response(response_text)
                for i, result in enumerate(results):
                    idx = batch_start + i
                    if result and isinstance(result, dict):
                        llm_results[idx] = result
                    else:
                        logger.warning(f"LLM returned invalid result for index {idx}")
            else:
                warnings.append(
                    f"LLM call failed for batch {batch_start // BATCH_SIZE + 1}. "
                    "Falling back to keyword rules for these transactions."
                )

    # Step 2: Apply categorization to each transaction
    for i, txn in enumerate(transactions):
        llm_result = llm_results.get(i)
        rule_category, rule_confidence, rule_merchant = categorize_by_keywords(
            txn.original_description or txn.description
        )

        if use_llm and llm_result:
            llm_category = llm_result.get("category", "Other")
            llm_confidence = float(llm_result.get("confidence", 0.0))
            llm_merchant = llm_result.get("merchant") or txn.merchant
            llm_cleaned = llm_result.get("cleaned", txn.description)

            # Hybrid logic
            if llm_confidence >= HIGH_CONFIDENCE:
                # Use LLM result directly
                txn.category = llm_category if llm_category in ALL_CATEGORIES else "Other"
                txn.category_confidence = llm_confidence
                if llm_merchant:
                    txn.merchant = llm_merchant
                txn.description = llm_cleaned

            elif llm_confidence >= MEDIUM_CONFIDENCE:
                # Re-check with rules, use whichever has higher confidence
                if rule_confidence > llm_confidence:
                    txn.category = rule_category
                    txn.category_confidence = rule_confidence
                    if rule_merchant:
                        txn.merchant = rule_merchant
                else:
                    txn.category = llm_category if llm_category in ALL_CATEGORIES else "Other"
                    txn.category_confidence = llm_confidence
                    if llm_merchant:
                        txn.merchant = llm_merchant
                    txn.description = llm_cleaned
            else:
                # Low LLM confidence — use rules
                txn.category = rule_category
                txn.category_confidence = rule_confidence
        else:
            # LLM not available or forced rules only
            txn.category = rule_category
            txn.category_confidence = rule_confidence

        # If no merchant was set, try from rules
        if not txn.merchant and rule_merchant:
            txn.merchant = rule_merchant

        categorized.append(txn)

    # Step 3: Count categorization results
    categorized_count = sum(1 for t in categorized if t.category != "Other")
    ai_count = sum(1 for t in categorized if t.category_confidence >= HIGH_CONFIDENCE)
    rules_count = sum(1 for t in categorized if t.category_confidence < HIGH_CONFIDENCE and t.category != "Other")

    logger.info(
        f"Categorized {len(categorized)} transactions: "
        f"{categorized_count} categorized, "
        f"{ai_count} via LLM (conf>={HIGH_CONFIDENCE}), "
        f"{rules_count} via rules"
    )

    if use_llm and not llm_results:
        warnings.append(
            "AI categorization was unavailable. Used keyword-based rules only. "
            f"Set {provider.upper()}_API_KEY in .env to enable AI categorization."
        )

    return categorized, warnings
