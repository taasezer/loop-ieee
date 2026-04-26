from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.database import get_db
from app.models.orm import Order, User, OrderStatus, UserRole
from app.dependencies import get_current_user
from app.services.pricing import calculate_order_price
from pydantic import BaseModel
from app.services.order_workflow import order_workflow_service
from app.services.maps_service import maps_service

router = APIRouter()

class OrderCreate(BaseModel):
    pickup_address: str
    pickup_latitude: float
    pickup_longitude: float
    delivery_address: str
    delivery_latitude: float
    delivery_longitude: float
    distance_km: float # In a real app, this would be calculated server-side via OSRM

class OrderResponse(BaseModel):
    id: int
    status: str
    price: float
    pickup_address: str
    delivery_address: str
    created_at: str

    class Config:
        from_attributes = True

@router.post("/", response_model=OrderResponse)
async def create_order(
    order_in: OrderCreate, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify distance server-side
    verified_distance = order_in.distance_km
    distance_data = maps_service.calculate_distance_duration(
        origin=(order_in.pickup_latitude, order_in.pickup_longitude),
        destination=(order_in.delivery_latitude, order_in.delivery_longitude)
    )
    if distance_data:
        verified_distance = distance_data['distance_km']
        
    # Calculate price
    price = await calculate_order_price(db, verified_distance)
    
    new_order = Order(
        customer_id=current_user.id,
        pickup_address=order_in.pickup_address,
        pickup_latitude=order_in.pickup_latitude,
        pickup_longitude=order_in.pickup_longitude,
        delivery_address=order_in.delivery_address,
        delivery_latitude=order_in.delivery_latitude,
        delivery_longitude=order_in.delivery_longitude,
        distance_km=verified_distance,
        price=price,
        status=OrderStatus.CREATED
    )
    
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    
    return OrderResponse(
        id=new_order.id,
        status=new_order.status,
        price=new_order.price,
        pickup_address=new_order.pickup_address,
        delivery_address=new_order.delivery_address,
        created_at=str(new_order.created_at)
    )

@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.customer_id == current_user.id))
    orders = result.scalars().all()
    return [
        OrderResponse(
            id=o.id,
            status=o.status,
            price=o.price,
            pickup_address=o.pickup_address,
            delivery_address=o.delivery_address,
            created_at=str(o.created_at)
        ) for o in orders
    ]

@router.get("/active", response_model=List[OrderResponse])
async def get_active_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get active (non-completed) orders for current user"""
    orders = await order_workflow_service.get_active_orders(
        db=db,
        user_id=current_user.id
    )
    
    return [
        OrderResponse(
            id=o.id,
            status=o.status,
            price=o.price,
            pickup_address=o.pickup_address,
            delivery_address=o.delivery_address,
            created_at=str(o.created_at)
        ) for o in orders
    ]

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.customer_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.DISPATCHER]:
         raise HTTPException(status_code=403, detail="Not authorized")

    return OrderResponse(
        id=order.id,
        status=order.status,
        price=order.price,
        pickup_address=order.pickup_address,
        delivery_address=order.delivery_address,
        created_at=str(order.created_at)
    )

@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel an order"""
    # Verify order belongs to user
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Cancel order
    cancel_result = await order_workflow_service.cancel_order(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
        reason=reason
    )
    
    if not cancel_result["success"]:
        raise HTTPException(status_code=400, detail=cancel_result["error"])
    
    return {"message": "Order cancelled successfully", **cancel_result}

@router.put("/{order_id}/status")
async def update_order_status(
    order_id: int,
    new_status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update order status (admin only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.DISPATCHER]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    result = await order_workflow_service.update_order_status(
        db=db,
        order_id=order_id,
        new_status=new_status,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"message": "Status updated successfully", **result}
