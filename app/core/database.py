"""
LOOP Lojistik Platformu - Veritabanı Yönetimi
PostgreSQL + PostGIS + Redis bağlantı yönetimi
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
import redis.asyncio as redis
from typing import AsyncGenerator, Optional
from loguru import logger

from .config import settings


# Custom metadata with naming convention
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Tüm modeller için base class"""
    metadata = metadata
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', 'None')})>"


# PostgreSQL Async Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

# Redis client
redis_client: Optional[redis.Redis] = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def get_redis() -> redis.Redis:
    """Redis client dependency"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf-8"
        )
    return redis_client


async def init_db():
    """Veritabanını başlat"""
    try:
        async with engine.begin() as conn:
            # PostGIS extension'ı etkinleştir
            await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")
            
            # Tüm tabloları oluştur
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Veritabanı başarıyla başlatıldı")
        
    except Exception as e:
        logger.error(f"Veritabanı başlatma hatası: {e}")
        raise


async def close_db():
    """Veritabanı bağlantılarını kapat"""
    global redis_client
    
    if engine:
        await engine.dispose()
        
    if redis_client:
        await redis_client.close()
        
    logger.info("Veritabanı bağlantıları kapatıldı")


# Cache helper functions
async def get_cached_data(key: str) -> Optional[str]:
    """Redis'ten cache verisi al"""
    try:
        redis = await get_redis()
        return await redis.get(key)
    except Exception as e:
        logger.error(f"Redis get error: {e}")
        return None


async def set_cached_data(key: str, value: str, ttl: int = 300) -> bool:
    """Redis'e cache verisi kaydet"""
    try:
        redis = await get_redis()
        return await redis.setex(key, ttl, value)
    except Exception as e:
        logger.error(f"Redis set error: {e}")
        return False


async def delete_cached_data(key: str) -> bool:
    """Redis'ten cache verisi sil"""
    try:
        redis = await get_redis()
        return await redis.delete(key) > 0
    except Exception as e:
        logger.error(f"Redis delete error: {e}")
        return False