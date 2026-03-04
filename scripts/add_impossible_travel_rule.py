"""
One-off script to insert the 'impossible_travel' fraud rule into the existing DB.

Run from project root with DB available:
  python -m scripts.add_impossible_travel_rule
"""
from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from app.models import FraudRule  # noqa: E402


async def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL not set")
    if not database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if rule already exists
        result = await session.execute(
            select(FraudRule).where(FraudRule.name == "impossible_travel")
        )
        existing = result.scalars().first()
        if existing:
            print("Rule 'impossible_travel' already exists, nothing to do.")
            return

        # Insert rule once
        rule = FraudRule(
            name="impossible_travel",
            feature_name="travel_speed_kmh",
            threshold=1000.0,
            weight=40.0,
            is_active=True,
        )
        session.add(rule)
        await session.commit()
        print("Inserted fraud rule 'impossible_travel'.")


if __name__ == "__main__":
    asyncio.run(main())

