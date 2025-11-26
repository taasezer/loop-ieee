from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.config import settings
from app.routes import maps, weather, currency, tracking, orders, couriers, ai_engine, auth, payments, analytics, notifications, courier_orders, admin, promotions
from app.websockets.server import manager
from app.middleware.rate_limit import limiter, custom_rate_limit_handler
from app.services.cache_service import cache_service
from slowapi.errors import RateLimitExceeded

app = FastAPI(
    title="LOOP Logistics API",
    description="Backend API for LOOP Logistics Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# Lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await cache_service.connect()
    print("✅ Redis cache connected")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await cache_service.disconnect()
    print("👋 Redis cache disconnected")

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle incoming messages (e.g., location updates)
            # Expected format: {"type": "location_update", "lat": ..., "lon": ..., "order_id": ...}
            if data.get("type") == "location_update":
                # Broadcast to order room
                order_id = str(data.get("order_id"))
                await manager.broadcast_to_room(order_id, data)
            elif data.get("type") == "join_room":
                room_id = str(data.get("room_id"))
                manager.join_room(user_id, room_id)
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(promotions.router, prefix="/api/promotions", tags=["Promotions"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(maps.router, prefix="/api/maps", tags=["Maps & GPS"])
app.include_router(weather.router, prefix="/api/weather", tags=["Weather"])
app.include_router(currency.router, prefix="/api/currency", tags=["Currency"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["Real-Time Tracking"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(couriers.router, prefix="/api/couriers", tags=["Couriers"])
app.include_router(courier_orders.router, prefix="/api/courier/orders", tags=["Courier Orders"])
app.include_router(ai_engine.router, prefix="/api/ai", tags=["AI Decision Engine"])

@app.get("/")
async def root():
    return {
        "message": "LOOP Logistics API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
