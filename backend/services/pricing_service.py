from typing import Dict
import logging
from datetime import datetime, timezone
from services.weather_service import weather_service
from services.currency_service import currency_service

logger = logging.getLogger(__name__)

class PricingService:
    def __init__(self):
        # Base pricing configuration
        self.base_price = 5.0  # Base price in USD
        self.price_per_km = 1.5
        self.price_per_minute = 0.3
        self.priority_multipliers = {
            "low": 0.8,
            "normal": 1.0,
            "high": 1.3,
            "urgent": 1.8
        }
        # Peak hours (24-hour format)
        self.peak_hours = [(7, 9), (17, 20)]  # Morning and evening rush
        self.peak_multiplier = 1.4
    
    async def calculate_price(
        self,
        distance_km: float,
        duration_minutes: float,
        priority: str = "normal",
        pickup_location: Dict[str, float] = None,
        currency: str = "USD"
    ) -> Dict:
        """Calculate delivery price with all factors"""
        try:
            # Base calculation
            base_cost = self.base_price
            distance_cost = distance_km * self.price_per_km
            time_cost = duration_minutes * self.price_per_minute
            
            subtotal = base_cost + distance_cost + time_cost
            
            # Apply priority multiplier
            priority_multiplier = self.priority_multipliers.get(priority, 1.0)
            subtotal *= priority_multiplier
            
            # Check for peak hours
            current_hour = datetime.now(timezone.utc).hour
            is_peak = any(start <= current_hour < end for start, end in self.peak_hours)
            peak_multiplier = self.peak_multiplier if is_peak else 1.0
            subtotal *= peak_multiplier
            
            # Weather impact
            weather_multiplier = 1.0
            if pickup_location:
                try:
                    weather = await weather_service.get_current_weather(
                        pickup_location["latitude"],
                        pickup_location["longitude"]
                    )
                    weather_multiplier = weather_service.calculate_weather_impact(weather)
                except Exception as e:
                    logger.error(f"Weather fetch error in pricing: {e}")
            
            subtotal *= weather_multiplier
            
            # Currency conversion if needed
            final_price = subtotal
            exchange_rate = 1.0
            if currency != "USD":
                try:
                    conversion = await currency_service.convert_currency(subtotal, "USD", currency)
                    final_price = conversion["converted_amount"]
                    exchange_rate = conversion["exchange_rate"]
                except Exception as e:
                    logger.error(f"Currency conversion error in pricing: {e}")
            
            return {
                "base_price": round(base_cost, 2),
                "distance_cost": round(distance_cost, 2),
                "time_cost": round(time_cost, 2),
                "priority_multiplier": priority_multiplier,
                "peak_multiplier": peak_multiplier,
                "weather_multiplier": round(weather_multiplier, 2),
                "subtotal_usd": round(subtotal, 2),
                "final_price": round(final_price, 2),
                "currency": currency,
                "exchange_rate": exchange_rate,
                "is_peak_hour": is_peak,
                "calculated_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Pricing calculation error: {e}")
            # Return fallback pricing
            return {
                "final_price": round(self.base_price + (distance_km * self.price_per_km), 2),
                "currency": currency,
                "error": "Detailed pricing calculation failed, using simplified pricing"
            }
    
    def calculate_courier_earnings(self, order_price: float, commission_rate: float = 0.20) -> Dict:
        """Calculate courier earnings after commission"""
        commission = order_price * commission_rate
        courier_earnings = order_price - commission
        
        return {
            "order_price": round(order_price, 2),
            "commission_rate": commission_rate,
            "commission_amount": round(commission, 2),
            "courier_earnings": round(courier_earnings, 2)
        }

pricing_service = PricingService()
