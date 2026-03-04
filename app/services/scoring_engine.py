from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Tuple

from redis.asyncio import Redis
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import FraudRule, Transaction
from app.services.velocity import get_velocity
from app.services.geoip import GeoIPService


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points on Earth (km)."""
    r = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(
        d_lambda / 2
    ) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _last_location_key(user_id: str) -> str:
    return f"user:last_loc:{user_id}"


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
        client_ip: str | None = None,
        geoip: GeoIPService | None = None,
    ) -> Tuple[float, Dict[str, Any]]:
        if now_ts is None:
            now_ts = txn.timestamp.timestamp() if txn.timestamp else time.time()

        rules = await self._get_active_rules()

        amount_value = float(txn.amount)
        features: Dict[str, Any] = {"amount": amount_value}

        # Geo-based distance and speed features, if we have an IP and GeoIP service.
        if client_ip and geoip:
            current_loc = geoip.get_location(client_ip)
            if current_loc is not None:
                lat_now, lon_now = current_loc
                features["location_lat"] = lat_now
                features["location_lon"] = lon_now

                key = _last_location_key(txn.user_id)
                prev = await self._redis.hgetall(key)

                distance_km = 0.0
                speed_kmh = 0.0

                try:
                    if prev and "lat" in prev and "lon" in prev and "ts" in prev:
                        lat_prev = float(prev["lat"])
                        lon_prev = float(prev["lon"])
                        ts_prev = float(prev["ts"])

                        distance_km = _haversine_km(
                            lat_prev, lon_prev, lat_now, lon_now
                        )
                        dt_hours = max((now_ts - ts_prev) / 3600.0, 1e-6)
                        speed_kmh = distance_km / dt_hours
                except (ValueError, TypeError):
                    distance_km = 0.0
                    speed_kmh = 0.0

                features["travel_distance_km"] = distance_km
                features["travel_speed_kmh"] = speed_kmh

                # Update last location for this user.
                await self._redis.hset(
                    key, mapping={"lat": lat_now, "lon": lon_now, "ts": now_ts}
                )

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

            elif rule.feature_name == "travel_distance_km":
                feature_value = float(features.get("travel_distance_km", 0.0))

            elif rule.feature_name == "travel_speed_kmh":
                feature_value = float(features.get("travel_speed_kmh", 0.0))

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

