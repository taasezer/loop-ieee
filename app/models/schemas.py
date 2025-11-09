from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class CourierStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"

class OrderStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Location(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None
    timestamp: Optional[datetime] = None

class CourierCreate(BaseModel):
    name: str
    phone: str
    email: str
    vehicle_type: str
    license_plate: Optional[str] = None

class CourierUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[CourierStatus] = None
    current_location: Optional[Location] = None

class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    pickup_location: Location
    delivery_location: Location
    package_weight: float
    package_description: str
    delivery_notes: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=5)

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    courier_id: Optional[str] = None
    pickup_time: Optional[datetime] = None
    delivery_time: Optional[datetime] = None
    delivery_notes: Optional[str] = None

class LocationUpdate(BaseModel):
    courier_id: str
    location: Location

class AssignmentRequest(BaseModel):
    order_id: str
    auto_assign: bool = True
    preferred_courier_id: Optional[str] = None

class RouteOptimization(BaseModel):
    courier_id: str
    waypoints: List[Location]
