from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.database import supabase_admin
from app.services.maps_service import maps_service

class TrackingService:
    async def update_courier_location(
        self,
        courier_id: str,
        latitude: float,
        longitude: float,
        accuracy: Optional[float] = None,
        speed: Optional[float] = None,
        heading: Optional[float] = None
    ) -> Dict:
        """Update courier's current location"""
        try:
            address = maps_service.reverse_geocode(latitude, longitude)

            location_data = {
                "courier_id": courier_id,
                "latitude": latitude,
                "longitude": longitude,
                "accuracy": accuracy,
                "speed": speed,
                "heading": heading,
                "address": address,
                "timestamp": datetime.utcnow().isoformat()
            }

            result = supabase_admin.table("courier_locations").insert(location_data).execute()

            history_data = {
                "courier_id": courier_id,
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": datetime.utcnow().isoformat()
            }
            supabase_admin.table("location_history").insert(history_data).execute()

            return {
                "success": True,
                "location": result.data[0] if result.data else location_data
            }

        except Exception as e:
            print(f"Location update error: {e}")
            return {"success": False, "error": str(e)}

    async def get_courier_location(self, courier_id: str) -> Optional[Dict]:
        """Get courier's latest location"""
        try:
            result = supabase_admin.table("courier_locations") \
                .select("*") \
                .eq("courier_id", courier_id) \
                .order("timestamp", desc=True) \
                .limit(1) \
                .execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            print(f"Error fetching courier location: {e}")
            return None

    async def get_all_active_locations(self, status: str = "available") -> List[Dict]:
        """Get locations of all active couriers"""
        try:
            couriers = supabase_admin.table("couriers") \
                .select("id, name, status, vehicle_type") \
                .eq("status", status) \
                .execute()

            if not couriers.data:
                return []

            courier_ids = [c["id"] for c in couriers.data]

            locations = []
            for courier_id in courier_ids:
                location = await self.get_courier_location(courier_id)
                if location:
                    courier_info = next(c for c in couriers.data if c["id"] == courier_id)
                    locations.append({
                        **location,
                        "courier_name": courier_info["name"],
                        "vehicle_type": courier_info["vehicle_type"]
                    })

            return locations

        except Exception as e:
            print(f"Error fetching active locations: {e}")
            return []

    async def get_location_history(
        self,
        courier_id: str,
        hours: int = 24
    ) -> List[Dict]:
        """Get courier's location history"""
        try:
            since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

            result = supabase_admin.table("location_history") \
                .select("*") \
                .eq("courier_id", courier_id) \
                .gte("timestamp", since) \
                .order("timestamp", desc=True) \
                .execute()

            return result.data if result.data else []

        except Exception as e:
            print(f"Error fetching location history: {e}")
            return []

    async def track_order_delivery(self, order_id: str) -> Optional[Dict]:
        """Track order delivery in real-time"""
        try:
            order = supabase_admin.table("orders") \
                .select("*, courier_id, delivery_latitude, delivery_longitude") \
                .eq("id", order_id) \
                .maybeSingle() \
                .execute()

            if not order.data or not order.data.get("courier_id"):
                return None

            courier_location = await self.get_courier_location(order.data["courier_id"])

            if not courier_location:
                return None

            destination = (order.data["delivery_latitude"], order.data["delivery_longitude"])
            current = (courier_location["latitude"], courier_location["longitude"])

            distance_data = maps_service.calculate_distance_duration(current, destination)

            return {
                "order_id": order_id,
                "order_status": order.data["status"],
                "courier_location": {
                    "latitude": courier_location["latitude"],
                    "longitude": courier_location["longitude"],
                    "address": courier_location.get("address"),
                    "speed": courier_location.get("speed"),
                    "heading": courier_location.get("heading"),
                    "last_updated": courier_location["timestamp"]
                },
                "delivery_location": {
                    "latitude": order.data["delivery_latitude"],
                    "longitude": order.data["delivery_longitude"],
                    "address": order.data["delivery_address"]
                },
                "eta": distance_data if distance_data else None
            }

        except Exception as e:
            print(f"Error tracking order: {e}")
            return None

    async def get_nearby_couriers(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 10.0,
        status: str = "available"
    ) -> List[Dict]:
        """Find available couriers near a location"""
        try:
            active_locations = await self.get_all_active_locations(status)

            if not active_locations:
                return []

            location = (latitude, longitude)
            nearby = maps_service.find_nearby_couriers(location, active_locations, max_distance_km)

            return nearby

        except Exception as e:
            print(f"Error finding nearby couriers: {e}")
            return []

tracking_service = TrackingService()
