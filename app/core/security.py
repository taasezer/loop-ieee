"""
Security utilities for authentication and authorization
Includes JWT token handling, password hashing, and OTP generation
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import string

from app.config import settings
from app.core.exceptions import (
    InvalidTokenException,
    TokenExpiredException,
    AuthenticationException
)


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityUtils:
    """Security utility functions"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token
        
        Args:
            data: Data to encode in the token
            expires_delta: Token expiration time
            
        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token
        
        Args:
            data: Data to encode in the token
            expires_delta: Token expiration time
            
        Returns:
            str: Encoded JWT refresh token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Dict[str, Any]: Decoded token payload
            
        Raises:
            InvalidTokenException: If token is invalid
            TokenExpiredException: If token has expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredException("Token has expired")
        except JWTError:
            raise InvalidTokenException("Invalid token")
    
    @staticmethod
    def generate_otp(length: Optional[int] = None) -> str:
        """
        Generate a random OTP (One-Time Password)
        
        Args:
            length: Length of OTP (default from settings)
            
        Returns:
            str: Generated OTP
        """
        if length is None:
            length = settings.OTP_LENGTH
        
        digits = string.digits
        otp = ''.join(secrets.choice(digits) for _ in range(length))
        return otp
    
    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """
        Generate a secure random API key
        
        Args:
            length: Length of the API key
            
        Returns:
            str: Generated API key
        """
        characters = string.ascii_letters + string.digits
        api_key = ''.join(secrets.choice(characters) for _ in range(length))
        return api_key
    
    @staticmethod
    def generate_reset_token() -> str:
        """
        Generate a password reset token
        
        Returns:
            str: Reset token
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
        """
        Verify that the token is of the expected type
        
        Args:
            payload: Decoded token payload
            expected_type: Expected token type ('access' or 'refresh')
            
        Returns:
            bool: True if token type matches
        """
        token_type = payload.get("type")
        return token_type == expected_type


# Create singleton instance
security = SecurityUtils()
