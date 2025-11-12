from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime, timezone
import socketio

# Import all route modules
from routes import (
    auth,
    orders,
    couriers,
    tracking,
    maps,
    weather,
    currency,
    payments,
    notifications,
    analytics,
    admin,
    pricing,
    n8n_webhooks
)
from database import db
from middleware.rate_limiter import RateLimitMiddleware
from websocket_manager import WebSocketManager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app
app = FastAPI(title="LOOP Logistics API", version="1.0.0")

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)
socket_app = socketio.ASGIApp(sio, app)

# WebSocket Manager for real-time tracking
ws_manager = WebSocketManager()

# Create API router with prefix
api_router = APIRouter(prefix="/api")

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "LOOP Logistics Backend"
    }

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(couriers.router, prefix="/couriers", tags=["Couriers"])
api_router.include_router(tracking.router, prefix="/tracking", tags=["Tracking"])
api_router.include_router(maps.router, prefix="/maps", tags=["Maps"])
api_router.include_router(weather.router, prefix="/weather", tags=["Weather"])
api_router.include_router(currency.router, prefix="/currency", tags=["Currency"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["Pricing"])
api_router.include_router(n8n_webhooks.router, prefix="/webhooks", tags=["N8N Webhooks"])

# Include the router in the main app
app.include_router(api_router)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Socket.IO events
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    await sio.emit('connection_established', {'sid': sid}, room=sid)

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def join_tracking(sid, data):
    """Join a tracking room for real-time order updates"""
    order_id = data.get('order_id')
    if order_id:
        sio.enter_room(sid, f"order_{order_id}")
        logger.info(f"Client {sid} joined tracking room for order {order_id}")

@sio.event
async def courier_location_update(sid, data):
    """Receive location updates from courier"""
    courier_id = data.get('courier_id')
    location = data.get('location')
    
    if courier_id and location:
        # Save to database
        location_data = {
            "courier_id": courier_id,
            "latitude": location.get('latitude'),
            "longitude": location.get('longitude'),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "speed": location.get('speed', 0),
            "heading": location.get('heading', 0)
        }
        await db.locations.insert_one(location_data)
        
        # Broadcast to all clients tracking this courier
        await sio.emit('courier_location', {
            'courier_id': courier_id,
            'location': location
        }, room=f"courier_{courier_id}")

@app.on_event("startup")
async def startup_event():
    logger.info("LOOP Logistics Backend starting up...")
    # Initialize database indexes
    await db.locations.create_index([("courier_id", 1), ("timestamp", -1)])
    await db.orders.create_index([("status", 1), ("created_at", -1)])
    await db.users.create_index([("email", 1)], unique=True)
    await db.users.create_index([("phone", 1)])
    logger.info("Database indexes created")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down LOOP Logistics Backend...")
    db.client.close()
