# token-bucket-rate-limiter

Simple token-bucket rate limiter backed by Redis.

## Quick start (with Docker Redis)

Start a Redis instance in Docker (binds to localhost:6379):

```bash
docker run --name redis -p 6379:6379 -d redis:7-alpine
```

## Python setup

Create a virtual environment and install the minimal dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install redis pytest
```

Run tests:

```bash
pytest -q
```

## Files

- `token_bucket.py` — `TokenBucket` implementation. Uses a `RedisStore` to persist per-client token counts and last-refill timestamps.
- `redis_store.py` — thin wrapper around `redis-py` providing `get_key` / `set_key` helpers.
- `tests/test_token_bucket.py` — pytest tests that exercise the implementation against a running Redis instance.

## Implementation overview

The `TokenBucket` implements a basic token-bucket algorithm:

- Config: `token_rate` (tokens added per second) and `max_cap` (bucket capacity).
- Keys per client:
	- `rate:limit:{client_id}:count` — integer token count stored as a string.
	- `rate:limit:{client_id}:last_refill` — last refill timestamp string in `%Y-%m-%d %H:%M:%S` format.
- On the first request for a client the bucket keys are created (count = 0, last_refill = now) and the request is allowed.
- On subsequent requests the implementation:
	1. Reads `count` and `last_refill` from Redis.
	2. Computes elapsed seconds = now - last_refill.
	3. Adds `elapsed_seconds * token_rate` to the stored `count`, caps at `max_cap`.
	4. If there is at least 1 token, consumes one token, updates Redis, and allows the request; otherwise denies it.

The `RedisStore` provides simple `get_key` and `set_key` operations used by `TokenBucket`.

## Usage example

```python
from redis_store import RedisStore
from token_bucket import TokenBucket

rs = RedisStore()
tb = TokenBucket(token_rate=1.0, max_cap=10, redis_store=rs)
allowed = tb.check_limit('client-123')
if allowed:
		# serve request
else:
		# return 429 Too Many Requests
```



