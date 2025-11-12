"""Location repository"""
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timedelta

from app.models.location import Location
from app.repositories.base_repository import BaseRepository

class LocationRepository(BaseRepository[Location]):
    def __init__(self, db: AsyncSession):
        super().__init__(Location, db)
    
    async def get_courier_locations(self, courier_id: UUID, limit: int = 100) -> List[Location]:
        result = await self.db.execute(
            select(Location)
            .where(Location.courier_id == courier_id)
            .order_by(Location.recorded_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_latest_location(self, courier_id: UUID) -> Location:
        result = await self.db.execute(
            select(Location)
            .where(Location.courier_id == courier_id)
            .order_by(Location.recorded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
