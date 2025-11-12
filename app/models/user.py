"""
User model - Multi-role user system
Supports customer, courier, admin, and dispatcher roles
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    CUSTOMER = "customer"
    COURIER = "courier"
    ADMIN = "admin"
    DISPATCHER = "dispatcher"


class UserStatus(str, enum.Enum):
    """User status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class User(Base):
    """User model"""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Profile fields
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    profile_image = Column(String(500), nullable=True)
    
    # Role and status
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.PENDING_VERIFICATION)
    
    # Verification fields
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)
    phone_verification_otp = Column(String(10), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    
    # Password reset
    reset_token = Column(String(255), nullable=True)
    reset_token_expires_at = Column(DateTime, nullable=True)
    
    # Additional info
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Preferences and settings
    preferences = Column(JSONB, nullable=True, default={})
    notification_settings = Column(JSONB, nullable=True, default={
        "email": True,
        "sms": True,
        "push": True
    })
    
    # Device tokens for push notifications
    device_tokens = Column(JSONB, nullable=True, default=[])
    
    # Social login
    google_id = Column(String(255), unique=True, nullable=True)
    apple_id = Column(String(255), unique=True, nullable=True)
    
    # Two-factor authentication
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255), nullable=True)
    
    # Session management
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    
    # Relationships
    courier = relationship("Courier", back_populates="user", uselist=False, cascade="all, delete-orphan")
    orders_as_customer = relationship("Order", foreign_keys="Order.customer_id", back_populates="customer")
    ratings_given = relationship("Rating", foreign_keys="Rating.customer_id", back_populates="customer")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    payment_transactions = relationship("PaymentTransaction", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
    
    @property
    def full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self):
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE
    
    @property
    def is_verified(self):
        """Check if user is verified"""
        return self.email_verified and self.phone_verified
