"""
Location model - Real-time courier location tracking
"""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Location(Base):
    """Location tracking model"""
    
    __tablename__ = "locations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to courier
    courier_id = Column(UUID(as_uuid=True), ForeignKey("couriers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Location coordinates
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Accuracy and speed
    accuracy = Column(Float, nullable=True)  # in meters
    speed = Column(Float, nullable=True)  # in km/h
    heading = Column(Float, nullable=True)  # in degrees
    altitude = Column(Float, nullable=True)  # in meters
    
    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    courier = relationship("Courier", back_populates="locations")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_courier_recorded', 'courier_id', 'recorded_at'),
    )
    
    def __repr__(self):
        return f"<Location {self.courier_id} at ({self.latitude}, {self.longitude})>"
