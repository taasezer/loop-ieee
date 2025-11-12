from fastapi import APIRouter, HTTPException, Depends
from utils.auth import require_role
from database import db
from datetime import datetime, timezone
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class BroadcastMessage(BaseModel):
    title: str
    message: str
    target: str = "all"  # all, customers, couriers

class SystemConfigUpdate(BaseModel):
    key: str
    value: str

@router.get("/orders/all")
async def get_all_orders(
    status: str = None,
    limit: int = 100,
    skip: int = 0,
    current_user: dict = Depends(require_role(["admin", "dispatcher"]))
):
    """Get all orders with admin privileges"""
    try:
        query = {}
        if status:
            query["status"] = status
        
        orders = await db.orders.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        total_count = await db.orders.count_documents(query)
        
        return {
            "orders": orders,
            "count": len(orders),
            "total": total_count,
            "page": skip // limit + 1 if limit > 0 else 1
        }
    except Exception as e:
        logger.error(f"Get all orders error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch orders")

@router.get("/users/all")
async def get_all_users(
    role: str = None,
    limit: int = 100,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Get all users"""
    try:
        query = {}
        if role:
            query["role"] = role
        
        users = await db.users.find(
            query,
            {"_id": 0, "password_hash": 0}
        ).to_list(limit)
        
        return {
            "users": users,
            "count": len(users)
        }
    except Exception as e:
        logger.error(f"Get all users error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")

@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Activate or deactivate user"""
    try:
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": {"is_active": is_active, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User status updated", "is_active": is_active}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user status")

@router.post("/broadcast")
async def broadcast_message(
    message: BroadcastMessage,
    current_user: dict = Depends(require_role(["admin", "dispatcher"]))
):
    """Broadcast message to users"""
    try:
        # Get target users
        query = {}
        if message.target == "customers":
            query["role"] = "customer"
        elif message.target == "couriers":
            query["role"] = "courier"
        
        users = await db.users.find(query, {"device_tokens": 1}).to_list(10000)
        
        # Collect all device tokens
        all_tokens = []
        for user in users:
            all_tokens.extend(user.get("device_tokens", []))
        
        logger.info(f"Broadcasting to {len(all_tokens)} devices")
        
        # In production, this would actually send notifications
        # For now, just log it
        return {
            "message": "Broadcast initiated",
            "target": message.target,
            "recipient_count": len(all_tokens),
            "title": message.title
        }
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast message")

@router.get("/config")
async def get_system_config(current_user: dict = Depends(require_role(["admin"]))):
    """Get system configuration"""
    try:
        config = await db.system_config.find({}, {"_id": 0}).to_list(100)
        return {"config": config}
    except Exception as e:
        logger.error(f"Get config error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch system config")

@router.post("/config")
async def update_system_config(
    config_update: SystemConfigUpdate,
    current_user: dict = Depends(require_role(["admin"]))
):
    """Update system configuration"""
    try:
        await db.system_config.update_one(
            {"key": config_update.key},
            {"$set": {
                "key": config_update.key,
                "value": config_update.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        return {"message": "Configuration updated", "key": config_update.key}
    except Exception as e:
        logger.error(f"Update config error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update configuration")
