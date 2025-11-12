import httpx
import os
from typing import Dict
import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class CurrencyService:
    def __init__(self):
        self.api_key = os.getenv("EXCHANGERATE_API_KEY", "")
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        self.cache = {}
        self.cache_duration = timedelta(hours=24)  # Update once per day
        self.base_currency = "USD"
    
    def _is_cache_valid(self, currency: str) -> bool:
        if currency in self.cache:
            cached_time = self.cache[currency].get("cached_at")
            if cached_time and datetime.now(timezone.utc) - cached_time < self.cache_duration:
                return True
        return False
    
    async def get_exchange_rates(self, base_currency: str = "USD") -> Dict:
        """Get current exchange rates"""
        if self._is_cache_valid(base_currency):
            logger.info(f"Returning cached rates for {base_currency}")
            return self.cache[base_currency]["data"]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/{base_currency}")
                
                if response.status_code == 200:
                    data = response.json()
                    rates_data = {
                        "base": data["base"],
                        "date": data["date"],
                        "rates": data["rates"],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Cache the result
                    self.cache[base_currency] = {
                        "data": rates_data,
                        "cached_at": datetime.now(timezone.utc)
                    }
                    
                    return rates_data
                else:
                    logger.error(f"Exchange rate API error: {response.status_code}")
                    return self._get_default_rates(base_currency)
        except Exception as e:
            logger.error(f"Currency service error: {e}")
            return self._get_default_rates(base_currency)
    
    async def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Dict:
        """Convert amount from one currency to another"""
        try:
            rates = await self.get_exchange_rates(from_currency)
            
            if to_currency in rates["rates"]:
                converted_amount = amount * rates["rates"][to_currency]
                return {
                    "original_amount": amount,
                    "original_currency": from_currency,
                    "converted_amount": round(converted_amount, 2),
                    "target_currency": to_currency,
                    "exchange_rate": rates["rates"][to_currency],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                raise HTTPException(status_code=400, detail=f"Currency {to_currency} not supported")
        except Exception as e:
            logger.error(f"Currency conversion error: {e}")
            raise HTTPException(status_code=500, detail="Currency conversion failed")
    
    def _get_default_rates(self, base_currency: str) -> Dict:
        """Return default rates when API fails"""
        return {
            "base": base_currency,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "rates": {
                "USD": 1.0,
                "EUR": 0.85,
                "GBP": 0.73,
                "TRY": 27.5,
                "JPY": 110.0
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "Default rates - API unavailable"
        }

currency_service = CurrencyService()
