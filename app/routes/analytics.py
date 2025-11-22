from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, extract
from app.database import get_db
from app.models.orm import Order, User, UserRole, Courier, OrderStatus, Rating
from app.dependencies import get_current_user
from datetime import datetime, timedelta
from typing import List, Dict

router = APIRouter()

# Admin check
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRole.ADMIN, UserRole.DISPATCHER]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@router.get("/dashboard")
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Admin only check
    if current_user.role not in [UserRole.ADMIN, UserRole.DISPATCHER]:
        return {"message": "User stats placeholder"}

    # Total Orders
    total_orders_query = await db.execute(select(func.count(Order.id)))
    total_orders = total_orders_query.scalar()

    # Active Couriers
    couriers_query = await db.execute(select(func.count(Courier.id)).where(Courier.is_online == True))
    active_couriers = couriers_query.scalar()

    # Total Revenue
    revenue_query = await db.execute(
        select(func.sum(Order.price)).where(Order.status == OrderStatus.DELIVERED)
    )
    total_revenue = revenue_query.scalar() or 0.0

    return {
        "total_orders": total_orders,
        "active_couriers": active_couriers,
        "total_revenue": round(total_revenue, 2)
    }

@router.get("/revenue")
async def get_revenue_analytics(
    days: int = Query(default=30, le=365),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Revenue breakdown by day/week/month"""
    
    # Revenue by status
    delivered_revenue = await db.execute(
        select(func.sum(Order.price)).where(Order.status == OrderStatus.DELIVERED)
    )
    total_revenue = delivered_revenue.scalar() or 0.0
    
    # Revenue in last N days
    since_date = datetime.utcnow() - timedelta(days=days)
    recent_revenue_result = await db.execute(
        select(func.sum(Order.price)).where(
            and_(
                Order.status == OrderStatus.DELIVERED,
                Order.completed_at >= since_date
            )
        )
    )
    recent_revenue = recent_revenue_result.scalar() or 0.0
    
    # Average order value
    avg_order_result = await db.execute(
        select(func.avg(Order.price)).where(Order.status == OrderStatus.DELIVERED)
    )
    avg_order_value = avg_order_result.scalar() or 0.0
    
    # Total delivered orders
    delivered_count_result = await db.execute(
        select(func.count(Order.id)).where(Order.status == OrderStatus.DELIVERED)
    )
    delivered_count = delivered_count_result.scalar() or 0
    
    return {
        "total_revenue": round(total_revenue, 2),
        f"revenue_last_{days}_days": round(recent_revenue, 2),
        "average_order_value": round(avg_order_value, 2),
        "total_delivered_orders": delivered_count,
        "period_days": days
    }

@router.get("/delivery-metrics")
async def get_delivery_metrics(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delivery success rate and performance metrics"""
    
    # Total orders
    total_result = await db.execute(select(func.count(Order.id)))
    total_orders = total_result.scalar() or 0
    
    # Delivered orders
    delivered_result = await db.execute(
        select(func.count(Order.id)).where(Order.status == OrderStatus.DELIVERED)
    )
    delivered = delivered_result.scalar() or 0
    
    # Cancelled orders
    cancelled_result = await db.execute(
        select(func.count(Order.id)).where(Order.status == OrderStatus.CANCELLED)
    )
    cancelled = cancelled_result.scalar() or 0
    
    # In progress
    in_progress_result = await db.execute(
        select(func.count(Order.id)).where(
            Order.status.in_([
                OrderStatus.CREATED,
                OrderStatus.ASSIGNED,
                OrderStatus.PICKED_UP,
                OrderStatus.IN_TRANSIT
            ])
        )
    )
    in_progress = in_progress_result.scalar() or 0
    
    # Calculate success rate
    success_rate = (delivered / total_orders * 100) if total_orders > 0 else 0
    cancellation_rate = (cancelled / total_orders * 100) if total_orders > 0 else 0
    
    # Average delivery distance
    avg_distance_result = await db.execute(
        select(func.avg(Order.distance_km)).where(Order.status == OrderStatus.DELIVERED)
    )
    avg_distance = avg_distance_result.scalar() or 0.0
    
    return {
        "total_orders": total_orders,
        "delivered_orders": delivered,
        "cancelled_orders": cancelled,
        "in_progress_orders": in_progress,
        "success_rate": round(success_rate, 2),
        "cancellation_rate": round(cancellation_rate, 2),
        "average_delivery_distance_km": round(avg_distance, 2)
    }

@router.get("/courier-performance")
async def get_courier_performance_analytics(
    limit: int = Query(default=10, le=50),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Top performing couriers"""
    
    # Get all couriers
    couriers_result = await db.execute(select(Courier))
    couriers = couriers_result.scalars().all()
    
    courier_stats = []
    for courier in couriers:
        # Count deliveries
        deliveries_result = await db.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.courier_id == courier.id,
                    Order.status == OrderStatus.DELIVERED
                )
            )
        )
        deliveries = deliveries_result.scalar() or 0
        
        # Get ratings
        ratings_result = await db.execute(
            select(Rating).where(Rating.courier_id == courier.id)
        )
        ratings = ratings_result.scalars().all()
        avg_rating = sum(r.score for r in ratings) / len(ratings) if ratings else 0.0
        
        # Calculate revenue generated
        revenue_result = await db.execute(
            select(func.sum(Order.price)).where(
                and_(
                    Order.courier_id == courier.id,
                    Order.status == OrderStatus.DELIVERED
                )
            )
        )
        revenue = revenue_result.scalar() or 0.0
        
        courier_stats.append({
            "courier_id": courier.id,
            "deliveries": deliveries,
            "rating": round(avg_rating, 2),
            "total_ratings": len(ratings),
            "revenue_generated": round(revenue, 2),
            "is_online": courier.is_online
        })
    
    # Sort by deliveries
    courier_stats.sort(key=lambda x: x["deliveries"], reverse=True)
    
    return {
        "top_performers": courier_stats[:limit],
        "total_couriers": len(courier_stats)
    }

@router.get("/heatmap")
async def get_geographic_heatmap(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Geographic data for heatmap visualization"""
    
    # Get all delivered orders
    orders_result = await db.execute(
        select(Order).where(Order.status == OrderStatus.DELIVERED)
    )
    orders = orders_result.scalars().all()
    
    # Collect pickup and delivery locations
    pickup_points = []
    delivery_points = []
    
    for order in orders:
        pickup_points.append({
            "latitude": order.pickup_latitude,
            "longitude": order.pickup_longitude,
            "weight": 1
        })
        delivery_points.append({
            "latitude": order.delivery_latitude,
            "longitude": order.delivery_longitude,
            "weight": 1
        })
    
    return {
        "pickup_heatmap": pickup_points,
        "delivery_heatmap": delivery_points,
        "total_points": len(orders) * 2
    }

@router.get("/peak-hours")
async def get_peak_hours_analytics(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Analyze order volume by hour of day"""
    
    # Get all orders
    orders_result = await db.execute(select(Order))
    orders = orders_result.scalars().all()
    
    # Group by hour
    hourly_counts = {hour: 0 for hour in range(24)}
    
    for order in orders:
        hour = order.created_at.hour
        hourly_counts[hour] += 1
    
    # Find peak hours
    sorted_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)
    peak_hours = sorted_hours[:5]
    
    return {
        "hourly_distribution": hourly_counts,
        "peak_hours": [{"hour": h, "orders": c} for h, c in peak_hours],
        "total_orders_analyzed": len(orders)
    }

@router.get("/customer-insights")
async def get_customer_insights(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Customer behavior analytics"""
    
    # Total customers
    customers_result = await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.CUSTOMER)
    )
    total_customers = customers_result.scalar() or 0
    
    # Customers with orders
    customers_with_orders_result = await db.execute(
        select(func.count(func.distinct(Order.customer_id)))
    )
    active_customers = customers_with_orders_result.scalar() or 0
    
    # Average orders per customer
    avg_orders_result = await db.execute(
        select(func.count(Order.id))
    )
    total_orders = avg_orders_result.scalar() or 0
    avg_orders = total_orders / active_customers if active_customers > 0 else 0
    
    # Repeat customers (more than 1 order)
    repeat_customers_query = await db.execute(
        select(Order.customer_id, func.count(Order.id).label('order_count'))
        .group_by(Order.customer_id)
    )
    customer_orders = repeat_customers_query.all()
    repeat_customers = sum(1 for _, count in customer_orders if count > 1)
    
    return {
        "total_customers": total_customers,
        "active_customers": active_customers,
        "repeat_customers": repeat_customers,
        "average_orders_per_customer": round(avg_orders, 2),
        "customer_retention_rate": round((repeat_customers / active_customers * 100) if active_customers > 0 else 0, 2)
    }
