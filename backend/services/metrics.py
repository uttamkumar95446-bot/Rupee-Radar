"""Financial metrics computation engine.

Calculates all KPIs from cleaned transaction data:
total income, total spend, savings, top categories, top merchants, etc.
"""

import logging
from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from backend.models.schemas import (
    CategorySpend,
    FinancialMetrics,
    MerchantSpend,
    Transaction,
)

logger = logging.getLogger(__name__)


def compute_metrics(
    transactions: List[Transaction],
) -> FinancialMetrics:
    """Compute all financial metrics from a list of cleaned transactions.

    Args:
        transactions: List of cleaned and categorized transactions.

    Returns:
        FinancialMetrics with all computed values.
    """
    if not transactions:
        return FinancialMetrics()

    # Separate credits and debits
    credits = [t for t in transactions if t.txn_type == "credit"]
    debits = [t for t in transactions if t.txn_type == "debit"]

    total_income = sum(t.amount for t in credits)
    total_spend = sum(t.amount for t in debits)
    savings = total_income - total_spend
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0.0

    # Category breakdown (only for debits/spending)
    category_spend: Dict[str, float] = defaultdict(float)
    category_count: Dict[str, int] = defaultdict(int)
    for t in debits:
        category_spend[t.category] += t.amount
        category_count[t.category] += 1

    # Build CategorySpend list sorted by amount descending
    top_categories = []
    for cat, amount in sorted(category_spend.items(), key=lambda x: -x[1]):
        percentage = (amount / total_spend * 100) if total_spend > 0 else 0.0
        top_categories.append(
            CategorySpend(
                category=cat,
                amount=round(amount, 2),
                percentage=round(percentage, 1),
                transaction_count=category_count[cat],
            )
        )

    # Merchant breakdown
    merchant_spend: Dict[str, Dict] = defaultdict(lambda: {"amount": 0.0, "category": "", "count": 0})
    for t in debits:
        merchant_name = t.merchant or "Unknown"
        merchant_spend[merchant_name]["amount"] += t.amount
        merchant_spend[merchant_name]["category"] = t.category
        merchant_spend[merchant_name]["count"] += 1

    top_merchants = [
        MerchantSpend(
            merchant=name,
            amount=round(data["amount"], 2),
            category=data["category"],
            transaction_count=data["count"],
        )
        for name, data in sorted(merchant_spend.items(), key=lambda x: -x[1]["amount"])
    ][:5]  # Top 5 merchants

    # Biggest transactions
    biggest_debit = max(debits, key=lambda t: t.amount) if debits else None
    biggest_credit = max(credits, key=lambda t: t.amount) if credits else None
    biggest_transaction = max(
        [t for t in transactions if t.amount > 0],
        key=lambda t: t.amount,
    ) if transactions else None

    # Average daily spend
    if debits and len(debits) > 0:
        dates = [t.date for t in debits if t.date]
        if dates:
            date_range = (max(dates) - min(dates)).days + 1
            avg_daily = round(total_spend / max(date_range, 1), 2)
        else:
            avg_daily = total_spend
    else:
        avg_daily = 0.0

    return FinancialMetrics(
        total_income=round(total_income, 2),
        total_spend=round(total_spend, 2),
        savings=round(savings, 2),
        savings_rate=round(savings_rate, 1),
        top_categories=top_categories,
        top_merchants=top_merchants,
        biggest_transaction=biggest_transaction,
        biggest_credit=biggest_credit,
        monthly_spend=round(total_spend, 2),
        transaction_count=len(transactions),
        average_daily_spend=avg_daily,
    )
