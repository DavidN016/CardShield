from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Index, Column, Numeric, DateTime, Boolean, Float, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Transaction(SQLModel, table=True):
    """Matches: transactions (id, user_id, amount, timestamp, is_fraud, fraud_score, metadata).
    Index idx_transactions_user_timestamp (user_id, timestamp DESC) should be created in migration
    for optimal velocity lookups.
    """
    __tablename__ = "transactions"
    __table_args__ = (
        Index("idx_transactions_user_timestamp", "user_id", "timestamp"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(max_length=255, nullable=False)
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False),
    )
    is_fraud: bool = Field(default=False, sa_column=Column(Boolean, server_default=text("false"), nullable=False))
    fraud_score: float = Field(default=0.0, sa_column=Column(Float, server_default=text("0.0"), nullable=False))
    metadata_: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column("metadata", JSONB, nullable=True),
    )
