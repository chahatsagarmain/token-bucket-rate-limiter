from token_bucket import TokenBucket
from redis_store import RedisStore


def main():
    redis_store = RedisStore()
    token_rate_limiter = TokenBucket(0.5 , 5 , redis_store)

if __name__ == "__main__":
    main()