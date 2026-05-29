"""
Seed script to populate database with test data
Run: python seed_test_data.py
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.orm import (
    User, Courier, Order, OrderStatus, UserRole, 
    PricingRule, PromotionCode, Notification
)
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

from sqlalchemy import text

async def seed_data():
    """Seed database with test data"""
    from app.database import engine, Base
    
    # Tüm tabloları sıfırla ve baştan oluştur (Şema güncellemeleri için en garantisi)
    print("🔧 Dropping and recreating all database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as db:
        print("🌱 Seeding database with test data...")
        
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
            current_longitude=28.9784,  # Istanbul
            supplier_id=supplier1.id
        )
        db.add(courier1)
        
        courier2 = Courier(
            user_id=courier_user2.id,
            vehicle_type="car",
            vehicle_plate="34XYZ456",
            is_online=True,
            rating=4.6,
            current_latitude=41.0150,
            current_longitude=28.9850,
            supplier_id=supplier1.id
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
                pickup_address=f"Pickup Location {i+1}, Istanbul",
                pickup_latitude=41.0 + (i * 0.001),
                pickup_longitude=29.0 + (i * 0.001),
                delivery_address=f"Delivery Location {i+1}, Istanbul",
                delivery_latitude=41.0 + (i * 0.002),
                delivery_longitude=29.0 + (i * 0.002),
                distance_km=3.0 + (i % 10),
                price=20.0 + (i % 20),
                status=OrderStatus.DELIVERED,
                completed_at=datetime.utcnow() - timedelta(hours=(i % 24)),
                tracking_code=f"LOOP-TEST-D{i}",
                cargo_type="Kutu",
                cargo_weight=2.0 + (i % 5)
            )
            db.add(order)
        
        # In-progress orders (8 total)
        for i in range(8):
            order = Order(
                customer_id=customer1.id if i % 2 == 0 else customer2.id,
                courier_id=courier1.id if i % 2 == 0 else courier2.id,
                pickup_address=f"In Progress Pickup {i+1}, Istanbul",
                pickup_latitude=41.0 + (i * 0.001),
                pickup_longitude=29.0 + (i * 0.001),
                delivery_address=f"In Progress Delivery {i+1}, Istanbul",
                delivery_latitude=41.0 + (i * 0.002),
                delivery_longitude=29.0 + (i * 0.002),
                distance_km=4.0 + (i % 8),
                price=25.0 + (i % 15),
                status=OrderStatus.IN_TRANSIT,
                tracking_code=f"LOOP-TEST-T{i}",
                cargo_type="Zarf" if i % 2 == 0 else "Kutu",
                cargo_weight=0.5 if i % 2 == 0 else 5.5
            )
            db.add(order)
        
        # Cancelled orders (4 total)
        for i in range(4):
            order = Order(
                customer_id=customer1.id if i % 2 == 0 else customer2.id,
                pickup_address=f"Cancelled Pickup {i+1}, Istanbul",
                pickup_latitude=41.0 + (i * 0.001),
                pickup_longitude=29.0 + (i * 0.001),
                delivery_address=f"Cancelled Delivery {i+1}, Istanbul",
                delivery_latitude=41.0 + (i * 0.002),
                delivery_longitude=29.0 + (i * 0.002),
                distance_km=2.0 + i,
                price=18.0 + (i * 2),
                status=OrderStatus.CANCELLED,
                tracking_code=f"LOOP-TEST-C{i}",
                cargo_type="Koli",
                cargo_weight=15.0
            )
            db.add(order)
        
        # Supplier 'CREATED' orders for courier assignment testing (3 total)
        for i in range(3):
            order = Order(
                customer_id=customer1.id,
                supplier_id=supplier1.id,
                pickup_address=f"Tedarikçi Deposu {i+1}, Istanbul",
                pickup_latitude=41.0100 + (i * 0.005),
                pickup_longitude=28.9800 + (i * 0.005),
                delivery_address=f"Müşteri Adresi {i+1}, Istanbul",
                delivery_latitude=41.0200 + (i * 0.010),
                delivery_longitude=28.9900 + (i * 0.010),
                distance_km=5.0 + i,
                price=30.0 + (i * 5),
                status=OrderStatus.CREATED,
                tracking_code=f"LOOP-TEST-S{i}",
                cargo_type="Koli" if i == 0 else "Kutu",
                cargo_weight=15.0 if i == 0 else 3.5  # First is heavy (forces Car/Van), others light
            )
            db.add(order)
        
        await db.commit()
        
        print(f"✅ Created 47 orders (35 delivered, 8 in-progress, 4 cancelled)")
        
        # 6. Create notifications
        print("\n🔔 Creating notifications...")
        
        notif1 = Notification(
            user_id=customer1.id,
            title="Order Confirmed",
            body=f"Your order has been confirmed!",
            is_read=True
        )
        db.add(notif1)
        
        notif2 = Notification(
            user_id=customer1.id,
            title="Courier Assigned",
            body=f"A courier has been assigned to your order",
            is_read=False
        )
        db.add(notif2)
        
        notif3 = Notification(
            user_id=courier_user1.id,
            title="New Order",
            body=f"You have been assigned a new order",
            is_read=False
        )
        db.add(notif3)
        
        await db.commit()
        
        print(f"✅ Created 3 notifications")
        
        print("\n" + "="*50)
        print("🎉 Seed completed successfully!")
        print("="*50)
        print("\n📝 Test Credentials:")
        print("  Admin:     admin@loop.com / admin123")
        print("  Customer1: customer1@test.com / test123")
        print("  Customer2: customer2@test.com / test123")
        print("  Supplier:  tedarikci@loop.com / admin123")
        print("  Courier1:  courier1@loop.com / courier123")
        print("  Courier2:  courier2@loop.com / courier123")
        print("\n🎁 Promotion Codes:")
        print("  WELCOME20 - 20% off (max 50₺)")
        print("  SAVE10    - 10₺ fixed discount")
        print("\n")

if __name__ == "__main__":
    asyncio.run(seed_data())
