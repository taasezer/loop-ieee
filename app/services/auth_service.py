"""
Authentication service
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import secrets

from app.models.user import User, UserStatus
from app.repositories.user_repository import UserRepository
from app.core.security import security
from app.core.cache import cache
from app.core.exceptions import (
    InvalidCredentialsException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    ValidationException,
    TokenExpiredException
)
from app.config import settings
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    LoginResponse,
    RegisterResponse,
    TokenResponse
)
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def register(self, request: UserRegisterRequest) -> RegisterResponse:
        """Register a new user"""
        logger.info(f"Registering new user: {request.email}")
        
        # Check if email already exists
        if await self.user_repo.email_exists(request.email):
            raise ResourceAlreadyExistsException("User with this email")
        
        # Check if phone already exists
        if await self.user_repo.phone_exists(request.phone_number):
            raise ResourceAlreadyExistsException("User with this phone number")
        
        # Hash password
        password_hash = security.hash_password(request.password)
        
        # Generate OTP for verification
        email_otp = security.generate_otp()
        phone_otp = security.generate_otp()
        otp_expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        
        # Create user
        user_data = {
            "email": request.email,
            "phone_number": request.phone_number,
            "password_hash": password_hash,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "role": request.role,
            "status": UserStatus.PENDING_VERIFICATION,
            "email_verification_token": email_otp,
            "phone_verification_otp": phone_otp,
            "otp_expires_at": otp_expires_at
        }
        
        user = await self.user_repo.create(user_data)
        await self.db.commit()
        
        # TODO: Send verification email and SMS
        # await notification_service.send_verification_email(user.email, email_otp)
        # await notification_service.send_verification_sms(user.phone_number, phone_otp)
        
        logger.info(f"User registered successfully: {user.id}")
        
        return RegisterResponse(
            message="Registration successful. Please verify your email and phone.",
            user_id=user.id,
            email_sent=True,
            sms_sent=True
        )
    
    async def login(self, request: UserLoginRequest) -> LoginResponse:
        """Login user"""
        logger.info(f"Login attempt: {request.email_or_phone}")
        
        # Find user by email or phone
        user = await self.user_repo.get_by_email_or_phone(request.email_or_phone)
        
        if not user:
            raise InvalidCredentialsException("Invalid email/phone or password")
        
        # Verify password
        if not security.verify_password(request.password, user.password_hash):
            raise InvalidCredentialsException("Invalid email/phone or password")
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            raise ValidationException(f"Account is {user.status.value}. Please verify your account.")
        
        # Generate tokens
        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.value
        }
        
        access_token = security.create_access_token(token_data)
        refresh_token = security.create_refresh_token({"user_id": str(user.id)})
        
        # Update last login
        await self.user_repo.update(user.id, {
            "last_login_at": datetime.utcnow(),
            "last_login_ip": "0.0.0.0"  # TODO: Get real IP from request
        })
        await self.db.commit()
        
        logger.info(f"User logged in successfully: {user.id}")
        
        from app.schemas.user import UserResponse
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
    
    async def verify_otp(self, user_id: UUID, otp: str, verification_type: str) -> bool:
        """Verify OTP"""
        logger.info(f"Verifying OTP for user: {user_id}")
        
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User")
        
        # Check if OTP expired
        if user.otp_expires_at and user.otp_expires_at < datetime.utcnow():
            raise TokenExpiredException("OTP has expired")
        
        # Verify OTP based on type
        if verification_type == "email":
            if user.email_verification_token != otp:
                raise InvalidCredentialsException("Invalid OTP")
            
            await self.user_repo.update(user.id, {
                "email_verified": True,
                "email_verification_token": None,
                "status": UserStatus.ACTIVE if user.phone_verified else user.status
            })
        
        elif verification_type == "phone":
            if user.phone_verification_otp != otp:
                raise InvalidCredentialsException("Invalid OTP")
            
            await self.user_repo.update(user.id, {
                "phone_verified": True,
                "phone_verification_otp": None,
                "status": UserStatus.ACTIVE if user.email_verified else user.status
            })
        
        await self.db.commit()
        logger.info(f"OTP verified successfully for user: {user_id}")
        return True
    
    async def resend_otp(self, user_id: UUID, verification_type: str) -> datetime:
        """Resend OTP"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User")
        
        new_otp = security.generate_otp()
        otp_expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        
        if verification_type == "email":
            await self.user_repo.update(user.id, {
                "email_verification_token": new_otp,
                "otp_expires_at": otp_expires_at
            })
            # TODO: Send email
        else:
            await self.user_repo.update(user.id, {
                "phone_verification_otp": new_otp,
                "otp_expires_at": otp_expires_at
            })
            # TODO: Send SMS
        
        await self.db.commit()
        return otp_expires_at
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token"""
        try:
            payload = security.decode_token(refresh_token)
            
            if not security.verify_token_type(payload, "refresh"):
                raise InvalidCredentialsException("Invalid token type")
            
            user_id = UUID(payload["user_id"])
            user = await self.user_repo.get_by_id(user_id)
            
            if not user:
                raise ResourceNotFoundException("User")
            
            token_data = {
                "user_id": str(user.id),
                "email": user.email,
                "role": user.role.value
            }
            
            new_access_token = security.create_access_token(token_data)
            
            from app.schemas.user import UserResponse
            return TokenResponse(
                access_token=new_access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=UserResponse.from_orm(user)
            )
        
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise InvalidCredentialsException("Invalid or expired refresh token")
    
    async def logout(self, access_token: str) -> bool:
        """Logout user (blacklist token)"""
        try:
            payload = security.decode_token(access_token)
            token_exp = payload.get("exp")
            
            # Calculate TTL for blacklist
            ttl = token_exp - int(datetime.utcnow().timestamp())
            
            if ttl > 0:
                # Add token to blacklist
                await cache.set(
                    f"blacklist:{access_token}",
                    "true",
                    expire=ttl,
                    db="cache"
                )
            
            return True
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return False
    
    async def forgot_password(self, email: str) -> str:
        """Generate password reset token"""
        user = await self.user_repo.get_by_email(email)
        if not user:
            # Don't reveal if email exists
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return "If email exists, reset link will be sent"
        
        reset_token = security.generate_reset_token()
        reset_expires_at = datetime.utcnow() + timedelta(hours=1)
        
        await self.user_repo.update(user.id, {
            "reset_token": reset_token,
            "reset_token_expires_at": reset_expires_at
        })
        await self.db.commit()
        
        # TODO: Send reset email
        logger.info(f"Password reset token generated for user: {user.id}")
        return "Password reset email sent"
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token"""
        # Find user by reset token
        users = await self.user_repo.get_all(filters={"reset_token": token})
        
        if not users:
            raise InvalidCredentialsException("Invalid or expired reset token")
        
        user = users[0]
        
        # Check if token expired
        if user.reset_token_expires_at < datetime.utcnow():
            raise TokenExpiredException("Reset token has expired")
        
        # Update password
        password_hash = security.hash_password(new_password)
        await self.user_repo.update(user.id, {
            "password_hash": password_hash,
            "reset_token": None,
            "reset_token_expires_at": None
        })
        await self.db.commit()
        
        logger.info(f"Password reset successfully for user: {user.id}")
        return True
