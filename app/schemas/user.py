"""
User Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.user import UserRole, UserStatus


# Base schemas
class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    phone_number: str = Field(..., min_length=10, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


# Request schemas
class UserRegisterRequest(UserBase):
    """User registration request"""
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.CUSTOMER
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLoginRequest(BaseModel):
    """User login request"""
    email_or_phone: str
    password: str


class UserUpdateRequest(BaseModel):
    """User update request"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    profile_image: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, bool]] = None


class VerifyOTPRequest(BaseModel):
    """OTP verification request"""
    user_id: UUID
    otp: str = Field(..., min_length=4, max_length=10)
    verification_type: str = Field(..., regex="^(email|phone)$")


class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


# Response schemas
class UserResponse(BaseModel):
    """User response schema"""
    id: UUID
    email: EmailStr
    phone_number: str
    first_name: str
    last_name: str
    profile_image: Optional[str]
    role: UserRole
    status: UserStatus
    email_verified: bool
    phone_verified: bool
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserBasicResponse(BaseModel):
    """Basic user info for nested responses"""
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    profile_image: Optional[str]
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class LoginResponse(BaseModel):
    """Login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RegisterResponse(BaseModel):
    """Registration response"""
    message: str
    user_id: UUID
    email_sent: bool
    sms_sent: bool


class OTPResponse(BaseModel):
    """OTP response"""
    message: str
    sent: bool
    expires_at: datetime


class VerificationResponse(BaseModel):
    """Verification response"""
    message: str
    verified: bool


class UserListResponse(BaseModel):
    """User list response"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


class UserStatsResponse(BaseModel):
    """User statistics response"""
    total_users: int
    active_users: int
    verified_users: int
    customers: int
    couriers: int
    admins: int
