"""
Authentication API endpoints - Full Implementation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.database import get_db
from app.core.security import security
from app.core.exceptions import *
from app.services.auth_service import AuthService
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    RegisterResponse,
    LoginResponse,
    VerifyOTPRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()
security_scheme = HTTPBearer()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user
    
    - **email**: User email address
    - **phone_number**: User phone number
    - **password**: User password (min 8 characters, must contain uppercase, lowercase, and digit)
    - **first_name**: User first name
    - **last_name**: User last name
    - **role**: User role (customer, courier, admin, dispatcher)
    """
    try:
        auth_service = AuthService(db)
        return await auth_service.register(request)
    except ResourceAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    User login
    
    - **email_or_phone**: Email address or phone number
    - **password**: User password
    """
    try:
        auth_service = AuthService(db)
        return await auth_service.login(request)
    except InvalidCredentialsException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    try:
        auth_service = AuthService(db)
        refresh_token = credentials.credentials
        result = await auth_service.refresh_token(refresh_token)
        
        return {
            "access_token": result.access_token,
            "refresh_token": result.refresh_token,
            "token_type": result.token_type,
            "expires_in": result.expires_in
        }
    except (InvalidCredentialsException, TokenExpiredException) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/verify-otp", response_model=dict)
async def verify_otp(
    request: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify OTP for email or phone verification
    """
    try:
        auth_service = AuthService(db)
        success = await auth_service.verify_otp(
            request.user_id,
            request.otp,
            request.verification_type
        )
        
        return {
            "message": "Verification successful",
            "verified": success
        }
    except (ResourceNotFoundException, InvalidCredentialsException, TokenExpiredException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )


@router.post("/resend-otp", response_model=dict)
async def resend_otp(
    user_id: str,
    verification_type: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Resend OTP for verification
    """
    try:
        from uuid import UUID
        auth_service = AuthService(db)
        expires_at = await auth_service.resend_otp(UUID(user_id), verification_type)
        
        return {
            "message": "OTP sent successfully",
            "sent": True,
            "expires_at": expires_at
        }
    except ResourceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Resend OTP error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend OTP"
        )


@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset
    """
    try:
        auth_service = AuthService(db)
        message = await auth_service.forgot_password(request.email)
        
        return {
            "message": message,
            "sent": True
        }
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        # Always return success to prevent email enumeration
        return {
            "message": "If email exists, reset link will be sent",
            "sent": True
        }


@router.post("/reset-password", response_model=dict)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using reset token
    """
    try:
        auth_service = AuthService(db)
        success = await auth_service.reset_password(request.token, request.new_password)
        
        return {
            "message": "Password reset successful",
            "success": success
        }
    except (InvalidCredentialsException, TokenExpiredException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/logout", response_model=dict)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    User logout (invalidate token)
    """
    try:
        auth_service = AuthService(db)
        access_token = credentials.credentials
        success = await auth_service.logout(access_token)
        
        return {
            "message": "Logout successful",
            "success": success
        }
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user information
    """
    try:
        from uuid import UUID
        from app.repositories.user_repository import UserRepository
        
        # Decode token
        token = credentials.credentials
        payload = security.decode_token(token)
        user_id = UUID(payload["user_id"])
        
        # Get user from database
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_orm(user)
    
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
