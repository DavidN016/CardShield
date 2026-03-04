# CardShield

Fraud scoring REST API with Redis sliding-window velocity and dynamic rules from Postgres.

## Testing Redis and the scoring engine

### 1. Start dependencies and API

```bash
# From project root
docker compose up -d db redis
# Optional: run API in Docker too, or run locally:
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If you run the API **on your machine**, ensure `.env` uses `localhost` for DB and Redis (so scripts and tests can connect):

- `DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cardshield`
- `REDIS_URL=redis://localhost:6379/0`

Create tables and seed rules once:

```bash
python -m scripts.create_tables
python -m scripts.seed_fraud_rules
```

### 2. Manual checks with curl

**Health (Redis connectivity):**

```bash
curl -s http://localhost:8000/health
# Expect: {"status":"ok"}
```

**Score a single transaction (Redis + scoring engine):**

```bash
curl -s -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","amount":"15000.00"}'
```

You should get JSON with `score` (e.g. 50 from high_value_check), `rules_triggered`, and `velocity_1m`. Send the same request a few more times for `user_id":"u1"`; `velocity_1m` should increase (sliding window in Redis).

### 3. Automated tests (pytest)

With `db` and `redis` (and optionally the API) running and `.env` pointing at `localhost`:

```bash
# From project root, with venv activated
pip install pytest httpx
pytest tests/ -v
```

The test suite calls `/health` and `/score` and verifies that multiple score requests for the same user increase `velocity_1m`.
