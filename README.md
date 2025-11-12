# LOOP Logistics Platform

A comprehensive full-stack logistics and delivery management system with real-time tracking, AI-powered courier assignment, dynamic pricing, and multi-channel notifications.

## 🚀 Features

### Core Modules (18 Components)

1. **Authentication & Authorization**
   - JWT-based authentication
   - Multi-role support (Admin, Dispatcher, Courier, Customer)
   - Role-based access control
   - Refresh token mechanism

2. **Order Management**
   - Complete order lifecycle management
   - Real-time status tracking
   - Proof of delivery (POD) support
   - Scheduled deliveries
   - Multi-delivery batching

3. **Courier Management**
   - Courier profiles with vehicle types
   - Real-time online/offline status
   - Performance scoring and ratings
   - Earnings tracking
   - Shift management

4. **Map & Routing Services**
   - OpenStreetMap Nominatim geocoding
   - OSRM route optimization
   - Distance matrix calculations
   - Multi-stop route optimization
   - Real-time location tracking

5. **Weather Integration**
   - OpenWeatherMap API integration
   - Weather-based dynamic pricing
   - Bad weather alerts
   - Forecast data for planning

6. **Currency & Pricing**
   - Live currency exchange rates
   - Multi-currency support
   - Dynamic pricing engine
   - Peak hour surge pricing
   - Weather-based adjustments
   - Priority-based pricing

7. **AI-Powered Assignment**
   - Machine learning courier matching
   - Smart assignment based on:
     - Distance to pickup
     - Courier rating
     - Performance score
     - Current workload
   - Route optimization algorithms

8. **Real-Time Tracking**
   - WebSocket/Socket.IO integration
   - Live courier location updates
   - ETA calculations
   - Customer tracking interface

9. **Payment Integration**
   - Stripe payment processing
   - Cash on delivery tracking
   - Automatic courier payouts
   - Payment history

10. **Notification System**
    - Firebase Cloud Messaging (FCM)
    - Email notifications (SendGrid)
    - SMS notifications (Twilio)
    - In-app notifications

11. **Analytics & Reporting**
    - Real-time dashboard metrics
    - Revenue analytics
    - Order statistics
    - Courier performance tracking
    - Custom report generation

12. **Admin Dashboard**
    - Complete order oversight
    - User management
    - System configuration
    - Broadcast messaging
    - Manual courier assignment

13. **n8n Automation**
    - Webhook endpoints for workflow automation
    - Event-driven architecture
    - Analytics logging
    - Decision tracking

## 💻 Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB with Motor (async)
- **Authentication**: JWT with python-jose
- **Real-time**: Socket.IO / WebSocket
- **HTTP Client**: httpx (async)
- **Password Hashing**: bcrypt

### Frontend
- **Framework**: React 19
- **Routing**: React Router DOM
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn/UI (Radix UI)
- **HTTP Client**: Axios
- **Notifications**: Sonner

### Third-Party Integrations
- **Maps**: OpenStreetMap, Nominatim, OSRM, Mapbox
- **Weather**: OpenWeatherMap
- **Currency**: ExchangeRate-API
- **Payments**: Stripe
- **Notifications**: Firebase FCM, SendGrid, Twilio
- **Automation**: n8n

## 🔧 Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB
- API Keys (see below)

### 1. Backend Setup

```bash
cd /app/backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### 2. Frontend Setup

```bash
cd /app/frontend

# Install dependencies
yarn install

# Start development server
yarn start
```

### 3. Required API Keys

Update `/app/backend/.env` with your API keys:

```bash
# Maps
MAPBOX_ACCESS_TOKEN="your_mapbox_token"

# Weather
OPENWEATHER_API_KEY="your_openweather_key"

# Currency
EXCHANGERATE_API_KEY="your_exchangerate_key"

# Payment
STRIPE_SECRET_KEY="your_stripe_key"

# Notifications
FCM_SERVER_KEY="your_fcm_key"
SENDGRID_API_KEY="your_sendgrid_key"
TWILIO_ACCOUNT_SID="your_twilio_sid"
TWILIO_AUTH_TOKEN="your_twilio_token"

# n8n
N8N_WEBHOOK_URL="your_n8n_webhook_url"
```

### Where to Get API Keys:

1. **Mapbox**: https://account.mapbox.com/access-tokens/
2. **OpenWeatherMap**: https://openweathermap.org/api
3. **ExchangeRate-API**: https://www.exchangerate-api.com/
4. **Stripe**: https://dashboard.stripe.com/apikeys
5. **Firebase FCM**: Firebase Console > Project Settings > Cloud Messaging
6. **SendGrid**: https://app.sendgrid.com/settings/api_keys
7. **Twilio**: https://console.twilio.com/
8. **n8n**: Self-hosted or https://n8n.io/

## 📚 API Documentation

Once the backend is running, visit:
```
http://localhost:8001/docs
```

For interactive API documentation (Swagger UI).

## 🔑 Default Admin Credentials

Create an admin account via the registration page:
- Role: Admin
- Email: your-email@example.com
- Password: your-secure-password

## 📋 Database Collections

- `users` - User accounts (customers, couriers, admins)
- `couriers` - Courier profiles and vehicle info
- `orders` - Delivery orders and tracking
- `locations` - Real-time location history
- `pricing_rules` - Dynamic pricing configuration
- `earnings` - Courier payment records
- `ratings` - Customer-courier reviews
- `notifications` - Notification history
- `route_history` - Route optimization logs
- `payment_transactions` - Payment records
- `promotions` - Discount codes and promotions
- `system_config` - System configuration

## 🎯 API Endpoints Overview

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token

### Orders
- `POST /api/orders` - Create new order
- `GET /api/orders` - List orders (filtered)
- `GET /api/orders/{id}` - Get order details
- `PATCH /api/orders/{id}/status` - Update order status
- `POST /api/orders/{id}/assign/{courier_id}` - Assign courier

### Couriers
- `POST /api/couriers` - Create courier profile
- `GET /api/couriers` - List couriers
- `GET /api/couriers/me` - Get my courier profile
- `PATCH /api/couriers/status` - Update online status
- `POST /api/couriers/location` - Update location
- `GET /api/couriers/{id}/stats` - Get courier statistics

### Tracking
- `GET /api/tracking/order/{id}` - Track order
- `GET /api/tracking/order/{id}/eta` - Calculate ETA
- `GET /api/tracking/courier/{id}/location-history` - Location history

### Maps
- `GET /api/maps/geocode` - Address to coordinates
- `GET /api/maps/reverse-geocode` - Coordinates to address
- `POST /api/maps/route` - Calculate route
- `POST /api/maps/optimize-route` - Optimize multi-stop route
- `POST /api/maps/distance-matrix` - Distance matrix

### Weather
- `GET /api/weather/current` - Current weather
- `GET /api/weather/forecast` - Weather forecast
- `GET /api/weather/impact` - Weather impact factor

### Currency
- `GET /api/currency/rates` - Exchange rates
- `GET /api/currency/convert` - Convert currency

### Payments
- `POST /api/payments/create-intent` - Create payment intent
- `POST /api/payments/cash` - Record cash payment
- `POST /api/payments/payout/{courier_id}` - Process payout

### Notifications
- `POST /api/notifications/push` - Send push notification
- `POST /api/notifications/email` - Send email
- `POST /api/notifications/sms` - Send SMS

### Analytics
- `GET /api/analytics/dashboard` - Dashboard metrics
- `GET /api/analytics/orders/stats` - Order statistics
- `GET /api/analytics/couriers/performance` - Courier performance
- `GET /api/analytics/revenue` - Revenue analytics

### Admin
- `GET /api/admin/orders/all` - All orders
- `GET /api/admin/users/all` - All users
- `PATCH /api/admin/users/{id}/status` - Update user status
- `POST /api/admin/broadcast` - Broadcast message
- `GET /api/admin/config` - System configuration
- `POST /api/admin/config` - Update configuration

### Pricing
- `POST /api/pricing/calculate` - Calculate delivery price
- `POST /api/pricing/earnings` - Calculate courier earnings
- `GET /api/pricing/rules` - Get pricing rules

### n8n Webhooks
- `POST /api/webhooks/order-created` - Order created event
- `POST /api/webhooks/courier-assigned` - Courier assigned event
- `POST /api/webhooks/delivery-completed` - Delivery completed event
- `POST /api/webhooks/analytics-event` - Generic analytics event

## 🐛 Known Issues & Limitations

1. **Free Tier APIs**: Some features use free tier APIs which have rate limits
2. **Payment Integration**: Stripe is in test mode - use test cards
3. **n8n Setup**: Requires separate n8n instance setup
4. **Real-time Tracking**: WebSocket connection requires proper configuration

## 🚀 Deployment

The application is containerized and ready for deployment. Make sure to:

1. Set all environment variables
2. Configure MongoDB connection
3. Set up SSL/TLS for production
4. Configure CORS properly
5. Set up proper logging and monitoring
6. Configure backup strategies

## 📝 Flutter Integration Notes

The API is designed to be Flutter-compatible:

1. **RESTful**: All endpoints follow REST principles
2. **JSON**: Standard JSON request/response format
3. **JWT**: Standard bearer token authentication
4. **CORS**: Configured for cross-origin requests
5. **WebSocket**: Socket.IO client available for Flutter
6. **Error Handling**: Consistent error response format

### Flutter Packages Recommended:
- `dio` - HTTP client
- `socket_io_client` - Real-time communication
- `flutter_map` - Map display
- `geolocator` - Location services
- `firebase_messaging` - Push notifications

## 🤝 Contributing

This is a comprehensive logistics platform built as an MVP. Contributions and improvements are welcome!

## 📝 License

Private project - All rights reserved.

## 📧 Support

For issues or questions, please check the API documentation at `/docs` endpoint.

---

**Built with ❤️ for modern logistics management**
