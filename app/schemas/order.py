"""
Order Pydantic schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.order import OrderStatus, OrderType, PaymentMethod


class OrderCreateRequest(BaseModel):
    """Create order request"""
    # Pickup details
    pickup_address: str
    pickup_latitude: float = Field(..., ge=-90, le=90)
    pickup_longitude: float = Field(..., ge=-180, le=180)
    pickup_contact_name: Optional[str] = None
    pickup_contact_phone: Optional[str] = None
    pickup_instructions: Optional[str] = None
    
    # Delivery details
    delivery_address: str
    delivery_latitude: float = Field(..., ge=-90, le=90)
    delivery_longitude: float = Field(..., ge=-180, le=180)
    delivery_contact_name: str
    delivery_contact_phone: str
    delivery_instructions: Optional[str] = None
    
    # Package details
    package_description: Optional[str] = None
    package_weight: Optional[float] = Field(None, gt=0)
    package_dimensions: Optional[Dict[str, float]] = None
    package_value: Optional[float] = Field(None, ge=0)
    fragile: bool = False
    
    # Order type and payment
    order_type: OrderType = OrderType.STANDARD
    payment_method: PaymentMethod
    
    # Scheduling
    scheduled_pickup_time: Optional[datetime] = None
    scheduled_delivery_time: Optional[datetime] = None
    
    # Notes
    customer_notes: Optional[str] = None
    
    # Promo code
    promo_code: Optional[str] = None


class OrderUpdateRequest(BaseModel):
    """Update order request"""
    status: Optional[OrderStatus] = None
    courier_notes: Optional[str] = None
    admin_notes: Optional[str] = None


class OrderCancelRequest(BaseModel):
    """Cancel order request"""
    cancellation_reason: str
    cancelled_by: str


class ProofOfDeliveryRequest(BaseModel):
    """Proof of delivery request"""
    signature: Optional[str] = None
    photo: Optional[str] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Order response"""
    id: UUID
    order_number: str
    status: OrderStatus
    order_type: OrderType
    
    # Addresses
    pickup_address: str
    delivery_address: str
    
    # Pricing
    total_price: float
    payment_method: PaymentMethod
    payment_status: str
    
    # Timestamps
    created_at: datetime
    assigned_at: Optional[datetime]
    picked_up_at: Optional[datetime]
    delivered_at: Optional[datetime]
    
    # Related entities
    customer_id: Optional[UUID]
    courier_id: Optional[UUID]
    
    class Config:
        from_attributes = True


class OrderDetailResponse(BaseModel):
    """Detailed order response"""
    id: UUID
    order_number: str
    status: OrderStatus
    order_type: OrderType
    
    # Pickup details
    pickup_address: str
    pickup_latitude: float
    pickup_longitude: float
    pickup_contact_name: Optional[str]
    pickup_contact_phone: Optional[str]
    pickup_instructions: Optional[str]
    
    # Delivery details
    delivery_address: str
    delivery_latitude: float
    delivery_longitude: float
    delivery_contact_name: str
    delivery_contact_phone: str
    delivery_instructions: Optional[str]
    
    # Package details
    package_description: Optional[str]
    package_weight: Optional[float]
    fragile: bool
    
    # Distance and duration
    distance_km: Optional[float]
    estimated_duration_minutes: Optional[float]
    
    # Pricing
    base_price: float
    distance_price: float
    surge_multiplier: float
    weather_multiplier: float
    discount_amount: float
    tax_amount: float
    total_price: float
    
    # Payment
    payment_method: PaymentMethod
    payment_status: str
    
    # Timestamps
    created_at: datetime
    assigned_at: Optional[datetime]
    accepted_at: Optional[datetime]
    picked_up_at: Optional[datetime]
    delivered_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    
    # Notes
    customer_notes: Optional[str]
    courier_notes: Optional[str]
    
    # Proof of delivery
    proof_of_delivery: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Order list response"""
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int


class OrderStatsResponse(BaseModel):
    """Order statistics"""
    total_orders: int
    active_orders: int
    completed_orders: int
    cancelled_orders: int
    total_revenue: float
    average_order_value: float
