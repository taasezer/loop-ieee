"""
LOOP Lojistik Platformu - IoT Servisi
IoT sensörleri ve drone yönetimi
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from loguru import logger
import paho.mqtt.client as mqtt
import threading
import queue

from core.config import settings
from core.websocket import notify_courier_location_update, notify_system_event
from services.mapbox_service import MapboxService


class SensorType(Enum):
    """Sensör tipleri"""
    GPS = "gps"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    ACCELEROMETER = "accelerometer"
    GYROSCOPE = "gyroscope"
    PROXIMITY = "proximity"
    BATTERY = "battery"
    FUEL = "fuel"
    SPEED = "speed"


class DroneStatus(Enum):
    """Drone durumları"""
    IDLE = "idle"
    TAKING_OFF = "taking_off"
    FLYING = "flying"
    LANDING = "landing"
    LANDED = "landed"
    CHARGING = "charging"
    MAINTENANCE = "maintenance"
    ERROR = "error"


@dataclass
class SensorData:
    """Sensör verisi"""
    sensor_id: str
    sensor_type: SensorType
    value: float
    unit: str
    timestamp: datetime
    location: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Drone:
    """Drone bilgileri"""
    id: str
    model: str
    status: DroneStatus
    battery_level: float
    location: Dict[str, float]
    altitude: float
    speed: float
    payload_weight: float
    max_payload: float
    flight_time: float
    last_maintenance: datetime
    assigned_order: Optional[str] = None


@dataclass
class DroneMission:
    """Drone görevi"""
    id: str
    drone_id: str
    order_id: str
    pickup_location: Dict[str, float]
    delivery_location: Dict[str, float]
    payload_weight: float
    estimated_duration: float
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class MQTTClient:
    """MQTT client yöneticisi"""
    
    def __init__(self, broker_host: str, broker_port: int = 1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.message_queue = queue.Queue()
        self.is_connected = False
        
        # Callback'leri ayarla
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT bağlantı callback'i"""
        if rc == 0:
            self.is_connected = True
            logger.info(f"MQTT bağlantısı kuruldu: {self.broker_host}:{self.broker_port}")
            
            # Topic'lere abone ol
            client.subscribe("loop/sensors/+")
            client.subscribe("loop/drones/+/status")
            client.subscribe("loop/drones/+/location")
            client.subscribe("loop/drones/+/sensors")
            
        else:
            logger.error(f"MQTT bağlantı hatası: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT bağlantı kesilme callback'i"""
        self.is_connected = False
        logger.info("MQTT bağlantısı kesildi")
    
    def _on_message(self, client, userdata, msg):
        """MQTT mesaj callback'i"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"MQTT mesajı alındı: {topic}")
            
            # Mesajı kuyruğa ekle
            self.message_queue.put({
                'topic': topic,
                'payload': payload,
                'timestamp': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"MQTT mesaj işleme hatası: {e}")
    
    def connect(self):
        """MQTT broker'a bağlan"""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"MQTT bağlantı hatası: {e}")
    
    def disconnect(self):
        """MQTT bağlantısını kapat"""
        self.client.loop_stop()
        self.client.disconnect()
    
    def publish(self, topic: str, payload: Dict):
        """MQTT mesajı yayınla"""
        try:
            self.client.publish(topic, json.dumps(payload))
        except Exception as e:
            logger.error(f"MQTT publish hatası: {e}")


class IoTService:
    """IoT sensör ve drone yönetim servisi"""
    
    def __init__(self):
        self.mqtt_client = MQTTClient(
            broker_host=settings.MQTT_BROKER_HOST or "localhost",
            broker_port=settings.MQTT_BROKER_PORT or 1883
        )
        
        self.drones: Dict[str, Drone] = {}
        self.active_missions: Dict[str, DroneMission] = {}
        self.sensor_data_buffer: List[SensorData] = []
        self.mapbox_service = MapboxService()
        
        # Konfigürasyon
        self.buffer_size = 1000
        self.batch_size = 100
        self.save_interval = 60  # Saniye
        
        # Arka plan görevleri
        self.running = False
        self.message_processor_task = None
        self.data_saver_task = None
    
    async def start(self):
        """IoT servisini başlat"""
        try:
            self.running = True
            
            # MQTT bağlantısını başlat
            self.mqtt_client.connect()
            
            # Arka plan görevlerini başlat
            self.message_processor_task = asyncio.create_task(self._message_processor())
            self.data_saver_task = asyncio.create_task(self._data_saver())
            
            logger.info("IoT servisi başlatıldı")
            
        except Exception as e:
            logger.error(f"IoT servisi başlatma hatası: {e}")
            raise
    
    async def stop(self):
        """IoT servisini durdur"""
        try:
            self.running = False
            
            # Arka plan görevlerini durdur
            if self.message_processor_task:
                self.message_processor_task.cancel()
            
            if self.data_saver_task:
                self.data_saver_task.cancel()
            
            # MQTT bağlantısını kapat
            self.mqtt_client.disconnect()
            
            # Kalan verileri kaydet
            await self._save_sensor_data()
            
            logger.info("IoT servisi durduruldu")
            
        except Exception as e:
            logger.error(f"IoT servisi durdurma hatası: {e}")
    
    async def _message_processor(self):
        """MQTT mesajlarını işle"""
        while self.running:
            try:
                # Mesaj kuyruğunu kontrol et
                if not self.mqtt_client.message_queue.empty():
                    message = self.mqtt_client.message_queue.get_nowait()
                    await self._process_mqtt_message(message)
                
                else:
                    # CPU'yu rahatlat
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Mesaj işleme hatası: {e}")
                await asyncio.sleep(1)
    
    async def _data_saver(self):
        """Sensör verilerini periyodik olarak kaydet"""
        while self.running:
            try:
                await asyncio.sleep(self.save_interval)
                await self._save_sensor_data()
                
            except Exception as e:
                logger.error(f"Veri kaydetme hatası: {e}")
    
    async def _process_mqtt_message(self, message: Dict):
        """MQTT mesajını işle"""
        try:
            topic = message['topic']
            payload = json.loads(message['payload'])
            
            # Topic'e göre mesajı yönlendir
            if topic.startswith('loop/sensors/'):
                await self._process_sensor_data(payload)
            
            elif topic.startswith('loop/drones/'):
                if '/status' in topic:
                    await self._process_drone_status(payload)
                elif '/location' in topic:
                    await self._process_drone_location(payload)
                elif '/sensors' in topic:
                    await self._process_drone_sensors(payload)
            
        except json.JSONDecodeError:
            logger.error(f"Geçersiz JSON mesajı: {message}")
        except Exception as e:
            logger.error(f"MQTT mesaj işleme hatası: {e}")
    
    async def _process_sensor_data(self, data: Dict):
        """Sensör verisini işle"""
        try:
            sensor_data = SensorData(
                sensor_id=data['sensor_id'],
                sensor_type=SensorType(data['sensor_type']),
                value=data['value'],
                unit=data['unit'],
                timestamp=datetime.fromisoformat(data['timestamp']),
                location=data.get('location'),
                metadata=data.get('metadata')
            )
            
            # Veriyi buffer'a ekle
            self.sensor_data_buffer.append(sensor_data)
            
            # Anlık alarm kontrolü
            await self._check_sensor_alarms(sensor_data)
            
            # WebSocket ile bildir
            await notify_system_event('sensor_data', asdict(sensor_data))
            
        except Exception as e:
            logger.error(f"Sensör verisi işleme hatası: {e}")
    
    async def _process_drone_status(self, data: Dict):
        """Drone durumunu işle"""
        try:
            drone_id = data['drone_id']
            
            # Drone'u güncelle veya oluştur
            if drone_id not in self.drones:
                self.drones[drone_id] = Drone(
                    id=drone_id,
                    model=data.get('model', 'Unknown'),
                    status=DroneStatus(data['status']),
                    battery_level=data.get('battery_level', 0),
                    location=data.get('location', {'lat': 0, 'lng': 0}),
                    altitude=data.get('altitude', 0),
                    speed=data.get('speed', 0),
                    payload_weight=data.get('payload_weight', 0),
                    max_payload=data.get('max_payload', 5),
                    flight_time=data.get('flight_time', 0),
                    last_maintenance=datetime.fromisoformat(data.get('last_maintenance', datetime.now().isoformat()))
                )
            else:
                # Mevcut drone'u güncelle
                drone = self.drones[drone_id]
                drone.status = DroneStatus(data['status'])
                drone.battery_level = data.get('battery_level', drone.battery_level)
                drone.altitude = data.get('altitude', drone.altitude)
                drone.speed = data.get('speed', drone.speed)
                drone.flight_time = data.get('flight_time', drone.flight_time)
            
            logger.info(f"Drone durumu güncellendi: {drone_id} - {data['status']}")
            
            # WebSocket ile bildir
            await notify_system_event('drone_status', {
                'drone_id': drone_id,
                'status': data['status'],
                'battery_level': data.get('battery_level', 0)
            })
            
        except Exception as e:
            logger.error(f"Drone durumu işleme hatası: {e}")
    
    async def _process_drone_location(self, data: Dict):
        """Drone konumunu işle"""
        try:
            drone_id = data['drone_id']
            location = data['location']
            
            if drone_id in self.drones:
                self.drones[drone_id].location = location
            
            # WebSocket ile konum güncellemesi
            await notify_courier_location_update(drone_id, location)
            
        except Exception as e:
            logger.error(f"Drone konumu işleme hatası: {e}")
    
    async def _process_drone_sensors(self, data: Dict):
        """Drone sensör verilerini işle"""
        try:
            drone_id = data['drone_id']
            sensors = data.get('sensors', [])
            
            for sensor_info in sensors:
                sensor_data = SensorData(
                    sensor_id=f"{drone_id}_{sensor_info['type']}",
                    sensor_type=SensorType(sensor_info['type']),
                    value=sensor_info['value'],
                    unit=sensor_info['unit'],
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    location=self.drones.get(drone_id, {}).location
                )
                
                self.sensor_data_buffer.append(sensor_data)
                await self._check_sensor_alarms(sensor_data)
            
        except Exception as e:
            logger.error(f"Drone sensör verisi işleme hatası: {e}")
    
    async def _check_sensor_alarms(self, sensor_data: SensorData):
        """Sensör alarm kontrolü"""
        try:
            alarm_triggered = False
            
            if sensor_data.sensor_type == SensorType.BATTERY:
                if sensor_data.value < 20:
                    alarm_triggered = True
                    logger.warning(f"Düşük batarya alarmı: {sensor_data.sensor_id} - %{sensor_data.value}")
            
            elif sensor_data.sensor_type == SensorType.TEMPERATURE:
                if sensor_data.value > 60 or sensor_data.value < -20:
                    alarm_triggered = True
                    logger.warning(f"Sıcaklık alarmı: {sensor_data.sensor_id} - {sensor_data.value}°C")
            
            elif sensor_data.sensor_type == SensorType.SPEED:
                if sensor_data.value > 120:  # km/sa
                    alarm_triggered = True
                    logger.warning(f"Hız alarmı: {sensor_data.sensor_id} - {sensor_data.value} km/s")
            
            if alarm_triggered:
                await notify_system_event('sensor_alarm', {
                    'sensor_id': sensor_data.sensor_id,
                    'sensor_type': sensor_data.sensor_type.value,
                    'value': sensor_data.value,
                    'threshold_exceeded': True
                })
        
        except Exception as e:
            logger.error(f"Alarm kontrolü hatası: {e}")
    
    async def _save_sensor_data(self):
        """Sensör verilerini kaydet"""
        try:
            if len(self.sensor_data_buffer) == 0:
                return
            
            # Batch olarak kaydet
            batch_size = min(len(self.sensor_data_buffer), self.batch_size)
            batch_data = self.sensor_data_buffer[:batch_size]
            
            # Veritabanına kaydet (mock)
            await self._save_to_database(batch_data)
            
            # Buffer'dan sil
            self.sensor_data_buffer = self.sensor_data_buffer[batch_size:]
            
            logger.debug(f"{len(batch_data)} sensör verisi kaydedildi")
            
        except Exception as e:
            logger.error(f"Sensör verisi kaydetme hatası: {e}")
    
    async def _save_to_database(self, sensor_data_list: List[SensorData]):
        """Veritabanına kaydet (mock implementasyon)"""
        # Bu fonksiyon gerçek veritabanı kaydı yapacak
        for sensor_data in sensor_data_list:
            logger.debug(f"Kaydediliyor: {sensor_data.sensor_id} - {sensor_data.value}")
    
    # Public API metodları
    async def register_drone(self, drone_data: Dict) -> bool:
        """Yeni drone kaydet"""
        try:
            drone = Drone(
                id=drone_data['id'],
                model=drone_data.get('model', 'Unknown'),
                status=DroneStatus.IDLE,
                battery_level=100.0,
                location=drone_data.get('location', {'lat': 0, 'lng': 0}),
                altitude=0,
                speed=0,
                payload_weight=0,
                max_payload=drone_data.get('max_payload', 5),
                flight_time=0,
                last_maintenance=datetime.now()
            )
            
            self.drones[drone.id] = drone
            logger.info(f"Drone kaydedildi: {drone.id}")
            return True
            
        except Exception as e:
            logger.error(f"Drone kaydetme hatası: {e}")
            return False
    
    async def assign_mission(self, mission_data: Dict) -> Optional[str]:
        """Drone'a görev ata"""
        try:
            drone_id = mission_data['drone_id']
            
            # Drone kontrolü
            if drone_id not in self.drones:
                logger.error(f"Drone bulunamadı: {drone_id}")
                return None
            
            drone = self.drones[drone_id]
            
            # Uygunluk kontrolü
            if drone.status != DroneStatus.IDLE:
                logger.error(f"Drone meşgul: {drone_id} - {drone.status}")
                return None
            
            if drone.battery_level < 30:
                logger.error(f"Düşük batarya: {drone_id} - %{drone.battery_level}")
                return None
            
            # Görev oluştur
            mission = DroneMission(
                id=f"mission_{datetime.now().timestamp()}",
                drone_id=drone_id,
                order_id=mission_data['order_id'],
                pickup_location=mission_data['pickup_location'],
                delivery_location=mission_data['delivery_location'],
                payload_weight=mission_data['payload_weight'],
                estimated_duration=mission_data.get('estimated_duration', 600),  # 10 dakika
                status='assigned',
                created_at=datetime.now()
            )
            
            self.active_missions[mission.id] = mission
            drone.assigned_order = mission.order_id
            drone.status = DroneStatus.TAKING_OFF
            
            logger.info(f"Görev atandı: {mission.id} -> {drone_id}")
            
            # MQTT ile drone'a bildir
            self.mqtt_client.publish(f"loop/drones/{drone_id}/mission", {
                'mission_id': mission.id,
                'pickup_location': mission.pickup_location,
                'delivery_location': mission.delivery_location,
                'payload_weight': mission.payload_weight
            })
            
            return mission.id
            
        except Exception as e:
            logger.error(f"Görev atama hatası: {e}")
            return None
    
    async def get_drone_status(self, drone_id: str) -> Optional[Dict]:
        """Drone durumunu al"""
        if drone_id not in self.drones:
            return None
        
        drone = self.drones[drone_id]
        return {
            'id': drone.id,
            'model': drone.model,
            'status': drone.status.value,
            'battery_level': drone.battery_level,
            'location': drone.location,
            'altitude': drone.altitude,
            'speed': drone.speed,
            'payload_weight': drone.payload_weight,
            'max_payload': drone.max_payload,
            'flight_time': drone.flight_time,
            'assigned_order': drone.assigned_order
        }
    
    async def get_available_drones(self) -> List[Dict]:
        """Müsait drone'ları al"""
        available_drones = []
        
        for drone in self.drones.values():
            if (drone.status == DroneStatus.IDLE and 
                drone.battery_level > 50 and 
                not drone.assigned_order):
                available_drones.append({
                    'id': drone.id,
                    'model': drone.model,
                    'battery_level': drone.battery_level,
                    'max_payload': drone.max_payload,
                    'location': drone.location
                })
        
        return available_drones
    
    async def get_sensor_analytics(self, sensor_type: SensorType, time_range: int = 3600) -> Dict:
        """Sensör analitiği al"""
        try:
            # Son 1 saatlik veriyi analiz et (mock)
            current_time = datetime.now()
            
            analytics = {
                'sensor_type': sensor_type.value,
                'time_range': time_range,
                'total_readings': 0,
                'average_value': 0,
                'min_value': float('inf'),
                'max_value': float('-inf'),
                'alerts_count': 0,
                'devices_count': 0
            }
            
            # Buffer'daki verileri analiz et
            for sensor_data in self.sensor_data_buffer:
                if sensor_data.sensor_type == sensor_type:
                    time_diff = (current_time - sensor_data.timestamp).total_seconds()
                    
                    if time_diff <= time_range:
                        analytics['total_readings'] += 1
                        analytics['average_value'] += sensor_data.value
                        analytics['min_value'] = min(analytics['min_value'], sensor_data.value)
                        analytics['max_value'] = max(analytics['max_value'], sensor_data.value)
            
            if analytics['total_readings'] > 0:
                analytics['average_value'] /= analytics['total_readings']
            else:
                analytics['min_value'] = 0
                analytics['max_value'] = 0
            
            analytics['devices_count'] = len(set(
                sd.sensor_id for sd in self.sensor_data_buffer 
                if sd.sensor_type == sensor_type
            ))
            
            return analytics
            
        except Exception as e:
            logger.error(f"Sensör analitiği alma hatası: {e}")
            return {}


# Global IoT service instance
iot_service = IoTService()


# Yardımcı fonksiyonlar
async def start_iot_services():
    """IoT servislerini başlat"""
    await iot_service.start()


async def stop_iot_services():
    """IoT servislerini durdur"""
    await iot_service.stop()


async def register_iot_drone(drone_data: Dict) -> bool:
    """IoT drone kaydet"""
    return await iot_service.register_drone(drone_data)


async def assign_drone_mission(mission_data: Dict) -> Optional[str]:
    """Drone görevi ata"""
    return await iot_service.assign_mission(mission_data)


async def get_iot_analytics(sensor_type: str, time_range: int = 3600) -> Dict:
    """IoT analitiği al"""
    sensor_enum = SensorType(sensor_type)
    return await iot_service.get_sensor_analytics(sensor_enum, time_range)


# MQTT Topic yapısı
MQTT_TOPICS = {
    # Sensörler
    'SENSORS': 'loop/sensors/+',
    'SENSOR_DATA': 'loop/sensors/{sensor_id}/data',
    'SENSOR_STATUS': 'loop/sensors/{sensor_id}/status',
    
    # Drone'lar
    'DRONES': 'loop/drones/+',
    'DRONE_STATUS': 'loop/drones/{drone_id}/status',
    'DRONE_LOCATION': 'loop/drones/{drone_id}/location',
    'DRONE_SENSORS': 'loop/drones/{drone_id}/sensors',
    'DRONE_MISSION': 'loop/drones/{drone_id}/mission',
    'DRONE_COMMAND': 'loop/drones/{drone_id}/command',
    
    # Sistem
    'SYSTEM_ALERTS': 'loop/system/alerts',
    'SYSTEM_EVENTS': 'loop/system/events',
    'SYSTEM_HEARTBEAT': 'loop/system/heartbeat'
}