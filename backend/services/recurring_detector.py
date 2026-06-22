"""Recurring payment detection service.

Detects recurring transactions (subscriptions, EMIs, rent, SIPs, insurance)
using a combination of interval-based pattern matching and keyword detection.

Architecture alignment: §8 Recurring Transaction Detection Algorithm.
"""

import logging
from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from backend.models.schemas import RecurringPayment, Transaction

logger = logging.getLogger(__name__)

# Amount tolerance for grouping same merchant transactions
AMOUNT_TOLERANCE = 0.05  # ±5%

# Interval tolerances (in days)
WEEKLY_MIN = 5
WEEKLY_MAX = 9
MONTHLY_MIN = 28
MONTHLY_MAX = 31
QUARTERLY_MIN = 85
QUARTERLY_MAX = 95

# Minimum occurrences needed to confirm a recurring pattern
MIN_OCCURRENCES = 2  # Minimum 2 to detect; 3+ for high confidence

# Keywords that strongly suggest recurring payments
RECURRING_KEYWORDS = {
    "subscription": ["subs", "subscription", "membership", "premium", "pro ", "plus "],
    "emi": ["emi", "loan emi", "instalment", "installment"],
    "rent": ["rent", "rental", "lease"],
    "sip": ["sip", "mutual fund sip"],
    "insurance": ["insurance", "premium", "life insurance", "health insurance", "motor insurance"],
}


def _normalize_merchant_for_grouping(merchant: Optional[str], description: str) -> str:
    """Normalize a merchant name for grouping transactions.

    Uses the merchant name if available, otherwise extracts from description.
    """
    if merchant and merchant != "Unknown":
        return merchant.lower().strip()
    # Fallback: use first word of description
    first_word = description.split()[0] if description else ""
    return first_word.lower().strip("*#- ")


def _is_amount_similar(amount1: float, amount2: float, tolerance: float = AMOUNT_TOLERANCE) -> bool:
    """Check if two amounts are within tolerance of each other."""
    if amount1 == 0 and amount2 == 0:
        return True
    max_amount = max(amount1, amount2)
    if max_amount == 0:
        return True
    return abs(amount1 - amount2) / max_amount <= tolerance


def _detect_frequency(intervals: List[int]) -> Optional[str]:
    """Detect the frequency pattern from a list of day intervals.

    Args:
        intervals: List of days between consecutive transactions.

    Returns:
        Frequency string: "weekly", "monthly", "quarterly", or None.
    """
    if not intervals:
        return None

    avg_interval = sum(intervals) / len(intervals)

    if WEEKLY_MIN <= avg_interval <= WEEKLY_MAX:
        # Verify all intervals are within tolerance
        if all(WEEKLY_MIN <= d <= WEEKLY_MAX for d in intervals):
            return "weekly"

    if MONTHLY_MIN <= avg_interval <= MONTHLY_MAX:
        if all(MONTHLY_MIN <= d <= MONTHLY_MAX for d in intervals):
            return "monthly"

    if QUARTERLY_MIN <= avg_interval <= QUARTERLY_MAX:
        if all(QUARTERLY_MIN <= d <= QUARTERLY_MAX for d in intervals):
            return "quarterly"

    # Check if intervals are somewhat consistent (within 3 days of average)
    if all(abs(d - avg_interval) <= 3 for d in intervals):
        if 5 <= avg_interval <= 9:
            return "weekly"
        elif 25 <= avg_interval <= 35:
            return "monthly"
        elif 80 <= avg_interval <= 100:
            return "quarterly"

    return None


def _calculate_next_expected_date(transactions: List[Transaction], frequency: str) -> Optional[date]:
    """Calculate the next expected date for a recurring payment."""
    if not transactions:
        return None

    last_date = max(t.date for t in transactions if t.date)
    if not last_date:
        return None

    delta_map = {
        "weekly": timedelta(days=7),
        "monthly": timedelta(days=30),
        "quarterly": timedelta(days=90),
    }

    delta = delta_map.get(frequency)
    if delta:
        return last_date + delta

    # Fallback: use average interval
    dates = sorted([t.date for t in transactions if t.date])
    if len(dates) >= 2:
        intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        avg_interval = sum(intervals) / len(intervals)
        return last_date + timedelta(days=int(avg_interval))

    return None


def _detect_recurring_type_from_keywords(description: str, merchant: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Detect if a transaction is recurring based on description keywords.

    Args:
        description: Transaction description.
        merchant: Extracted merchant name.

    Returns:
        Tuple of (is_recurring, recurring_type).
    """
    desc_lower = (description + " " + (merchant or "")).lower()

    for r_type, keywords in RECURRING_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_lower:
                return True, r_type

    return False, None


def detect_recurring_payments(
    transactions: List[Transaction],
    min_occurrences: int = MIN_OCCURRENCES,
) -> Tuple[List[RecurringPayment], List[str]]:
    """Detect recurring payments from a list of categorized transactions.

    Uses two-pronged approach per architecture §8:
    1. Pattern-based: group by merchant + amount, check for consistent intervals
    2. Keyword-based: detect via description keywords

    Args:
        transactions: List of categorized transactions.
        min_occurrences: Minimum occurrences needed to confirm pattern.

    Returns:
        Tuple of (recurring_payments, flags/warnings).
    """
    if not transactions:
        return [], []

    warnings: List[str] = []
    recurring_payments: List[RecurringPayment] = []

    # Only consider debit transactions for recurring detection
    debits = [t for t in transactions if t.txn_type == "debit"]

    if len(debits) < 2:
        warnings.append("Less than 2 debit transactions. Recurring detection requires more data.")
        return [], warnings

    # ── Step 1: Group by (merchant, amount_range) ──
    # Key: (normalized_merchant, amount_bucket)
    # amount_bucket rounds to nearest tolerance bucket
    groups: Dict[Tuple[str, float], List[Transaction]] = defaultdict(list)

    for txn in debits:
        merchant_key = _normalize_merchant_for_grouping(txn.merchant, txn.description)
        # Bucket amount: round to nearest 5% bucket
        bucket_size = max(txn.amount * AMOUNT_TOLERANCE, 1.0)
        amount_bucket = round(txn.amount / bucket_size) * bucket_size
        groups[(merchant_key, amount_bucket)].append(txn)

    # ── Step 2: Check each group for interval patterns ──
    for (merchant_key, amount_bucket), group in groups.items():
        if len(group) < min_occurrences:
            continue

        # Sort by date
        sorted_txns = sorted(group, key=lambda t: t.date)

        # Calculate intervals between consecutive transactions
        dates = [t.date for t in sorted_txns]
        intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]

        if not intervals:
            continue

        # Try to detect frequency
        frequency = _detect_frequency(intervals)

        if frequency:
            # Determine recurring type: try keyword match first
            sample_desc = sorted_txns[0].description
            sample_merchant = sorted_txns[0].merchant
            is_recurring, r_type = _detect_recurring_type_from_keywords(sample_desc, sample_merchant)

            if not r_type:
                # Infer type from merchant/category
                category = sorted_txns[0].category
                type_map = {
                    "EMI": "emi",
                    "Subscriptions": "subscription",
                    "Rent": "rent",
                    "Investments": "sip",
                }
                r_type = type_map.get(category, "subscription")

            next_date = _calculate_next_expected_date(sorted_txns, frequency)

            recurring_payments.append(
                RecurringPayment(
                    merchant=sorted_txns[0].merchant or merchant_key.title(),
                    category=sorted_txns[0].category,
                    amount=round(sum(t.amount for t in sorted_txns) / len(sorted_txns), 2),
                    frequency=frequency,
                    next_expected_date=next_date or date.today(),
                    r_type=r_type,
                    transactions=sorted_txns,
                )
            )

            logger.info(
                f"Detected recurring: {merchant_key} "
                f"₹{sum(t.amount for t in sorted_txns) / len(sorted_txns):.2f}/{frequency} "
                f"({len(sorted_txns)} occurrences)"
            )

    # ── Step 3: Keyword-based detection for single-instance recurring ──
    # Check transactions that weren't caught by pattern matching
    grouped_merchants = {merchant_key for merchant_key, _ in groups}
    for txn in debits:
        merchant_key = _normalize_merchant_for_grouping(txn.merchant, txn.description)
        if merchant_key in grouped_merchants:
            continue  # Already caught by pattern matching

        is_recurring, r_type = _detect_recurring_type_from_keywords(
            txn.description, txn.merchant
        )

        if is_recurring and r_type:
            # Mark individual transactions as recurring
            # (will show up in the dashboard as flagged but without full pattern)
            warnings.append(
                f"Possible recurring {r_type}: "
                f"'{txn.description[:40]}' — ₹{txn.amount:.2f}. "
                "Upload more statements to confirm the pattern."
            )

            # Still add as a single-occurrence recurring payment
            next_date = txn.date + timedelta(days=30)  # Assume monthly as default
            recurring_payments.append(
                RecurringPayment(
                    merchant=txn.merchant or merchant_key.title(),
                    category=txn.category,
                    amount=txn.amount,
                    frequency="monthly",
                    next_expected_date=next_date,
                    r_type=r_type,
                    transactions=[txn],
                )
            )

    # ── Step 4: Mark transactions as recurring ──
    for payment in recurring_payments:
        for txn in payment.transactions:
            txn.is_recurring = True
            txn.recurring_type = payment.r_type

    # Deduplicate recurring payments by (merchant, amount_bucket, frequency)
    # Use rounding to nearest 10 to avoid false dedup of close amounts
    seen: set = set()
    unique_payments: List[RecurringPayment] = []
    for payment in recurring_payments:
        amount_bucket = round(payment.amount, -1) if payment.amount >= 10 else round(payment.amount, 0)
        key = (payment.merchant.lower(), amount_bucket, payment.frequency)
        if key not in seen:
            seen.add(key)
            unique_payments.append(payment)
        else:
            logger.debug(f"Deduplicated recurring payment: {payment.merchant}")

    logger.info(
        f"Recurring detection complete: "
        f"{len(unique_payments)} recurring patterns found "
        f"({len(recurring_payments) - len(unique_payments)} duplicates removed)"
    )

    return unique_payments, warnings


def update_recurring_flag(
    transaction_id: str,
    is_recurring: bool,
    recurring_type: Optional[str],
    transactions: List[Transaction],
) -> Optional[Transaction]:
    """Manually override the recurring flag on a transaction.

    Args:
        transaction_id: ID of the transaction to update.
        is_recurring: New recurring flag value.
        recurring_type: New recurring type (if applicable).
        transactions: List of all transactions to search.

    Returns:
        Updated Transaction or None if not found.
    """
    for txn in transactions:
        if txn.id == transaction_id:
            txn.is_recurring = is_recurring
            txn.recurring_type = recurring_type if is_recurring else None
            return txn
    return None
