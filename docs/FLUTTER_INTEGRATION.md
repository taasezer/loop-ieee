# LOOP Logistics - Flutter Integration Guide

## Overview

This guide provides comprehensive instructions for integrating the LOOP Logistics backend API with your Flutter application.

## Base Configuration

### 1. Add Dependencies

Add these to your `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  web_socket_channel: ^2.4.0
  google_maps_flutter: ^2.5.0
  geolocator: ^10.1.0
  provider: ^6.1.0
  shared_preferences: ^2.2.2
```

### 2. API Configuration

Create `lib/config/api_config.dart`:

```dart
class ApiConfig {
  static const String baseUrl = 'http://your-api-url:8000';
  static const String apiVersion = '/api';

  // Endpoints
  static const String maps = '$apiVersion/maps';
  static const String weather = '$apiVersion/weather';
  static const String currency = '$apiVersion/currency';
  static const String tracking = '$apiVersion/tracking';
  static const String orders = '$apiVersion/orders';
  static const String couriers = '$apiVersion/couriers';
  static const String ai = '$apiVersion/ai';

  // WebSocket
  static const String wsUrl = 'ws://your-api-url:8000/api/tracking/ws';
}
```

## API Services

### 1. HTTP Client Service

Create `lib/services/api_service.dart`:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';

class ApiService {
  final http.Client client = http.Client();

  Future<Map<String, dynamic>> get(String endpoint) async {
    try {
      final response = await client.get(
        Uri.parse('${ApiConfig.baseUrl}$endpoint'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load data: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<Map<String, dynamic>> post(
    String endpoint,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await client.post(
        Uri.parse('${ApiConfig.baseUrl}$endpoint'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(data),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to post data: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<Map<String, dynamic>> patch(
    String endpoint,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await client.patch(
        Uri.parse('${ApiConfig.baseUrl}$endpoint'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(data),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to update data: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }
}
```

### 2. Location Tracking Service

Create `lib/services/location_service.dart`:

```dart
import 'package:geolocator/geolocator.dart';
import 'api_service.dart';

class LocationService {
  final ApiService _apiService = ApiService();

  Future<Position> getCurrentLocation() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      throw Exception('Location services are disabled.');
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        throw Exception('Location permissions are denied');
      }
    }

    return await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high,
    );
  }

  Future<void> updateCourierLocation(String courierId) async {
    final position = await getCurrentLocation();

    await _apiService.post('/tracking/update', {
      'courier_id': courierId,
      'latitude': position.latitude,
      'longitude': position.longitude,
      'accuracy': position.accuracy,
      'speed': position.speed,
      'heading': position.heading,
    });
  }

  Stream<Position> trackLocationContinuously() {
    return Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10, // Update every 10 meters
      ),
    );
  }
}
```

### 3. Order Service

Create `lib/services/order_service.dart`:

```dart
import 'api_service.dart';
import '../models/order.dart';

class OrderService {
  final ApiService _apiService = ApiService();

  Future<Order> createOrder({
    required String customerName,
    required String customerPhone,
    required String pickupAddress,
    required String deliveryAddress,
    required double packageWeight,
    required String packageDescription,
    String? deliveryNotes,
    int priority = 1,
  }) async {
    final response = await _apiService.post('/orders/', {
      'customer_name': customerName,
      'customer_phone': customerPhone,
      'pickup_address': pickupAddress,
      'delivery_address': deliveryAddress,
      'package_weight': packageWeight,
      'package_description': packageDescription,
      'delivery_notes': deliveryNotes,
      'priority': priority,
    });

    return Order.fromJson(response);
  }

  Future<List<Order>> getOrders({String? status, String? courierId}) async {
    String endpoint = '/orders/';
    List<String> params = [];

    if (status != null) params.add('status=$status');
    if (courierId != null) params.add('courier_id=$courierId');

    if (params.isNotEmpty) {
      endpoint += '?${params.join('&')}';
    }

    final response = await _apiService.get(endpoint);
    final orders = (response['orders'] as List)
        .map((order) => Order.fromJson(order))
        .toList();

    return orders;
  }

  Future<Order> getOrder(String orderId) async {
    final response = await _apiService.get('/orders/$orderId');
    return Order.fromJson(response);
  }

  Future<Order> updateOrderStatus(String orderId, String status) async {
    final response = await _apiService.patch('/orders/$orderId', {
      'status': status,
    });
    return Order.fromJson(response);
  }

  Future<Map<String, dynamic>> trackOrder(String orderId) async {
    return await _apiService.get('/tracking/order/$orderId');
  }
}
```

### 4. AI Assignment Service

Create `lib/services/ai_service.dart`:

```dart
import 'api_service.dart';

class AIService {
  final ApiService _apiService = ApiService();

  Future<Map<String, dynamic>> recommendCourier(String orderId) async {
    return await _apiService.post('/ai/recommend', {
      'order_id': orderId,
    });
  }

  Future<Map<String, dynamic>> autoAssignCourier(String orderId) async {
    return await _apiService.post('/ai/assign', {
      'order_id': orderId,
    });
  }

  Future<Map<String, dynamic>> optimizeRoute(String courierId) async {
    return await _apiService.post('/ai/optimize-route', {
      'courier_id': courierId,
    });
  }
}
```

## Models

### Order Model

Create `lib/models/order.dart`:

```dart
class Order {
  final String id;
  final String orderNumber;
  final String customerName;
  final String customerPhone;
  final double pickupLatitude;
  final double pickupLongitude;
  final String pickupAddress;
  final double deliveryLatitude;
  final double deliveryLongitude;
  final String deliveryAddress;
  final double packageWeight;
  final String packageDescription;
  final String? deliveryNotes;
  final int priority;
  final String status;
  final double? distanceKm;
  final int? estimatedDurationMinutes;
  final String? courierId;
  final DateTime createdAt;

  Order({
    required this.id,
    required this.orderNumber,
    required this.customerName,
    required this.customerPhone,
    required this.pickupLatitude,
    required this.pickupLongitude,
    required this.pickupAddress,
    required this.deliveryLatitude,
    required this.deliveryLongitude,
    required this.deliveryAddress,
    required this.packageWeight,
    required this.packageDescription,
    this.deliveryNotes,
    required this.priority,
    required this.status,
    this.distanceKm,
    this.estimatedDurationMinutes,
    this.courierId,
    required this.createdAt,
  });

  factory Order.fromJson(Map<String, dynamic> json) {
    return Order(
      id: json['id'],
      orderNumber: json['order_number'],
      customerName: json['customer_name'],
      customerPhone: json['customer_phone'],
      pickupLatitude: json['pickup_latitude'].toDouble(),
      pickupLongitude: json['pickup_longitude'].toDouble(),
      pickupAddress: json['pickup_address'],
      deliveryLatitude: json['delivery_latitude'].toDouble(),
      deliveryLongitude: json['delivery_longitude'].toDouble(),
      deliveryAddress: json['delivery_address'],
      packageWeight: json['package_weight'].toDouble(),
      packageDescription: json['package_description'],
      deliveryNotes: json['delivery_notes'],
      priority: json['priority'],
      status: json['status'],
      distanceKm: json['distance_km']?.toDouble(),
      estimatedDurationMinutes: json['estimated_duration_minutes'],
      courierId: json['courier_id'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}
```

## WebSocket Integration

Create `lib/services/websocket_service.dart`:

```dart
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../config/api_config.dart';

class WebSocketService {
  WebSocketChannel? _channel;

  void connect() {
    _channel = WebSocketChannel.connect(
      Uri.parse(ApiConfig.wsUrl),
    );
  }

  void subscribeToOrder(String orderId) {
    if (_channel != null) {
      _channel!.sink.add(json.encode({
        'type': 'subscribe_order',
        'order_id': orderId,
      }));
    }
  }

  Stream<dynamic> get stream {
    if (_channel != null) {
      return _channel!.stream.map((data) => json.decode(data));
    }
    return Stream.empty();
  }

  void disconnect() {
    _channel?.sink.close();
  }
}
```

## Example Usage

### Courier App - Location Tracking

```dart
import 'package:flutter/material.dart';
import 'services/location_service.dart';

class CourierTrackingScreen extends StatefulWidget {
  final String courierId;

  const CourierTrackingScreen({required this.courierId});

  @override
  _CourierTrackingScreenState createState() => _CourierTrackingScreenState();
}

class _CourierTrackingScreenState extends State<CourierTrackingScreen> {
  final LocationService _locationService = LocationService();

  @override
  void initState() {
    super.initState();
    _startTracking();
  }

  void _startTracking() {
    _locationService.trackLocationContinuously().listen((position) {
      _locationService.updateCourierLocation(widget.courierId);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Location Tracking')),
      body: Center(child: Text('Tracking active...')),
    );
  }
}
```

### Customer App - Order Tracking

```dart
import 'package:flutter/material.dart';
import 'services/websocket_service.dart';

class OrderTrackingScreen extends StatefulWidget {
  final String orderId;

  const OrderTrackingScreen({required this.orderId});

  @override
  _OrderTrackingScreenState createState() => _OrderTrackingScreenState();
}

class _OrderTrackingScreenState extends State<OrderTrackingScreen> {
  final WebSocketService _wsService = WebSocketService();
  Map<String, dynamic>? _trackingData;

  @override
  void initState() {
    super.initState();
    _wsService.connect();
    _wsService.subscribeToOrder(widget.orderId);

    _wsService.stream.listen((data) {
      if (data['type'] == 'order_update') {
        setState(() {
          _trackingData = data['data'];
        });
      }
    });
  }

  @override
  void dispose() {
    _wsService.disconnect();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Track Order')),
      body: _trackingData == null
          ? Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Text('Status: ${_trackingData!['order_status']}'),
                Text('ETA: ${_trackingData!['eta']['duration_minutes']} min'),
              ],
            ),
    );
  }
}
```

## API Endpoints Reference

### Maps & GPS
- `POST /api/maps/geocode` - Convert address to coordinates
- `POST /api/maps/reverse-geocode` - Convert coordinates to address
- `POST /api/maps/distance` - Calculate distance between points
- `POST /api/maps/route` - Get optimized route

### Weather
- `POST /api/weather/current` - Get current weather
- `POST /api/weather/forecast` - Get weather forecast
- `POST /api/weather/impact` - Get weather impact score

### Currency
- `POST /api/currency/rates` - Get exchange rates
- `POST /api/currency/convert` - Convert currency
- `GET /api/currency/popular` - Get popular currencies

### Tracking
- `POST /api/tracking/update` - Update courier location
- `GET /api/tracking/courier/{id}` - Get courier location
- `GET /api/tracking/active` - Get all active couriers
- `GET /api/tracking/order/{id}` - Track order delivery
- `WS /api/tracking/ws` - WebSocket for real-time updates

### Orders
- `POST /api/orders/` - Create new order
- `GET /api/orders/` - List orders
- `GET /api/orders/{id}` - Get order details
- `PATCH /api/orders/{id}` - Update order
- `DELETE /api/orders/{id}` - Cancel order

### Couriers
- `POST /api/couriers/` - Create courier
- `GET /api/couriers/` - List couriers
- `GET /api/couriers/{id}` - Get courier details
- `PATCH /api/couriers/{id}` - Update courier
- `GET /api/couriers/{id}/stats` - Get courier statistics

### AI Engine
- `POST /api/ai/recommend` - Get courier recommendation
- `POST /api/ai/assign` - Auto-assign courier
- `POST /api/ai/optimize-route` - Optimize route
- `GET /api/ai/analytics/assignments` - Get assignment analytics

## Error Handling

All API calls should handle errors properly:

```dart
try {
  final order = await orderService.createOrder(...);
  // Success
} catch (e) {
  // Handle error
  showDialog(
    context: context,
    builder: (context) => AlertDialog(
      title: Text('Error'),
      content: Text(e.toString()),
    ),
  );
}
```

## Best Practices

1. **Location Permissions**: Always request and check location permissions
2. **Network Status**: Check network connectivity before API calls
3. **Loading States**: Show loading indicators during API calls
4. **Error Handling**: Implement comprehensive error handling
5. **Caching**: Cache data locally when appropriate
6. **Battery Optimization**: Adjust location update frequency based on battery level
7. **Background Tasks**: Use background services for location tracking
8. **Security**: Never store API keys in client code

## Support

For issues or questions, refer to the main API documentation or contact the development team.
