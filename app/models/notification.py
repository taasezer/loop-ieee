"""
Notification model - Push notification history
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class NotificationType(str, enum.Enum):
    """Notification type enumeration"""
    ORDER_CREATED = "order_created"
    ORDER_ASSIGNED = "order_assigned"
    ORDER_ACCEPTED = "order_accepted"
    ORDER_PICKED_UP = "order_picked_up"
    ORDER_IN_TRANSIT = "order_in_transit"
    ORDER_DELIVERED = "order_delivered"
    ORDER_CANCELLED = "order_cancelled"
    PAYMENT_RECEIVED = "payment_received"
    PAYOUT_PROCESSED = "payout_processed"
    RATING_RECEIVED = "rating_received"
    SYSTEM_ALERT = "system_alert"
    PROMOTIONAL = "promotional"


class NotificationChannel(str, enum.Enum):
    """Notification channel enumeration"""
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"


class NotificationStatus(str, enum.Enum):
    """Notification status enumeration"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class Notification(Base):
    """Notification model"""
    
    __tablename__ = "notifications"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Notification details
    type = Column(SQLEnum(NotificationType), nullable=False)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    status = Column(SQLEnum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING)
    
    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Additional data
    data = Column(JSONB, nullable=True, default={})
    
    # Related entities
    order_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Delivery tracking
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Float, default=0)
    
    # Priority
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Expiry
    expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification {self.type} to User {self.user_id}>"
