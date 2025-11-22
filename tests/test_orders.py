import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_order(client: AsyncClient):
    # Register and login first
    await client.post("/api/auth/register", json={
        "email": "order@example.com",
        "password": "password123",
        "full_name": "Order User",
        "phone_number": "+1122334455",
        "role": "customer"
    })
    
    login_res = await client.post("/api/auth/login", data={
        "username": "order@example.com",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create Order
    response = await client.post("/api/orders/", json={
        "pickup_address": "123 Main St",
        "pickup_latitude": 40.7128,
        "pickup_longitude": -74.0060,
        "delivery_address": "456 Elm St",
        "delivery_latitude": 40.7328,
        "delivery_longitude": -74.0160,
        "distance_km": 5.0
    }, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["pickup_address"] == "123 Main St"
    assert data["status"] == "created"
    assert "price" in data

@pytest.mark.asyncio
async def test_get_orders(client: AsyncClient):
    # Register and login
    await client.post("/api/auth/register", json={
        "email": "orders@example.com",
        "password": "password123",
        "full_name": "Orders User",
        "phone_number": "+5544332211",
        "role": "customer"
    })
    
    login_res = await client.post("/api/auth/login", data={
        "username": "orders@example.com",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create an order
    await client.post("/api/orders/", json={
        "pickup_address": "Start",
        "pickup_latitude": 10.0,
        "pickup_longitude": 10.0,
        "delivery_address": "End",
        "delivery_latitude": 10.1,
        "delivery_longitude": 10.1,
        "distance_km": 2.0
    }, headers=headers)
    
    # Get Orders
    response = await client.get("/api/orders/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["pickup_address"] == "Start"
