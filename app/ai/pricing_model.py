"""Dynamic Pricing Model"""
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DynamicPricingModel:
    """AI-powered dynamic pricing"""
    
    def __init__(self):
        self.base_price = 10.0
        self.price_per_km = 2.5
    
    def calculate_price(
        self,
        distance_km: float,
        order_type: str,
        weather_data: Dict[str, Any] = None,
        demand_level: float = 1.0
    ) -> Dict[str, float]:
        """Calculate dynamic price"""
        
        # Base calculation
        base = self.base_price
        distance_price = distance_km * self.price_per_km
        
        # Order type multiplier
        type_multiplier = 1.5 if order_type == "EXPRESS" else 1.0
        
        # Weather multiplier
        weather_multiplier = 1.0
        if weather_data:
            if weather_data.get("weather") in ["Rain", "Snow"]:
                weather_multiplier = 1.3
            elif weather_data.get("wind_speed", 0) > 15:
                weather_multiplier = 1.2
        
        # Demand surge multiplier
        surge_multiplier = min(demand_level, 2.0)
        
        # Time-based pricing (peak hours)
        hour = datetime.utcnow().hour
        time_multiplier = 1.2 if 17 <= hour <= 20 else 1.0
        
        # Calculate total
        subtotal = (base + distance_price) * type_multiplier
        total = subtotal * weather_multiplier * surge_multiplier * time_multiplier
        
        return {
            "base_price": base,
            "distance_price": distance_price,
            "type_multiplier": type_multiplier,
            "weather_multiplier": weather_multiplier,
            "surge_multiplier": surge_multiplier,
            "time_multiplier": time_multiplier,
            "total_price": round(total, 2)
        }

pricing_model = DynamicPricingModel()
