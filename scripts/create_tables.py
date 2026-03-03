"""
Create all SQLModel tables (transactions, fraud_rules). Run once with DB available:
  python -m scripts.create_tables

Uses DATABASE_URL from .env. Then run: python -m scripts.seed_fraud_rules
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# Import models so they are registered with SQLModel.metadata
from app.models import FraudRule, Transaction  # noqa: F401

load_dotenv()


async def create_all():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL not set")
    if not database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: SQLModel.metadata.create_all(sync_conn))
    print("Created tables: transactions, fraud_rules")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_all())
