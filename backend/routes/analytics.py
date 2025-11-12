from fastapi import APIRouter, HTTPException, Depends
from utils.auth import require_role
from database import db
from datetime import datetime, timedelta, timezone
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/dashboard")
async def get_dashboard_metrics(current_user: dict = Depends(require_role(["admin", "dispatcher"]))):
    """Get overall dashboard metrics"""
    try:
        # Total orders
        total_orders = await db.orders.count_documents({})
        
        # Active orders
        active_orders = await db.orders.count_documents({
            "status": {"$in": ["created", "assigned", "accepted", "picked", "in_transit"]}
        })
        
        # Completed orders today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        completed_today = await db.orders.count_documents({
            "status": "delivered",
            "delivery_time": {"$gte": today_start.isoformat()}
        })
        
        # Online couriers
        online_couriers = await db.couriers.count_documents({"status": "online"})
        
        # Total revenue (simplified)
        all_orders = await db.orders.find(
            {"status": "delivered"},
            {"final_price": 1, "_id": 0}
        ).to_list(10000)
        total_revenue = sum([o.get("final_price", o.get("estimated_price", 0)) for o in all_orders])
        
        return {
            "total_orders": total_orders,
            "active_orders": active_orders,
            "completed_today": completed_today,
            "online_couriers": online_couriers,
            "total_revenue": round(total_revenue, 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Dashboard metrics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard metrics")

@router.get("/orders/stats")
async def get_order_statistics(
    days: int = 30,
    current_user: dict = Depends(require_role(["admin", "dispatcher"]))
):
    """Get order statistics for specified period"""
    try:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        orders = await db.orders.find(
            {"created_at": {"$gte": start_date.isoformat()}},
            {"_id": 0}
        ).to_list(10000)
        
        # Calculate stats
        status_breakdown = {}
        for order in orders:
            status = order.get("status", "unknown")
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        # Average delivery time
        completed_orders = [o for o in orders if o.get("status") == "delivered" and o.get("created_at") and o.get("delivery_time")]
        avg_delivery_time = 0
        if completed_orders:
            total_time = 0
            for order in completed_orders:
                try:
                    created = datetime.fromisoformat(order["created_at"])
                    delivered = datetime.fromisoformat(order["delivery_time"])
                    total_time += (delivered - created).total_seconds() / 60
                except:
                    pass
            avg_delivery_time = total_time / len(completed_orders) if completed_orders else 0
        
        return {
            "period_days": days,
            "total_orders": len(orders),
            "status_breakdown": status_breakdown,
            "average_delivery_time_minutes": round(avg_delivery_time, 2),
            "success_rate": round(status_breakdown.get("delivered", 0) / len(orders) * 100, 2) if orders else 0
        }
    except Exception as e:
        logger.error(f"Order statistics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch order statistics")

@router.get("/couriers/performance")
async def get_courier_performance(current_user: dict = Depends(require_role(["admin", "dispatcher"]))):
    """Get courier performance metrics"""
    try:
        couriers = await db.couriers.find({}, {"_id": 0}).to_list(1000)
        
        performance_data = []
        for courier in couriers:
            performance_data.append({
                "courier_id": courier["id"],
                "rating": courier.get("rating", 5.0),
                "total_deliveries": courier.get("total_deliveries", 0),
                "completed_deliveries": courier.get("completed_deliveries", 0),
                "performance_score": courier.get("performance_score", 100.0),
                "total_earnings": courier.get("total_earnings", 0),
                "status": courier.get("status"),
                "vehicle_type": courier.get("vehicle_type")
            })
        
        # Sort by performance score
        performance_data.sort(key=lambda x: x["performance_score"], reverse=True)
        
        return {
            "total_couriers": len(couriers),
            "top_performers": performance_data[:10],
            "all_couriers": performance_data
        }
    except Exception as e:
        logger.error(f"Courier performance error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch courier performance")

@router.get("/revenue")
async def get_revenue_analytics(
    days: int = 30,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get revenue analytics"""
    try:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        orders = await db.orders.find(
            {
                "status": "delivered",
                "delivery_time": {"$gte": start_date.isoformat()}
            },
            {"_id": 0}
        ).to_list(10000)
        
        total_revenue = sum([o.get("final_price", o.get("estimated_price", 0)) for o in orders])
        average_order_value = total_revenue / len(orders) if orders else 0
        
        # Payment method breakdown
        payment_methods = {}
        for order in orders:
            method = order.get("payment_method", "unknown")
            payment_methods[method] = payment_methods.get(method, 0) + 1
        
        return {
            "period_days": days,
            "total_revenue": round(total_revenue, 2),
            "total_orders": len(orders),
            "average_order_value": round(average_order_value, 2),
            "payment_method_breakdown": payment_methods
        }
    except Exception as e:
        logger.error(f"Revenue analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch revenue analytics")
