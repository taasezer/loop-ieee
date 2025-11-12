"""Admin API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.core.database import get_db
from app.schemas.analytics import DashboardStatsResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get admin dashboard statistics"""
    try:
        from app.repositories.order_repository import OrderRepository
        from app.repositories.courier_repository import CourierRepository
        
        order_repo = OrderRepository(db)
        courier_repo = CourierRepository(db)
        
        total_orders = await order_repo.count()
        active_orders = len(await order_repo.get_active_orders())
        online_couriers = len(await courier_repo.get_online_couriers())
        
        return DashboardStatsResponse(
            total_orders=total_orders,
            active_orders=active_orders,
            total_revenue=0.0,
            active_couriers=online_couriers,
            average_delivery_time=0.0
        )
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard stats")
