import redis
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class RedisStore():
    """Redis store for persisting token bucket state."""
    
    def __init__(self):
        self.__r = self.__connect_redis()

    def __connect_redis(self) -> redis.Redis:
        """Connect to Redis instance."""
        try:
            r = redis.Redis(host='localhost',
                            port=6379,
                            db=0,
                            decode_responses=True)
            logger.info("redis connected !")
            return r
        except Exception as e:
            logger.error(f"redis connection error : {str(e)}")
            raise

    def get_key(self , key : str) -> Optional[str]:
        """Get value from Redis.
        
        Args:
            key: Redis key
            
        Returns:
            Value if key exists, None otherwise
        """
        return self.__r.get(key)
    
    def set_key(self , key : str , value : str) -> bool:
        """Set value in Redis.
        
        Args:
            key: Redis key
            value: Value to set
            
        Returns:
            True if successful
        """
        return self.__r.set(key , value)
