"""Exchange rate API client"""
import httpx
from typing import Optional, Dict
import logging
from app.core.cache import cache

logger = logging.getLogger(__name__)

class ExchangeRateClient:
    def __init__(self):
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
    
    async def get_latest_rates(self, base: str = "USD") -> Optional[Dict[str, float]]:
        """Get latest exchange rates"""
        try:
            # Check cache first
            cached = await cache.get(f"exchange_rates:{base}", db="cache")
            if cached:
                return cached
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/{base}", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    rates = data.get("rates", {})
                    # Cache for 1 hour
                    await cache.set(f"exchange_rates:{base}", rates, expire=3600, db="cache")
                    return rates
                return None
        except Exception as e:
            logger.error(f"Exchange rate API error: {str(e)}")
            return None
    
    async def convert(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """Convert amount between currencies"""
        rates = await self.get_latest_rates(from_currency)
        if rates and to_currency in rates:
            return amount * rates[to_currency]
        return None

exchange_rate_client = ExchangeRateClient()
