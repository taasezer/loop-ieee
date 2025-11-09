from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import supabase_admin
from datetime import datetime

router = APIRouter()

class CourierCreate(BaseModel):
    name: str
    phone: str
    email: str
    vehicle_type: str
    license_plate: Optional[str] = None

class CourierUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    vehicle_type: Optional[str] = None
    license_plate: Optional[str] = None

@router.post("/")
async def create_courier(courier: CourierCreate):
    """Create a new courier"""
    try:
        result = supabase_admin.table("couriers").insert({
            "name": courier.name,
            "phone": courier.phone,
            "email": courier.email,
            "vehicle_type": courier.vehicle_type,
            "license_plate": courier.license_plate,
            "status": "offline"
        }).execute()

        return result.data[0] if result.data else None

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create courier: {str(e)}")

@router.get("/")
async def list_couriers(status: Optional[str] = None, limit: int = 100):
    """List all couriers"""
    try:
        query = supabase_admin.table("couriers").select("*")

        if status:
            query = query.eq("status", status)

        result = query.order("created_at", desc=True).limit(limit).execute()

        return {"couriers": result.data, "count": len(result.data)}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch couriers: {str(e)}")

@router.get("/{courier_id}")
async def get_courier(courier_id: str):
    """Get courier details"""
    try:
        result = supabase_admin.table("couriers") \
            .select("*") \
            .eq("id", courier_id) \
            .maybeSingle() \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Courier not found")

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch courier: {str(e)}")

@router.patch("/{courier_id}")
async def update_courier(courier_id: str, update: CourierUpdate):
    """Update courier information"""
    try:
        update_data = {k: v for k, v in update.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        result = supabase_admin.table("couriers") \
            .update(update_data) \
            .eq("id", courier_id) \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Courier not found")

        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update courier: {str(e)}")

@router.delete("/{courier_id}")
async def delete_courier(courier_id: str):
    """Delete a courier"""
    try:
        result = supabase_admin.table("couriers") \
            .delete() \
            .eq("id", courier_id) \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Courier not found")

        return {"success": True, "message": "Courier deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete courier: {str(e)}")

@router.get("/{courier_id}/stats")
async def get_courier_stats(courier_id: str):
    """Get courier statistics"""
    try:
        courier = supabase_admin.table("couriers") \
            .select("*") \
            .eq("id", courier_id) \
            .maybeSingle() \
            .execute()

        if not courier.data:
            raise HTTPException(status_code=404, detail="Courier not found")

        orders = supabase_admin.table("orders") \
            .select("status, created_at, delivered_at") \
            .eq("courier_id", courier_id) \
            .execute()

        completed = len([o for o in orders.data if o["status"] == "delivered"])
        in_progress = len([o for o in orders.data if o["status"] in ["assigned", "picked_up", "in_transit"]])

        return {
            "courier": courier.data,
            "statistics": {
                "total_deliveries": courier.data["total_deliveries"],
                "rating": float(courier.data["rating"]),
                "completed_orders": completed,
                "orders_in_progress": in_progress,
                "current_status": courier.data["status"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch stats: {str(e)}")
