"""
LOOP Lojistik Platformu - Kurye Modeli
Kurye (Courier) veritabanı modeli ve işlemleri
"""

from sqlalchemy import Column, String, Enum, Float, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from geoalchemy2 import Geography
from sqlalchemy.orm import relationship
import uuid
from enum import Enum as PyEnum

from core.database import Base


class CourierStatus(PyEnum):
    AVAILABLE = "available"
    BUSY = "busy" 
    OFFLINE = "offline"
    ON_BREAK = "on_break"


class VehicleType(PyEnum):
    MOTORCYCLE = "motorcycle"
    CAR = "car"
    VAN = "van"
    BICYCLE = "bicycle"
    WALKING = "walking"


class Courier(Base):
    __tablename__ = "couriers"
    
    # Temel bilgiler
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    
    # Durum ve konum
    status = Column(
        Enum(CourierStatus, name="courier_status"), 
        nullable=False, 
        default=CourierStatus.AVAILABLE,
        index=True
    )
    current_location = Column(Geography('POINT', 4326), nullable=True)
    
    # Araç bilgisi
    vehicle_type = Column(
        Enum(VehicleType, name="vehicle_type"), 
        nullable=False, 
        default=VehicleType.MOTORCYCLE
    )
    
    # Performans metrikleri
    rating = Column(Float, nullable=False, default=5.0)
    total_deliveries = Column(Integer, nullable=False, default=0)
    total_distance_km = Column(Float, nullable=False, default=0.0)
    
    # İletişim ve yetenekler
    languages = Column(ARRAY(String), nullable=True, default=list)
    skills = Column(ARRAY(String), nullable=True, default=list)
    
    # Sertifikalar ve belgeler
    license_number = Column(String(50), nullable=True)
    vehicle_registration = Column(String(50), nullable=True)
    insurance_info = Column(Text, nullable=True)
    
    # Zaman damgaları
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    
    # İlişkiler
    orders = relationship("Order", back_populates="assigned_courier")
    routes = relationship("Route", back_populates="courier")
    
    def __repr__(self):
        return f"<Courier(id={self.id}, name={self.name}, status={self.status})>"
    
    @property
    def is_available(self) -> bool:
        """Kurye müsait mi?"""
        return self.status == CourierStatus.AVAILABLE
    
    @property
    def location_tuple(self) -> tuple:
        """Konumu (lat, lng) tuple olarak döndür"""
        if self.current_location:
            # PostGIS POINT formatından (lng, lat) çevir
            coords = self.current_location.coords[0]
            return (coords[1], coords[0])  # (lat, lng)
        return None
    
    def update_rating(self, new_rating: float):
        """Rating'i güncelle (ortalama hesapla)"""
        if self.total_deliveries > 0:
            self.rating = ((self.rating * self.total_deliveries) + new_rating) / (self.total_deliveries + 1)
        else:
            self.rating = new_rating
    
    def increment_deliveries(self, distance_km: float = 0.0):
        """Teslimat sayısını ve mesafeyi artır"""
        self.total_deliveries += 1
        self.total_distance_km += distance_km
        self.last_active_at = func.now()