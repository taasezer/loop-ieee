"""
Order model - Order management and tracking
"""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Float, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class OrderStatus(str, enum.Enum):
    """Order status enumeration"""
    CREATED = "created"
    PENDING_ASSIGNMENT = "pending_assignment"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OrderType(str, enum.Enum):
    """Order type enumeration"""
    STANDARD = "standard"
    EXPRESS = "express"
    SCHEDULED = "scheduled"
    RECURRING = "recurring"


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration"""
    CASH = "cash"
    CARD = "card"
    WALLET = "wallet"
    ONLINE = "online"


class Order(Base):
    """Order model"""
    
    __tablename__ = "orders"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Order number (human-readable)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    courier_id = Column(UUID(as_uuid=True), ForeignKey("couriers.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Order details
    order_type = Column(SQLEnum(OrderType), nullable=False, default=OrderType.STANDARD)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.CREATED, index=True)
    
    # Pickup information
    pickup_address = Column(Text, nullable=False)
    pickup_latitude = Column(Float, nullable=False)
    pickup_longitude = Column(Float, nullable=False)
    pickup_contact_name = Column(String(100), nullable=True)
    pickup_contact_phone = Column(String(20), nullable=True)
    pickup_instructions = Column(Text, nullable=True)
    
    # Delivery information
    delivery_address = Column(Text, nullable=False)
    delivery_latitude = Column(Float, nullable=False)
    delivery_longitude = Column(Float, nullable=False)
    delivery_contact_name = Column(String(100), nullable=False)
    delivery_contact_phone = Column(String(20), nullable=False)
    delivery_instructions = Column(Text, nullable=True)
    
    # Package details
    package_description = Column(Text, nullable=True)
    package_weight = Column(Float, nullable=True)  # in kg
    package_dimensions = Column(JSONB, nullable=True, default={})  # length, width, height
    package_value = Column(Float, nullable=True)
    fragile = Column(Boolean, default=False)
    
    # Distance and duration
    distance_km = Column(Float, nullable=True)
    estimated_duration_minutes = Column(Float, nullable=True)
    actual_duration_minutes = Column(Float, nullable=True)
    
    # Pricing
    base_price = Column(Float, nullable=False)
    distance_price = Column(Float, nullable=False, default=0.0)
    surge_multiplier = Column(Float, default=1.0)
    weather_multiplier = Column(Float, default=1.0)
    discount_amount = Column(Float, default=0.0)
    promo_code = Column(String(50), nullable=True)
    tax_amount = Column(Float, default=0.0)
    total_price = Column(Float, nullable=False)
    
    # Payment
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    payment_status = Column(String(50), default="pending")
    payment_transaction_id = Column(String(255), nullable=True)
    
    # Commission
    platform_commission = Column(Float, default=0.0)
    courier_earnings = Column(Float, default=0.0)
    
    # Scheduling
    scheduled_pickup_time = Column(DateTime, nullable=True)
    scheduled_delivery_time = Column(DateTime, nullable=True)
    
    # Recurring order
    is_recurring = Column(Boolean, default=False)
    recurring_pattern = Column(JSONB, nullable=True)  # frequency, days, etc.
    parent_order_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    assigned_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    picked_up_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Cancellation
    cancellation_reason = Column(Text, nullable=True)
    cancelled_by = Column(String(50), nullable=True)  # customer, courier, admin
    
    # Proof of delivery
    proof_of_delivery = Column(JSONB, nullable=True, default={
        "signature": None,
        "photo": None,
        "notes": None
    })
    
    # SLA tracking
    sla_target_minutes = Column(Float, nullable=True)
    sla_met = Column(Boolean, nullable=True)
    
    # Weather conditions at order time
    weather_conditions = Column(JSONB, nullable=True)
    
    # Notes
    customer_notes = Column(Text, nullable=True)
    courier_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True, default={})
    
    # Updated timestamp
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    customer = relationship("User", foreign_keys=[customer_id], back_populates="orders_as_customer")
    courier = relationship("Courier", foreign_keys=[courier_id], back_populates="orders")
    rating = relationship("Rating", back_populates="order", uselist=False, cascade="all, delete-orphan")
    route_history = relationship("RouteHistory", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order {self.order_number} - {self.status}>"
    
    @property
    def is_active(self):
        """Check if order is active"""
        return self.status not in [OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.FAILED]
    
    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.CREATED, OrderStatus.PENDING_ASSIGNMENT, OrderStatus.ASSIGNED]
