# LOOP API Documentation

## Base URL

```
Production: https://api.loop-logistics.com
Development: http://localhost:8000
```

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## API Endpoints

### Authentication

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "phone_number": "+1234567890",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "customer"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email_or_phone": "user@example.com",
  "password": "SecurePass123!"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "customer"
  }
}
```

### Orders

#### Create Order
```http
POST /api/v1/orders
Authorization: Bearer <token>
Content-Type: application/json

{
  "pickup_address": "123 Main St",
  "pickup_latitude": 40.7128,
  "pickup_longitude": -74.0060,
  "delivery_address": "456 Oak Ave",
  "delivery_latitude": 40.7589,
  "delivery_longitude": -73.9851,
  "delivery_contact_name": "Jane Smith",
  "delivery_contact_phone": "+1234567890",
  "package_description": "Documents",
  "payment_method": "card",
  "order_type": "STANDARD"
}
```

#### Get Order
```http
GET /api/v1/orders/{order_id}
Authorization: Bearer <token>
```

#### Track Order
```http
GET /api/v1/orders/{order_id}/track
```

Response:
```json
{
  "order_id": "uuid",
  "order_number": "ORD-20231112-ABC123",
  "status": "IN_TRANSIT",
  "courier_id": "uuid",
  "courier_location": {
    "latitude": 40.7300,
    "longitude": -74.0100,
    "last_updated": "2023-11-12T10:30:00Z"
  },
  "estimated_delivery_time": "2023-11-12T11:00:00Z"
}
```

### Couriers

#### List Available Couriers
```http
GET /api/v1/couriers
Authorization: Bearer <token>
```

#### Update Location
```http
PUT /api/v1/couriers/{courier_id}/location
Authorization: Bearer <token>
Content-Type: application/json

{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "accuracy": 10.5,
  "speed": 25.0,
  "heading": 180.0
}
```

### WebSocket Connections

#### Track Order (WebSocket)
```javascript
const ws = new WebSocket('wss://api.loop-logistics.com/ws/tracking/{order_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Order update:', data);
};
```

#### Courier Connection (WebSocket)
```javascript
const ws = new WebSocket('wss://api.loop-logistics.com/ws/courier/{courier_id}');

// Send location update
ws.send(JSON.stringify({
  type: 'location_update',
  location: {
    latitude: 40.7128,
    longitude: -74.0060
  }
}));
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2023-11-12T10:30:00Z"
}
```

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Rate Limiting

- **Per minute**: 60 requests
- **Per hour**: 1000 requests

Headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699790400
```

## Pagination

List endpoints support pagination:

```http
GET /api/v1/orders?skip=0&limit=20
```

Response:
```json
{
  "orders": [...],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

## Interactive Documentation

- **Swagger UI**: https://api.loop-logistics.com/docs
- **ReDoc**: https://api.loop-logistics.com/redoc

---

For more details, visit the interactive API documentation.
