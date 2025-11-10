"""
LOOP Lojistik Platformu - Konfigürasyon Yönetimi
Environment bazlı konfigürasyon ayarları
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Uygulama konfigürasyon sınıfı"""
    
    # Uygulama Ayarları
    APP_NAME: str = "LOOP Lojistik Platformu"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # Güvenlik Ayarları
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 gün
    
    # CORS Ayarları
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://loop.com",
        "https://app.loop.com"
    ]
    
    # Veritabanı Ayarları
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/loop_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Redis Ayarları
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # API Anahtarları
    MAPBOX_ACCESS_TOKEN: str = ""
    OPENWEATHER_API_KEY: str = ""
    CURRENCY_API_KEY: str = ""
    N8N_WEBHOOK_URL: str = ""
    
    # Harita ve GPS Ayarları
    DEFAULT_MAP_CENTER_LAT: float = 41.0082  # Istanbul
    DEFAULT_MAP_CENTER_LNG: float = 28.9784
    DEFAULT_MAP_ZOOM: int = 12
    MAX_ROUTE_DISTANCE_KM: int = 100
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Cache Ayarları
    CACHE_TTL_SECONDS: int = 300  # 5 dakika
    WEATHER_CACHE_TTL: int = 1800  # 30 dakika
    CURRENCY_CACHE_TTL: int = 3600  # 1 saat
    
    # Kurye ve Teslimat Ayarları
    MAX_COURIER_ASSIGNMENT_DISTANCE_KM: int = 10
    DEFAULT_DELIVERY_TIME_MINUTES: int = 45
    PRIORITY_DELIVERY_TIME_MINUTES: int = 25
    
    # Notification Ayarları
    SMS_API_KEY: Optional[str] = None
    EMAIL_SMTP_HOST: Optional[str] = None
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Settings singleton'ı döndürür"""
    return Settings()


# Global settings instance
settings = get_settings()