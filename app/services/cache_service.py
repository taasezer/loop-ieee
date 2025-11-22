import redis.asyncio as redis
from typing import Optional, Any, Callable
from datetime import timedelta
import json
from functools import wraps
from app.config import settings

class CacheService:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = 300  # 5 minutes
    
    async def connect(self):
        """Initialize Redis connection"""
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            await self.connect()
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL"""
        if not self.redis_client:
            await self.connect()
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value)
            await self.redis_client.setex(
                key,
                ttl,
                serialized_value
            )
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            await self.connect()
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> bool:
        """Delete all keys matching pattern"""
        if not self.redis_client:
            await self.connect()
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
            return True
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            await self.connect()
        
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        if not self.redis_client:
            await self.connect()
        
        try:
            return await self.redis_client.incrby(key, amount)
        except Exception as e:
            print(f"Cache increment error: {e}")
            return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on existing key"""
        if not self.redis_client:
            await self.connect()
        
        try:
            await self.redis_client.expire(key, ttl)
            return True
        except Exception as e:
            print(f"Cache expire error: {e}")
            return False

# Global cache service instance
cache_service = CacheService()


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function args"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    return ":".join(key_parts)


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching async function results
    
    Usage:
        @cached(ttl=600, key_prefix="weather")
        async def get_weather(lat, lon):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            func_name = f"{key_prefix}:{func.__name__}" if key_prefix else func.__name__
            key = f"{func_name}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = await cache_service.get(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            if result is not None:
                await cache_service.set(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
