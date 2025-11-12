"""
PaymentTransaction model - Payment records and statuses
"""

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class TransactionType(str, enum.Enum):
    """Transaction type enumeration"""
    PAYMENT = "payment"
    REFUND = "refund"
    PAYOUT = "payout"
    ADJUSTMENT = "adjustment"


class TransactionStatus(str, enum.Enum):
    """Transaction status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentGateway(str, enum.Enum):
    """Payment gateway enumeration"""
    STRIPE = "stripe"
    IYZICO = "iyzico"
    PAYTR = "paytr"
    CASH = "cash"
    WALLET = "wallet"


class PaymentTransaction(Base):
    """Payment transaction model"""
    
    __tablename__ = "payment_transactions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Transaction reference
    transaction_reference = Column(String(100), unique=True, index=True, nullable=False)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Transaction details
    type = Column(SQLEnum(TransactionType), nullable=False)
    status = Column(SQLEnum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    gateway = Column(SQLEnum(PaymentGateway), nullable=False)
    
    # Amount
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    
    # Gateway specific
    gateway_transaction_id = Column(String(255), nullable=True)
    gateway_response = Column(JSONB, nullable=True)
    
    # Payment method details
    payment_method_type = Column(String(50), nullable=True)  # card, bank_transfer, etc.
    payment_method_details = Column(JSONB, nullable=True)  # last4, brand, etc.
    
    # Fees
    gateway_fee = Column(Float, default=0.0)
    platform_fee = Column(Float, default=0.0)
    net_amount = Column(Float, nullable=False)
    
    # Refund information
    refund_amount = Column(Float, default=0.0)
    refund_reason = Column(Text, nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default={})
    
    # Error tracking
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="payment_transactions")
    
    def __repr__(self):
        return f"<PaymentTransaction {self.transaction_reference} - {self.status}>"
