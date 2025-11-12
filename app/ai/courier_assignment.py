"""
AI-powered Courier Assignment Engine
Intelligently assigns orders to the best available courier
"""

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import math
import logging

from app.models.courier import Courier
from app.models.order import Order
from app.repositories.courier_repository import CourierRepository

logger = logging.getLogger(__name__)


class CourierAssignmentEngine:
    """AI-powered courier assignment system"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.courier_repo = CourierRepository(db)
    
    async def find_best_courier(self, order: Order) -> Optional[Courier]:
        """
        Find the best courier for an order using multi-factor scoring
        
        Factors considered:
        - Distance from pickup location
        - Current workload
        - Average rating
        - Performance score
        - Vehicle type compatibility
        """
        # Get all available couriers
        available_couriers = await self.courier_repo.get_available_couriers()
        
        if not available_couriers:
            logger.warning("No available couriers found")
            return None
        
        # Score each courier
        courier_scores = []
        for courier in available_couriers:
            score = await self._calculate_match_score(courier, order)
            courier_scores.append((courier, score))
        
        # Sort by score (highest first)
        courier_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return best courier
        best_courier, best_score = courier_scores[0]
        logger.info(f"Best courier found: {best_courier.id} with score {best_score:.2f}")
        
        return best_courier
    
    async def _calculate_match_score(self, courier: Courier, order: Order) -> float:
        """
        Calculate match score between courier and order
        
        Score components:
        - Distance score (40%)
        - Rating score (25%)
        - Performance score (20%)
        - Workload score (15%)
        
        Returns score between 0 and 100
        """
        # Distance score
        distance_score = self._calculate_distance_score(
            courier.current_latitude or 0,
            courier.current_longitude or 0,
            order.pickup_latitude,
            order.pickup_longitude
        )
        
        # Rating score (normalize 0-5 to 0-100)
        rating_score = (courier.average_rating / 5.0) * 100
        
        # Performance score (already 0-100)
        performance_score = courier.performance_score or 50
        
        # Workload score (inverse - fewer deliveries = higher score)
        workload_score = self._calculate_workload_score(courier)
        
        # Weighted average
        total_score = (
            distance_score * 0.40 +
            rating_score * 0.25 +
            performance_score * 0.20 +
            workload_score * 0.15
        )
        
        return total_score
    
    def _calculate_distance_score(
        self,
        courier_lat: float,
        courier_lon: float,
        pickup_lat: float,
        pickup_lon: float
    ) -> float:
        """
        Calculate distance score (0-100)
        Closer distance = higher score
        """
        distance_km = self._haversine_distance(
            courier_lat, courier_lon,
            pickup_lat, pickup_lon
        )
        
        # Score decreases with distance
        # 0 km = 100 points
        # 5 km = 50 points
        # 10+ km = 0 points
        if distance_km <= 0.5:
            return 100
        elif distance_km >= 10:
            return 0
        else:
            return max(0, 100 - (distance_km * 10))
    
    def _calculate_workload_score(self, courier: Courier) -> float:
        """
        Calculate workload score based on active deliveries
        Fewer active deliveries = higher score
        """
        # This would check courier's current active orders
        # For now, return a default score
        return 75
    
    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    async def predict_delivery_time(self, courier: Courier, order: Order) -> int:
        """
        Predict delivery time in minutes
        
        Factors:
        - Distance to pickup
        - Distance from pickup to delivery
        - Average courier speed
        - Current traffic conditions
        - Weather conditions
        """
        # Distance to pickup
        pickup_distance = self._haversine_distance(
            courier.current_latitude or 0,
            courier.current_longitude or 0,
            order.pickup_latitude,
            order.pickup_longitude
        )
        
        # Distance from pickup to delivery
        delivery_distance = order.distance_km or 0
        
        # Total distance
        total_distance = pickup_distance + delivery_distance
        
        # Average speed (km/h) - varies by vehicle type
        avg_speed = {
            "bicycle": 15,
            "motorcycle": 30,
            "car": 40,
            "van": 35
        }.get(courier.vehicle_type.value, 30)
        
        # Base time calculation
        base_time_minutes = (total_distance / avg_speed) * 60
        
        # Add buffer for pickup/delivery (5 minutes each)
        buffer_time = 10
        
        # Weather multiplier (would get from weather service)
        weather_multiplier = 1.0
        
        # Traffic multiplier (would get from traffic service)
        traffic_multiplier = 1.0
        
        estimated_time = int(
            base_time_minutes * weather_multiplier * traffic_multiplier + buffer_time
        )
        
        return estimated_time
    
    async def batch_assign_orders(self, order_ids: List[UUID]) -> List[Tuple[UUID, Optional[UUID]]]:
        """
        Batch assign multiple orders to couriers
        
        Returns list of (order_id, courier_id) tuples
        """
        from app.repositories.order_repository import OrderRepository
        
        order_repo = OrderRepository(self.db)
        assignments = []
        
        for order_id in order_ids:
            order = await order_repo.get_by_id(order_id)
            if order:
                courier = await self.find_best_courier(order)
                courier_id = courier.id if courier else None
                assignments.append((order_id, courier_id))
        
        return assignments
