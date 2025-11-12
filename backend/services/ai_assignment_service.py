import httpx
import os
from typing import Dict, List, Optional
import logging
from datetime import datetime, timezone
import math
from database import db

logger = logging.getLogger(__name__)

class AIAssignmentService:
    def __init__(self):
        self.n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL", "")
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance = R * c
        
        return distance
    
    async def find_best_courier(self, order: Dict) -> Optional[str]:
        """AI-powered courier assignment based on multiple factors"""
        try:
            pickup_lat = order["pickup_address"]["latitude"]
            pickup_lon = order["pickup_address"]["longitude"]
            
            # Get all available couriers
            available_couriers = await db.couriers.find({
                "status": {"$in": ["online"]},
                "is_verified": True
            }).to_list(100)
            
            if not available_couriers:
                logger.warning("No available couriers found")
                return None
            
            # Score each courier
            courier_scores = []
            for courier in available_couriers:
                if not courier.get("current_location"):
                    continue
                
                courier_lat = courier["current_location"]["lat"]
                courier_lon = courier["current_location"]["lng"]
                
                # Calculate distance to pickup
                distance = self.calculate_distance(pickup_lat, pickup_lon, courier_lat, courier_lon)
                
                # Scoring factors
                distance_score = max(0, 100 - (distance * 10))  # Closer is better
                rating_score = courier.get("rating", 5.0) * 20  # Max 100
                performance_score = courier.get("performance_score", 100)
                workload_score = max(0, 100 - (len(courier.get("current_orders", [])) * 25))
                
                # Weighted total score
                total_score = (
                    distance_score * 0.4 +
                    rating_score * 0.2 +
                    performance_score * 0.2 +
                    workload_score * 0.2
                )
                
                courier_scores.append({
                    "courier_id": courier["id"],
                    "score": total_score,
                    "distance": distance,
                    "rating": courier.get("rating", 5.0),
                    "current_orders": len(courier.get("current_orders", []))
                })
            
            if not courier_scores:
                return None
            
            # Sort by score and get best courier
            courier_scores.sort(key=lambda x: x["score"], reverse=True)
            best_courier = courier_scores[0]
            
            logger.info(f"Best courier selected: {best_courier['courier_id']} with score {best_courier['score']}")
            
            # Send to n8n workflow if configured
            if self.n8n_webhook_url:
                await self._trigger_n8n_workflow(order, best_courier)
            
            return best_courier["courier_id"]
            
        except Exception as e:
            logger.error(f"Courier assignment error: {e}")
            return None
    
    async def _trigger_n8n_workflow(self, order: Dict, assignment: Dict):
        """Trigger n8n workflow for AI decision logging"""
        try:
            payload = {
                "event": "courier_assigned",
                "order_id": order.get("id"),
                "courier_id": assignment["courier_id"],
                "assignment_score": assignment["score"],
                "distance_to_pickup": assignment["distance"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.n8n_webhook_url, json=payload, timeout=5.0)
                logger.info(f"n8n workflow triggered: {response.status_code}")
        except Exception as e:
            logger.error(f"n8n workflow trigger error: {e}")
    
    async def optimize_courier_routes(self, courier_id: str) -> Dict:
        """Optimize route for courier with multiple orders"""
        try:
            # Get courier's current orders
            orders = await db.orders.find({
                "courier_id": courier_id,
                "status": {"$in": ["accepted", "picked", "in_transit"]}
            }).to_list(50)
            
            if len(orders) <= 1:
                return {"optimized": False, "reason": "Not enough orders to optimize"}
            
            # Extract waypoints
            waypoints = []
            for order in orders:
                if order["status"] == "accepted":
                    waypoints.append(order["pickup_address"])
                waypoints.append(order["delivery_address"])
            
            # Use map service to optimize (would integrate with OSRM)
            # For now, return basic info
            return {
                "optimized": True,
                "total_orders": len(orders),
                "total_waypoints": len(waypoints),
                "suggested_sequence": [o["id"] for o in orders]
            }
            
        except Exception as e:
            logger.error(f"Route optimization error: {e}")
            return {"optimized": False, "error": str(e)}

ai_assignment_service = AIAssignmentService()
