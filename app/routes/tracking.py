from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List
from app.services.tracking_service import tracking_service
import json
import asyncio

router = APIRouter()

class LocationUpdate(BaseModel):
    courier_id: str
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None

class NearbyRequest(BaseModel):
    latitude: float
    longitude: float
    max_distance_km: float = 10.0
    status: str = "available"

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@router.post("/update")
async def update_location(update: LocationUpdate):
    """Update courier location"""
    result = await tracking_service.update_courier_location(
        courier_id=update.courier_id,
        latitude=update.latitude,
        longitude=update.longitude,
        accuracy=update.accuracy,
        speed=update.speed,
        heading=update.heading
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Update failed"))

    await manager.broadcast({
        "type": "location_update",
        "courier_id": update.courier_id,
        "location": result["location"]
    })

    return result

@router.get("/courier/{courier_id}")
async def get_courier_location(courier_id: str):
    """Get courier's current location"""
    location = await tracking_service.get_courier_location(courier_id)
    if not location:
        raise HTTPException(status_code=404, detail="Courier location not found")
    return location

@router.get("/active")
async def get_all_active_locations(status: str = "available"):
    """Get all active courier locations"""
    locations = await tracking_service.get_all_active_locations(status)
    return {"couriers": locations, "count": len(locations)}

@router.get("/history/{courier_id}")
async def get_location_history(courier_id: str, hours: int = 24):
    """Get courier's location history"""
    history = await tracking_service.get_location_history(courier_id, hours)
    return {"courier_id": courier_id, "history": history, "count": len(history)}

@router.get("/order/{order_id}")
async def track_order(order_id: str):
    """Track order delivery in real-time"""
    tracking_info = await tracking_service.track_order_delivery(order_id)
    if not tracking_info:
        raise HTTPException(status_code=404, detail="Order tracking not available")
    return tracking_info

@router.post("/nearby")
async def find_nearby_couriers(request: NearbyRequest):
    """Find nearby available couriers"""
    couriers = await tracking_service.get_nearby_couriers(
        latitude=request.latitude,
        longitude=request.longitude,
        max_distance_km=request.max_distance_km,
        status=request.status
    )
    return {"couriers": couriers, "count": len(couriers)}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time location updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "subscribe_order":
                order_id = message.get("order_id")
                while True:
                    tracking_info = await tracking_service.track_order_delivery(order_id)
                    if tracking_info:
                        await websocket.send_json({
                            "type": "order_update",
                            "data": tracking_info
                        })
                    await asyncio.sleep(5)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
