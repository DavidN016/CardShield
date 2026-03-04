from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

from redis.asyncio import Redis
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import FraudRule, Transaction
from app.services.velocity import get_velocity


class ScoringEngine:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self._session = session
        self._redis = redis

    async def _get_active_rules(self) -> List[FraudRule]:
        # Use execute + scalars() so we get FraudRule instances (exec() can return Rows without model attrs)
        result = await self._session.execute(select(FraudRule).where(FraudRule.is_active == True))  # noqa: E712
        return list(result.scalars().all())

    async def score_transaction(
        self,
        txn: Transaction,
        now_ts: float | None = None,
    ) -> Tuple[float, Dict[str, Any]]:
        if now_ts is None:
            now_ts = txn.timestamp.timestamp() if txn.timestamp else time.time()

        rules = await self._get_active_rules()

        amount_value = float(txn.amount)
        features: Dict[str, Any] = {"amount": amount_value}

        velocity_cache: Dict[int, int] = {}

        total_score = 0.0
        triggered: List[str] = []

        for rule in rules:
            feature_value: float | int | None = None

            if rule.feature_name == "amount":
                feature_value = amount_value

            elif rule.feature_name == "transaction_count":
                window = 60
                if window not in velocity_cache:
                    velocity_cache[window] = await get_velocity(
                        self._redis,
                        txn.user_id,
                        window_seconds=window,
                        now_ts=now_ts,
                    )
                feature_value = velocity_cache[window]
                features["transaction_count_60s"] = velocity_cache[window]

            if feature_value is None:
                continue

            if feature_value > rule.threshold:
                total_score += rule.weight
                triggered.append(rule.name)

        metadata = {
            "rules_triggered": triggered,
            "features": features,
        }

        return total_score, metadata

