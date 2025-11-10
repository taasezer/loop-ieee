"""
LOOP Lojistik Platformu - Courier Schemas
Kurye API request/response şemaları
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

from models.courier import CourierStatus, VehicleType


class CourierCreate(BaseModel):
    """Yeni kurye oluşturma şeması"""
    
    name: str = Field(..., min_length=2, max_length=100, description="Kurye adı")
    phone: str = Field(..., regex=r"^\+?[0-9]{10,15}$", description="Telefon numarası")
    email: Optional[EmailStr] = Field(None, description="Email adresi")
    vehicle_type: VehicleType = Field(..., description="Araç tipi")
    license_number: Optional[str] = Field(None, max_length=50, description="Ehliyet numarası")
    vehicle_registration: Optional[str] = Field(None, max_length=50, description="Araç plakası")
    languages: Optional[List[str]] = Field(default_factory=list, description="Dil yetenekleri")
    skills: Optional[List[str]] = Field(default_factory=list, description="Özel yetenekler")
    
    @validator('phone')
    def validate_phone(cls, v):
        """Telefon numarası formatını doğrula"""
        # Türkiye telefon formatı kontrolü
        if v.startswith('0'):
            v = '+90' + v[1:]
        elif v.startswith('5'):
            v = '+90' + v
        return v


class CourierUpdate(BaseModel):
    """Kurye güncelleme şeması"""
    
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, regex=r"^\+?[0-9]{10,15}$")
    email: Optional[EmailStr] = None
    vehicle_type: Optional[VehicleType] = None
    license_number: Optional[str] = Field(None, max_length=50)
    vehicle_registration: Optional[str] = Field(None, max_length=50)
    languages: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    insurance_info: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            if v.startswith('0'):
                v = '+90' + v[1:]
            elif v.startswith('5'):
                v = '+90' + v
        return v


class CourierLocationUpdate(BaseModel):
    """Kurye konum güncelleme şeması"""
    
    latitude: float = Field(..., ge=-90, le=90, description="Enlem")
    longitude: float = Field(..., ge=-180, le=180, description="Boylam")
    accuracy: Optional[float] = Field(None, ge=0, description="GPS hassasiyeti (metre)")
    timestamp: Optional[datetime] = Field(None, description="Konum zaman damgası")


class CourierResponse(BaseModel):
    """Kurye response şeması"""
    
    id: UUID
    name: str
    phone: str
    email: Optional[str]
    status: CourierStatus
    current_location: Optional[dict] = None
    vehicle_type: VehicleType
    rating: float
    total_deliveries: int
    total_distance_km: float
    languages: Optional[List[str]]
    skills: Optional[List[str]]
    license_number: Optional[str]
    vehicle_registration: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    last_active_at: Optional[datetime]
    
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    @classmethod
    def from_orm(cls, obj):
        """ORM objesinden response objesi oluştur"""
        response = super().from_orm(obj)
        
        # Konum bilgisini dict formatına çevir
        if obj.current_location:
            coords = obj.current_location.coords[0]
            response.current_location = {
                "latitude": coords[1],  # PostGIS: (lng, lat)
                "longitude": coords[0]
            }
        
        return response


class CourierListResponse(BaseModel):
    """Kurye listesi response şeması"""
    
    data: List[CourierResponse]
    total: int
    skip: int
    limit: int


class CourierPerformanceResponse(BaseModel):
    """Kurye performans istatistikleri"""
    
    courier_id: UUID
    name: str
    rating: float
    total_deliveries: int
    total_distance_km: float
    recent_deliveries_count: int
    average_delivery_time: Optional[float]
    on_time_delivery_rate: Optional[float]
    current_status: str
    vehicle_type: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class CourierStatsResponse(BaseModel):
    """Kurye istatistikleri response şeması"""
    
    total_couriers: int
    available_couriers: int
    busy_couriers: int
    offline_couriers: int
    average_rating: float
    total_deliveries_today: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }