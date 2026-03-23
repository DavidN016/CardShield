# CardShield

CardShield is an async fraud-scoring API built with FastAPI, Redis, and PostgreSQL.
It evaluates each transaction in real time using a microservice-style pipeline:
record event in Redis, build features (amount, velocity, geo), load active rules, and return a risk score.

## What this project does

- Exposes `POST /score` to score transactions.
- Uses Redis sorted sets for low-latency sliding-window velocity features.
- Loads active fraud rules from PostgreSQL via SQLModel.
- Returns a numeric score, triggered rules, and velocity metadata.
- Includes a latency test with a sub-60 ms median target for `/score`.

## Stack

- FastAPI + Uvicorn (async API server)
- SQLModel + async SQLAlchemy + `asyncpg` (PostgreSQL access)
- `redis.asyncio` (Redis feature store for velocity and geo state)
- Docker Compose for local infrastructure (`db`, `redis`, `api`)

## Quick start

### 1) Start services

Run everything in Docker:

```bash
docker compose up -d --build
```

Or run only dependencies in Docker and API locally:

```bash
docker compose up -d db redis
```

### 2) Configure environment

If running API locally, set `.env` to localhost endpoints:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cardshield
REDIS_URL=redis://localhost:6379/0
GEOIP_DB_PATH=data/GeoLite2-City.mmdb
```

If running API in Docker Compose, service hostnames are used automatically (`db`, `redis`).

### 3) Initialize database

```bash
python -m scripts.create_tables
python -m scripts.seed_fraud_rules
```

Optional one-off utility if needed:

```bash
python -m scripts.add_index_fraud_rules_is_active
```

## Use the API

Health check:

```bash
curl -s http://localhost:8000/health
```

Score a transaction:

```bash
curl -s -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","amount":"15000.00"}'
```

Example response fields:

- `score`: total risk score from triggered rules
- `rules_triggered`: list of rule names that fired
- `velocity_1m`: transaction count in the last 60 seconds

## Run tests

Install test dependencies:

```bash
pip install -r requirements.txt pytest httpx
```

Run all tests:

```bash
pytest tests/ -v
```

Run latency test only:

```bash
pytest tests/test_latency.py -v -s
```
