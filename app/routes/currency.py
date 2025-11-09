from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.services.currency_service import currency_service

router = APIRouter()

class ExchangeRateRequest(BaseModel):
    base_currency: str = "USD"

class ConvertRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str

class MultipleRatesRequest(BaseModel):
    base_currency: str
    target_currencies: List[str]

@router.post("/rates")
async def get_exchange_rates(request: ExchangeRateRequest):
    """Get all exchange rates for a base currency"""
    result = await currency_service.get_exchange_rates(request.base_currency)
    if not result:
        raise HTTPException(status_code=404, detail="Exchange rates not available")
    return result

@router.post("/convert")
async def convert_currency(request: ConvertRequest):
    """Convert amount from one currency to another"""
    result = await currency_service.convert_currency(
        request.amount,
        request.from_currency,
        request.to_currency
    )
    if not result:
        raise HTTPException(status_code=400, detail="Currency conversion failed")
    return result

@router.post("/multiple")
async def get_multiple_rates(request: MultipleRatesRequest):
    """Get exchange rates for specific currencies"""
    result = await currency_service.get_multiple_rates(
        request.base_currency,
        request.target_currencies
    )
    if not result:
        raise HTTPException(status_code=404, detail="Exchange rates not available")
    return result

@router.get("/popular")
async def get_popular_currencies():
    """Get exchange rates for popular currencies"""
    result = await currency_service.get_popular_currencies()
    return result
