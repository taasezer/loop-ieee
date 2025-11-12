"""
Custom Exception Classes for LOOP Application
"""

from typing import Optional, Any
from fastapi import status


class LoopException(Exception):
    """Base exception class for LOOP application"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "LOOP_ERROR",
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


# Authentication Exceptions
class AuthenticationException(LoopException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_FAILED",
            details=details
        )


class InvalidCredentialsException(LoopException):
    """Invalid credentials provided"""
    def __init__(self, message: str = "Invalid credentials", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_CREDENTIALS",
            details=details
        )


class TokenExpiredException(LoopException):
    """JWT token has expired"""
    def __init__(self, message: str = "Token has expired", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="TOKEN_EXPIRED",
            details=details
        )


class InvalidTokenException(LoopException):
    """Invalid JWT token"""
    def __init__(self, message: str = "Invalid token", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_TOKEN",
            details=details
        )


# Authorization Exceptions
class AuthorizationException(LoopException):
    """User not authorized for this action"""
    def __init__(self, message: str = "Not authorized", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="NOT_AUTHORIZED",
            details=details
        )


class InsufficientPermissionsException(LoopException):
    """User lacks required permissions"""
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="INSUFFICIENT_PERMISSIONS",
            details=details
        )


# Resource Exceptions
class ResourceNotFoundException(LoopException):
    """Requested resource not found"""
    def __init__(self, resource: str = "Resource", details: Optional[Any] = None):
        super().__init__(
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details=details
        )


class ResourceAlreadyExistsException(LoopException):
    """Resource already exists"""
    def __init__(self, resource: str = "Resource", details: Optional[Any] = None):
        super().__init__(
            message=f"{resource} already exists",
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_ALREADY_EXISTS",
            details=details
        )


class ResourceConflictException(LoopException):
    """Resource conflict"""
    def __init__(self, message: str = "Resource conflict", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_CONFLICT",
            details=details
        )


# Validation Exceptions
class ValidationException(LoopException):
    """Validation error"""
    def __init__(self, message: str = "Validation failed", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )


class InvalidInputException(LoopException):
    """Invalid input data"""
    def __init__(self, message: str = "Invalid input", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_INPUT",
            details=details
        )


# Business Logic Exceptions
class OrderException(LoopException):
    """Order-related error"""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="ORDER_ERROR",
            details=details
        )


class CourierException(LoopException):
    """Courier-related error"""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="COURIER_ERROR",
            details=details
        )


class PaymentException(LoopException):
    """Payment-related error"""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            error_code="PAYMENT_ERROR",
            details=details
        )


class PricingException(LoopException):
    """Pricing calculation error"""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="PRICING_ERROR",
            details=details
        )


# External Service Exceptions
class ExternalServiceException(LoopException):
    """External service error"""
    def __init__(self, service: str, message: str = "Service unavailable", details: Optional[Any] = None):
        super().__init__(
            message=f"{service}: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details
        )


class MapServiceException(LoopException):
    """Map service error"""
    def __init__(self, message: str = "Map service error", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="MAP_SERVICE_ERROR",
            details=details
        )


class WeatherServiceException(LoopException):
    """Weather service error"""
    def __init__(self, message: str = "Weather service error", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="WEATHER_SERVICE_ERROR",
            details=details
        )


class NotificationException(LoopException):
    """Notification service error"""
    def __init__(self, message: str = "Notification failed", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="NOTIFICATION_ERROR",
            details=details
        )


# Rate Limiting Exceptions
class RateLimitExceededException(LoopException):
    """Rate limit exceeded"""
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )


# Database Exceptions
class DatabaseException(LoopException):
    """Database error"""
    def __init__(self, message: str = "Database error", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details=details
        )


# Cache Exceptions
class CacheException(LoopException):
    """Cache error"""
    def __init__(self, message: str = "Cache error", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="CACHE_ERROR",
            details=details
        )
