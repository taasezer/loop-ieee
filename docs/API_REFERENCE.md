# LOOP Logistics API Reference

## Base URL
```
http://your-api-url:8000
```

## Authentication
Currently, the API uses service-level authentication. For production, implement JWT tokens.

---

## Maps & GPS APIs

### Geocode Address
Convert address to GPS coordinates.

**Endpoint:** `POST /api/maps/geocode`

**Request Body:**
```json
{
  "address": "1600 Amphitheatre Parkway, Mountain View, CA"
}
```

**Response:**
```json
{
  "latitude": 37.4224764,
  "longitude": -122.0842499,
  "formatted_address": "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA"
}
```

### Reverse Geocode
Convert GPS coordinates to address.

**Endpoint:** `POST /api/maps/reverse-geocode`

**Request Body:**
```json
{
  "latitude": 37.4224764,
  "longitude": -122.0842499
}
```

**Response:**
```json
{
  "address": "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA"
}
```

### Calculate Distance
Calculate distance and duration between two points.

**Endpoint:** `POST /api/maps/distance`

**Request Body:**
```json
{
  "origin_lat": 37.4224764,
  "origin_lng": -122.0842499,
  "destination_lat": 37.7749295,
  "destination_lng": -122.4194155,
  "mode": "driving"
}
```

**Response:**
```json
{
  "distance_km": 54.2,
  "distance_text": "54.2 km",
  "duration_minutes": 45.5,
  "duration_text": "46 mins",
  "duration_in_traffic_minutes": 52.3
}
```

### Get Route
Get optimized route with turn-by-turn directions.

**Endpoint:** `POST /api/maps/route`

**Request Body:**
```json
{
  "origin_lat": 37.4224764,
  "origin_lng": -122.0842499,
  "destination_lat": 37.7749295,
  "destination_lng": -122.4194155,
  "waypoints": [
    {"lat": 37.5, "lng": -122.1}
  ],
  "optimize": true
}
```

**Response:**
```json
{
  "distance_km": 54.2,
  "duration_minutes": 45.5,
  "start_address": "Mountain View, CA",
  "end_address": "San Francisco, CA",
  "steps": [...],
  "polyline": "encoded_polyline_string"
}
```

---

## Weather APIs

### Get Current Weather
Get current weather conditions for a location.

**Endpoint:** `POST /api/weather/current`

**Request Body:**
```json
{
  "latitude": 37.7749,
  "longitude": -122.4194
}
```

**Response:**
```json
{
  "temperature": 18.5,
  "feels_like": 17.2,
  "humidity": 75,
  "pressure": 1013,
  "weather": "Clouds",
  "description": "scattered clouds",
  "wind_speed": 5.2,
  "wind_direction": 270,
  "visibility": 10,
  "clouds": 40,
  "rain": 0,
  "snow": 0,
  "location": "San Francisco"
}
```

### Get Weather Forecast
Get weather forecast for next 24 hours.

**Endpoint:** `POST /api/weather/forecast`

**Request Body:**
```json
{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "hours": 24
}
```

**Response:**
```json
{
  "location": "San Francisco",
  "forecasts": [
    {
      "timestamp": 1234567890,
      "datetime": "2024-01-15 12:00:00",
      "temperature": 18.5,
      "weather": "Clear",
      "description": "clear sky",
      "wind_speed": 3.5,
      "rain_probability": 10,
      "rain_volume": 0
    }
  ]
}
```

### Weather Impact Score
Calculate weather impact score for deliveries.

**Endpoint:** `POST /api/weather/impact`

**Request Body:**
```json
{
  "latitude": 37.7749,
  "longitude": -122.4194
}
```

**Response:**
```json
{
  "weather_conditions": {...},
  "impact_score": 0.85,
  "recommendation": "Good conditions"
}
```

---

## Currency APIs

### Get Exchange Rates
Get all exchange rates for a base currency.

**Endpoint:** `POST /api/currency/rates`

**Request Body:**
```json
{
  "base_currency": "USD"
}
```

**Response:**
```json
{
  "base_currency": "USD",
  "last_updated": "2024-01-15T12:00:00Z",
  "next_update": "2024-01-16T12:00:00Z",
  "rates": {
    "EUR": 0.85,
    "GBP": 0.73,
    "TRY": 28.5,
    ...
  }
}
```

### Convert Currency
Convert amount from one currency to another.

**Endpoint:** `POST /api/currency/convert`

**Request Body:**
```json
{
  "amount": 100,
  "from_currency": "USD",
  "to_currency": "EUR"
}
```

**Response:**
```json
{
  "from_currency": "USD",
  "to_currency": "EUR",
  "from_amount": 100,
  "to_amount": 85.5,
  "exchange_rate": 0.855,
  "last_updated": "2024-01-15T12:00:00Z"
}
```

### Popular Currencies
Get exchange rates for popular currencies.

**Endpoint:** `GET /api/currency/popular`

**Response:**
```json
{
  "base_currency": "USD",
  "last_updated": "2024-01-15T12:00:00Z",
  "popular_rates": {
    "EUR": 0.85,
    "GBP": 0.73,
    "TRY": 28.5,
    "JPY": 110.5
  }
}
```

---

## Tracking APIs

### Update Location
Update courier's current location.

**Endpoint:** `POST /api/tracking/update`

**Request Body:**
```json
{
  "courier_id": "uuid",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "accuracy": 10.5,
  "speed": 25.3,
  "heading": 180
}
```

**Response:**
```json
{
  "success": true,
  "location": {
    "id": "uuid",
    "courier_id": "uuid",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "address": "San Francisco, CA",
    "timestamp": "2024-01-15T12:00:00Z"
  }
}
```

### Get Courier Location
Get courier's latest location.

**Endpoint:** `GET /api/tracking/courier/{courier_id}`

**Response:**
```json
{
  "id": "uuid",
  "courier_id": "uuid",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "accuracy": 10.5,
  "speed": 25.3,
  "heading": 180,
  "address": "San Francisco, CA",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

### Get Active Locations
Get all active courier locations.

**Endpoint:** `GET /api/tracking/active?status=available`

**Response:**
```json
{
  "couriers": [
    {
      "id": "uuid",
      "courier_id": "uuid",
      "courier_name": "John Doe",
      "vehicle_type": "motorcycle",
      "latitude": 37.7749,
      "longitude": -122.4194,
      "timestamp": "2024-01-15T12:00:00Z"
    }
  ],
  "count": 15
}
```

### Track Order
Track order delivery in real-time.

**Endpoint:** `GET /api/tracking/order/{order_id}`

**Response:**
```json
{
  "order_id": "uuid",
  "order_status": "in_transit",
  "courier_location": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "address": "San Francisco, CA",
    "speed": 25.3,
    "heading": 180,
    "last_updated": "2024-01-15T12:00:00Z"
  },
  "delivery_location": {
    "latitude": 37.8,
    "longitude": -122.4,
    "address": "Oakland, CA"
  },
  "eta": {
    "distance_km": 5.2,
    "duration_minutes": 12
  }
}
```

### Find Nearby Couriers
Find available couriers near a location.

**Endpoint:** `POST /api/tracking/nearby`

**Request Body:**
```json
{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "max_distance_km": 10.0,
  "status": "available"
}
```

**Response:**
```json
{
  "couriers": [
    {
      "courier_id": "uuid",
      "distance_km": 2.5,
      "duration_minutes": 8,
      "location": [37.78, -122.42]
    }
  ],
  "count": 5
}
```

---

## Order APIs

### Create Order
Create a new delivery order.

**Endpoint:** `POST /api/orders/`

**Request Body:**
```json
{
  "customer_name": "Jane Smith",
  "customer_phone": "+1234567890",
  "pickup_address": "123 Main St, San Francisco, CA",
  "delivery_address": "456 Oak Ave, Oakland, CA",
  "package_weight": 2.5,
  "package_description": "Electronics",
  "delivery_notes": "Call upon arrival",
  "priority": 1
}
```

**Response:**
```json
{
  "id": "uuid",
  "order_number": "LOOP-20240115-1234",
  "customer_name": "Jane Smith",
  "status": "pending",
  "distance_km": 15.2,
  "estimated_duration_minutes": 25,
  "created_at": "2024-01-15T12:00:00Z"
}
```

### List Orders
List orders with optional filters.

**Endpoint:** `GET /api/orders/?status=pending&limit=50`

**Response:**
```json
{
  "orders": [...],
  "count": 15
}
```

### Get Order
Get order details.

**Endpoint:** `GET /api/orders/{order_id}`

**Response:**
```json
{
  "id": "uuid",
  "order_number": "LOOP-20240115-1234",
  "customer_name": "Jane Smith",
  "status": "assigned",
  "courier_id": "uuid",
  ...
}
```

### Update Order
Update order status or details.

**Endpoint:** `PATCH /api/orders/{order_id}`

**Request Body:**
```json
{
  "status": "picked_up"
}
```

---

## Courier APIs

### Create Courier
Create a new courier.

**Endpoint:** `POST /api/couriers/`

**Request Body:**
```json
{
  "name": "John Doe",
  "phone": "+1234567890",
  "email": "john@example.com",
  "vehicle_type": "motorcycle",
  "license_plate": "ABC123"
}
```

### List Couriers
List all couriers.

**Endpoint:** `GET /api/couriers/?status=available&limit=100`

**Response:**
```json
{
  "couriers": [...],
  "count": 25
}
```

### Get Courier Stats
Get courier statistics.

**Endpoint:** `GET /api/couriers/{courier_id}/stats`

**Response:**
```json
{
  "courier": {...},
  "statistics": {
    "total_deliveries": 150,
    "rating": 4.8,
    "completed_orders": 145,
    "orders_in_progress": 2,
    "current_status": "busy"
  }
}
```

---

## AI Engine APIs

### Recommend Courier
Get AI recommendation for best courier.

**Endpoint:** `POST /api/ai/recommend`

**Request Body:**
```json
{
  "order_id": "uuid"
}
```

**Response:**
```json
{
  "order_id": "uuid",
  "recommended_courier": {
    "courier_id": "uuid",
    "courier_name": "John Doe",
    "total_score": 0.87,
    "distance_km": 2.5,
    "estimated_time_minutes": 8,
    "scores": {
      "distance": 0.875,
      "rating": 0.96,
      "weather": 0.85,
      "traffic": 0.90,
      "workload": 1.0,
      "vehicle_match": 1.0
    }
  },
  "alternatives": [...],
  "total_candidates": 5
}
```

### Auto Assign
Automatically assign best courier to order.

**Endpoint:** `POST /api/ai/assign`

**Request Body:**
```json
{
  "order_id": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "order_id": "uuid",
  "assigned_courier": {...},
  "assignment_details": {...}
}
```

### Optimize Route
Optimize delivery route for courier.

**Endpoint:** `POST /api/ai/optimize-route`

**Request Body:**
```json
{
  "courier_id": "uuid"
}
```

**Response:**
```json
{
  "courier_id": "uuid",
  "total_orders": 3,
  "total_stops": 6,
  "optimized_route": [...]
}
```

---

## WebSocket

### Real-Time Tracking

**Endpoint:** `WS /api/tracking/ws`

**Subscribe to Order:**
```json
{
  "type": "subscribe_order",
  "order_id": "uuid"
}
```

**Receive Updates:**
```json
{
  "type": "order_update",
  "data": {
    "order_id": "uuid",
    "courier_location": {...},
    "eta": {...}
  }
}
```

---

## Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `500` - Server Error

## Rate Limiting

Currently no rate limiting. Implement in production.

## Support

For support, contact the development team.
