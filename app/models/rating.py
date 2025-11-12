"""
Rating model - Customer-courier reviews and ratings
"""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Rating(Base):
    """Rating and review model"""
    
    __tablename__ = "ratings"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    courier_id = Column(UUID(as_uuid=True), ForeignKey("couriers.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Rating (1-5 stars)
    rating = Column(Float, nullable=False)
    
    # Detailed ratings
    professionalism_rating = Column(Float, nullable=True)
    speed_rating = Column(Float, nullable=True)
    communication_rating = Column(Float, nullable=True)
    
    # Review text
    review = Column(Text, nullable=True)
    
    # Flags
    is_positive = Column(Boolean, nullable=True)
    is_flagged = Column(Boolean, default=False)
    flagged_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="rating")
    customer = relationship("User", foreign_keys=[customer_id], back_populates="ratings_given")
    courier = relationship("Courier", foreign_keys=[courier_id], back_populates="ratings_received")
    
    def __repr__(self):
        return f"<Rating {self.rating} stars for Order {self.order_id}>"
