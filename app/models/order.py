"""
LOOP Lojistik Platformu - Sipariş Modeli
Sipariş (Order) veritabanı modeli ve işlemleri
"""

from sqlalchemy import Column, String, Enum, Float, Integer, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from geoalchemy2 import Geography
from sqlalchemy.orm import relationship
import uuid
from enum import Enum as PyEnum
from datetime import datetime

from core.database import Base


class OrderStatus(PyEnum):
    PENDING = "pending"           # Sipariş oluşturuldu, atama bekleniyor
    ASSIGNED = "assigned"         # Kurye atandı
    PICKED_UP = "picked_up"      # Kurye paketi aldı
    IN_TRANSIT = "in_transit"    # Yolda
    DELIVERED = "delivered"       # Teslim edildi
    CANCELLED = "cancelled"       # İptal edildi
    FAILED = "failed"             # Teslimat başarısız


class PriorityLevel(PyEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class PaymentMethod(PyEnum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DIGITAL_WALLET = "digital_wallet"
    CORPORATE = "corporate"


class Order(Base):
    __tablename__ = "orders"
    
    # Temel bilgiler
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Müşteri bilgileri
    customer_name = Column(String(100), nullable=False)
    customer_phone = Column(String(20), nullable=False, index=True)
    customer_email = Column(String(100), nullable=True)
    
    # Teslimat adresleri
    pickup_address = Column(Text, nullable=False)
    pickup_location = Column(Geography('POINT', 4326), nullable=False)
    pickup_instructions = Column(Text, nullable=True)
    
    delivery_address = Column(Text, nullable=False)
    delivery_location = Column(Geography('POINT', 4326), nullable=False)
    delivery_instructions = Column(Text, nullable=True)
    
    # Sipariş durumu
    status = Column(
        Enum(OrderStatus, name="order_status"), 
        nullable=False, 
        default=OrderStatus.PENDING,
        index=True
    )
    
    # Kurye ataması
    assigned_courier_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('couriers.id'), 
        nullable=True,
        index=True
    )
    
    # Öncelik ve zamanlama
    priority = Column(
        Enum(PriorityLevel, name="priority_level"), 
        nullable=False, 
        default=PriorityLevel.NORMAL,
        index=True
    )
    scheduled_pickup_time = Column(DateTime(timezone=True), nullable=True)
    scheduled_delivery_time = Column(DateTime(timezone=True), nullable=True)
    
    # Mesafe ve süre tahminleri
    estimated_distance_km = Column(Float, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    actual_distance_km = Column(Float, nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)
    
    # Ücret ve ödeme
    base_price = Column(Float, nullable=False, default=0.0)
    distance_fee = Column(Float, nullable=False, default=0.0)
    priority_fee = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)
    currency = Column(String(3), nullable=False, default="TRY")
    
    payment_method = Column(
        Enum(PaymentMethod, name="payment_method"), 
        nullable=False, 
        default=PaymentMethod.CASH
    )
    
    # Paket bilgileri
    package_type = Column(String(50), nullable=True)
    package_weight_kg = Column(Float, nullable=True)
    package_dimensions = Column(String(50), nullable=True)  # "30x20x15" format
    fragile = Column(Boolean, nullable=False, default=False)
    
    # Özel notlar ve etiketler
    notes = Column(Text, nullable=True)
    tags = Column(ARRAY(String), nullable=True, default=list)
    
    # Zaman damgaları
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # İlişkiler
    assigned_courier = relationship("Courier", back_populates="orders")
    route = relationship("Route", back_populates="order", uselist=False)
    
    def __repr__(self):
        return f"<Order(id={self.id}, number={self.order_number}, status={self.status})>"
    
    @property
    def pickup_location_tuple(self) -> tuple:
        """Alış konumunu (lat, lng) tuple olarak döndür"""
        if self.pickup_location:
            coords = self.pickup_location.coords[0]
            return (coords[1], coords[0])  # (lat, lng)
        return None
    
    @property
    def delivery_location_tuple(self) -> tuple:
        """Teslimat konumunu (lat, lng) tuple olarak döndür"""
        if self.delivery_location:
            coords = self.delivery_location.coords[0]
            return (coords[1], coords[0])  # (lat, lng)
        return None
    
    @property
    def is_active(self) -> bool:
        """Sipariş aktif mi?"""
        return self.status in [
            OrderStatus.ASSIGNED,
            OrderStatus.PICKED_UP,
            OrderStatus.IN_TRANSIT
        ]
    
    @property
    def is_completed(self) -> bool:
        """Sipariş tamamlandı mı?"""
        return self.status == OrderStatus.DELIVERED
    
    def update_status(self, new_status: OrderStatus):
        """Sipariş durumunu güncelle ve zaman damgalarını ayarla"""
        self.status = new_status
        
        now = datetime.utcnow()
        if new_status == OrderStatus.ASSIGNED:
            self.assigned_at = now
        elif new_status == OrderStatus.PICKED_UP:
            self.picked_up_at = now
        elif new_status == OrderStatus.DELIVERED:
            self.delivered_at = now
    
    def calculate_total_price(self):
        """Toplam fiyatı hesapla"""
        self.total_price = self.base_price + self.distance_fee + self.priority_fee
        
        # Öncelik ek ücreti ekle
        if self.priority == PriorityLevel.HIGH:
            self.priority_fee = self.base_price * 0.2
        elif self.priority == PriorityLevel.URGENT:
            self.priority_fee = self.base_price * 0.4
        
        self.total_price = self.base_price + self.distance_fee + self.priority_fee
    
    def get_delivery_time_estimate(self) -> int:
        """Teslimat süresi tahmini (dakika)"""
        base_time = self.DEFAULT_DELIVERY_TIME_MINUTES
        
        # Önceliğe göre ayarla
        if self.priority == PriorityLevel.HIGH:
            base_time *= 0.8
        elif self.priority == PriorityLevel.URGENT:
            base_time *= 0.6
        elif self.priority == PriorityLevel.LOW:
            base_time *= 1.2
        
        return int(base_time)