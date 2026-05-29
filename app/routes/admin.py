from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models.orm import Order, User, Courier, UserRole, OrderStatus
from app.dependencies import get_current_user
from app.services.order_workflow import order_workflow_service
from pydantic import BaseModel

router = APIRouter()

# Admin authorization dependency
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin or dispatcher role"""
    if current_user.role not in [UserRole.ADMIN, UserRole.DISPATCHER]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

class OrderDetailResponse(BaseModel):
    id: int
    customer_id: int
    courier_id: Optional[int]
    status: str
    pickup_address: str
    delivery_address: str
    price: float
    distance_km: float
    tracking_code: Optional[str] = None
    customer_note: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True

class CourierStatsResponse(BaseModel):
    id: int
    user_id: int
    vehicle_type: str
    is_online: bool
    rating: float
    total_deliveries: int
    active_orders: int
    supplier_name: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/orders", response_model=List[OrderDetailResponse])
async def get_all_orders(
    status: Optional[str] = None,
    courier_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all orders with optional filters (admin only)"""
    query = select(Order)
    
    # Apply filters
    if status:
        query = query.where(Order.status == status)
    if courier_id:
        query = query.where(Order.courier_id == courier_id)
    if customer_id:
        query = query.where(Order.customer_id == customer_id)
    
    query = query.order_by(Order.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return [
        OrderDetailResponse(
            id=o.id,
            customer_id=o.customer_id,
            courier_id=o.courier_id,
            status=o.status,
            pickup_address=o.pickup_address,
            delivery_address=o.delivery_address,
            price=o.price,
            distance_km=o.distance_km or 0.0,
            tracking_code=o.tracking_code,
            customer_note=o.customer_note,
            created_at=str(o.created_at)
        ) for o in orders
    ]

@router.get("/couriers", response_model=List[CourierStatsResponse])
async def get_all_couriers(
    is_online: Optional[bool] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all couriers with statistics (admin only)"""
    query = select(Courier).options(selectinload(Courier.supplier))
    
    if is_online is not None:
        query = query.where(Courier.is_online == is_online)
    
    result = await db.execute(query)
    couriers = result.scalars().all()
    
    courier_stats = []
    for courier in couriers:
        # Get total deliveries
        deliveries_result = await db.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.courier_id == courier.id,
                    Order.status == OrderStatus.DELIVERED
                )
            )
        )
        total_deliveries = deliveries_result.scalar() or 0
        
        # Get active orders
        active_result = await db.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.courier_id == courier.id,
                    Order.status.not_in([OrderStatus.DELIVERED, OrderStatus.CANCELLED])
                )
            )
        )
        active_orders = active_result.scalar() or 0
        
        courier_stats.append(
            CourierStatsResponse(
                id=courier.id,
                user_id=courier.user_id,
                vehicle_type=courier.vehicle_type,
                is_online=courier.is_online,
                rating=courier.rating,
                total_deliveries=total_deliveries,
                active_orders=active_orders,
                supplier_name=courier.supplier.company_name if courier.supplier else None
            )
        )
    
    return courier_stats

@router.post("/orders/{order_id}/assign/{courier_id}")
async def manual_assign_courier(
    order_id: int,
    courier_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Manually assign courier to order (admin only)"""
    result = await order_workflow_service.assign_courier(
        db=db,
        order_id=order_id,
        courier_id=courier_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"message": "Courier assigned successfully", **result}

@router.get("/realtime-map")
async def get_realtime_map_data(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get real-time courier locations and active orders for map view"""
    # Get online couriers with their locations
    courier_result = await db.execute(
        select(Courier).where(Courier.is_online == True)
    )
    couriers = courier_result.scalars().all()
    
    courier_locations = []
    for courier in couriers:
        if courier.current_latitude and courier.current_longitude:
            courier_locations.append({
                "courier_id": courier.id,
                "latitude": courier.current_latitude,
                "longitude": courier.current_longitude,
                "vehicle_type": courier.vehicle_type,
                "rating": courier.rating
            })
    
    # Get active orders
    active_orders_result = await db.execute(
        select(Order).where(
            Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP, OrderStatus.IN_TRANSIT])
        )
    )
    active_orders = active_orders_result.scalars().all()
    
    order_markers = []
    for order in active_orders:
        order_markers.append({
            "order_id": order.id,
            "status": order.status,
            "pickup": {
                "latitude": order.pickup_latitude,
                "longitude": order.pickup_longitude,
                "address": order.pickup_address
            },
            "delivery": {
                "latitude": order.delivery_latitude,
                "longitude": order.delivery_longitude,
                "address": order.delivery_address
            },
            "courier_id": order.courier_id
        })
    
    return {
        "courier_locations": courier_locations,
        "active_orders": order_markers,
        "total_online_couriers": len(courier_locations),
        "total_active_orders": len(order_markers)
    }

@router.put("/pricing-rules/{rule_id}")
async def update_pricing_rule(
    rule_id: int,
    base_price: float,
    price_per_km: float,
    surge_multiplier: float = 1.0,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update pricing rules (admin only)"""
    from app.models.orm import PricingRule
    
    result = await db.execute(select(PricingRule).where(PricingRule.id == rule_id))
    rule = result.scalar_one_or_none()
    
    if not rule:
        # Create it if it doesn't exist
        rule = PricingRule(
            id=rule_id,
            base_price=base_price,
            price_per_km=price_per_km,
            surge_multiplier=surge_multiplier,
            is_active=True
        )
        db.add(rule)
    else:
        rule.base_price = base_price
        rule.price_per_km = price_per_km
        rule.surge_multiplier = surge_multiplier
    
    await db.commit()
    
    return {
        "message": "Pricing rule updated",
        "rule_id": rule_id,
        "base_price": base_price,
        "price_per_km": price_per_km,
        "surge_multiplier": surge_multiplier
    }

@router.get("/statistics")
async def get_admin_statistics(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get overall system statistics"""
    # Total orders
    total_orders_result = await db.execute(select(func.count(Order.id)))
    total_orders = total_orders_result.scalar() or 0
    
    # Active orders
    active_orders_result = await db.execute(
        select(func.count(Order.id)).where(
            Order.status.not_in([OrderStatus.DELIVERED, OrderStatus.CANCELLED])
        )
    )
    active_orders = active_orders_result.scalar() or 0
    
    # Total revenue
    revenue_result = await db.execute(
        select(func.sum(Order.price)).where(Order.status == OrderStatus.DELIVERED)
    )
    total_revenue = revenue_result.scalar() or 0.0
    
    # Online couriers
    online_couriers_result = await db.execute(
        select(func.count(Courier.id)).where(Courier.is_online == True)
    )
    online_couriers = online_couriers_result.scalar() or 0
    
    # Total couriers
    total_couriers_result = await db.execute(select(func.count(Courier.id)))
    total_couriers = total_couriers_result.scalar() or 0
    
    return {
        "total_orders": total_orders,
        "active_orders": active_orders,
        "total_revenue": round(total_revenue, 2),
        "online_couriers": online_couriers,
        "total_couriers": total_couriers
    }
