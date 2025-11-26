from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.orm import Courier, Location, Order
from app.websockets.server import manager
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()

class LocationUpdate(BaseModel):
    courier_id: int
    latitude: float
    longitude: float

@router.post("/update")
async def update_location(
    update: LocationUpdate,
    db: AsyncSession = Depends(get_db)
):
    # Update Courier current location
    result = await db.execute(select(Courier).where(Courier.id == update.courier_id))
    courier = result.scalar_one_or_none()
    
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    courier.current_latitude = update.latitude
    courier.current_longitude = update.longitude
    courier.last_location_update = datetime.utcnow()
    
    # Log location history
    new_location = Location(
        courier_id=update.courier_id,
        latitude=update.latitude,
        longitude=update.longitude
    )
    db.add(new_location)
    
    await db.commit()
    
    # Broadcast via WebSocket
    # We need to find active orders for this courier to broadcast to correct rooms
    orders_result = await db.execute(select(Order).where(Order.courier_id == update.courier_id))
    active_orders = orders_result.scalars().all()
    
    for order in active_orders:
        if order.status in ["assigned", "picked_up", "in_transit"]:
            await manager.broadcast_to_room(str(order.id), {
                "type": "location_update",
                "courier_id": update.courier_id,
                "lat": update.latitude,
                "lon": update.longitude,
                "order_id": order.id
            })
            
    return {"status": "updated"}

@router.get("/courier/{courier_id}")
async def get_courier_location(
    courier_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Courier).where(Courier.id == courier_id))
    courier = result.scalar_one_or_none()
    
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
        
    return {
        "courier_id": courier.id,
        "latitude": courier.current_latitude,
        "longitude": courier.current_longitude,
        "last_updated": str(courier.last_location_update)
    }

@router.get("/active")
async def get_active_couriers(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all currently active couriers (online with assigned orders).
    Used by n8n weather alert workflow to monitor couriers in the field.
    """
    # Get couriers who are online and have active orders
    result = await db.execute(
        select(Courier).where(Courier.is_online == True)
    )
    couriers = result.scalars().all()
    
    active_couriers = []
    for courier in couriers:
        # Get active orders for this courier
        orders_result = await db.execute(
            select(Order).where(
                Order.courier_id == courier.id,
                Order.status.in_(["assigned", "picked_up", "in_transit"])
            )
        )
        active_orders = orders_result.scalars().all()
        
        # Include courier in response if they have active orders or are online
        if active_orders or courier.is_online:
            active_couriers.append({
                "courier_id": courier.id,
                "courier_name": f"{courier.user.name if courier.user else 'Unknown'}",
                "phone": courier.user.phone if courier.user else None,
                "latitude": courier.current_latitude,
                "longitude": courier.current_longitude,
                "last_location_update": str(courier.last_location_update) if courier.last_location_update else None,
                "is_online": courier.is_online,
                "active_order_count": len(active_orders),
                "active_orders": [
                    {
                        "order_id": order.id,
                        "status": order.status,
                        "pickup_latitude": order.pickup_latitude,
                        "pickup_longitude": order.pickup_longitude,
                        "delivery_latitude": order.delivery_latitude,
                        "delivery_longitude": order.delivery_longitude
                    }
                    for order in active_orders
                ]
            })
    
    return {
        "total_active_couriers": len(active_couriers),
        "couriers": active_couriers
    }

