from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import List
from app.database import get_db
from app.models.orm import Courier, User, UserRole, Order, OrderStatus
from app.dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter()

class CourierResponse(BaseModel):
    id: int
    vehicle_type: str
    is_online: bool
    rating: float
    created_at: str
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[CourierResponse])
async def get_couriers(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Courier))
    couriers = result.scalars().all()
    
    return [
        CourierResponse(
            id=c.id,
            vehicle_type=c.vehicle_type,
            is_online=c.is_online,
            rating=c.rating,
            created_at=str(c.user.created_at) if hasattr(c, 'user') and c.user else "N/A"
        ) for c in couriers
    ]

@router.put("/status")
async def toggle_online_status(
    is_online: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle courier online/offline status"""
    if current_user.role != UserRole.COURIER:
        raise HTTPException(status_code=403, detail="Only couriers can update status")
    
    courier_result = await db.execute(select(Courier).where(Courier.user_id == current_user.id))
    courier = courier_result.scalar_one_or_none()
    
    if not courier:
        raise HTTPException(status_code=404, detail="Courier profile not found")
    
    courier.is_online = is_online
    await db.commit()
    
    return {
        "message": f"Status updated to {'online' if is_online else 'offline'}",
        "is_online": is_online
    }

@router.get("/earnings")
async def get_courier_earnings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get courier earnings summary"""
    if current_user.role != UserRole.COURIER:
        raise HTTPException(status_code=403, detail="Only couriers can access earnings")
    
    courier_result = await db.execute(select(Courier).where(Courier.user_id == current_user.id))
    courier = courier_result.scalar_one_or_none()
    
    if not courier:
        raise HTTPException(status_code=404, detail="Courier profile not found")
    
    # Get total earnings
    from app.models.orm import Earning
    earnings_result = await db.execute(select(Earning).where(Earning.courier_id == courier.id))
    earnings = earnings_result.scalars().all()
    
    total = sum(e.amount for e in earnings)
    
    return {
        "total_earnings": total,
        "num_deliveries": len(earnings),
        "average_per_delivery": total / len(earnings) if earnings else 0
    }

@router.get("/performance")
async def get_courier_performance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get courier performance metrics"""
    if current_user.role != UserRole.COURIER:
        raise HTTPException(status_code=403, detail="Only couriers can access performance")
    
    courier_result = await db.execute(select(Courier).where(Courier.user_id == current_user.id))
    courier = courier_result.scalar_one_or_none()
    
    if not courier:
        raise HTTPException(status_code=404, detail="Courier profile not found")
    
    # Get completed orders
    orders_result = await db.execute(
        select(Order).where(
            and_(
                Order.courier_id == courier.id,
                Order.status == OrderStatus.DELIVERED
            )
        )
    )
    completed_orders = orders_result.scalars().all()
    
    # Get ratings
    from app.models.orm import Rating
    ratings_result = await db.execute(select(Rating).where(Rating.courier_id == courier.id))
    ratings = ratings_result.scalars().all()
    
    avg_rating = sum(r.score for r in ratings) / len(ratings) if ratings else 0.0
    
    return {
        "completed_deliveries": len(completed_orders),
        "current_rating": courier.rating,
        "average_rating": avg_rating,
        "total_ratings": len(ratings)
    }
