"""Courier repository"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.courier import Courier, CourierStatus
from app.repositories.base_repository import BaseRepository

class CourierRepository(BaseRepository[Courier]):
    def __init__(self, db: AsyncSession):
        super().__init__(Courier, db)
    
    async def get_by_user_id(self, user_id: UUID) -> Optional[Courier]:
        result = await self.db.execute(
            select(Courier).where(Courier.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_available_couriers(self) -> List[Courier]:
        result = await self.db.execute(
            select(Courier).where(
                Courier.status == CourierStatus.ONLINE,
                Courier.is_available == True
            )
        )
        return list(result.scalars().all())
    
    async def get_online_couriers(self) -> List[Courier]:
        result = await self.db.execute(
            select(Courier).where(Courier.status == CourierStatus.ONLINE)
        )
        return list(result.scalars().all())
