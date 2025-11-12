"""Users API endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def placeholder_endpoint(db: AsyncSession = Depends(get_db)):
    """Placeholder endpoint for users"""
    return {"message": "users endpoint - to be implemented"}
