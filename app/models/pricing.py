"""
Pricing model - Dynamic pricing rules and configurations
"""

from sqlalchemy import Column, String, DateTime, Float, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from app.core.database import Base


class Pricing(Base):
    """Pricing rules model"""
    
    __tablename__ = "pricing"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Rule name and description
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Base pricing
    base_price = Column(Float, nullable=False)
    price_per_km = Column(Float, nullable=False)
    price_per_minute = Column(Float, nullable=True, default=0.0)
    
    # Minimum and maximum prices
    min_price = Column(Float, nullable=True)
    max_price = Column(Float, nullable=True)
    
    # Surge pricing
    surge_enabled = Column(Boolean, default=True)
    surge_multiplier_min = Column(Float, default=1.0)
    surge_multiplier_max = Column(Float, default=3.0)
    
    # Weather-based pricing
    weather_multiplier_enabled = Column(Boolean, default=True)
    bad_weather_multiplier = Column(Float, default=1.2)
    
    # Time-based pricing
    peak_hours_enabled = Column(Boolean, default=True)
    peak_hours = Column(JSONB, nullable=True, default=[])  # [{start: "08:00", end: "10:00", multiplier: 1.3}]
    
    # Distance-based tiers
    distance_tiers = Column(JSONB, nullable=True, default=[])  # [{max_km: 5, price_per_km: 2.5}, ...]
    
    # Vehicle type pricing
    vehicle_type_multipliers = Column(JSONB, nullable=True, default={
        "bicycle": 0.8,
        "motorcycle": 1.0,
        "car": 1.2,
        "van": 1.5,
        "truck": 2.0
    })
    
    # Commission rates
    platform_commission_percent = Column(Float, default=20.0)
    
    # Tax
    tax_percent = Column(Float, default=0.0)
    
    # Active status
    is_active = Column(Boolean, default=True)
    
    # Geographic area (optional)
    applicable_areas = Column(JSONB, nullable=True, default=[])
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Pricing {self.name}>"
