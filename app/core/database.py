"""
Database connection and session management
Uses SQLAlchemy with async support
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from typing import AsyncGenerator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    poolclass=QueuePool if settings.APP_ENV == "production" else NullPool,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database - create all tables
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully")


async def close_db():
    """
    Close database connections
    """
    await engine.dispose()
    logger.info("Database connections closed")


class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    async def create_tables():
        """Create all database tables"""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    @staticmethod
    async def drop_tables():
        """Drop all database tables (use with caution!)"""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    @staticmethod
    async def check_connection() -> bool:
        """
        Check if database connection is working
        
        Returns:
            bool: True if connection is successful
        """
        try:
            async with AsyncSessionLocal() as session:
                await session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {str(e)}")
            return False


# Create database manager instance
db_manager = DatabaseManager()
