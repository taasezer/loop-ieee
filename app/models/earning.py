"""
Earning model - Courier earnings tracking
"""

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class EarningStatus(str, enum.Enum):
    """Earning status enumeration"""
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class Earning(Base):
    """Courier earnings model"""
    
    __tablename__ = "earnings"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    courier_id = Column(UUID(as_uuid=True), ForeignKey("couriers.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    
    # Earning details
    order_amount = Column(Float, nullable=False)
    platform_commission = Column(Float, nullable=False)
    courier_earning = Column(Float, nullable=False)
    
    # Bonuses and incentives
    bonus_amount = Column(Float, default=0.0)
    incentive_amount = Column(Float, default=0.0)
    
    # Total
    total_earning = Column(Float, nullable=False)
    
    # Status
    status = Column(SQLEnum(EarningStatus), nullable=False, default=EarningStatus.PENDING)
    
    # Payout information
    payout_date = Column(DateTime, nullable=True)
    payout_method = Column(String(50), nullable=True)
    payout_reference = Column(String(255), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    courier = relationship("Courier", back_populates="earnings")
    
    def __repr__(self):
        return f"<Earning {self.id} - {self.courier_earning}>"
