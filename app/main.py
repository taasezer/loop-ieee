from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import maps, weather, currency, tracking, orders, couriers, ai_engine

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

app.include_router(maps.router, prefix="/api/maps", tags=["Maps & GPS"])
app.include_router(weather.router, prefix="/api/weather", tags=["Weather"])
app.include_router(currency.router, prefix="/api/currency", tags=["Currency"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["Real-Time Tracking"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(couriers.router, prefix="/api/couriers", tags=["Couriers"])
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
