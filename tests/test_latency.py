"""
Latency test for POST /score. Asserts sub-60 ms median latency.

Requires the API to be running (e.g. docker compose up -d api).
Run: pytest tests/test_latency.py -v -s
     ( -s to see printed percentiles )
"""
import json
import time
import urllib.request
from typing import List

# Base URL for the running API (override with env or pytest -k if needed)
BASE_URL = "http://localhost:8000"


def _post_score(user_id: str = "latency-test", amount: str = "100") -> float:
    """POST /score and return latency in milliseconds."""
    url = f"{BASE_URL}/score"
    data = json.dumps({"user_id": user_id, "amount": amount}).encode()
    req = urllib.request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=5) as resp:
        resp.read()
    return (time.perf_counter() - start) * 1000.0


def _percentile(sorted_latencies: List[float], p: float) -> float:
    """Return the p-th percentile (0-100) of sorted latencies."""
    if not sorted_latencies:
        return 0.0
    k = (len(sorted_latencies) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_latencies) else f
    return sorted_latencies[f] + (k - f) * (sorted_latencies[c] - sorted_latencies[f])


def test_score_endpoint_sub_60ms_median_latency():
    """
    Call POST /score repeatedly and assert median latency is under 60 ms.
    """
    n_requests = 30
    latencies_ms: List[float] = []

    for _ in range(n_requests):
        latencies_ms.append(_post_score())

    latencies_ms.sort()
    median_ms = _percentile(latencies_ms, 50)
    p95_ms = _percentile(latencies_ms, 95)
    p99_ms = _percentile(latencies_ms, 99)

    print(f"\nPOST /score latency (n={n_requests}): median={median_ms:.2f} ms, p95={p95_ms:.2f} ms, p99={p99_ms:.2f} ms")

    assert median_ms < 60.0, (
        f"Median latency {median_ms:.2f} ms exceeds 60 ms (p95={p95_ms:.2f} ms, p99={p99_ms:.2f} ms)"
    )
