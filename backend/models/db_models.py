"""SQLAlchemy ORM models for database storage."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class TransactionDB(Base):
    """SQLAlchemy model for a cleaned and categorized transaction."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    original_description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # "debit" or "credit"
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="Other", index=True)
    category_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    merchant: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recurring_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[float | None] = mapped_column(Float, nullable=True)
    transaction_hash: Mapped[str] = mapped_column(String(64), nullable=True, unique=True)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    suspicious_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<TransactionDB {self.date} {self.description[:30]} ₹{self.amount}>"


class StatementSummaryDB(Base):
    """SQLAlchemy model for statement-level financial summary."""

    __tablename__ = "statement_summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    job_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    parsed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    total_income: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_spend: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    savings: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    savings_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    transaction_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    opening_balance: Mapped[float | None] = mapped_column(Float, nullable=True)
    closing_balance: Mapped[float | None] = mapped_column(Float, nullable=True)
    balance_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    monthly_spend: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    def __repr__(self) -> str:
        return f"<StatementSummaryDB {self.file_name} ₹{self.total_income} / ₹{self.total_spend}>"
