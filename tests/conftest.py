import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.config import settings
import asyncio

# Use an in-memory SQLite database for testing, or a separate test Postgres DB
# For simplicity in this environment, we'll try to use the same DB but different tables (or just mock it)
# Ideally: TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
# But we don't have a test DB easily available. We will use SQLite for tests to be safe and fast.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

from httpx import AsyncClient, ASGITransport

@pytest.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        try:
            yield db_session
        finally:
            await db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
