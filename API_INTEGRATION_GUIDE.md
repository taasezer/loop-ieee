# LOOP Logistics - API Integration Guide

This guide helps you integrate LOOP Logistics APIs into your Flutter or any other mobile/web application.

## Base URL

```
Development: http://localhost:8001
Production: https://your-domain.com
```

All API endpoints are prefixed with `/api`.

## Authentication

### 1. Register User

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "phone": "+1234567890",
  "password": "securePassword123",
  "full_name": "John Doe",
  "role": "customer"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "role": "customer"
  }
}
```

### 2. Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

### 3. Using Access Token

For all protected endpoints, include the access token in the Authorization header:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## Creating an Order

```http
POST /api/orders
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "customer_id": "your-user-id",
  "pickup_address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA",
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "delivery_address": {
    "street": "456 Park Ave",
    "city": "New York",
    "state": "NY",
    "postal_code": "10022",
    "country": "USA",
    "latitude": 40.7614,
    "longitude": -73.9776
  },
  "package_description": "Electronics package",
  "package_weight": 2.5,
  "priority": "normal",
  "payment_method": "card"
}
```

**Response:**
```json
{
  "message": "Order created successfully",
  "order": {
    "id": "order-uuid",
    "tracking_code": "LOOP12345678",
    "status": "assigned",
    "estimated_distance": 5.2,
    "estimated_duration": 25,
    "estimated_price": 15.50
  },
  "route_info": {...},
  "pricing_breakdown": {...}
}
```

## Tracking an Order

```http
GET /api/tracking/order/{order_id}
```

**Response:**
```json
{
  "order_id": "order-uuid",
  "tracking_code": "LOOP12345678",
  "status": "in_transit",
  "courier_location": {
    "lat": 40.7500,
    "lng": -73.9800
  },
  "courier_info": {
    "vehicle_type": "motorcycle",
    "rating": 4.8
  }
}
```

## Real-Time Updates with WebSocket

### Socket.IO Connection (Flutter Example)

```dart
import 'package:socket_io_client/socket_io_client.dart' as IO;

IO.Socket socket = IO.io('http://localhost:8001', <String, dynamic>{
  'transports': ['websocket'],
  'autoConnect': false,
});

socket.connect();

// Listen for connection
socket.on('connect', (_) {
  print('Connected to server');
});

// Join tracking room for specific order
socket.emit('join_tracking', {'order_id': 'your-order-id'});

// Listen for courier location updates
socket.on('courier_location', (data) {
  print('Courier location: ${data['location']}');
  // Update UI with new location
});

// Send courier location updates (for courier app)
socket.emit('courier_location_update', {
  'courier_id': 'courier-id',
  'location': {
    'latitude': 40.7128,
    'longitude': -74.0060,
    'speed': 15.5,
    'heading': 90
  }
});
```

## Flutter Integration Example

### 1. Setup Dependencies (pubspec.yaml)

```yaml
dependencies:
  dio: ^5.0.0
  socket_io_client: ^2.0.0
  geolocator: ^10.0.0
  firebase_messaging: ^14.0.0
  flutter_map: ^5.0.0
```

### 2. API Service Class

```dart
import 'package:dio/dio.dart';

class LoopApiService {
  final Dio _dio;
  final String baseUrl = 'http://localhost:8001/api';
  String? _accessToken;

  LoopApiService() : _dio = Dio() {
    _dio.options.baseUrl = baseUrl;
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          if (_accessToken != null) {
            options.headers['Authorization'] = 'Bearer $_accessToken';
          }
          return handler.next(options);
        },
      ),
    );
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final response = await _dio.post('/auth/login', data: {
        'email': email,
        'password': password,
      });
      _accessToken = response.data['access_token'];
      return response.data;
    } catch (e) {
      throw Exception('Login failed: $e');
    }
  }

  Future<Map<String, dynamic>> createOrder(Map<String, dynamic> orderData) async {
    try {
      final response = await _dio.post('/orders', data: orderData);
      return response.data;
    } catch (e) {
      throw Exception('Order creation failed: $e');
    }
  }

  Future<Map<String, dynamic>> trackOrder(String orderId) async {
    try {
      final response = await _dio.get('/tracking/order/$orderId');
      return response.data;
    } catch (e) {
      throw Exception('Tracking failed: $e');
    }
  }

  Future<List<dynamic>> getMyOrders() async {
    try {
      final response = await _dio.get('/orders');
      return response.data['orders'];
    } catch (e) {
      throw Exception('Failed to fetch orders: $e');
    }
  }
}
```

### 3. Location Service (for Couriers)

```dart
import 'package:geolocator/geolocator.dart';
import 'package:socket_io_client/socket_io_client.dart' as IO;

class LocationService {
  IO.Socket? socket;
  String? courierId;

  void initialize(String socketUrl, String courierId) {
    this.courierId = courierId;
    socket = IO.io(socketUrl, <String, dynamic>{
      'transports': ['websocket'],
    });
    socket!.connect();
  }

  Future<void> startLocationTracking() async {
    // Check permissions
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }

    // Start tracking
    Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10, // Update every 10 meters
      ),
    ).listen((Position position) {
      // Send location to server
      socket?.emit('courier_location_update', {
        'courier_id': courierId,
        'location': {
          'latitude': position.latitude,
          'longitude': position.longitude,
          'speed': position.speed,
          'heading': position.heading,
        }
      });
    });
  }
}
```

### 4. Push Notifications Setup

```dart
import 'package:firebase_messaging/firebase_messaging.dart';

class NotificationService {
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;

  Future<void> initialize() async {
    // Request permission
    await _messaging.requestPermission();

    // Get FCM token
    String? token = await _messaging.getToken();
    print('FCM Token: $token');
    
    // Send token to backend to store in user's device_tokens array
    // await apiService.updateDeviceToken(token);

    // Handle foreground messages
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      print('Received message: ${message.notification?.title}');
      // Show local notification
    });
  }
}
```

## Error Handling

All API errors follow this format:

```json
{
  "detail": "Error message here"
}
```

HTTP Status Codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Rate Limit Exceeded
- `500`: Internal Server Error

## Rate Limiting

Default rate limit: 100 requests per minute per IP address.

If exceeded, you'll receive:
```json
{
  "error": "Rate limit exceeded. Please try again later."
}
```

## Testing

### Using cURL

```bash
# Login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password123"}'

# Create Order (with token)
curl -X POST http://localhost:8001/api/orders \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...order data...}'
```

### Using Postman

1. Import the OpenAPI spec from `http://localhost:8001/docs`
2. Set up environment variables for `base_url` and `access_token`
3. Use the collection runner for testing multiple endpoints

## Best Practices

1. **Token Storage**: Store access tokens securely (Flutter Secure Storage)
2. **Token Refresh**: Implement automatic token refresh before expiration
3. **Error Handling**: Always handle network errors gracefully
4. **Loading States**: Show loading indicators during API calls
5. **Offline Support**: Cache critical data for offline access
6. **Real-time Updates**: Use WebSocket for real-time features
7. **Location Permissions**: Always request and handle location permissions properly
8. **Battery Optimization**: Implement smart location tracking (reduce frequency when idle)

## Support

For detailed API documentation, visit: `http://localhost:8001/docs`

---

**Happy Integration! 🚀**
