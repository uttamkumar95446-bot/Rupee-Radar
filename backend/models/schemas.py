"""Pydantic v2 schemas for API request/response validation.

All models match the architecture document §5 data model specifications.
"""

import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

DateType = datetime.date
DateTimeType = datetime.datetime


class Transaction(BaseModel):
    """A cleaned and categorized financial transaction (Architecture §5.1)."""

    id: str = ""
    date: DateType
    description: str = ""
    original_description: str = ""
    amount: float = 0.0
    txn_type: Literal["debit", "credit"] = "debit"
    category: str = "Other"
    category_confidence: float = 0.0
    merchant: Optional[str] = None
    is_recurring: bool = False
    recurring_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_suspicious: bool = False
    suspicious_reason: Optional[str] = None

    model_config = {"from_attributes": True}


class CategorySpend(BaseModel):
    """Spend breakdown by category (Architecture §5.3)."""

    category: str
    amount: float
    percentage: float = Field(..., ge=0, le=100, description="% of total spend")
    transaction_count: int


class MerchantSpend(BaseModel):
    """Spend breakdown by merchant."""

    merchant: str
    amount: float
    category: str
    transaction_count: int


class RecurringPayment(BaseModel):
    """A detected recurring payment (Architecture §5.4)."""

    merchant: str
    category: str
    amount: float
    frequency: str = "monthly"
    next_expected_date: DateType
    r_type: str = "subscription"
    transactions: list[Transaction] = Field(default_factory=list)


class Insight(BaseModel):
    """A personalized financial insight (Architecture §5.5)."""

    title: str = Field(..., description="Short headline")
    description: str = Field(..., description="Human-readable sentence")
    insight_type: str = "spending"
    severity: str = "info"
    amount: float | None = Field(None, description="Relevant amount if applicable")


class FinancialMetrics(BaseModel):
    """Computed financial metrics (Architecture §5.2)."""

    total_income: float = 0.0
    total_spend: float = 0.0
    savings: float = 0.0
    savings_rate: float = 0.0
    top_categories: list[CategorySpend] = Field(default_factory=list)
    top_merchants: list[MerchantSpend] = Field(default_factory=list)
    biggest_transaction: Transaction | None = None
    biggest_credit: Transaction | None = None
    monthly_spend: float = 0.0
    transaction_count: int = 0
    average_daily_spend: float = 0.0


class AnalysisResponse(BaseModel):
    """Complete analysis result (Architecture §5.6)."""

    file_name: str
    parsed_at: DateTimeType
    transactions: list[Transaction] = Field(default_factory=list)
    total_transactions: int = 0
    recurring_payments: list[RecurringPayment] = Field(default_factory=list)
    metrics: FinancialMetrics = Field(default_factory=FinancialMetrics)
    insights: list[Insight] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    total_parsed: int = 0
    total_skipped: int = 0
    balance_verified: bool = False


# ========================
# API-specific schemas
# ========================


class UploadResponse(BaseModel):
    """Response for POST /api/upload."""

    job_id: str
    status: str = "processing"
    message: str = "File received. Analysis in progress."


class JobStatus(BaseModel):
    """Response for GET /api/analysis/{job_id}."""

    status: str  # "processing", "completed", "failed"
    data: AnalysisResponse | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    """Response for GET /api/health."""

    status: str = "ok"
    version: str = "1.0.0"


# ========================
# Internal models
# ========================


class RawTransaction(BaseModel):
    """Raw parsed transaction before cleaning/categorization."""

    date: Optional[DateType] = None
    description: str = ""
    amount: float | None = None
    txn_type: Literal["debit", "credit"] | None = None
    balance: float | None = None
    original_line: str = ""
    row_number: int = 0
    warnings: list[str] = Field(default_factory=list)
