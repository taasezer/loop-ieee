"""
Redis cache manager for caching and session management
"""

import redis.asyncio as redis
from typing import Optional, Any
import json
import logging
from datetime import timedelta

from app.config import settings
from app.core.exceptions import CacheException

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.cache_db_client: Optional[redis.Redis] = None
        self.session_db_client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Initialize Redis connections"""
        try:
            # Main Redis connection
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Cache database connection
            cache_url = settings.REDIS_URL.rsplit('/', 1)[0] + f"/{settings.REDIS_CACHE_DB}"
            self.cache_db_client = await redis.from_url(
                cache_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Session database connection
            session_url = settings.REDIS_URL.rsplit('/', 1)[0] + f"/{settings.REDIS_SESSION_DB}"
            self.session_db_client = await redis.from_url(
                session_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connections
            await self.redis_client.ping()
            await self.cache_db_client.ping()
            await self.session_db_client.ping()
            
            logger.info("Redis connections established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise CacheException(f"Redis connection failed: {str(e)}")
    
    async def disconnect(self):
        """Close Redis connections"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            if self.cache_db_client:
                await self.cache_db_client.close()
            if self.session_db_client:
                await self.session_db_client.close()
            
            logger.info("Redis connections closed")
            
        except Exception as e:
            logger.error(f"Error closing Redis connections: {str(e)}")
    
    async def get(self, key: str, db: str = "cache") -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            db: Database to use ('cache' or 'session')
            
        Returns:
            Cached value or None
        """
        try:
            client = self.cache_db_client if db == "cache" else self.session_db_client
            value = await client.get(key)
            
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        db: str = "cache"
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds
            db: Database to use ('cache' or 'session')
            
        Returns:
            bool: True if successful
        """
        try:
            client = self.cache_db_client if db == "cache" else self.session_db_client
            
            # Serialize value if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            if expire:
                await client.setex(key, expire, value)
            else:
                await client.set(key, value)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str, db: str = "cache") -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
            db: Database to use ('cache' or 'session')
            
        Returns:
            bool: True if successful
        """
        try:
            client = self.cache_db_client if db == "cache" else self.session_db_client
            await client.delete(key)
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    async def exists(self, key: str, db: str = "cache") -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
            db: Database to use ('cache' or 'session')
            
        Returns:
            bool: True if key exists
        """
        try:
            client = self.cache_db_client if db == "cache" else self.session_db_client
            return await client.exists(key) > 0
            
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False
    
    async def increment(self, key: str, amount: int = 1, db: str = "cache") -> int:
        """
        Increment a counter in cache
        
        Args:
            key: Cache key
            amount: Amount to increment
            db: Database to use ('cache' or 'session')
            
        Returns:
            int: New value after increment
        """
        try:
            client = self.cache_db_client if db == "cache" else self.session_db_client
            return await client.incrby(key, amount)
            
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {str(e)}")
            return 0
    
    async def expire(self, key: str, seconds: int, db: str = "cache") -> bool:
        """
        Set expiration time for a key
        
        Args:
            key: Cache key
            seconds: Expiration time in seconds
            db: Database to use ('cache' or 'session')
            
        Returns:
            bool: True if successful
        """
        try:
            client = self.cache_db_client if db == "cache" else self.session_db_client
            return await client.expire(key, seconds)
            
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {str(e)}")
            return False
    
    async def flush_db(self, db: str = "cache"):
        """
        Flush all keys from database (use with caution!)
        
        Args:
            db: Database to flush ('cache' or 'session')
        """
        try:
            client = self.cache_db_client if db == "cache" else self.session_db_client
            await client.flushdb()
            logger.warning(f"Flushed {db} database")
            
        except Exception as e:
            logger.error(f"Cache flush error: {str(e)}")
    
    async def get_pattern(self, pattern: str, db: str = "cache") -> list:
        """
        Get all keys matching a pattern
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            db: Database to use ('cache' or 'session')
            
        Returns:
            list: List of matching keys
        """
        try:
            client = self.cache_db_client if db == "cache" else self.session_db_client
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            return keys
            
        except Exception as e:
            logger.error(f"Cache get_pattern error: {str(e)}")
            return []
    
    async def health_check(self) -> bool:
        """
        Check if Redis is healthy
        
        Returns:
            bool: True if healthy
        """
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False


# Create cache manager instance
cache = CacheManager()


async def get_cache() -> CacheManager:
    """
    Dependency function to get cache manager
    
    Returns:
        CacheManager: Cache manager instance
    """
    return cache
