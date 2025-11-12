from fastapi import APIRouter, HTTPException, Request
from database import db
from datetime import datetime, timezone
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/order-created")
async def order_created_webhook(request: Request):
    """Webhook endpoint for n8n when order is created"""
    try:
        data = await request.json()
        logger.info(f"n8n webhook - order created: {data}")
        
        # Process order creation event
        # This can trigger automated workflows in n8n
        
        return {"status": "received", "event": "order_created"}
    except Exception as e:
        logger.error(f"Order created webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/courier-assigned")
async def courier_assigned_webhook(request: Request):
    """Webhook endpoint for n8n when courier is assigned"""
    try:
        data = await request.json()
        logger.info(f"n8n webhook - courier assigned: {data}")
        
        # Log assignment decision
        assignment_log = {
            "order_id": data.get("order_id"),
            "courier_id": data.get("courier_id"),
            "assignment_score": data.get("assignment_score"),
            "distance_to_pickup": data.get("distance_to_pickup"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "courier_assigned"
        }
        
        await db.route_history.insert_one(assignment_log)
        
        return {"status": "received", "event": "courier_assigned"}
    except Exception as e:
        logger.error(f"Courier assigned webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/delivery-completed")
async def delivery_completed_webhook(request: Request):
    """Webhook endpoint for n8n when delivery is completed"""
    try:
        data = await request.json()
        logger.info(f"n8n webhook - delivery completed: {data}")
        
        # Process delivery completion
        # Can trigger payment processing, notifications, etc.
        
        return {"status": "received", "event": "delivery_completed"}
    except Exception as e:
        logger.error(f"Delivery completed webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/analytics-event")
async def analytics_event_webhook(request: Request):
    """Generic webhook for analytics events from n8n"""
    try:
        data = await request.json()
        logger.info(f"n8n webhook - analytics event: {data}")
        
        # Store analytics event
        event_log = {
            "event_type": data.get("event_type"),
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await db.route_history.insert_one(event_log)
        
        return {"status": "received", "event": "analytics_event"}
    except Exception as e:
        logger.error(f"Analytics event webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
