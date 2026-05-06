"""
Seed script to populate database with test data (using in-memory SQLite)
Run: python seed_test_data_sqlite.py
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.orm import (
    User, Courier, Order, OrderStatus, UserRole, 
    PricingRule, PromotionCode, Notification
)
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Use in-memory SQLite instead of PostgreSQL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed_data():
    """Seed database with test data"""
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as db:
        print("🌱 Seeding test database with sample data...")
        
        # 1. Create test users
        print("\n👥 Creating users...")
        
        # Admin user
        admin = User(
            email="admin@loop.com",
            phone_number="+905551234567",
            full_name="Admin User",
            hashed_password=pwd_context.hash("admin123"),
            role=UserRole.ADMIN
        )
        db.add(admin)
        
        # Customer users
        customer1 = User(
            email="customer1@test.com",
            phone_number="+905551234568",
            full_name="Ahmet Yılmaz",
            hashed_password=pwd_context.hash("test123"),
            role=UserRole.CUSTOMER
        )
        db.add(customer1)
        
        customer2 = User(
            email="customer2@test.com",
            phone_number="+905551234569",
            full_name="Ayşe Demir",
            hashed_password=pwd_context.hash("test123"),
            role=UserRole.CUSTOMER
        )
        db.add(customer2)
        
        # Supplier users
        supplier1 = User(
            email="tedarikci@loop.com",
            phone_number="+905551234572",
            full_name="Tedarikçi Test",
            hashed_password=pwd_context.hash("admin123"),
            role=UserRole.SUPPLIER,
            company_name="Test Tedarikçi A.Ş.",
            supplier_code="SUP-TEST01"
        )
        db.add(supplier1)
        
        # Courier users
        courier_user1 = User(
            email="courier1@loop.com",
            phone_number="+905551234570",
            full_name="Mehmet Kaya",
            hashed_password=pwd_context.hash("courier123"),
            role=UserRole.COURIER
        )
        db.add(courier_user1)
        
        courier_user2 = User(
            email="courier2@loop.com",
            phone_number="+905551234571",
            full_name="Fatma Şahin",
            hashed_password=pwd_context.hash("courier123"),
            role=UserRole.COURIER
        )
        db.add(courier_user2)
        
        await db.commit()
        await db.refresh(admin)
        await db.refresh(customer1)
        await db.refresh(customer2)
        await db.refresh(supplier1)
        await db.refresh(courier_user1)
        await db.refresh(courier_user2)
        
        print(f"✅ Created 6 users (1 admin, 2 customers, 1 supplier, 2 couriers)")
        
        # 2. Create courier profiles
        print("\n🚗 Creating courier profiles...")
        
        courier1 = Courier(
            user_id=courier_user1.id,
            vehicle_type="motorcycle",
            vehicle_plate="34ABC123",
            is_online=True,
            rating=4.8,
            current_latitude=41.0082,
            current_longitude=28.9784  # Istanbul
        )
        db.add(courier1)
        
        courier2 = Courier(
            user_id=courier_user2.id,
            vehicle_type="car",
            vehicle_plate="34XYZ456",
            is_online=True,
            rating=4.6,
            current_latitude=41.0150,
            current_longitude=28.9850
        )
        db.add(courier2)
        
        await db.commit()
        await db.refresh(courier1)
        await db.refresh(courier2)
        
        print(f"✅ Created 2 courier profiles")
        
        # 3. Create pricing rule
        print("\n💰 Creating pricing rule...")
        
        pricing = PricingRule(
            name="Standard Pricing",
            base_price=15.0,
            price_per_km=3.5,
            surge_multiplier=1.0,
            is_active=True
        )
        db.add(pricing)
        await db.commit()
        
        print(f"✅ Created pricing rule: base=15₺, per_km=3.5₺")
        
        # 4. Create promotion codes
        print("\n🎁 Creating promotion codes...")
        
        promo1 = PromotionCode(
            code="WELCOME20",
            discount_type="percentage",
            discount_value=20,
            max_discount=50,
            min_order_amount=10,
            max_uses=100,
            current_uses=0,
            is_active=True,
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        db.add(promo1)
        
        promo2 = PromotionCode(
            code="SAVE10",
            discount_type="fixed",
            discount_value=10,
            max_uses=50,
            current_uses=5,
            is_active=True,
            valid_until=datetime.utcnow() + timedelta(days=15)
        )
        db.add(promo2)
        
        await db.commit()
        
        print(f"✅ Created 2 promotion codes (WELCOME20, SAVE10)")
        
        # 5. Create test orders with varied statuses
        print("\n📦 Creating orders...")
        
        # Delivered orders (35 total)
        for i in range(35):
            order = Order(
                customer_id=customer1.id if i % 2 == 0 else customer2.id,
                courier_id=courier1.id if i % 2 == 0 else courier2.id,
                pickup_address=f"Pickup Location {i+1}",
                pickup_latitude=41.0 + (i * 0.001),
                pickup_longitude=29.0 + (i * 0.001),
                delivery_address=f"Delivery Location {i+1}",
                delivery_latitude=41.0 + (i * 0.002),
                delivery_longitude=29.0 + (i * 0.002),
                distance_km=3.0 + (i % 10),
                price=20.0 + (i % 20),
                status=OrderStatus.DELIVERED,
                completed_at=datetime.utcnow() - timedelta(hours=(i % 24))
            )
            db.add(order)
        
        # In-progress orders (8 total)
        for i in range(8):
            order = Order(
                customer_id=customer1.id if i % 2 == 0 else customer2.id,
                courier_id=courier1.id if i % 2 == 0 else courier2.id,
                pickup_address=f"In Progress Pickup {i+1}",
                pickup_latitude=41.0 + (i * 0.001),
                pickup_longitude=29.0 + (i * 0.001),
                delivery_address=f"In Progress Delivery {i+1}",
                delivery_latitude=41.0 + (i * 0.002),
                delivery_longitude=29.0 + (i * 0.002),
                distance_km=4.0 + (i % 8),
                price=25.0 + (i % 15),
                status=OrderStatus.IN_TRANSIT
            )
            db.add(order)
        
        # Cancelled orders (4 total)
        for i in range(4):
            order = Order(
                customer_id=customer1.id if i % 2 == 0 else customer2.id,
                pickup_address=f"Cancelled Pickup {i+1}",
                pickup_latitude=41.0 + (i * 0.001),
                pickup_longitude=29.0 + (i * 0.001),
                delivery_address=f"Cancelled Delivery {i+1}",
                delivery_latitude=41.0 + (i * 0.002),
                delivery_longitude=29.0 + (i * 0.002),
                distance_km=2.0 + i,
                price=18.0 + (i * 2),
                status=OrderStatus.CANCELLED
            )
            db.add(order)
        
        await db.commit()
        
        print(f"✅ Created 47 orders (35 delivered, 8 in-progress, 4 cancelled)")
        
        print("\n" + "="*50)
        print("🎉 Seed completed successfully!")
        print("="*50)
        print("\n📝 Test Credentials:")
        print("  Admin:     admin@loop.com / admin123")
        print("  Customer1: customer1@test.com / test123")
        print("  Customer2: customer2@test.com / test123")
        print("  Courier1:  courier1@loop.com / courier123")
        print("  Courier2:  courier2@loop.com / courier123")
        print("\n🎁 Promotion Codes:")
        print("  WELCOME20 - 20% off (max 50₺)")
        print("  SAVE10    - 10₺ fixed discount")
        print("\n📊 Data Summary:")
        print(f"  Total Orders: 47")
        print(f"  Delivered: 35 (74.5%)")
        print(f"  In Progress: 8 (17.0%)")
        print(f"  Cancelled: 4 (8.5%)")
        print("\n⚠️  Note: Data is in-memory only (SQLite)")
        print("    For production, use seed_test_data.py with PostgreSQL")
        print("\n")

if __name__ == "__main__":
    asyncio.run(seed_data())
