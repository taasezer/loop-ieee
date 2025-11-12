"""
Application Configuration
Loads settings from environment variables
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application Settings
    APP_NAME: str = Field(default="LOOP", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    APP_ENV: str = Field(default="development", env="APP_ENV")
    DEBUG: bool = Field(default=True, env="DEBUG")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    API_V1_PREFIX: str = Field(default="/api/v1", env="API_V1_PREFIX")
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    RELOAD: bool = Field(default=True, env="RELOAD")
    
    # Database Configuration
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    
    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_CACHE_DB: int = Field(default=1, env="REDIS_CACHE_DB")
    REDIS_SESSION_DB: int = Field(default=2, env="REDIS_SESSION_DB")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # OpenStreetMap / Nominatim
    NOMINATIM_URL: str = Field(
        default="https://nominatim.openstreetmap.org",
        env="NOMINATIM_URL"
    )
    NOMINATIM_USER_AGENT: str = Field(
        default="LOOP-Logistics-App",
        env="NOMINATIM_USER_AGENT"
    )
    
    # OSRM
    OSRM_URL: str = Field(
        default="http://router.project-osrm.org",
        env="OSRM_URL"
    )
    
    # Mapbox
    MAPBOX_ACCESS_TOKEN: Optional[str] = Field(default=None, env="MAPBOX_ACCESS_TOKEN")
    MAPBOX_API_URL: str = Field(
        default="https://api.mapbox.com",
        env="MAPBOX_API_URL"
    )
    
    # OpenWeatherMap
    OPENWEATHER_API_KEY: Optional[str] = Field(default=None, env="OPENWEATHER_API_KEY")
    OPENWEATHER_API_URL: str = Field(
        default="https://api.openweathermap.org/data/2.5",
        env="OPENWEATHER_API_URL"
    )
    
    # Currency Exchange API
    EXCHANGE_RATE_API_KEY: Optional[str] = Field(default=None, env="EXCHANGE_RATE_API_KEY")
    EXCHANGE_RATE_API_URL: str = Field(
        default="https://api.exchangerate-api.com/v4/latest",
        env="EXCHANGE_RATE_API_URL"
    )
    
    # Firebase Cloud Messaging
    FIREBASE_CREDENTIALS_PATH: Optional[str] = Field(
        default=None,
        env="FIREBASE_CREDENTIALS_PATH"
    )
    FIREBASE_PROJECT_ID: Optional[str] = Field(default=None, env="FIREBASE_PROJECT_ID")
    
    # Twilio SMS
    TWILIO_ACCOUNT_SID: Optional[str] = Field(default=None, env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = Field(default=None, env="TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = Field(default=None, env="TWILIO_PHONE_NUMBER")
    
    # SendGrid Email
    SENDGRID_API_KEY: Optional[str] = Field(default=None, env="SENDGRID_API_KEY")
    SENDGRID_FROM_EMAIL: str = Field(
        default="noreply@loop-logistics.com",
        env="SENDGRID_FROM_EMAIL"
    )
    SENDGRID_FROM_NAME: str = Field(
        default="LOOP Logistics",
        env="SENDGRID_FROM_NAME"
    )
    
    # Stripe Payment
    STRIPE_API_KEY: Optional[str] = Field(default=None, env="STRIPE_API_KEY")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = Field(default=None, env="STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=None, env="STRIPE_WEBHOOK_SECRET")
    
    # İyzico Payment
    IYZICO_API_KEY: Optional[str] = Field(default=None, env="IYZICO_API_KEY")
    IYZICO_SECRET_KEY: Optional[str] = Field(default=None, env="IYZICO_SECRET_KEY")
    IYZICO_BASE_URL: str = Field(
        default="https://sandbox-api.iyzipay.com",
        env="IYZICO_BASE_URL"
    )
    
    # n8n Webhook
    N8N_WEBHOOK_URL: Optional[str] = Field(
        default="http://localhost:5678/webhook",
        env="N8N_WEBHOOK_URL"
    )
    N8N_API_KEY: Optional[str] = Field(default=None, env="N8N_API_KEY")
    
    # Celery Configuration
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/3",
        env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/4",
        env="CELERY_RESULT_BACKEND"
    )
    
    # File Upload
    MAX_UPLOAD_SIZE: int = Field(default=10485760, env="MAX_UPLOAD_SIZE")  # 10MB
    UPLOAD_DIR: str = Field(default="./uploads", env="UPLOAD_DIR")
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=["jpg", "jpeg", "png", "pdf"],
        env="ALLOWED_EXTENSIONS"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    LOG_FILE: str = Field(default="./logs/app.log", env="LOG_FILE")
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    PROMETHEUS_PORT: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    # AI/ML Settings
    ML_MODEL_PATH: str = Field(default="./app/ai/models", env="ML_MODEL_PATH")
    COURIER_ASSIGNMENT_MODEL: str = Field(
        default="courier_assignment_v1.pkl",
        env="COURIER_ASSIGNMENT_MODEL"
    )
    ROUTE_OPTIMIZATION_ENABLED: bool = Field(default=True, env="ROUTE_OPTIMIZATION_ENABLED")
    
    # WebSocket Settings
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    WS_MAX_CONNECTIONS: int = Field(default=10000, env="WS_MAX_CONNECTIONS")
    
    # Geofencing
    DEFAULT_GEOFENCE_RADIUS_KM: float = Field(default=50.0, env="DEFAULT_GEOFENCE_RADIUS_KM")
    
    # Pricing Configuration
    BASE_PRICE: float = Field(default=10.0, env="BASE_PRICE")
    PRICE_PER_KM: float = Field(default=2.5, env="PRICE_PER_KM")
    SURGE_MULTIPLIER_MAX: float = Field(default=3.0, env="SURGE_MULTIPLIER_MAX")
    WEATHER_PRICE_MULTIPLIER: float = Field(default=1.2, env="WEATHER_PRICE_MULTIPLIER")
    
    # Notification Settings
    NOTIFICATION_RETRY_ATTEMPTS: int = Field(default=3, env="NOTIFICATION_RETRY_ATTEMPTS")
    NOTIFICATION_BATCH_SIZE: int = Field(default=100, env="NOTIFICATION_BATCH_SIZE")
    
    # Session Configuration
    SESSION_EXPIRE_SECONDS: int = Field(default=3600, env="SESSION_EXPIRE_SECONDS")
    
    # OTP Configuration
    OTP_EXPIRE_MINUTES: int = Field(default=5, env="OTP_EXPIRE_MINUTES")
    OTP_LENGTH: int = Field(default=6, env="OTP_LENGTH")
    
    # Admin Configuration
    ADMIN_EMAIL: str = Field(default="admin@loop-logistics.com", env="ADMIN_EMAIL")
    ADMIN_PASSWORD: str = Field(default="change-this-password", env="ADMIN_PASSWORD")
    
    # Backup Configuration
    BACKUP_ENABLED: bool = Field(default=True, env="BACKUP_ENABLED")
    BACKUP_SCHEDULE: str = Field(default="0 2 * * *", env="BACKUP_SCHEDULE")
    BACKUP_RETENTION_DAYS: int = Field(default=30, env="BACKUP_RETENTION_DAYS")
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_EXTENSIONS", pre=True)
    def parse_allowed_extensions(cls, v):
        """Parse allowed extensions from string or list"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()
