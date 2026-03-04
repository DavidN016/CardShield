import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

from app.api.scoring import router as scoring_router
from app.db.redis import close_redis_client, get_redis_client
from app.services.geoip import GeoIPService


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await get_redis_client()

    geoip_path = os.getenv("GEOIP_DB_PATH", "data/GeoLite2-City.mmdb")
    app.state.geoip: Optional[GeoIPService] = None
    if os.path.isfile(geoip_path):
        app.state.geoip = GeoIPService(geoip_path)

    try:
        yield
    finally:
        if app.state.geoip is not None:
            app.state.geoip.close()
        await close_redis_client()


app = FastAPI(title="CardShield", version="0.1.0", lifespan=lifespan)
app.include_router(scoring_router)


@app.get("/health")
async def health():
    await app.state.redis.ping()
    return {"status": "ok"}
