from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from utils.auth import get_current_user
from database import db
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/order/{order_id}")
async def track_order(order_id: str):
    """Get current tracking information for an order"""
    try:
        order = await db.orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        tracking_info = {
            "order_id": order["id"],
            "tracking_code": order["tracking_code"],
            "status": order["status"],
            "created_at": order["created_at"],
            "updated_at": order["updated_at"],
            "pickup_address": order["pickup_address"],
            "delivery_address": order["delivery_address"],
            "estimated_duration": order.get("estimated_duration"),
            "courier_id": order.get("courier_id")
        }
        
        # If courier assigned, get current location
        if order.get("courier_id"):
            courier = await db.couriers.find_one({"id": order["courier_id"]}, {"_id": 0})
            if courier and courier.get("current_location"):
                tracking_info["courier_location"] = courier["current_location"]
                tracking_info["courier_info"] = {
                    "vehicle_type": courier.get("vehicle_type"),
                    "rating": courier.get("rating")
                }
        
        return tracking_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Track order error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tracking information")

@router.get("/courier/{courier_id}/location-history")
async def get_courier_location_history(
    courier_id: str,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get courier's location history"""
    try:
        locations = await db.locations.find(
            {"courier_id": courier_id},
            {"_id": 0}
        ).sort("timestamp", -1).to_list(limit)
        
        return {
            "courier_id": courier_id,
            "locations": locations,
            "count": len(locations)
        }
    except Exception as e:
        logger.error(f"Get location history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve location history")

@router.get("/order/{order_id}/eta")
async def calculate_eta(order_id: str):
    """Calculate estimated time of arrival for order"""
    try:
        order = await db.orders.find_one({"id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if not order.get("courier_id"):
            return {
                "eta_minutes": None,
                "message": "Courier not yet assigned"
            }
        
        courier = await db.couriers.find_one({"id": order["courier_id"]})
        if not courier or not courier.get("current_location"):
            return {
                "eta_minutes": order.get("estimated_duration"),
                "message": "Using estimated time"
            }
        
        # In production, calculate real-time ETA based on current location and traffic
        # For now, return estimated duration
        return {
            "eta_minutes": order.get("estimated_duration"),
            "order_status": order["status"],
            "courier_location": courier["current_location"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Calculate ETA error: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate ETA")
