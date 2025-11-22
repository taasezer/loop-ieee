from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from typing import Callable
import redis.asyncio as redis
from app.config import settings

# Initialize limiter with Redis backend
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=["200/hour"]
)

# Custom rate limit handler
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded"""
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Please try again later.",
            "retry_after": exc.detail
        }
    )

# Pre-defined rate limit decorators for common use cases
def rate_limit_strict(func: Callable):
    """Strict rate limit: 10 requests per minute"""
    return limiter.limit("10/minute")(func)

def rate_limit_moderate(func: Callable):
    """Moderate rate limit: 30 requests per minute"""
    return limiter.limit("30/minute")(func)

def rate_limit_relaxed(func: Callable):
    """Relaxed rate limit: 60 requests per minute"""
    return limiter.limit("60/minute")(func)

def rate_limit_auth(func: Callable):
    """Auth endpoints: 5 requests per minute (prevent brute force)"""
    return limiter.limit("5/minute")(func)
