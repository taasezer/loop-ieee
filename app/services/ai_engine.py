import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from app.database import supabase_admin
from app.services.tracking_service import tracking_service
from app.services.weather_service import weather_service
from app.services.maps_service import maps_service

class AIDecisionEngine:
    def __init__(self):
        self.weights = {
            "distance": 0.35,
            "courier_rating": 0.20,
            "weather": 0.15,
            "traffic": 0.15,
            "workload": 0.10,
            "vehicle_match": 0.05
        }

    async def calculate_courier_score(
        self,
        courier: Dict,
        order: Dict,
        courier_location: Dict,
        weather_data: Optional[Dict] = None
    ) -> Dict:
        """Calculate assignment score for a courier"""
        try:
            pickup_coords = (order["pickup_latitude"], order["pickup_longitude"])
            courier_coords = (courier_location["latitude"], courier_location["longitude"])

            distance_data = maps_service.calculate_distance_duration(courier_coords, pickup_coords)

            if not distance_data:
                return None

            distance_score = max(0, 1 - (distance_data["distance_km"] / 20))

            rating_score = float(courier.get("rating", 5.0)) / 5.0

            weather_score = 0.8
            if weather_data:
                weather_score = weather_service.calculate_weather_impact(weather_data)

            traffic_factor = 1.0
            if distance_data.get("duration_in_traffic_minutes", 0) > 0:
                traffic_ratio = distance_data["duration_in_traffic_minutes"] / distance_data["duration_minutes"]
                traffic_factor = max(0, 1 - ((traffic_ratio - 1) * 2))

            active_orders = supabase_admin.table("orders") \
                .select("id") \
                .eq("courier_id", courier["id"]) \
                .in_("status", ["assigned", "picked_up", "in_transit"]) \
                .execute()

            workload_count = len(active_orders.data) if active_orders.data else 0
            workload_score = max(0, 1 - (workload_count * 0.3))

            vehicle_score = self._calculate_vehicle_match(
                courier.get("vehicle_type", ""),
                order.get("package_weight", 0)
            )

            total_score = (
                distance_score * self.weights["distance"] +
                rating_score * self.weights["courier_rating"] +
                weather_score * self.weights["weather"] +
                traffic_factor * self.weights["traffic"] +
                workload_score * self.weights["workload"] +
                vehicle_score * self.weights["vehicle_match"]
            )

            return {
                "courier_id": courier["id"],
                "courier_name": courier["name"],
                "total_score": round(total_score, 3),
                "distance_km": distance_data["distance_km"],
                "estimated_time_minutes": int(distance_data["duration_minutes"]),
                "scores": {
                    "distance": round(distance_score, 3),
                    "rating": round(rating_score, 3),
                    "weather": round(weather_score, 3),
                    "traffic": round(traffic_factor, 3),
                    "workload": round(workload_score, 3),
                    "vehicle_match": round(vehicle_score, 3)
                },
                "courier_details": {
                    "rating": float(courier.get("rating", 5.0)),
                    "vehicle_type": courier.get("vehicle_type"),
                    "active_orders": workload_count
                }
            }

        except Exception as e:
            print(f"Score calculation error: {e}")
            return None

    def _calculate_vehicle_match(self, vehicle_type: str, package_weight: float) -> float:
        """Calculate vehicle-package compatibility score"""
        vehicle_capacity = {
            "bicycle": 5,
            "motorcycle": 15,
            "car": 50,
            "van": 200,
            "truck": 1000
        }

        capacity = vehicle_capacity.get(vehicle_type.lower(), 50)

        if package_weight > capacity:
            return 0.0
        elif package_weight <= capacity * 0.5:
            return 1.0
        else:
            return 0.7

    async def find_best_courier(self, order_id: str) -> Optional[Dict]:
        """Find the best courier for an order using AI scoring"""
        try:
            order = supabase_admin.table("orders") \
                .select("*") \
                .eq("id", order_id) \
                .maybeSingle() \
                .execute()

            if not order.data:
                return None

            nearby_couriers = await tracking_service.get_nearby_couriers(
                latitude=order.data["pickup_latitude"],
                longitude=order.data["pickup_longitude"],
                max_distance_km=20.0,
                status="available"
            )

            if not nearby_couriers:
                return {"error": "No available couriers found"}

            weather_data = await weather_service.get_current_weather(
                order.data["pickup_latitude"],
                order.data["pickup_longitude"]
            )

            courier_scores = []

            for nearby in nearby_couriers:
                courier = supabase_admin.table("couriers") \
                    .select("*") \
                    .eq("id", nearby["courier_id"]) \
                    .maybeSingle() \
                    .execute()

                if not courier.data:
                    continue

                courier_location = await tracking_service.get_courier_location(nearby["courier_id"])

                if not courier_location:
                    continue

                score = await self.calculate_courier_score(
                    courier.data,
                    order.data,
                    courier_location,
                    weather_data
                )

                if score:
                    courier_scores.append(score)

            if not courier_scores:
                return {"error": "Could not calculate scores for available couriers"}

            courier_scores.sort(key=lambda x: x["total_score"], reverse=True)

            return {
                "order_id": order_id,
                "recommended_courier": courier_scores[0],
                "alternatives": courier_scores[1:min(5, len(courier_scores))],
                "total_candidates": len(courier_scores)
            }

        except Exception as e:
            print(f"Best courier selection error: {e}")
            return None

    async def auto_assign_courier(self, order_id: str) -> Optional[Dict]:
        """Automatically assign the best courier to an order"""
        try:
            recommendation = await self.find_best_courier(order_id)

            if not recommendation or "error" in recommendation:
                return recommendation

            best_courier = recommendation["recommended_courier"]

            order_update = supabase_admin.table("orders") \
                .update({
                    "courier_id": best_courier["courier_id"],
                    "status": "assigned",
                    "assigned_at": datetime.utcnow().isoformat()
                }) \
                .eq("id", order_id) \
                .execute()

            courier_update = supabase_admin.table("couriers") \
                .update({"status": "busy"}) \
                .eq("id", best_courier["courier_id"]) \
                .execute()

            assignment_history = supabase_admin.table("assignment_history") \
                .insert({
                    "order_id": order_id,
                    "courier_id": best_courier["courier_id"],
                    "assignment_score": best_courier["total_score"],
                    "distance_to_pickup": best_courier["distance_km"],
                    "estimated_time": best_courier["estimated_time_minutes"],
                    "weather_factor": best_courier["scores"]["weather"],
                    "traffic_factor": best_courier["scores"]["traffic"],
                    "assigned_by": "ai"
                }) \
                .execute()

            return {
                "success": True,
                "order_id": order_id,
                "assigned_courier": best_courier,
                "assignment_details": recommendation
            }

        except Exception as e:
            print(f"Auto-assignment error: {e}")
            return {"success": False, "error": str(e)}

    async def optimize_route_for_courier(self, courier_id: str) -> Optional[Dict]:
        """Optimize delivery route for a courier with multiple orders"""
        try:
            orders = supabase_admin.table("orders") \
                .select("*") \
                .eq("courier_id", courier_id) \
                .in_("status", ["assigned", "picked_up"]) \
                .execute()

            if not orders.data or len(orders.data) == 0:
                return {"message": "No orders to optimize"}

            courier_location = await tracking_service.get_courier_location(courier_id)

            if not courier_location:
                return {"error": "Courier location not available"}

            start_point = (courier_location["latitude"], courier_location["longitude"])

            waypoints = []
            for order in orders.data:
                if order["status"] == "assigned":
                    waypoints.append({
                        "order_id": order["id"],
                        "type": "pickup",
                        "coords": (order["pickup_latitude"], order["pickup_longitude"]),
                        "address": order["pickup_address"]
                    })
                waypoints.append({
                    "order_id": order["id"],
                    "type": "delivery",
                    "coords": (order["delivery_latitude"], order["delivery_longitude"]),
                    "address": order["delivery_address"]
                })

            optimized_sequence = self._optimize_waypoint_order(start_point, waypoints)

            return {
                "courier_id": courier_id,
                "total_orders": len(orders.data),
                "total_stops": len(waypoints),
                "optimized_route": optimized_sequence
            }

        except Exception as e:
            print(f"Route optimization error: {e}")
            return None

    def _optimize_waypoint_order(self, start: tuple, waypoints: List[Dict]) -> List[Dict]:
        """Simple nearest neighbor optimization for waypoints"""
        current = start
        remaining = waypoints.copy()
        optimized = []

        while remaining:
            nearest = None
            min_distance = float('inf')

            for wp in remaining:
                lat_diff = wp["coords"][0] - current[0]
                lon_diff = wp["coords"][1] - current[1]
                distance = np.sqrt(lat_diff**2 + lon_diff**2)

                if distance < min_distance:
                    min_distance = distance
                    nearest = wp

            if nearest:
                optimized.append(nearest)
                remaining.remove(nearest)
                current = nearest["coords"]

        return optimized

ai_engine = AIDecisionEngine()
