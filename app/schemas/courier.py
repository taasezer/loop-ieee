"""
Courier Pydantic schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.courier import VehicleType, CourierStatus, VerificationStatus


class CourierCreateRequest(BaseModel):
    """Create courier profile request"""
    user_id: UUID
    vehicle_type: VehicleType
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[str] = None
    vehicle_color: Optional[str] = None
    license_plate: Optional[str] = None
    driver_license_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class CourierUpdateRequest(BaseModel):
    """Update courier profile request"""
    vehicle_type: Optional[VehicleType] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    status: Optional[CourierStatus] = None
    is_available: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None


class LocationUpdateRequest(BaseModel):
    """Update courier location request"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None


class CourierResponse(BaseModel):
    """Courier response"""
    id: UUID
    user_id: UUID
    vehicle_type: VehicleType
    status: CourierStatus
    is_available: bool
    verification_status: VerificationStatus
    average_rating: float
    total_deliveries: int
    current_latitude: Optional[float]
    current_longitude: Optional[float]
    
    class Config:
        from_attributes = True


class CourierDetailResponse(BaseModel):
    """Detailed courier response"""
    id: UUID
    user_id: UUID
    vehicle_type: VehicleType
    vehicle_make: Optional[str]
    vehicle_model: Optional[str]
    status: CourierStatus
    is_available: bool
    verification_status: VerificationStatus
    
    # Performance
    total_deliveries: int
    successful_deliveries: int
    average_rating: float
    performance_score: float
    
    # Earnings
    total_earnings: float
    pending_earnings: float
    
    # Location
    current_latitude: Optional[float]
    current_longitude: Optional[float]
    last_location_update: Optional[datetime]
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class CourierListResponse(BaseModel):
    """Courier list response"""
    couriers: List[CourierResponse]
    total: int
    page: int
    page_size: int


class CourierStatsResponse(BaseModel):
    """Courier statistics"""
    total_couriers: int
    online_couriers: int
    available_couriers: int
    busy_couriers: int
    verified_couriers: int
