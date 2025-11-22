from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import List
from app.database import get_db
from app.models.orm import Order, User, OrderStatus, Courier, UserRole
from app.dependencies import get_current_user
from app.services.order_workflow import order_workflow_service
from pydantic import BaseModel

router = APIRouter()

class OrderResponse(BaseModel):
    id: int
    status: str
    pickup_address: str
    delivery_address: str
    price: float
    distance_km: float
    
    class Config:
        from_attributes = True

@router.get("/available", response_model=List[OrderResponse])
async def get_available_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available orders for courier to accept"""
    # Verify user is a courier
    if current_user.role != UserRole.COURIER:
        raise HTTPException(status_code=403, detail="Only couriers can access this endpoint")
    
    # Get courier profile
    courier_result = await db.execute(
        select(Courier).where(Courier.user_id == current_user.id)
    )
    courier = courier_result.scalar_one_or_none()
    
    if not courier:
        raise HTTPException(status_code=404, detail="Courier profile not found")
    
    # Get unassigned orders
    result = await db.execute(
        select(Order).where(
            and_(
                Order.status == OrderStatus.CREATED,
                Order.courier_id == None
            )
        ).order_by(Order.created_at.desc())
    )
    
    orders = result.scalars().all()
    
    return [
        OrderResponse(
            id=o.id,
            status=o.status,
            pickup_address=o.pickup_address,
            delivery_address=o.delivery_address,
            price=o.price,
            distance_km=o.distance_km or 0.0
        ) for o in orders
    ]

@router.post("/{order_id}/accept")
async def accept_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept an order as a courier"""
    if current_user.role != UserRole.COURIER:
        raise HTTPException(status_code=403, detail="Only couriers can accept orders")
    
    # Get courier profile
    courier_result = await db.execute(
        select(Courier).where(Courier.user_id == current_user.id)
    )
    courier = courier_result.scalar_one_or_none()
    
    if not courier:
        raise HTTPException(status_code=404, detail="Courier profile not found")
    
    # Assign courier to order
    result = await order_workflow_service.assign_courier(
        db=db,
        order_id=order_id,
        courier_id=courier.id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"message": "Order accepted successfully", **result}

@router.post("/{order_id}/reject")
async def reject_order(
    order_id: int,
    reason: str = "Courier declined",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject an order as a courier"""
    if current_user.role != UserRole.COURIER:
        raise HTTPException(status_code=403, detail="Only couriers can reject orders")
    
    # Just log the rejection for now
    # In production, you might want to track rejections
    return {
        "message": "Order rejected",
        "order_id": order_id,
        "reason": reason
    }

@router.post("/{order_id}/pickup")
async def confirm_pickup(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Confirm order pickup"""
    if current_user.role != UserRole.COURIER:
        raise HTTPException(status_code=403, detail="Only couriers can confirm pickup")
    
    result = await order_workflow_service.update_order_status(
        db=db,
        order_id=order_id,
        new_status=OrderStatus.PICKED_UP,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"message": "Pickup confirmed", **result}

@router.post("/{order_id}/start-delivery")
async def start_delivery(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark order as in transit"""
    if current_user.role != UserRole.COURIER:
        raise HTTPException(status_code=403, detail="Only couriers can start delivery")
    
    result = await order_workflow_service.update_order_status(
        db=db,
        order_id=order_id,
        new_status=OrderStatus.IN_TRANSIT,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"message": "Delivery started", **result}

@router.post("/{order_id}/complete")
async def complete_delivery(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Complete delivery"""
    if current_user.role != UserRole.COURIER:
        raise HTTPException(status_code=403, detail="Only couriers can complete delivery")
    
    result = await order_workflow_service.update_order_status(
        db=db,
        order_id=order_id,
        new_status=OrderStatus.DELIVERED,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"message": "Delivery completed", **result}

@router.get("/my-orders", response_model=List[OrderResponse])
async def get_my_courier_orders(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get courier's assigned orders"""
    if current_user.role != UserRole.COURIER:
        raise HTTPException(status_code=403, detail="Only couriers can access this endpoint")
    
    # Get courier profile
    courier_result = await db.execute(
        select(Courier).where(Courier.user_id == current_user.id)
    )
    courier = courier_result.scalar_one_or_none()
    
    if not courier:
        raise HTTPException(status_code=404, detail="Courier profile not found")
    
    # Get orders
    if active_only:
        orders = await order_workflow_service.get_active_orders(
            db=db,
            courier_id=courier.id
        )
    else:
        result = await db.execute(
            select(Order).where(Order.courier_id == courier.id).order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()
    
    return [
        OrderResponse(
            id=o.id,
            status=o.status,
            pickup_address=o.pickup_address,
            delivery_address=o.delivery_address,
            price=o.price,
            distance_km=o.distance_km or 0.0
        ) for o in orders
    ]
