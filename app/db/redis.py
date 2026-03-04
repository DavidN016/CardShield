from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from redis.asyncio import Redis, from_url


_redis_client: Optional[Redis] = None


def _get_redis_url() -> str:
    load_dotenv()
    url = os.getenv("REDIS_URL")
    if not url:
        raise RuntimeError("REDIS_URL is not set in environment or .env")
    return url


async def get_redis_client() -> Redis:
    global _redis_client

    if _redis_client is None:
        url = _get_redis_url()
        _redis_client = from_url(url, decode_responses=True)

    return _redis_client


async def close_redis_client() -> None:
    global _redis_client

    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None

