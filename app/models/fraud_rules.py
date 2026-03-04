from typing import Optional

from sqlalchemy import Boolean, Column, Float, Index, text
from sqlmodel import Field, SQLModel


class FraudRule(SQLModel, table=True):
    __tablename__ = "fraud_rules"
    __table_args__ = (Index("idx_fraud_rules_is_active", "is_active"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, nullable=False)
    feature_name: str = Field(max_length=100, nullable=False)
    threshold: float = Field(nullable=False)
    weight: float = Field(default=1.0, sa_column=Column(Float, server_default=text("1.0"), nullable=False))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, server_default=text("true"), nullable=False))
