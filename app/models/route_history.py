"""
RouteHistory model - Past route data for optimization
"""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class RouteHistory(Base):
    """Route history model for tracking completed routes"""
    
    __tablename__ = "route_history"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    courier_id = Column(UUID(as_uuid=True), ForeignKey("couriers.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Route details
    start_latitude = Column(Float, nullable=False)
    start_longitude = Column(Float, nullable=False)
    end_latitude = Column(Float, nullable=False)
    end_longitude = Column(Float, nullable=False)
    
    # Route path (array of coordinates)
    route_path = Column(JSONB, nullable=True, default=[])  # [{lat, lng, timestamp}]
    
    # Distance and duration
    total_distance_km = Column(Float, nullable=False)
    total_duration_minutes = Column(Float, nullable=False)
    
    # Planned vs actual
    planned_distance_km = Column(Float, nullable=True)
    planned_duration_minutes = Column(Float, nullable=True)
    deviation_distance_km = Column(Float, nullable=True)
    deviation_duration_minutes = Column(Float, nullable=True)
    
    # Traffic and weather conditions
    traffic_conditions = Column(JSONB, nullable=True)
    weather_conditions = Column(JSONB, nullable=True)
    
    # Performance metrics
    average_speed_kmh = Column(Float, nullable=True)
    stops_count = Column(Float, default=0)
    idle_time_minutes = Column(Float, default=0.0)
    
    # Optimization data
    optimization_score = Column(Float, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="route_history")
    courier = relationship("Courier", back_populates="route_history")
    
    def __repr__(self):
        return f"<RouteHistory for Order {self.order_id}>"
