from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime, timezone
import uuid
from enum import Enum

class VehicleType(str, Enum):
    BICYCLE = "bicycle"
    MOTORCYCLE = "motorcycle"
    CAR = "car"
    VAN = "van"

class CourierStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ON_BREAK = "on_break"
    BUSY = "busy"

class Courier(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    vehicle_type: VehicleType
    vehicle_number: str
    license_number: str
    status: CourierStatus = CourierStatus.OFFLINE
    current_location: Optional[Dict[str, float]] = None  # {"lat": x, "lng": y}
    rating: float = 5.0
    total_deliveries: int = 0
    completed_deliveries: int = 0
    cancelled_deliveries: int = 0
    total_earnings: float = 0.0
    is_verified: bool = False
    documents: Dict[str, str] = Field(default_factory=dict)  # {"license": "url", "id": "url"}
    availability_schedule: Dict = Field(default_factory=dict)
    performance_score: float = 100.0
    current_orders: list = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CourierCreate(BaseModel):
    user_id: str
    vehicle_type: VehicleType
    vehicle_number: str
    license_number: str

class CourierStatusUpdate(BaseModel):
    status: CourierStatus

class CourierLocationUpdate(BaseModel):
    latitude: float
    longitude: float
    speed: Optional[float] = 0
    heading: Optional[float] = 0
