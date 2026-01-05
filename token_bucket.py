import logging
from redis_store import RedisStore
from datetime import datetime

logger = logging.getLogger(__name__)

class TokenBucket():
    def __init__(self , token_rate : float , max_cap : int, redis_store : RedisStore):
        """Initialize token bucket with rate and max capacity.
        
        Args:
            token_rate: Number of tokens to refill per second
            max_cap: Maximum token capacity
            redis_store: RedisStore instance for persistence
        """
        # the number of tokens to allow for a client id in a second 
        self.rate = token_rate
        if self.rate <= 0:
            raise ValueError("invalid token rate")
        self.max_cap = max_cap
        if self.max_cap <= 0:
            raise ValueError("invalid max capacity")
        self.r = redis_store
        
    def __is_allowed(self , count_key : str, refill_key : str) -> bool:
        """Check if a request is allowed based on token availability."""
        count = self.r.get_key(count_key)
        last_refill = self.r.get_key(refill_key)
        now = datetime.now()
        if count is None:
            self.r.set_key(count_key , "0")
            self.r.set_key(refill_key , now.strftime("%Y-%m-%d %H:%M:%S"))
            return True
        else:
            last_refill_time = datetime.strptime(last_refill , "%Y-%m-%d %H:%M:%S")
            new_count = min(self.max_cap , int(count) + (now - last_refill_time).total_seconds() * self.rate)
            if new_count >= 1:
                new_count -= 1
                self.r.set_key(count_key , str(int(new_count)))
                self.r.set_key(refill_key , now.strftime("%Y-%m-%d %H:%M:%S"))
                return True
            else:
                return False

    @staticmethod
    def create_bucket_count_key(client_id : str) -> str:
        """Create Redis key for token count."""
        return f"rate:limit:{client_id}:count"
    
    @staticmethod
    def create_bucket_last_refill_key(client_id : str) -> str:
        """Create Redis key for last refill timestamp."""
        return f"rate:limit:{client_id}:last_refill"

    def check_limit(self , client_id : str) -> bool:
        """Check if a client is allowed to make a request.
        
        Args:
            client_id: Unique client identifier
            
        Returns:
            True if request is allowed, False otherwise
        """
        count_key = self.create_bucket_count_key(client_id)
        last_refill_key = self.create_bucket_last_refill_key(client_id)
        return self.__is_allowed(count_key , last_refill_key)
