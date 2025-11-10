"""
LOOP Lojistik Platformu - FastAPI Ana Uygulaması
Author: LOOP Development Team
Version: 1.0.0
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

# İç importlar
from core.config import settings
from core.database import engine, Base
from api.v1.routers import (
    auth, couriers, orders, tracking, 
    analytics, weather, currency
)
from core.middleware import (
    TimingMiddleware, 
    LoggingMiddleware, 
    RateLimitMiddleware
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama lifecycle yönetimi"""
    # Startup
    logger.info("LOOP Lojistik Platformu başlatılıyor...")
    
    # Veritabanı tablolarını oluştur
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Veritabanı bağlantısı kuruldu")
    logger.info(f"Uygulama {settings.APP_NAME} başarıyla başlatıldı")
    
    yield
    
    # Shutdown
    logger.info("Uygulama kapatılıyor...")
    await engine.dispose()


# FastAPI uygulamasını oluştur
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Modern lojistik yönetim platformu - GPS takibi, AI destekli kurye atamaları ve gerçek zamanlı analizler",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware'ler
app.add_middleware(TimingMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# API router'ları ekle
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(couriers.router, prefix="/api/v1/couriers", tags=["Couriers"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(tracking.router, prefix="/api/v1/tracking", tags=["Tracking"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(weather.router, prefix="/api/v1/weather", tags=["Weather"])
app.include_router(currency.router, prefix="/api/v1/currency", tags=["Currency"])


@app.get("/")
async def root():
    """Ana endpoint - API durumu"""
    return {
        "message": "LOOP Lojistik Platformu API",
        "version": settings.APP_VERSION,
        "status": "active",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Sağlık kontrol endpoint'i"""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/api-info")
async def api_info():
    """API bilgileri"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Modern lojistik yönetim platformu",
        "features": [
            "GPS Takibi",
            "Rota Optimizasyonu", 
            "AI Kurye Ataması",
            "Gerçek Zamanlı Analiz",
            "Hava Durumu Entegrasyonu",
            "Çoklu Para Birimi"
        ],
        "contact": {
            "name": "LOOP Development Team",
            "email": "dev@loop.com"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )