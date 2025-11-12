"""
WebSocket endpoints for real-time tracking and notifications
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, Set
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.order_tracking: Dict[str, Set[WebSocket]] = {}
        self.courier_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_type: str = "user"):
        await websocket.accept()
        if connection_type == "user":
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
        elif connection_type == "courier":
            self.courier_connections[user_id] = websocket
        logger.info(f"WebSocket connected: {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str, connection_type: str = "user"):
        if connection_type == "user" and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
        elif connection_type == "courier" and user_id in self.courier_connections:
            del self.courier_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Send error: {str(e)}")
    
    async def track_order(self, websocket: WebSocket, order_id: str):
        if order_id not in self.order_tracking:
            self.order_tracking[order_id] = set()
        self.order_tracking[order_id].add(websocket)


manager = ConnectionManager()


@router.websocket("/ws/tracking/{order_id}")
async def track_order(websocket: WebSocket, order_id: str):
    """Real-time order tracking"""
    await websocket.accept()
    await manager.track_order(websocket, order_id)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "order_id": order_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        logger.info(f"Disconnected from order: {order_id}")


@router.websocket("/ws/courier/{courier_id}")
async def courier_connection(websocket: WebSocket, courier_id: str):
    """Courier real-time connection"""
    await manager.connect(websocket, courier_id, "courier")
    
    try:
        await websocket.send_json({"type": "connected", "courier_id": courier_id})
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "ack"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, courier_id, "courier")
