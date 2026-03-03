"""
Seed initial fraud rules. Run from project root with DB available:
  python -m scripts.seed_fraud_rules
"""
import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from dotenv import load_dotenv

load_dotenv()

from app.models import FraudRule


async def seed():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL not set")
    if not database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.exec(select(FraudRule).where(FraudRule.name == "high_value_check"))
        if result.one_or_none():
            print("Fraud rules already seeded, skipping.")
            return

        session.add(FraudRule(name="high_value_check", feature_name="amount", threshold=10000.0, weight=50.0))
        session.add(FraudRule(name="velocity_check_1m", feature_name="transaction_count", threshold=5.0, weight=30.0))
        await session.commit()
        print("Seeded fraud_rules: high_value_check, velocity_check_1m.")


if __name__ == "__main__":
    asyncio.run(seed())
