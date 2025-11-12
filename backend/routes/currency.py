from fastapi import APIRouter, HTTPException
from services.currency_service import currency_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/rates")
async def get_exchange_rates(base_currency: str = "USD"):
    """Get current exchange rates"""
    try:
        rates = await currency_service.get_exchange_rates(base_currency)
        return rates
    except Exception as e:
        logger.error(f"Exchange rates fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch exchange rates")

@router.get("/convert")
async def convert_currency(
    amount: float,
    from_currency: str = "USD",
    to_currency: str = "EUR"
):
    """Convert amount from one currency to another"""
    try:
        result = await currency_service.convert_currency(amount, from_currency, to_currency)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Currency conversion error: {e}")
        raise HTTPException(status_code=500, detail="Currency conversion failed")
