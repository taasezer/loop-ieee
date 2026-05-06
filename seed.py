import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.orm import User, UserRole
from app.auth.security import get_password_hash
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def seed_data():
    async with AsyncSessionLocal() as db:
        # Check if supplier already exists
        from sqlalchemy.future import select
        result = await db.execute(select(User).where(User.supplier_code == "SUP-TEST01"))
        existing_supplier = result.scalar_one_or_none()
        
        if existing_supplier:
            print("Test supplier already exists.")
            return

        print("Creating test supplier...")
        
        test_supplier = User(
            email="tedarikci@loop.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Tedarikçi Test",
            phone_number="05555555555",
            role=UserRole.SUPPLIER,
            company_name="Test Tedarikçi A.Ş.",
            supplier_code="SUP-TEST01",
            is_active=True,
            is_verified=True
        )
        
        db.add(test_supplier)
        await db.commit()
        
        print("Successfully created test supplier with code: SUP-TEST01")

if __name__ == "__main__":
    asyncio.run(seed_data())
