# LOOP - Advanced Logistics and Courier Management System

![LOOP Logo](docs/logo.png)

## Overview

**LOOP** is a comprehensive, enterprise-grade logistics and courier management platform built with modern technologies. The system provides real-time tracking, AI-powered courier assignment, dynamic pricing, and seamless integration with multiple third-party services.

## Features

### Core Features
- ✅ **Multi-role Authentication System** (Customer, Courier, Admin, Dispatcher)
- ✅ **Real-time Location Tracking** with WebSocket support
- ✅ **AI-Powered Courier Assignment** using machine learning
- ✅ **Dynamic Pricing Engine** (weather, traffic, demand-based)
- ✅ **Route Optimization** with OSRM integration
- ✅ **Multi-channel Notifications** (Push, SMS, Email)
- ✅ **Payment Integration** (Stripe, İyzico/PayTR)
- ✅ **Comprehensive Admin Dashboard**
- ✅ **Analytics and Reporting**
- ✅ **Multi-currency Support**

### Technical Features
- 🚀 **FastAPI** - Modern, fast, async Python web framework
- 🗄️ **PostgreSQL** - Robust relational database
- ⚡ **Redis** - High-performance caching and session management
- 🔌 **WebSocket** - Real-time bidirectional communication
- 🐳 **Docker** - Containerized deployment
- 🔐 **JWT Authentication** - Secure token-based auth
- 📊 **Prometheus** - Monitoring and metrics
- 🤖 **n8n** - Workflow automation
- 🧠 **scikit-learn** - Machine learning capabilities

## Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **Celery** - Background tasks

### Database
- **PostgreSQL 15** - Primary database
- **Redis 7** - Cache and session store

### External Services
- **OpenStreetMap/Nominatim** - Geocoding
- **OSRM** - Routing engine
- **Mapbox** - Advanced mapping
- **OpenWeatherMap** - Weather data
- **ExchangeRate-API** - Currency rates
- **Firebase FCM** - Push notifications
- **Twilio** - SMS notifications
- **SendGrid** - Email notifications
- **Stripe** - International payments
- **İyzico/PayTR** - Turkish payment gateway

### DevOps
- **Docker & Docker Compose** - Containerization
- **Nginx** - Reverse proxy
- **Prometheus** - Monitoring
- **n8n** - Workflow automation

## Project Structure

```
LOOP/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── repositories/    # Data access layer
│   ├── core/            # Core utilities
│   ├── integrations/    # External services
│   ├── ai/              # ML components
│   ├── tasks/           # Background tasks
│   └── utils/           # Utilities
├── alembic/             # Database migrations
├── tests/               # Test suite
├── docker/              # Docker configs
├── docs/                # Documentation
└── scripts/             # Utility scripts
```

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/loop.git
cd loop
```

2. **Create virtual environment**
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
alembic upgrade head
```

6. **Run the application**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Build and run with Docker Compose**
```bash
docker-compose up -d
```

2. **Access services**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- n8n: http://localhost:5678
- Flower (Celery): http://localhost:5555
- Prometheus: http://localhost:9090

## Configuration

All configuration is managed through environment variables. See `.env.example` for all available options.

### Key Configuration Areas

#### Database
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/loop_db
```

#### Redis
```env
REDIS_URL=redis://localhost:6379/0
```

#### JWT
```env
JWT_SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

#### External Services
```env
OPENWEATHER_API_KEY=your-api-key
MAPBOX_ACCESS_TOKEN=your-token
STRIPE_API_KEY=your-stripe-key
```

## API Documentation

### Interactive API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints

#### Authentication
```
POST /api/v1/auth/register       - Register new user
POST /api/v1/auth/login          - User login
POST /api/v1/auth/refresh        - Refresh access token
POST /api/v1/auth/verify-otp     - Verify OTP
```

#### Orders
```
POST /api/v1/orders              - Create new order
GET /api/v1/orders/{id}          - Get order details
PUT /api/v1/orders/{id}/status   - Update order status
GET /api/v1/orders/history       - Get order history
```

#### Couriers
```
GET /api/v1/couriers             - List available couriers
POST /api/v1/couriers/location   - Update courier location
GET /api/v1/couriers/{id}/orders - Get courier orders
```

#### Real-time Tracking
```
WS /api/v1/ws/tracking/{order_id}    - Track order in real-time
WS /api/v1/ws/courier/{courier_id}   - Track courier location
WS /api/v1/ws/notifications          - Receive notifications
```

## Testing

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/unit/test_auth.py
```

### Load Testing
```bash
locust -f tests/load/locustfile.py
```

## Database Migrations

### Create Migration
```bash
alembic revision --autogenerate -m "Description"
```

### Apply Migrations
```bash
alembic upgrade head
```

### Rollback
```bash
alembic downgrade -1
```

## Background Tasks

The system uses Celery for background task processing:

- Currency rate updates (daily)
- Weather data updates (hourly)
- Analytics aggregation
- Notification batching
- Report generation

### Monitor Tasks
Access Flower dashboard at http://localhost:5555

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Prometheus Metrics
Available at http://localhost:9090

## Security

- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting
- CORS protection
- SQL injection prevention
- XSS protection
- HTTPS/TLS encryption
- GDPR compliance

## Performance Optimization

- Redis caching for hot data
- Database connection pooling
- Query optimization with indexes
- Async/await for I/O operations
- Background job processing
- Response compression (GZip)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, email support@loop-logistics.com or open an issue on GitHub.

## Roadmap

- [ ] GraphQL API support
- [ ] Microservices architecture
- [ ] Mobile SDK (Flutter)
- [ ] Advanced ML models
- [ ] Multi-tenant support
- [ ] Blockchain integration for transparency
- [ ] Voice assistant integration
- [ ] AR navigation for couriers

## Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

## Acknowledgments

- FastAPI team for the excellent framework
- OpenStreetMap community
- All open-source contributors

---

**Built with ❤️ for the logistics industry**
