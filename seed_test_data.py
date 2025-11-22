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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_data():
    """Seed database with test data"""
    async with AsyncSessionLocal() as db:
        print("🌱 Seeding database with test data...")
        
        # 1. Create test users
        print("\n👥 Creating users...")
        
        # Admin user
        admin = User(
            email="admin@loop.com",
            username="admin",
            phone="+905551234567",
            full_name="Admin User",
            hashed_password=pwd_context.hash("admin123"),
            role=UserRole.ADMIN
        )
        db.add(admin)
        
        # Customer users
        customer1 = User(
            email="customer1@test.com",
            username="customer1",
            phone="+905551234568",
            full_name="Ahmet Yılmaz",
            hashed_password=pwd_context.hash("test123"),
            role=UserRole.CUSTOMER
        )
        db.add(customer1)
        
        customer2 = User(
            email="customer2@test.com",
            username="customer2",
            phone="+905551234569",
            full_name="Ayşe Demir",
            hashed_password=pwd_context.hash("test123"),
            role=UserRole.CUSTOMER
        )
        db.add(customer2)
        
        # Courier users
        courier_user1 = User(
            email="courier1@loop.com",
            username="courier1",
            phone="+905551234570",
            full_name="Mehmet Kaya",
            hashed_password=pwd_context.hash("courier123"),
            role=UserRole.COURIER
        )
        db.add(courier_user1)
        
        courier_user2 = User(
            email="courier2@loop.com",
            username="courier2",
            phone="+905551234571",
            full_name="Fatma Şahin",
            hashed_password=pwd_context.hash("courier123"),
            role=UserRole.COURIER
        )
        db.add(courier_user2)
        
        await db.commit()
        await db.refresh(admin)
        await db.refresh(customer1)
        await db.refresh(customer2)
        await db.refresh(courier_user1)
        await db.refresh(courier_user2)
        
        print(f"✅ Created 5 users (1 admin, 2 customers, 2 couriers)")
        
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
        
        # 5. Create test orders
        print("\n📦 Creating orders...")
        
        order1 = Order(
            customer_id=customer1.id,
            courier_id=courier1.id,
            pickup_address="Taksim Meydanı, Beyoğlu, İstanbul",
            pickup_latitude=41.0369,
            pickup_longitude=28.9850,
            delivery_address="Beşiktaş Meydanı, İstanbul",
            delivery_latitude=41.0422,
            delivery_longitude=29.0079,
            distance_km=3.2,
            price=26.20,
            status=OrderStatus.IN_TRANSIT
        )
        db.add(order1)
        
        order2 = Order(
            customer_id=customer2.id,
            courier_id=courier2.id,
            pickup_address="Kadıköy İskele, İstanbul",
            pickup_latitude=40.9907,
            pickup_longitude=29.0258,
            delivery_address="Bağdat Caddesi, Kadıköy, İstanbul",
            delivery_latitude=40.9772,
            delivery_longitude=29.0613,
            distance_km=5.8,
            price=35.30,
            status=OrderStatus.DELIVERED,
            completed_at=datetime.utcnow() - timedelta(hours=2)
        )
        db.add(order2)
        
        order3 = Order(
            customer_id=customer1.id,
            pickup_address="Şişli Merkez, İstanbul",
            pickup_latitude=41.0602,
            pickup_longitude=28.9875,
            delivery_address="Mecidiyeköy, İstanbul",
            delivery_latitude=41.0688,
            delivery_longitude=28.9963,
            distance_km=2.1,
            price=22.35,
            status=OrderStatus.CREATED
        )
        db.add(order3)
        
        await db.commit()
        await db.refresh(order1)
        await db.refresh(order2)
        await db.refresh(order3)
        
        print(f"✅ Created 3 orders (1 in-transit, 1 delivered, 1 created)")
        
        # 6. Create notifications
        print("\n🔔 Creating notifications...")
        
        notif1 = Notification(
            user_id=customer1.id,
            title="Order Confirmed",
            body=f"Your order #{order1.id} has been confirmed!",
            is_read=True
        )
        db.add(notif1)
        
        notif2 = Notification(
            user_id=customer1.id,
            title="Courier Assigned",
            body=f"A courier has been assigned to order #{order1.id}",
            is_read=False
        )
        db.add(notif2)
        
        notif3 = Notification(
            user_id=courier_user1.id,
            title="New Order",
            body=f"You have been assigned order #{order1.id}",
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
        print("  Courier1:  courier1@loop.com / courier123")
        print("  Courier2:  courier2@loop.com / courier123")
        print("\n🎁 Promotion Codes:")
        print("  WELCOME20 - 20% off (max 50₺)")
        print("  SAVE10    - 10₺ fixed discount")
        print("\n")

if __name__ == "__main__":
    asyncio.run(seed_data())
