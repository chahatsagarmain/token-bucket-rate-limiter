from datetime import datetime, timedelta
import pytest
from token_bucket import TokenBucket
from redis_store import RedisStore

import redis as redis_py


def _redis_client():
    return redis_py.Redis(host="localhost", port=6379, db=0, decode_responses=True)


@pytest.fixture
def r():
    rs = RedisStore()
    client = _redis_client()

    # cleanup keys used by the tests before each run
    for key in client.scan_iter(match="rate:limit:*"):
        client.delete(key)

    yield rs

    # cleanup after test
    for key in client.scan_iter(match="rate:limit:*"):
        client.delete(key)


def test_initial_allow_creates_keys(r: RedisStore):
    tb = TokenBucket(token_rate=1.0, max_cap=5, redis_store=r)
    client = "client1"

    assert tb.check_limit(client) is True
    # keys should be initialized
    assert r.get_key(tb.create_bucket_count_key(client)) == "0"
    assert r.get_key(tb.create_bucket_last_refill_key(client)) is not None


def test_consumption_and_block(r: RedisStore):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # start with 1 token and last_refill == now so no refill
    r.set_key("rate:limit:client2:count", "1")
    r.set_key("rate:limit:client2:last_refill", now)

    tb = TokenBucket(token_rate=1.0, max_cap=2, redis_store=r)

    # first call consumes the single token
    assert tb.check_limit("client2") is True
    # immediate second call should be blocked (no tokens)
    assert tb.check_limit("client2") is False


def test_refill_over_time_allows_requests(r: RedisStore):
    # set count to 0 and last_refill to 5 seconds ago
    past = (datetime.now() - timedelta(seconds=5)).strftime("%Y-%m-%d %H:%M:%S")
    r.set_key("rate:limit:client3:count", "0")
    r.set_key("rate:limit:client3:last_refill", past)

    tb = TokenBucket(token_rate=1.0, max_cap=10, redis_store=r)

    # enough time has passed to accumulate tokens (5 tokens)
    assert tb.check_limit("client3") is True
    # after consuming one, there should still be tokens remaining
    assert tb.check_limit("client3") is True

