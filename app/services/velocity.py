from __future__ import annotations

import time
from typing import Final

from redis.asyncio import Redis


MAX_WINDOW_SECONDS: Final[int] = 3600


def build_user_key(user_id: str) -> str:
    return f"velocity:user:{user_id}"


async def record_transaction(
    redis: Redis,
    user_id: str,
    txn_id: str,
    ts: float | None = None,
    max_window_seconds: int = MAX_WINDOW_SECONDS,
) -> None:
    """
    Record a transaction timestamp in a per-user ZSET and prune old entries.
    """
    if ts is None:
        ts = time.time()

    key = build_user_key(user_id)

    # Add current event
    await redis.zadd(key, {txn_id: ts})

    # Remove events older than the configured max window
    cutoff = ts - max_window_seconds
    await redis.zremrangebyscore(key, "-inf", cutoff)


async def get_velocity(
    redis: Redis,
    user_id: str,
    window_seconds: int,
    now_ts: float | None = None,
) -> int:
    """
    Return the count of transactions for this user in the last `window_seconds`.
    """
    if now_ts is None:
        now_ts = time.time()

    key = build_user_key(user_id)
    start = now_ts - window_seconds

    count = await redis.zcount(key, start, now_ts)
    return int(count)

