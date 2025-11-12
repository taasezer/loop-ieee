from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List
from datetime import datetime, timezone
import uuid
from enum import Enum

class OrderStatus(str, Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    PICKED = "picked"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"

class OrderPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class Address(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    latitude: float
    longitude: float
    notes: Optional[str] = None

class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    courier_id: Optional[str] = None
    
    pickup_address: Address
    delivery_address: Address
    
    status: OrderStatus = OrderStatus.CREATED
    priority: OrderPriority = OrderPriority.NORMAL
    
    package_description: str
    package_weight: Optional[float] = None  # kg
    package_dimensions: Optional[Dict[str, float]] = None  # {"length": x, "width": y, "height": z}
    
    estimated_distance: Optional[float] = None  # km
    estimated_duration: Optional[int] = None  # minutes
    estimated_price: float
    final_price: Optional[float] = None
    
    pickup_time: Optional[datetime] = None
    delivery_time: Optional[datetime] = None
    scheduled_pickup: Optional[datetime] = None
    
    tracking_code: str = Field(default_factory=lambda: f"LOOP{uuid.uuid4().hex[:8].upper()}")
    
    proof_of_delivery: Optional[Dict[str, str]] = None  # {"signature": "url", "photo": "url"}
    customer_notes: Optional[str] = None
    courier_notes: Optional[str] = None
    
    payment_method: str = "cash"  # cash, card, wallet
    payment_status: str = "pending"  # pending, completed, failed
    
    weather_conditions: Optional[Dict] = None
    currency_rate: Optional[float] = 1.0
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class OrderCreate(BaseModel):
    customer_id: str
    pickup_address: Address
    delivery_address: Address
    package_description: str
    package_weight: Optional[float] = None
    package_dimensions: Optional[Dict[str, float]] = None
    priority: OrderPriority = OrderPriority.NORMAL
    scheduled_pickup: Optional[datetime] = None
    customer_notes: Optional[str] = None
    payment_method: str = "cash"

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    notes: Optional[str] = None
