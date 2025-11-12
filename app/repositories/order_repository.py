"""
Order repository
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.order import Order, OrderStatus
from app.repositories.base_repository import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """Order repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Order, db)
    
    async def get_by_order_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number"""
        result = await self.db.execute(
            select(Order).where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()
    
    async def get_by_customer(self, customer_id: UUID, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get orders by customer"""
        result = await self.db.execute(
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_courier(self, courier_id: UUID, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get orders by courier"""
        result = await self.db.execute(
            select(Order)
            .where(Order.courier_id == courier_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_status(self, status: OrderStatus, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get orders by status"""
        result = await self.db.execute(
            select(Order)
            .where(Order.status == status)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_active_orders(self) -> List[Order]:
        """Get all active orders"""
        active_statuses = [
            OrderStatus.CREATED,
            OrderStatus.PENDING_ASSIGNMENT,
            OrderStatus.ASSIGNED,
            OrderStatus.ACCEPTED,
            OrderStatus.PICKED_UP,
            OrderStatus.IN_TRANSIT
        ]
        result = await self.db.execute(
            select(Order).where(Order.status.in_(active_statuses))
        )
        return list(result.scalars().all())
    
    async def get_pending_assignment(self) -> List[Order]:
        """Get orders pending courier assignment"""
        result = await self.db.execute(
            select(Order).where(Order.status == OrderStatus.PENDING_ASSIGNMENT)
        )
        return list(result.scalars().all())
