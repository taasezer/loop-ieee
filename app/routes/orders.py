from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import supabase_admin
from app.services.maps_service import maps_service
from datetime import datetime

router = APIRouter()

class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    pickup_address: str
    delivery_address: str
    package_weight: float
    package_description: str
    delivery_notes: Optional[str] = None
    priority: int = 1

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    courier_id: Optional[str] = None
    delivery_notes: Optional[str] = None

@router.post("/")
async def create_order(order: OrderCreate):
    """Create a new delivery order"""
    try:
        pickup_coords = maps_service.geocode_address(order.pickup_address)
        delivery_coords = maps_service.geocode_address(order.delivery_address)

        if not pickup_coords or not delivery_coords:
            raise HTTPException(status_code=400, detail="Invalid address provided")

        distance_data = maps_service.calculate_distance_duration(
            (pickup_coords["latitude"], pickup_coords["longitude"]),
            (delivery_coords["latitude"], delivery_coords["longitude"])
        )

        order_data = {
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "pickup_latitude": pickup_coords["latitude"],
            "pickup_longitude": pickup_coords["longitude"],
            "pickup_address": pickup_coords["formatted_address"],
            "delivery_latitude": delivery_coords["latitude"],
            "delivery_longitude": delivery_coords["longitude"],
            "delivery_address": delivery_coords["formatted_address"],
            "package_weight": order.package_weight,
            "package_description": order.package_description,
            "delivery_notes": order.delivery_notes,
            "priority": order.priority,
            "status": "pending",
            "distance_km": distance_data["distance_km"] if distance_data else None,
            "estimated_duration_minutes": int(distance_data["duration_minutes"]) if distance_data else None
        }

        result = supabase_admin.table("orders").insert(order_data).execute()

        return result.data[0] if result.data else None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create order: {str(e)}")

@router.get("/")
async def list_orders(
    status: Optional[str] = None,
    courier_id: Optional[str] = None,
    limit: int = 100
):
    """List orders with optional filters"""
    try:
        query = supabase_admin.table("orders").select("*")

        if status:
            query = query.eq("status", status)

        if courier_id:
            query = query.eq("courier_id", courier_id)

        result = query.order("created_at", desc=True).limit(limit).execute()

        return {"orders": result.data, "count": len(result.data)}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch orders: {str(e)}")

@router.get("/{order_id}")
async def get_order(order_id: str):
    """Get order details"""
    try:
        result = supabase_admin.table("orders") \
            .select("*") \
            .eq("id", order_id) \
            .maybeSingle() \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Order not found")

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch order: {str(e)}")

@router.patch("/{order_id}")
async def update_order(order_id: str, update: OrderUpdate):
    """Update order status or details"""
    try:
        update_data = {k: v for k, v in update.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        if "status" in update_data:
            if update_data["status"] == "picked_up":
                update_data["picked_up_at"] = datetime.utcnow().isoformat()
            elif update_data["status"] == "delivered":
                update_data["delivered_at"] = datetime.utcnow().isoformat()

        if "courier_id" in update_data:
            update_data["assigned_at"] = datetime.utcnow().isoformat()
            update_data["status"] = "assigned"

        result = supabase_admin.table("orders") \
            .update(update_data) \
            .eq("id", order_id) \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Order not found")

        if "courier_id" in update_data and update_data["status"] == "assigned":
            courier = supabase_admin.table("couriers") \
                .update({"status": "busy"}) \
                .eq("id", update_data["courier_id"]) \
                .execute()

        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update order: {str(e)}")

@router.delete("/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an order"""
    try:
        result = supabase_admin.table("orders") \
            .update({"status": "cancelled"}) \
            .eq("id", order_id) \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Order not found")

        return {"success": True, "message": "Order cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to cancel order: {str(e)}")

@router.get("/{order_id}/route")
async def get_order_route(order_id: str):
    """Get optimized route for order"""
    try:
        order = supabase_admin.table("orders") \
            .select("*") \
            .eq("id", order_id) \
            .maybeSingle() \
            .execute()

        if not order.data:
            raise HTTPException(status_code=404, detail="Order not found")

        pickup = (order.data["pickup_latitude"], order.data["pickup_longitude"])
        delivery = (order.data["delivery_latitude"], order.data["delivery_longitude"])

        route = maps_service.get_route(pickup, delivery)

        if not route:
            raise HTTPException(status_code=400, detail="Could not calculate route")

        return route

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get route: {str(e)}")
