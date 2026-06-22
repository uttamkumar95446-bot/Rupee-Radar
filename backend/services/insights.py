"""Personalized financial insight generation service.

Uses Groq/OpenAI LLM as primary insight generator with rule-based template fallback.
Generates 3-5 insights per analysis referencing actual transaction amounts.

Architecture alignment: §5.5 Insight model, §7 AI/ML Integration.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from backend.core.config import settings
from backend.models.schemas import (
    FinancialMetrics,
    Insight,
    RecurringPayment,
    Transaction,
)
from backend.services.rate_limiter import estimate_tokens, get_limiter

logger = logging.getLogger(__name__)

MIN_INSIGHTS = 3
MAX_INSIGHTS = 5


def _call_llm(messages: List[Dict]) -> Optional[str]:
    """Call the configured LLM API with the given messages.

    Reuses the same pattern as categorizer.py — respects LLM_PROVIDER setting.
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
                f"~{estimated_tokens} needed). Falling back to rule-based insights."
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
                    temperature=0.3,
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
                    temperature=0.3,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content

            # Record token usage
            limiter.record_usage(estimated_tokens)
            return content

        except Exception as e:
            logger.error(f"{provider.upper()} API call failed: {e}")
            return None

    else:
        logger.info("LLM_PROVIDER=local. No cloud LLM call attempted.")
        return None


def _build_insight_prompt(
    metrics: FinancialMetrics,
    recurring: List[RecurringPayment],
    transactions: List[Transaction],
) -> List[Dict]:
    """Build the LLM prompt for generating personalized financial insights.

    Args:
        metrics: Computed financial metrics.
        recurring: Detected recurring payments.
        transactions: Full transaction list.

    Returns:
        List of message dicts for the chat API.
    """
    # Build a compact summary of the financial data
    top_categories_str = "\n".join(
        f"  - {c.category}: Rs.{c.amount:.2f} ({c.percentage:.1f}% of spend, {c.transaction_count} txns)"
        for c in metrics.top_categories[:5]
    )

    recurring_str = "\n".join(
        f"  - {r.merchant}: Rs.{r.amount:.2f}/{r.frequency} ({r.r_type})"
        for r in recurring[:10]
    )

    # Top transactions
    debits = [t for t in transactions if t.txn_type == "debit"]
    top_debits = sorted(debits, key=lambda t: t.amount, reverse=True)[:3]
    top_debits_str = "\n".join(
        f"  - {t.description}: Rs.{t.amount:.2f} on {t.date} ({t.category})"
        for t in top_debits
    )

    system_prompt = (
        "You are a personal finance analyst for an Indian user. "
        "Given the user's transaction data, generate 3-5 concise, personalized insights. "
        "Use actual amounts in Indian Rupee (Rs.) format. "
        "Focus on: biggest spending categories, unusual spending, recurring costs, "
        "savings opportunities, and positive habits.\n\n"
        "Rules:\n"
        "- Every insight MUST reference a specific amount from the data\n"
        "- Be specific: mention merchant names, categories, and exact amounts\n"
        "- Include both positive (savings rate, good habits) and constructive feedback\n"
        "- Use natural, helpful language — not judgmental\n\n"
        "Return a JSON object with a single key 'insights' containing an array of objects. "
        "Each object has fields: "
        '"title" (short headline), '
        '"description" (1-2 sentences with Rs. amounts), '
        '"type" ("spending"|"saving"|"recurring"|"alert"), '
        '"severity" ("info"|"warning"|"positive"), '
        '"amount" (the relevant amount as a number, or null).\n\n'
        "Example:\n"
        '{"insights": [\n'
        '  {"title": "Food delivery spending", '
        '"description": "You spent Rs.4,200 on Swiggy and Zomato this month — averaging Rs.140/day. Consider cooking at home 2 more days a week to save ~Rs.1,500/month.", '
        '"type": "spending", "severity": "warning", "amount": 4200.0}\n'
        "]}\n\n"
        "CRITICAL: Return ONLY valid JSON. No markdown, no code blocks, no extra text."
    )

    user_content = (
        f"Generate {MIN_INSIGHTS}-{MAX_INSIGHTS} personalized insights from this financial data:\n\n"
        f"--- Summary ---\n"
        f"Total Income: Rs.{metrics.total_income:.2f}\n"
        f"Total Spend: Rs.{metrics.total_spend:.2f}\n"
        f"Savings: Rs.{metrics.savings:.2f} ({metrics.savings_rate:.1f}% of income)\n"
        f"Transactions: {metrics.transaction_count}\n\n"
        f"--- Top Spending Categories ---\n"
        f"{top_categories_str}\n\n"
        f"--- Recurring Payments ({len(recurring)}) ---\n"
        f"{recurring_str if recurring else '  None detected'}\n\n"
        f"--- Biggest Expenses ---\n"
        f"{top_debits_str if top_debits_str else '  None'}\n"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]


def _parse_llm_response(response_text: str) -> List[Optional[Dict]]:
    """Parse the LLM JSON response into structured insight results.

    Handles variations: code blocks, trailing commas, extra text.

    Args:
        response_text: Raw response text from the LLM.

    Returns:
        List of parsed insight dicts.
    """
    text = response_text.strip()

    # Strip markdown code blocks if present
    if "```json" in text:
        text = text.split("```json")[1]
        if "```" in text:
            text = text.split("```")[0]
    elif "```" in text:
        text = text.split("```")[1]
        if "```" in text:
            text = text.split("```")[0]

    text = text.strip()

    # Try to find JSON in the response
    obj_start = text.find("{")
    obj_end = text.rfind("}")
    if obj_start >= 0 and obj_end > obj_start:
        text = text[obj_start : obj_end + 1]

    if not text:
        logger.warning("Empty LLM response after cleaning.")
        return []

    try:
        data = json.loads(text)
        insights = data.get("insights", data if isinstance(data, list) else [])
        if isinstance(insights, list):
            return insights
        return []
    except json.JSONDecodeError:
        # Try to fix common JSON issues
        try:
            fixed = text.replace("'", '"')
            fixed = re.sub(r",\s*}", "}", fixed)
            fixed = re.sub(r",\s*]", "]", fixed)
            data = json.loads(fixed)
            insights = data.get("insights", data if isinstance(data, list) else [])
            if isinstance(insights, list):
                return insights
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            return []

    return []


def _generate_fallback_insights(
    metrics: FinancialMetrics,
    recurring: List[RecurringPayment],
    transactions: List[Transaction],
) -> List[Insight]:
    """Generate rule-based fallback insights when AI is unavailable.

    Args:
        metrics: Computed financial metrics.
        recurring: Detected recurring payments.
        transactions: Full transaction list.

    Returns:
        List of Insight objects.
    """
    insights: List[Insight] = []

    # 1. Top spending category insight
    if metrics.top_categories:
        top_cat = metrics.top_categories[0]
        insights.append(Insight(
            title="Biggest spending category",
            description=(
                f"Your biggest spending category is {top_cat.category} at "
                f"Rs.{top_cat.amount:,.2f} — {top_cat.percentage:.1f}% of your total spend "
                f"across {top_cat.transaction_count} transactions."
            ),
            insight_type="spending",
            severity="warning",
            amount=top_cat.amount,
        ))

    # 2. Savings insight
    if metrics.savings > 0:
        insights.append(Insight(
            title="Savings summary",
            description=(
                f"You saved Rs.{metrics.savings:,.2f} this month — "
                f"that's {metrics.savings_rate:.1f}% of your income of "
                f"Rs.{metrics.total_income:,.2f}."
            ),
            insight_type="saving",
            severity="positive" if metrics.savings_rate >= 20 else "info",
            amount=metrics.savings,
        ))
    else:
        insights.append(Insight(
            title="Spending exceeds income",
            description=(
                f"Your spending of Rs.{metrics.total_spend:,.2f} "
                f"exceeds your income of Rs.{metrics.total_income:,.2f} "
                f"by Rs.{abs(metrics.savings):,.2f}. Consider reviewing your expenses."
            ),
            insight_type="alert",
            severity="warning",
            amount=abs(metrics.savings),
        ))

    # 3. Recurring payments insight
    if recurring:
        total_recurring = sum(r.amount for r in recurring)
        monthly_recurring = sum(r.amount for r in recurring if r.frequency == "monthly")
        insights.append(Insight(
            title="Recurring expenses",
            description=(
                f"You have {len(recurring)} recurring payment(s) totalling "
                f"Rs.{total_recurring:,.2f} per period. "
                f"Monthly recurring: Rs.{monthly_recurring:,.2f}."
            ),
            insight_type="recurring",
            severity="info",
            amount=total_recurring,
        ))

    # 4. Biggest transaction insight
    if metrics.biggest_transaction:
        bt = metrics.biggest_transaction
        insights.append(Insight(
            title="Largest transaction",
            description=(
                f"Your biggest transaction was '{bt.description}' "
                f"at Rs.{bt.amount:,.2f} on {bt.date} ({bt.category})."
            ),
            insight_type="spending",
            severity="info",
            amount=bt.amount,
        ))

    # 5. Category diversity insight
    if metrics.top_categories:
        if len(metrics.top_categories) >= 5:
            top_cat_name = metrics.top_categories[0].category
            insights.append(Insight(
                title="Spending diversity",
                description=(
                    f"Your spending is spread across {len(metrics.top_categories)} categories. "
                    f"Your highest category ({top_cat_name}) accounts for "
                    f"{metrics.top_categories[0].percentage:.1f}% of total spend."
                ),
                insight_type="spending",
                severity="positive" if top_cat_name != "Other" else "info",
                amount=metrics.top_categories[0].amount,
            ))

    return insights


def generate_insights(
    metrics: FinancialMetrics,
    recurring: List[RecurringPayment],
    transactions: List[Transaction],
    force_rules_only: bool = False,
) -> Tuple[List[Insight], List[str]]:
    """Generate personalized financial insights using AI + rule-based fallback.

    Uses LLM when available, falls back to rule-based templates.

    Args:
        metrics: Computed financial metrics.
        recurring: Detected recurring payments.
        transactions: Full transaction list.
        force_rules_only: If True, skip LLM and use only rule-based templates.

    Returns:
        Tuple of (insights, warnings).
    """
    warnings: List[str] = []
    insights: List[Insight] = []

    if not transactions:
        return [], ["No transactions available to generate insights."]

    # Step 1: Try AI insight generation
    provider = settings.LLM_PROVIDER
    llm_configured = (
        (provider == "groq" and bool(settings.GROQ_API_KEY)) or
        (provider == "openai" and bool(settings.OPENAI_API_KEY)) or
        (provider == "local")
    )
    use_llm = not force_rules_only and llm_configured and provider != "local"

    if use_llm:
        messages = _build_insight_prompt(metrics, recurring, transactions)
        logger.info("Calling LLM for insight generation...")
        response_text = _call_llm(messages)

        if response_text:
            raw_insights = _parse_llm_response(response_text)
            for raw in raw_insights:
                if raw and isinstance(raw, dict):
                    try:
                        insight = Insight(
                            title=str(raw.get("title", "Financial Insight")),
                            description=str(raw.get("description", "")),
                            insight_type=str(raw.get("type", "spending")),
                            severity=str(raw.get("severity", "info")),
                            amount=raw.get("amount"),
                        )
                        insights.append(insight)
                    except Exception as e:
                        logger.warning(f"Failed to parse AI insight: {e}")
        else:
            warnings.append("AI insight generation unavailable. Using rule-based insights.")

    # Step 2: If we don't have enough insights, generate fallback
    if len(insights) < MIN_INSIGHTS:
        fallback = _generate_fallback_insights(metrics, recurring, transactions)
        # Add fallback insights that don't duplicate existing ones
        existing_titles = {i.title.lower() for i in insights}
        for fi in fallback:
            if fi.title.lower() not in existing_titles:
                insights.append(fi)
                existing_titles.add(fi.title.lower())

        if use_llm and not response_text:
            warnings.append(
                f"AI insight generation was unavailable. "
                f"Used rule-based insights. "
                f"Set {provider.upper()}_API_KEY in .env to enable AI insights."
            )

    # Step 3: Limit to MAX_INSIGHTS, ensure at least MIN_INSIGHTS
    insights = insights[:MAX_INSIGHTS]

    if len(insights) < MIN_INSIGHTS:
        warnings.append(f"Only {len(insights)} insight(s) generated (minimum {MIN_INSIGHTS} requested).")

    logger.info(f"Generated {len(insights)} insights ({'AI' if use_llm and insights else 'rules'})")

    return insights, warnings
