"""
LOOP Lojistik Platformu - WebSocket Yöneticisi
Gerçek zamanlı bildirimler ve canlı veri akışı
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, List, Optional, Any
from datetime import datetime
import json
import asyncio
from dataclasses import dataclass, asdict
from loguru import logger
import redis.asyncio as redis

from core.config import settings
from core.database import get_redis


@dataclass
class WebSocketMessage:
    """WebSocket mesaj formatı"""
    type: str  # 'location_update', 'order_status', 'notification', 'system'
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    room: Optional[str] = None


class WebSocketManager:
    """WebSocket bağlantı yöneticisi"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_rooms: Dict[str, Set[str]] = {}  # user_id -> set of rooms
        self.room_users: Dict[str, Set[str]] = {}  # room -> set of user_ids
        self.redis_client: Optional[redis.Redis] = None
        
        # Mesaj türlerine göre handler'lar
        self.message_handlers = {
            'subscribe': self._handle_subscribe,
            'unsubscribe': self._handle_unsubscribe,
            'location_update': self._handle_location_update,
            'order_status': self._handle_order_status,
            'ping': self._handle_ping
        }
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """WebSocket bağlantısını kabul et"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_rooms[user_id] = set()
        
        # Redis'e bağlantı bildir
        await self._publish_to_redis('user_connected', {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"WebSocket bağlantısı kuruldu: {user_id}")
        
        # Hoş geldin mesajı gönder
        welcome_msg = WebSocketMessage(
            type='system',
            data={'message': 'Bağlantı başarılı', 'user_id': user_id},
            timestamp=datetime.now(),
            user_id=user_id
        )
        await self.send_personal_message(user_id, welcome_msg)
    
    async def disconnect(self, user_id: str):
        """WebSocket bağlantısını kapat"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            
            # Tüm odalardan çıkar
            if user_id in self.user_rooms:
                for room in self.user_rooms[user_id].copy():
                    await self._remove_from_room(user_id, room)
                del self.user_rooms[user_id]
            
            # Redis'e bağlantı kesme bildir
            await self._publish_to_redis('user_disconnected', {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"WebSocket bağlantısı kapatıldı: {user_id}")
    
    async def handle_message(self, user_id: str, message: str):
        """Gelen mesajı işle"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](user_id, data)
            else:
                logger.warning(f"Bilinmeyen mesaj tipi: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Geçersiz JSON mesajı: {message}")
        except Exception as e:
            logger.error(f"Mesaj işleme hatası: {e}")
    
    async def send_personal_message(self, user_id: str, message: WebSocketMessage):
        """Kişisel mesaj gönder"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(asdict(message)))
            except Exception as e:
                logger.error(f"Kişisel mesaj gönderme hatası: {e}")
                await self.disconnect(user_id)
    
    async def broadcast_to_room(self, room: str, message: WebSocketMessage, exclude_user: Optional[str] = None):
        """Odaya mesaj yayınla"""
        if room in self.room_users:
            for user_id in self.room_users[room]:
                if user_id != exclude_user:
                    await self.send_personal_message(user_id, message)
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        """Tüm bağlı kullanıcılara mesaj yayınla"""
        for user_id in self.active_connections:
            await self.send_personal_message(user_id, message)
    
    # Mesaj handler'ları
    async def _handle_subscribe(self, user_id: str, data: Dict):
        """Odaya abone ol"""
        room = data.get('room')
        if room:
            await self._add_to_room(user_id, room)
            
            # Onay mesajı gönder
            confirmation = WebSocketMessage(
                type='system',
                data={'message': f'{room} odasına abone olundu'},
                timestamp=datetime.now(),
                user_id=user_id,
                room=room
            )
            await self.send_personal_message(user_id, confirmation)
    
    async def _handle_unsubscribe(self, user_id: str, data: Dict):
        """Oda aboneliğini iptal et"""
        room = data.get('room')
        if room:
            await self._remove_from_room(user_id, room)
    
    async def _handle_location_update(self, user_id: str, data: Dict):
        """Konum güncelleme mesajı"""
        location_data = data.get('data', {})
        
        # Konum verisini Redis'e kaydet
        await self._update_location_in_redis(user_id, location_data)
        
        # İlgili odalara yayınla
        message = WebSocketMessage(
            type='location_update',
            data=location_data,
            timestamp=datetime.now(),
            user_id=user_id
        )
        
        # Kurye'nin bulunduğu odalara yayınla
        if user_id in self.user_rooms:
            for room in self.user_rooms[user_id]:
                await self.broadcast_to_room(room, message, exclude_user=user_id)
    
    async def _handle_order_status(self, user_id: str, data: Dict):
        """Sipariş durumu mesajı"""
        order_data = data.get('data', {})
        
        message = WebSocketMessage(
            type='order_status',
            data=order_data,
            timestamp=datetime.now(),
            user_id=user_id
        )
        
        # İlgili sipariş odasına yayınla
        order_id = order_data.get('order_id')
        if order_id:
            await self.broadcast_to_room(f'order_{order_id}', message)
    
    async def _handle_ping(self, user_id: str, data: Dict):
        """Ping-pong mekanizması"""
        pong_message = WebSocketMessage(
            type='pong',
            data={'timestamp': datetime.now().isoformat()},
            timestamp=datetime.now(),
            user_id=user_id
        )
        await self.send_personal_message(user_id, pong_message)
    
    # Yardımcı metodlar
    async def _add_to_room(self, user_id: str, room: str):
        """Kullanıcıyı odaya ekle"""
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        
        self.user_rooms[user_id].add(room)
        
        if room not in self.room_users:
            self.room_users[room] = set()
        
        self.room_users[room].add(user_id)
        
        logger.info(f"Kullanıcı {user_id} {room} odasına eklendi")
    
    async def _remove_from_room(self, user_id: str, room: str):
        """Kullanıcıyı odadan çıkar"""
        if user_id in self.user_rooms and room in self.user_rooms[user_id]:
            self.user_rooms[user_id].remove(room)
        
        if room in self.room_users and user_id in self.room_users[room]:
            self.room_users[room].remove(user_id)
            
            # Oda boşsa temizle
            if not self.room_users[room]:
                del self.room_users[room]
        
        logger.info(f"Kullanıcı {user_id} {room} odasından çıkarıldı")
    
    async def _update_location_in_redis(self, user_id: str, location_data: Dict):
        """Konum verisini Redis'e kaydet"""
        try:
            redis_client = await get_redis()
            
            location_key = f"courier:{user_id}:location"
            location_data['timestamp'] = datetime.now().isoformat()
            
            await redis_client.setex(
                location_key,
                300,  # 5 dakika TTL
                json.dumps(location_data)
            )
            
            # Geçmiş konumları kaydet
            history_key = f"courier:{user_id}:location_history"
            await redis_client.lpush(history_key, json.dumps(location_data))
            await redis_client.ltrim(history_key, 0, 999)  # Son 1000 konum
            
        except Exception as e:
            logger.error(f"Redis konum güncelleme hatası: {e}")
    
    async def _publish_to_redis(self, channel: str, data: Dict):
        """Redis'e mesaj yayınla"""
        try:
            redis_client = await get_redis()
            await redis_client.publish(channel, json.dumps(data))
        except Exception as e:
            logger.error(f"Redis publish hatası: {e}")


# Global WebSocket manager instance
ws_manager = WebSocketManager()


# WebSocket endpoint'leri için yardımcı fonksiyonlar
async def notify_order_status_change(order_id: str, status: str, user_id: str):
    """Sipariş durumu değişikliğini bildir"""
    message = WebSocketMessage(
        type='order_status',
        data={
            'order_id': order_id,
            'status': status,
            'timestamp': datetime.now().isoformat()
        },
        timestamp=datetime.now()
    )
    
    # Sipariş odasına ve kullanıcıya bildir
    await ws_manager.broadcast_to_room(f'order_{order_id}', message)
    await ws_manager.send_personal_message(user_id, message)


async def notify_courier_location_update(courier_id: str, location: Dict):
    """Kurye konum güncellemesini bildir"""
    message = WebSocketMessage(
        type='location_update',
        data={
            'courier_id': courier_id,
            'location': location,
            'timestamp': datetime.now().isoformat()
        },
        timestamp=datetime.now(),
        user_id=courier_id
    )
    
    # Kurye'nin odalarına yayınla
    if courier_id in ws_manager.user_rooms:
        for room in ws_manager.user_rooms[courier_id]:
            await ws_manager.broadcast_to_room(room, message)


async def notify_system_event(event_type: str, data: Dict, room: Optional[str] = None):
    """Sistem olaylarını bildir"""
    message = WebSocketMessage(
        type='system',
        data={'event_type': event_type, **data},
        timestamp=datetime.now()
    )
    
    if room:
        await ws_manager.broadcast_to_room(room, message)
    else:
        await ws_manager.broadcast_to_all(message)


# WebSocket connection handler
class WebSocketConnection:
    """WebSocket bağlantı yöneticisi"""
    
    def __init__(self, websocket: WebSocket, user_id: str):
        self.websocket = websocket
        self.user_id = user_id
        self.is_connected = True
    
    async def handle_connection(self):
        """Bağlantıyı yönet"""
        await ws_manager.connect(self.websocket, self.user_id)
        
        try:
            while self.is_connected:
                # Ping-pong mekanizması
                try:
                    data = await asyncio.wait_for(
                        self.websocket.receive_text(),
                        timeout=30.0
                    )
                    await ws_manager.handle_message(self.user_id, data)
                except asyncio.TimeoutError:
                    # Ping gönder
                    ping_msg = WebSocketMessage(
                        type='ping',
                        data={},
                        timestamp=datetime.now()
                    )
                    await ws_manager.send_personal_message(self.user_id, ping_msg)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket bağlantısı kesildi: {self.user_id}")
        except Exception as e:
            logger.error(f"WebSocket hatası: {e}")
        finally:
            await ws_manager.disconnect(self.user_id)
            self.is_connected = False