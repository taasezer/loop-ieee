import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.config import settings

class CurrencyService:
    def __init__(self):
        self.api_key = settings.EXCHANGE_RATE_API_KEY
        self.base_url = "https://v6.exchangerate-api.com/v6"
        self.cache = {}
        self.cache_duration = timedelta(minutes=30)

    async def get_exchange_rates(self, base_currency: str = "USD") -> Optional[Dict]:
        """Get latest exchange rates for base currency"""
        cache_key = f"rates_{base_currency}"

        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_data

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{self.api_key}/latest/{base_currency}"
                )
                response.raise_for_status()
                data = response.json()

                if data["result"] == "success":
                    result = {
                        "base_currency": base_currency,
                        "last_updated": data["time_last_update_utc"],
                        "next_update": data["time_next_update_utc"],
                        "rates": data["conversion_rates"]
                    }

                    self.cache[cache_key] = (result, datetime.now())
                    return result

            return None
        except Exception as e:
            print(f"Currency API error: {e}")
            return None

    async def convert_currency(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> Optional[Dict]:
        """Convert amount from one currency to another"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{self.api_key}/pair/{from_currency}/{to_currency}/{amount}"
                )
                response.raise_for_status()
                data = response.json()

                if data["result"] == "success":
                    return {
                        "from_currency": from_currency,
                        "to_currency": to_currency,
                        "from_amount": amount,
                        "to_amount": data["conversion_result"],
                        "exchange_rate": data["conversion_rate"],
                        "last_updated": data["time_last_update_utc"]
                    }

            return None
        except Exception as e:
            print(f"Currency conversion error: {e}")
            return None

    async def get_multiple_rates(
        self,
        base_currency: str,
        target_currencies: List[str]
    ) -> Optional[Dict]:
        """Get exchange rates for multiple target currencies"""
        rates_data = await self.get_exchange_rates(base_currency)

        if not rates_data:
            return None

        filtered_rates = {
            currency: rates_data["rates"][currency]
            for currency in target_currencies
            if currency in rates_data["rates"]
        }

        return {
            "base_currency": base_currency,
            "last_updated": rates_data["last_updated"],
            "rates": filtered_rates
        }

    async def get_popular_currencies(self) -> Dict:
        """Get exchange rates for popular currencies"""
        popular = ["USD", "EUR", "GBP", "TRY", "JPY", "CNY", "AUD", "CAD", "CHF", "INR"]

        rates_data = await self.get_exchange_rates("USD")

        if not rates_data:
            return {"error": "Unable to fetch currency data"}

        return {
            "base_currency": "USD",
            "last_updated": rates_data["last_updated"],
            "popular_rates": {
                currency: rates_data["rates"].get(currency, 0)
                for currency in popular
            }
        }

currency_service = CurrencyService()
