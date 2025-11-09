import googlemaps
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from app.config import settings

class MapsService:
    def __init__(self):
        self.gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

    def geocode_address(self, address: str) -> Optional[Dict]:
        """Convert address to coordinates"""
        try:
            result = self.gmaps.geocode(address)
            if result:
                location = result[0]['geometry']['location']
                return {
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'formatted_address': result[0]['formatted_address']
                }
            return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None

    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        """Convert coordinates to address"""
        try:
            result = self.gmaps.reverse_geocode((latitude, longitude))
            if result:
                return result[0]['formatted_address']
            return None
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            return None

    def calculate_distance_duration(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        mode: str = "driving"
    ) -> Optional[Dict]:
        """Calculate distance and duration between two points"""
        try:
            result = self.gmaps.distance_matrix(
                origins=[origin],
                destinations=[destination],
                mode=mode,
                departure_time=datetime.now()
            )

            if result['rows'][0]['elements'][0]['status'] == 'OK':
                element = result['rows'][0]['elements'][0]
                return {
                    'distance_km': element['distance']['value'] / 1000,
                    'distance_text': element['distance']['text'],
                    'duration_minutes': element['duration']['value'] / 60,
                    'duration_text': element['duration']['text'],
                    'duration_in_traffic_minutes': element.get('duration_in_traffic', {}).get('value', 0) / 60
                }
            return None
        except Exception as e:
            print(f"Distance calculation error: {e}")
            return None

    def get_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        waypoints: Optional[List[Tuple[float, float]]] = None,
        optimize_waypoints: bool = True
    ) -> Optional[Dict]:
        """Get optimized route with turn-by-turn directions"""
        try:
            directions_result = self.gmaps.directions(
                origin=origin,
                destination=destination,
                waypoints=waypoints,
                optimize_waypoints=optimize_waypoints,
                departure_time=datetime.now()
            )

            if directions_result:
                route = directions_result[0]
                leg = route['legs'][0]

                steps = []
                for step in leg['steps']:
                    steps.append({
                        'instruction': step['html_instructions'],
                        'distance': step['distance']['text'],
                        'duration': step['duration']['text'],
                        'start_location': step['start_location'],
                        'end_location': step['end_location']
                    })

                return {
                    'distance_km': leg['distance']['value'] / 1000,
                    'duration_minutes': leg['duration']['value'] / 60,
                    'start_address': leg['start_address'],
                    'end_address': leg['end_address'],
                    'steps': steps,
                    'polyline': route['overview_polyline']['points']
                }
            return None
        except Exception as e:
            print(f"Route calculation error: {e}")
            return None

    def find_nearby_couriers(
        self,
        location: Tuple[float, float],
        courier_locations: List[Dict],
        max_distance_km: float = 10.0
    ) -> List[Dict]:
        """Find couriers within specified distance"""
        nearby = []

        for courier in courier_locations:
            courier_coords = (courier['latitude'], courier['longitude'])

            distance_data = self.calculate_distance_duration(location, courier_coords)

            if distance_data and distance_data['distance_km'] <= max_distance_km:
                nearby.append({
                    'courier_id': courier['courier_id'],
                    'distance_km': distance_data['distance_km'],
                    'duration_minutes': distance_data['duration_minutes'],
                    'location': courier_coords
                })

        return sorted(nearby, key=lambda x: x['distance_km'])

maps_service = MapsService()
