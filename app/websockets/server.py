from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict

class ConnectionManager:
    def __init__(self):
        # Store active connections: {user_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Store room subscriptions: {order_id: [user_id]}
        self.rooms: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        # Cleanup rooms
        for room_id in self.rooms:
            if user_id in self.rooms[room_id]:
                self.rooms[room_id].remove(user_id)

    async def broadcast_to_room(self, room_id: str, message: dict):
        if room_id in self.rooms:
            for user_id in self.rooms[room_id]:
                if user_id in self.active_connections:
                    connection = self.active_connections[user_id]
                    await connection.send_json(message)

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

    def join_room(self, user_id: str, room_id: str):
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        if user_id not in self.rooms[room_id]:
            self.rooms[room_id].append(user_id)

manager = ConnectionManager()
