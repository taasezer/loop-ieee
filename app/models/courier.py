"""
Courier model - Courier profiles and vehicle information
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class VehicleType(str, enum.Enum):
    """Vehicle type enumeration"""
    BICYCLE = "bicycle"
    MOTORCYCLE = "motorcycle"
    CAR = "car"
    VAN = "van"
    TRUCK = "truck"
    SCOOTER = "scooter"
    ON_FOOT = "on_foot"


class CourierStatus(str, enum.Enum):
    """Courier status enumeration"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ON_BREAK = "on_break"


class VerificationStatus(str, enum.Enum):
    """Verification status enumeration"""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Courier(Base):
    """Courier model"""
    
    __tablename__ = "couriers"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Vehicle information
    vehicle_type = Column(SQLEnum(VehicleType), nullable=False)
    vehicle_make = Column(String(100), nullable=True)
    vehicle_model = Column(String(100), nullable=True)
    vehicle_year = Column(String(4), nullable=True)
    vehicle_color = Column(String(50), nullable=True)
    license_plate = Column(String(20), nullable=True)
    
    # Status and availability
    status = Column(SQLEnum(CourierStatus), nullable=False, default=CourierStatus.OFFLINE)
    is_available = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Current location (latest)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    last_location_update = Column(DateTime, nullable=True)
    
    # Verification
    verification_status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING)
    identity_verified = Column(Boolean, default=False)
    background_check_completed = Column(Boolean, default=False)
    
    # Documents
    driver_license_number = Column(String(50), nullable=True)
    driver_license_expiry = Column(DateTime, nullable=True)
    insurance_number = Column(String(100), nullable=True)
    insurance_expiry = Column(DateTime, nullable=True)
    
    # Document files (stored as URLs or paths)
    documents = Column(JSONB, nullable=True, default={
        "driver_license": None,
        "vehicle_registration": None,
        "insurance": None,
        "profile_photo": None,
        "background_check": None
    })
    
    # Performance metrics
    total_deliveries = Column(Float, default=0)
    successful_deliveries = Column(Float, default=0)
    cancelled_deliveries = Column(Float, default=0)
    average_rating = Column(Float, default=0.0)
    total_ratings = Column(Float, default=0)
    
    # Performance score (calculated by AI)
    performance_score = Column(Float, default=0.0)
    
    # Earnings
    total_earnings = Column(Float, default=0.0)
    pending_earnings = Column(Float, default=0.0)
    
    # Working hours and shifts
    working_hours = Column(JSONB, nullable=True, default={})
    shift_start = Column(DateTime, nullable=True)
    shift_end = Column(DateTime, nullable=True)
    
    # Break management
    on_break = Column(Boolean, default=False)
    break_start = Column(DateTime, nullable=True)
    
    # Service area (geofencing)
    service_radius_km = Column(Float, default=50.0)
    service_areas = Column(JSONB, nullable=True, default=[])
    
    # Capacity and limits
    max_concurrent_orders = Column(Float, default=1)
    current_order_count = Column(Float, default=0)
    
    # Preferences
    preferences = Column(JSONB, nullable=True, default={
        "auto_accept": False,
        "preferred_order_types": [],
        "min_order_value": 0
    })
    
    # Bank account for payouts
    bank_account_info = Column(JSONB, nullable=True, default={})
    
    # Emergency contact
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    
    # Notes (admin use)
    admin_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    last_active_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="courier")
    orders = relationship("Order", foreign_keys="Order.courier_id", back_populates="courier")
    locations = relationship("Location", back_populates="courier", cascade="all, delete-orphan")
    earnings = relationship("Earning", back_populates="courier", cascade="all, delete-orphan")
    ratings_received = relationship("Rating", foreign_keys="Rating.courier_id", back_populates="courier")
    route_history = relationship("RouteHistory", back_populates="courier", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Courier {self.id} - {self.vehicle_type} - {self.status}>"
    
    @property
    def success_rate(self):
        """Calculate delivery success rate"""
        if self.total_deliveries == 0:
            return 0.0
        return (self.successful_deliveries / self.total_deliveries) * 100
    
    @property
    def is_online(self):
        """Check if courier is online"""
        return self.status == CourierStatus.ONLINE
    
    @property
    def is_verified(self):
        """Check if courier is verified"""
        return self.verification_status == VerificationStatus.VERIFIED
