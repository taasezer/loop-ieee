from typing import Dict, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Active connections by connection type
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "couriers": set(),
            "customers": set(),
            "admin": set()
        }
        # Track which order/courier each connection is watching
        self.connection_subscriptions: Dict[WebSocket, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, connection_type: str):
        await websocket.accept()
        if connection_type in self.active_connections:
            self.active_connections[connection_type].add(websocket)
            self.connection_subscriptions[websocket] = set()
            logger.info(f"WebSocket connected: {connection_type}")
    
    def disconnect(self, websocket: WebSocket, connection_type: str):
        if connection_type in self.active_connections:
            self.active_connections[connection_type].discard(websocket)
            if websocket in self.connection_subscriptions:
                del self.connection_subscriptions[websocket]
            logger.info(f"WebSocket disconnected: {connection_type}")
    
    async def subscribe(self, websocket: WebSocket, resource_id: str):
        """Subscribe a connection to updates for a specific resource (order/courier)"""
        if websocket in self.connection_subscriptions:
            self.connection_subscriptions[websocket].add(resource_id)
    
    async def broadcast_to_type(self, message: dict, connection_type: str):
        """Broadcast message to all connections of a specific type"""
        disconnected = set()
        for connection in self.active_connections.get(connection_type, set()):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_type}: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn, connection_type)
    
    async def send_to_subscribers(self, message: dict, resource_id: str):
        """Send message to all connections subscribed to a specific resource"""
        disconnected = []
        for websocket, subscriptions in self.connection_subscriptions.items():
            if resource_id in subscriptions:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to subscriber: {e}")
                    disconnected.append(websocket)
        
        # Clean up disconnected
        for ws in disconnected:
            for conn_type in self.active_connections:
                if ws in self.active_connections[conn_type]:
                    self.disconnect(ws, conn_type)
                    break
