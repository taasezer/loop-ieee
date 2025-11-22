from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.orm import Courier, Order, OrderStatus
from typing import Optional
import math

async def find_best_courier(db: AsyncSession, order: Order) -> Optional[Courier]:
    # Simple heuristic: Find nearest online courier
    # In production, use Scikit-learn or more complex logic
    
    result = await db.execute(select(Courier).where(Courier.is_online == True))
    online_couriers = result.scalars().all()
    
    best_courier = None
    min_distance = float('inf')
    
    for courier in online_couriers:
        if courier.current_latitude and courier.current_longitude:
            dist = calculate_distance(
                order.pickup_latitude, order.pickup_longitude,
                courier.current_latitude, courier.current_longitude
            )
            if dist < min_distance:
                min_distance = dist
                best_courier = courier
                
    return best_courier

def calculate_distance(lat1, lon1, lat2, lon2):
    # Haversine formula
    R = 6371 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c
    return d

async def assign_order_to_courier(db: AsyncSession, order_id: int, courier_id: int):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if order:
        order.courier_id = courier_id
        order.status = OrderStatus.ASSIGNED
        await db.commit()
        await db.refresh(order)
        return order
    return None
