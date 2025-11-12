from fastapi import APIRouter, HTTPException, Depends
from models.order import Order, OrderCreate, OrderStatus, OrderStatusUpdate
from utils.auth import get_current_user, require_role
from database import db
from services.map_service import map_service
from services.pricing_service import pricing_service
from services.weather_service import weather_service
from services.ai_assignment_service import ai_assignment_service
from datetime import datetime, timezone
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=dict)
async def create_order(order_data: OrderCreate, current_user: dict = Depends(get_current_user)):
    """Create a new delivery order"""
    try:
        # Calculate route and distance
        route = await map_service.calculate_route(
            {"latitude": order_data.pickup_address.latitude, "longitude": order_data.pickup_address.longitude},
            {"latitude": order_data.delivery_address.latitude, "longitude": order_data.delivery_address.longitude}
        )
        
        # Get weather conditions
        weather = await weather_service.get_current_weather(
            order_data.pickup_address.latitude,
            order_data.pickup_address.longitude
        )
        
        # Calculate price
        pricing = await pricing_service.calculate_price(
            distance_km=route["distance"],
            duration_minutes=route["duration"],
            priority=order_data.priority,
            pickup_location={
                "latitude": order_data.pickup_address.latitude,
                "longitude": order_data.pickup_address.longitude
            }
        )
        
        # Create order
        order = Order(
            customer_id=order_data.customer_id,
            pickup_address=order_data.pickup_address,
            delivery_address=order_data.delivery_address,
            package_description=order_data.package_description,
            package_weight=order_data.package_weight,
            package_dimensions=order_data.package_dimensions,
            priority=order_data.priority,
            estimated_distance=route["distance"],
            estimated_duration=route["duration"],
            estimated_price=pricing["final_price"],
            scheduled_pickup=order_data.scheduled_pickup,
            customer_notes=order_data.customer_notes,
            payment_method=order_data.payment_method,
            weather_conditions=weather
        )
        
        order_dict = order.model_dump()
        order_dict["created_at"] = order_dict["created_at"].isoformat()
        order_dict["updated_at"] = order_dict["updated_at"].isoformat()
        if order_dict.get("scheduled_pickup"):
            order_dict["scheduled_pickup"] = order_dict["scheduled_pickup"].isoformat()
        
        await db.orders.insert_one(order_dict)
        
        # Try to auto-assign courier
        best_courier_id = await ai_assignment_service.find_best_courier(order_dict)
        if best_courier_id:
            await db.orders.update_one(
                {"id": order.id},
                {"$set": {"courier_id": best_courier_id, "status": OrderStatus.ASSIGNED}}
            )
            order_dict["courier_id"] = best_courier_id
            order_dict["status"] = OrderStatus.ASSIGNED
        
        return {
            "message": "Order created successfully",
            "order": order_dict,
            "route_info": route,
            "pricing_breakdown": pricing
        }
    except Exception as e:
        logger.error(f"Order creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Order creation failed: {str(e)}")

@router.get("/")
async def get_orders(
    status: str = None,
    customer_id: str = None,
    courier_id: str = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get orders with filters"""
    try:
        query = {}
        
        # Role-based filtering
        if current_user["role"] == "customer":
            query["customer_id"] = current_user["sub"]
        elif current_user["role"] == "courier":
            query["courier_id"] = current_user["sub"]
        
        # Additional filters
        if status:
            query["status"] = status
        if customer_id and current_user["role"] in ["admin", "dispatcher"]:
            query["customer_id"] = customer_id
        if courier_id and current_user["role"] in ["admin", "dispatcher"]:
            query["courier_id"] = courier_id
        
        orders = await db.orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
        
        return {
            "orders": orders,
            "count": len(orders)
        }
    except Exception as e:
        logger.error(f"Get orders error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve orders")

@router.get("/{order_id}")
async def get_order(order_id: str, current_user: dict = Depends(get_current_user)):
    """Get order by ID"""
    try:
        order = await db.orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check authorization
        if current_user["role"] == "customer" and order["customer_id"] != current_user["sub"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        if current_user["role"] == "courier" and order.get("courier_id") != current_user["sub"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get order error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve order")

@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update order status"""
    try:
        order = await db.orders.find_one({"id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        update_data = {
            "status": status_update.status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Add timestamp for specific status changes
        if status_update.status == OrderStatus.PICKED:
            update_data["pickup_time"] = datetime.now(timezone.utc).isoformat()
        elif status_update.status == OrderStatus.DELIVERED:
            update_data["delivery_time"] = datetime.now(timezone.utc).isoformat()
        
        if status_update.notes:
            if current_user["role"] == "courier":
                update_data["courier_notes"] = status_update.notes
            else:
                update_data["customer_notes"] = status_update.notes
        
        await db.orders.update_one({"id": order_id}, {"$set": update_data})
        
        return {"message": "Order status updated", "new_status": status_update.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update order status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update order status")

@router.post("/{order_id}/assign/{courier_id}")
async def assign_courier(
    order_id: str,
    courier_id: str,
    current_user: dict = Depends(require_role(["admin", "dispatcher"]))
):
    """Manually assign courier to order"""
    try:
        # Verify courier exists and is available
        courier = await db.couriers.find_one({"id": courier_id})
        if not courier:
            raise HTTPException(status_code=404, detail="Courier not found")
        
        if courier["status"] not in ["online"]:
            raise HTTPException(status_code=400, detail="Courier is not available")
        
        # Update order
        await db.orders.update_one(
            {"id": order_id},
            {"$set": {
                "courier_id": courier_id,
                "status": OrderStatus.ASSIGNED,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"message": "Courier assigned successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assign courier error: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign courier")
