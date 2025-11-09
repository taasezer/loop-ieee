from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str

    GOOGLE_MAPS_API_KEY: str
    OPENWEATHER_API_KEY: str
    EXCHANGE_RATE_API_KEY: str

    N8N_WEBHOOK_URL: str = ""
    REDIS_URL: str = "redis://localhost:6379"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
