"""
User repository
"""

from typing import Optional, List
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.user import User, UserRole, UserStatus
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository with custom queries"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_phone(self, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        result = await self.db.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email_or_phone(self, email_or_phone: str) -> Optional[User]:
        """Get user by email or phone"""
        result = await self.db.execute(
            select(User).where(
                or_(User.email == email_or_phone, User.phone_number == email_or_phone)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_role(self, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role"""
        result = await self.db.execute(
            select(User).where(User.role == role).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users"""
        result = await self.db.execute(
            select(User).where(User.status == UserStatus.ACTIVE).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    async def email_exists(self, email: str) -> bool:
        """Check if email exists"""
        user = await self.get_by_email(email)
        return user is not None
    
    async def phone_exists(self, phone_number: str) -> bool:
        """Check if phone exists"""
        user = await self.get_by_phone(phone_number)
        return user is not None
