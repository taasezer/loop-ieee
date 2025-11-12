"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient

from app.main import app
from app.core.database import Base, get_db
from app.config import settings


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://loop_user:loop_password@localhost:5432/loop_test_db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test client with database session override
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "phone_number": "+1234567890",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "customer"
    }


@pytest.fixture
def sample_courier_data():
    """Sample courier data for testing"""
    return {
        "vehicle_type": "motorcycle",
        "vehicle_make": "Honda",
        "vehicle_model": "CBR",
        "license_plate": "ABC123"
    }


@pytest.fixture
def sample_order_data():
    """Sample order data for testing"""
    return {
        "pickup_address": "123 Main St, City, Country",
        "pickup_latitude": 40.7128,
        "pickup_longitude": -74.0060,
        "delivery_address": "456 Oak Ave, City, Country",
        "delivery_latitude": 40.7589,
        "delivery_longitude": -73.9851,
        "delivery_contact_name": "John Doe",
        "delivery_contact_phone": "+1234567890",
        "package_description": "Test package",
        "payment_method": "card"
    }
