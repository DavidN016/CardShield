"""
One-off script to create an index on fraud_rules.is_active.

Useful when tables already exist (SQLModel create_all won't add indexes retroactively).

Run from project root with DB available:
  python -m scripts.add_index_fraud_rules_is_active
"""

from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


async def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL not set")
    if not database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, echo=False)
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_fraud_rules_is_active "
                "ON fraud_rules (is_active)"
            )
        )
    await engine.dispose()
    print("Ensured index exists: idx_fraud_rules_is_active on fraud_rules(is_active)")


if __name__ == "__main__":
    asyncio.run(main())

