"""
GeoIP lookups using MaxMind GeoIP2 and a local MMDB file (e.g. GeoLite2-City).

Set GEOIP_DB_PATH to the path to your .mmdb file.
We expose latitude/longitude so scoring can compute distance between subsequent uses.
"""
from __future__ import annotations

from typing import Optional, Tuple

import geoip2.database
import geoip2.errors


class GeoIPService:
    """Reader for MaxMind GeoIP2 / GeoLite2 MMDB."""

    def __init__(self, db_path: str) -> None:
        self._reader = geoip2.database.Reader(db_path)

    def get_location(self, ip: str) -> Optional[Tuple[float, float]]:
        """Return (lat, lon) for IP, or None if unknown/invalid."""
        if not ip or ip in ("127.0.0.1", "::1"):
            return None
        try:
            # Use city database so we get coordinates.
            r = self._reader.city(ip)
            if (
                not r
                or not r.location
                or r.location.latitude is None
                or r.location.longitude is None
            ):
                return None
            return float(r.location.latitude), float(r.location.longitude)
        except (geoip2.errors.AddressNotFoundError, ValueError):
            return None

    def close(self) -> None:
        self._reader.close()

