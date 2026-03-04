from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.redis import get_redis_client
from app.db.session import get_session
from app.models import Transaction
from app.services.scoring_engine import ScoringEngine
from app.services.velocity import record_transaction


router = APIRouter(prefix="/score", tags=["scoring"])


class ScoreRequest(BaseModel):
    user_id: str
    amount: Decimal
    transaction_id: str | None = None


class ScoreResponse(BaseModel):
    score: float
    rules_triggered: List[str]
    velocity_1m: int


async def _get_redis() -> Redis:
    return await get_redis_client()


def _client_ip(request: Request) -> str | None:
    """Client IP: X-Forwarded-For (first) or X-Real-IP or request.client.host."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real = request.headers.get("X-Real-IP")
    if real:
        return real.strip()
    if request.client:
        return request.client.host
    return None


@router.post("", response_model=ScoreResponse)
async def score(
    request: Request,
    payload: ScoreRequest,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(_get_redis),
) -> ScoreResponse:
    now = datetime.now(timezone.utc)
    now_ts = now.timestamp()

    txn = Transaction(
        user_id=payload.user_id,
        amount=payload.amount,
        timestamp=now,
    )

    txn_id = payload.transaction_id or f"{payload.user_id}:{now_ts}"
    await record_transaction(redis, payload.user_id, txn_id, ts=now_ts)

    client_ip = _client_ip(request)
    geoip = getattr(request.app.state, "geoip", None)

    engine = ScoringEngine(session=session, redis=redis)
    score_value, meta = await engine.score_transaction(
        txn, now_ts=now_ts, client_ip=client_ip, geoip=geoip
    )

    features = meta.get("features", {})
    velocity_1m = int(features.get("transaction_count_60s", 0))

    return ScoreResponse(
        score=score_value,
        rules_triggered=meta.get("rules_triggered", []),
        velocity_1m=velocity_1m,
    )

