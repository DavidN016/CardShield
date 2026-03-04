from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.scoring import router as scoring_router
from app.db.redis import close_redis_client, get_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await get_redis_client()
    try:
        yield
    finally:
        await close_redis_client()


app = FastAPI(title="CardShield", version="0.1.0", lifespan=lifespan)
app.include_router(scoring_router)


@app.get("/health")
async def health():
    await app.state.redis.ping()
    return {"status": "ok"}
