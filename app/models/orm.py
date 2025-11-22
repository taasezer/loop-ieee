from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum, JSON, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    COURIER = "courier"
    ADMIN = "admin"
    DISPATCHER = "dispatcher"

class OrderStatus(str, enum.Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class VehicleType(str, enum.Enum):
    MOTORCYCLE = "motorcycle"
    CAR = "car"
    VAN = "van"
    BICYCLE = "bicycle"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    courier_profile = relationship("Courier", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="customer")
    ratings_given = relationship("Rating", back_populates="reviewer")
    notifications = relationship("Notification", back_populates="user")

class Courier(Base):
    __tablename__ = "couriers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    vehicle_type = Column(String, default=VehicleType.MOTORCYCLE)
    vehicle_plate = Column(String, nullable=True)
    is_online = Column(Boolean, default=False)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    last_location_update = Column(DateTime(timezone=True), nullable=True)
    rating = Column(Float, default=5.0)
    
    user = relationship("User", back_populates="courier_profile")
    assigned_orders = relationship("Order", back_populates="courier")
    earnings = relationship("Earning", back_populates="courier")
    ratings_received = relationship("Rating", back_populates="courier")
    route_history = relationship("RouteHistory", back_populates="courier")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    
    status = Column(String, default=OrderStatus.CREATED)
    
    pickup_address = Column(String, nullable=False)
    pickup_latitude = Column(Float, nullable=False)
    pickup_longitude = Column(Float, nullable=False)
    
    delivery_address = Column(String, nullable=False)
    delivery_latitude = Column(Float, nullable=False)
    delivery_longitude = Column(Float, nullable=False)
    
    price = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=True)
    estimated_duration_mins = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    customer = relationship("User", back_populates="orders")
    courier = relationship("Courier", back_populates="assigned_orders")
    payment = relationship("PaymentTransaction", back_populates="order", uselist=False)
    rating = relationship("Rating", back_populates="order", uselist=False)

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class PricingRule(Base):
    __tablename__ = "pricing_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    base_price = Column(Float, default=10.0)
    price_per_km = Column(Float, default=2.0)
    surge_multiplier = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)

class Earning(Base):
    __tablename__ = "earnings"

    id = Column(Integer, primary_key=True, index=True)
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    courier = relationship("Courier", back_populates="earnings")

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Customer
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=False)
    score = Column(Integer, nullable=False) # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    reviewer = relationship("User", back_populates="ratings_given")
    courier = relationship("Courier", back_populates="ratings_received")
    order = relationship("Order", back_populates="rating")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="notifications")

class RouteHistory(Base):
    __tablename__ = "route_history"

    id = Column(Integer, primary_key=True, index=True)
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=False)
    route_data = Column(JSON, nullable=False) # Store GeoJSON or list of points
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    courier = relationship("Courier", back_populates="route_history")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="TRY")
    status = Column(String, default="pending") # pending, success, failed
    provider_transaction_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    order = relationship("Order", back_populates="payment")

class PromotionCode(Base):
    __tablename__ = "promotion_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    discount_type = Column(String, nullable=False)  # "percentage" or "fixed"
    discount_value = Column(Float, nullable=False)
    max_discount = Column(Float, nullable=True)
    min_order_amount = Column(Float, default=0)
    max_uses = Column(Integer, nullable=True)
    current_uses = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    valid_until = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

