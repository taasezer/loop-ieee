"""Courier service"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
import logging

from app.models.courier import Courier, CourierStatus
from app.repositories.courier_repository import CourierRepository
from app.repositories.location_repository import LocationRepository
from app.core.exceptions import ResourceNotFoundException
from app.schemas.courier import CourierResponse, CourierDetailResponse, LocationUpdateRequest

logger = logging.getLogger(__name__)

class CourierService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.courier_repo = CourierRepository(db)
        self.location_repo = LocationRepository(db)
    
    async def get_courier(self, courier_id: UUID) -> CourierDetailResponse:
        courier = await self.courier_repo.get_by_id(courier_id)
        if not courier:
            raise ResourceNotFoundException("Courier")
        return CourierDetailResponse.from_orm(courier)
    
    async def update_location(self, courier_id: UUID, location: LocationUpdateRequest):
        courier = await self.courier_repo.get_by_id(courier_id)
        if not courier:
            raise ResourceNotFoundException("Courier")
        
        location_data = {
            "courier_id": courier_id,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "accuracy": location.accuracy,
            "speed": location.speed,
            "heading": location.heading,
            "recorded_at": datetime.utcnow()
        }
        
        await self.location_repo.create(location_data)
        
        await self.courier_repo.update(courier_id, {
            "current_latitude": location.latitude,
            "current_longitude": location.longitude,
            "last_location_update": datetime.utcnow()
        })
        
        await self.db.commit()
        logger.info(f"Location updated for courier: {courier_id}")
        return True
    
    async def get_available_couriers(self) -> List[CourierResponse]:
        couriers = await self.courier_repo.get_available_couriers()
        return [CourierResponse.from_orm(c) for c in couriers]
    
    async def update_availability(self, courier_id: UUID, is_available: bool):
        await self.courier_repo.update(courier_id, {"is_available": is_available})
        await self.db.commit()
        return True
