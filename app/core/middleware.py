"""
Custom middleware for the application
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
from typing import Callable

from app.config import settings
from app.core.cache import cache
from app.core.exceptions import RateLimitExceededException

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details"""
        
        # Start timer
        start_time = time.time()
        
        # Get request details
        request_id = request.headers.get("X-Request-ID", "N/A")
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request failed: {str(e)}", exc_info=True)
            raise
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting based on IP address"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit before processing request"""
        
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Rate limit keys
        minute_key = f"rate_limit:minute:{client_ip}"
        hour_key = f"rate_limit:hour:{client_ip}"
        
        try:
            # Check minute limit
            minute_count = await cache.increment(minute_key)
            if minute_count == 1:
                await cache.expire(minute_key, 60)
            
            if minute_count > settings.RATE_LIMIT_PER_MINUTE:
                logger.warning(f"Rate limit exceeded for IP: {client_ip} (per minute)")
                raise RateLimitExceededException(
                    f"Rate limit exceeded: {settings.RATE_LIMIT_PER_MINUTE} requests per minute"
                )
            
            # Check hour limit
            hour_count = await cache.increment(hour_key)
            if hour_count == 1:
                await cache.expire(hour_key, 3600)
            
            if hour_count > settings.RATE_LIMIT_PER_HOUR:
                logger.warning(f"Rate limit exceeded for IP: {client_ip} (per hour)")
                raise RateLimitExceededException(
                    f"Rate limit exceeded: {settings.RATE_LIMIT_PER_HOUR} requests per hour"
                )
            
        except RateLimitExceededException:
            raise
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            # Continue processing if rate limit check fails
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Limit-Hour"] = str(settings.RATE_LIMIT_PER_HOUR)
        
        try:
            remaining_minute = settings.RATE_LIMIT_PER_MINUTE - minute_count
            remaining_hour = settings.RATE_LIMIT_PER_HOUR - hour_count
            response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, remaining_minute))
            response.headers["X-RateLimit-Remaining-Hour"] = str(max(0, remaining_hour))
        except:
            pass
        
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware (if needed beyond FastAPI's built-in)"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle CORS"""
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response
        
        # Process request
        response = await call_next(request)
        
        return response
