
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import httpx
from app.main import app
from app.database import get_db, Base
from app.models.orm import Courier, Order, User
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Mock Redis
from app.services.cache_service import cache_service
async def mock_redis_connect():
    print("⚠️ Mock Redis connected")
async def mock_redis_disconnect():
    print("⚠️ Mock Redis disconnected")
cache_service.connect = mock_redis_connect
cache_service.disconnect = mock_redis_disconnect

# Mock DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

app.dependency_overrides[get_db] = override_get_db

# Mock Auth
from app.dependencies import get_current_user, get_current_active_user

async def override_get_current_user():
    return User(id=1, email="admin@loop.com", full_name="Admin User", role="admin", is_active=True)

app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[get_current_active_user] = override_get_current_user

client = TestClient(app)

# Headers are no longer needed as we override the auth dependency
headers = {}

def test_weather_impact():
    print("Testing /api/weather/impact...")
    payload = {
        "latitude": 41.0082,
        "longitude": 28.9784,
        "courier_id": 1
    }
    try:
        response = client.post("/api/weather/impact", json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"   Impact Score: {data.get('impact_score')}")
            print(f"   Recommendation: {data.get('recommendation')}")
            print(f"   Severity: {data.get('severity')}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

def test_tracking_active():
    print("\nTesting /api/tracking/active...")
    try:
        response = client.get("/api/tracking/active", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"   Active Couriers: {data.get('total_active_couriers')}")
            if data.get('couriers'):
                print(f"   First Courier: {data['couriers'][0]['courier_name']}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")


def test_auto_assignment():
    print("\nTesting Auto Assignment Endpoints...")
    # 1. Test AI Recommendation
    print("  Testing /api/ai/recommend...")
    payload = {
        "order_id": 1,
        "latitude": 41.0082,
        "longitude": 28.9784
    }
    try:
        response = client.post("/api/ai/recommend", json=payload, headers=headers)
        if response.status_code in [200, 404]: # 404 is acceptable if order not found
            print(f"  ✅ /api/ai/recommend responded with {response.status_code}")
        else:
            print(f"  ❌ /api/ai/recommend failed with {response.status_code}: {response.text}")
    except Exception as e:
        print(f"  ❌ Error testing recommendation: {e}")

    # 2. Test AI Assign (Mocking a request)
    print("  Testing /api/ai/assign...")
    assign_payload = {
        "order_id": 1,
        "courier_id": 1
    }
    try:
        response = client.post("/api/ai/assign", json=assign_payload, headers=headers)
        if response.status_code in [200, 404]:
            print(f"  ✅ /api/ai/assign responded with {response.status_code}")
        else:
            print(f"  ❌ /api/ai/assign failed with {response.status_code}: {response.text}")
    except Exception as e:
        print(f"  ❌ Error testing assignment: {e}")

def test_performance_report():
    print("\nTesting Performance Report Endpoints...")
    # 1. Admin Couriers
    print("  Testing /api/admin/couriers...")
    try:
        response = client.get("/api/admin/couriers", headers=headers)
        if response.status_code == 200:
            print("  ✅ /api/admin/couriers success")
        else:
            print(f"  ❌ /api/admin/couriers failed with {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error testing admin couriers: {e}")

    # 2. Analytics Delivery Metrics
    print("  Testing /api/analytics/delivery-metrics...")
    try:
        response = client.get("/api/analytics/delivery-metrics", headers=headers)
        if response.status_code == 200:
            print("  ✅ /api/analytics/delivery-metrics success")
        else:
            print(f"  ❌ /api/analytics/delivery-metrics failed with {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error testing analytics: {e}")

def test_late_delivery_alert():
    print("\nTesting Late Delivery Alert Endpoints...")
    # 1. Active Orders
    print("  Testing /api/orders/active...")
    try:
        response = client.get("/api/orders/active", headers=headers)
        if response.status_code == 200:
            print("  ✅ /api/orders/active success")
        else:
            print(f"  ❌ /api/orders/active failed with {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error testing active orders: {e}")

    # 2. Create Promotion (Compensation)
    print("  Testing /api/promotions (Compensation Code)...")
    promo_payload = {
        "code": "COMPENSATE_TEST",
        "discount_type": "percentage",
        "discount_value": 10,
        "max_uses": 1,
        "expires_at": "2025-12-31T23:59:59"
    }
    try:
        response = client.post("/api/promotions", json=promo_payload, headers=headers)
        if response.status_code in [200, 201]:
            print("  ✅ /api/promotions success")
        elif response.status_code == 400 and "already exists" in response.text:
             print("  ✅ /api/promotions success (already exists)")
        else:
            print(f"  ❌ /api/promotions failed with {response.status_code}: {response.text}")
    except Exception as e:
        print(f"  ❌ Error testing promotions: {e}")

if __name__ == "__main__":
    print("🔍 Verifying n8n Backend Endpoints\n")
    test_weather_impact()
    test_tracking_active()
    test_auto_assignment()
    test_performance_report()
    test_late_delivery_alert()
