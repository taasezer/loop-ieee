from fastapi import APIRouter, HTTPException, Depends
from models.courier import Courier, CourierCreate, CourierStatus, CourierStatusUpdate, CourierLocationUpdate
from utils.auth import get_current_user, require_role
from database import db
from datetime import datetime, timezone
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=dict)
async def create_courier(
    courier_data: CourierCreate,
    current_user: dict = Depends(require_role(["admin", "dispatcher"]))
):
    """Create a new courier profile"""
    try:
        # Verify user exists
        user = await db.users.find_one({"id": courier_data.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if courier profile already exists
        existing = await db.couriers.find_one({"user_id": courier_data.user_id})
        if existing:
            raise HTTPException(status_code=400, detail="Courier profile already exists")
        
        courier = Courier(
            user_id=courier_data.user_id,
            vehicle_type=courier_data.vehicle_type,
            vehicle_number=courier_data.vehicle_number,
            license_number=courier_data.license_number
        )
        
        courier_dict = courier.model_dump()
        courier_dict["created_at"] = courier_dict["created_at"].isoformat()
        courier_dict["updated_at"] = courier_dict["updated_at"].isoformat()
        
        await db.couriers.insert_one(courier_dict)
        
        return {
            "message": "Courier profile created",
            "courier": courier_dict
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create courier error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create courier profile")

@router.get("/")
async def get_couriers(
    status: str = None,
    limit: int = 100,
    current_user: dict = Depends(require_role(["admin", "dispatcher"]))
):
    """Get all couriers"""
    try:
        query = {}
        if status:
            query["status"] = status
        
        couriers = await db.couriers.find(query, {"_id": 0}).to_list(limit)
        
        return {
            "couriers": couriers,
            "count": len(couriers)
        }
    except Exception as e:
        logger.error(f"Get couriers error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve couriers")

@router.get("/me")
async def get_my_courier_profile(current_user: dict = Depends(get_current_user)):
    """Get current courier's profile"""
    try:
        courier = await db.couriers.find_one({"user_id": current_user["sub"]}, {"_id": 0})
        if not courier:
            raise HTTPException(status_code=404, detail="Courier profile not found")
        
        return courier
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get courier profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve courier profile")

@router.patch("/status")
async def update_courier_status(
    status_update: CourierStatusUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update courier online/offline status"""
    try:
        result = await db.couriers.update_one(
            {"user_id": current_user["sub"]},
            {"$set": {
                "status": status_update.status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Courier profile not found")
        
        return {"message": "Status updated", "new_status": status_update.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update courier status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update status")

@router.post("/location")
async def update_location(
    location: CourierLocationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update courier's current location"""
    try:
        # Get courier profile
        courier = await db.couriers.find_one({"user_id": current_user["sub"]})
        if not courier:
            raise HTTPException(status_code=404, detail="Courier profile not found")
        
        location_data = {
            "lat": location.latitude,
            "lng": location.longitude
        }
        
        # Update courier's current location
        await db.couriers.update_one(
            {"user_id": current_user["sub"]},
            {"$set": {
                "current_location": location_data,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Save to location history
        location_history = {
            "courier_id": courier["id"],
            "latitude": location.latitude,
            "longitude": location.longitude,
            "speed": location.speed,
            "heading": location.heading,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.locations.insert_one(location_history)
        
        return {"message": "Location updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update location error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update location")

@router.get("/{courier_id}/stats")
async def get_courier_stats(
    courier_id: str,
    current_user: dict = Depends(require_role(["admin", "dispatcher"]))
):
    """Get courier statistics"""
    try:
        courier = await db.couriers.find_one({"id": courier_id}, {"_id": 0})
        if not courier:
            raise HTTPException(status_code=404, detail="Courier not found")
        
        # Get earnings data
        earnings = await db.earnings.find({"courier_id": courier_id}, {"_id": 0}).to_list(1000)
        total_earnings = sum([e.get("amount", 0) for e in earnings])
        
        return {
            "courier_id": courier_id,
            "total_deliveries": courier.get("total_deliveries", 0),
            "completed_deliveries": courier.get("completed_deliveries", 0),
            "cancelled_deliveries": courier.get("cancelled_deliveries", 0),
            "rating": courier.get("rating", 5.0),
            "performance_score": courier.get("performance_score", 100.0),
            "total_earnings": total_earnings,
            "current_status": courier.get("status"),
            "vehicle_type": courier.get("vehicle_type")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get courier stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve courier stats")
