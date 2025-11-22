import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User",
        "phone_number": "+1234567890",
        "role": "customer"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    # Register first
    await client.post("/api/auth/register", json={
        "email": "login@example.com",
        "password": "password123",
        "full_name": "Login User",
        "phone_number": "+0987654321",
        "role": "customer"
    })
    
    # Login
    response = await client.post("/api/auth/login", data={
        "username": "login@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
