# LOOP Project Structure

```
LOOP/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── config.py                    # Configuration and environment variables
│   ├── dependencies.py              # Dependency injection
│   │
│   ├── api/                         # API endpoints
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # Authentication endpoints
│   │   │   ├── orders.py            # Order management endpoints
│   │   │   ├── couriers.py          # Courier management endpoints
│   │   │   ├── users.py             # User management endpoints
│   │   │   ├── admin.py             # Admin dashboard endpoints
│   │   │   ├── tracking.py          # Real-time tracking endpoints
│   │   │   ├── payments.py          # Payment endpoints
│   │   │   ├── notifications.py     # Notification endpoints
│   │   │   ├── analytics.py         # Analytics endpoints
│   │   │   └── websocket.py         # WebSocket endpoints
│   │
│   ├── models/                      # Database models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── courier.py
│   │   ├── order.py
│   │   ├── location.py
│   │   ├── pricing.py
│   │   ├── earning.py
│   │   ├── rating.py
│   │   ├── notification.py
│   │   ├── route_history.py
│   │   └── payment_transaction.py
│   │
│   ├── schemas/                     # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── courier.py
│   │   ├── order.py
│   │   ├── location.py
│   │   ├── pricing.py
│   │   ├── payment.py
│   │   ├── notification.py
│   │   └── analytics.py
│   │
│   ├── services/                    # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── order_service.py
│   │   ├── courier_service.py
│   │   ├── pricing_service.py
│   │   ├── payment_service.py
│   │   ├── notification_service.py
│   │   ├── analytics_service.py
│   │   ├── map_service.py
│   │   ├── weather_service.py
│   │   ├── currency_service.py
│   │   ├── ai_assignment_service.py
│   │   └── tracking_service.py
│   │
│   ├── repositories/                # Data access layer
│   │   ├── __init__.py
│   │   ├── base_repository.py
│   │   ├── user_repository.py
│   │   ├── courier_repository.py
│   │   ├── order_repository.py
│   │   ├── location_repository.py
│   │   └── payment_repository.py
│   │
│   ├── core/                        # Core utilities
│   │   ├── __init__.py
│   │   ├── security.py              # JWT, password hashing
│   │   ├── database.py              # Database connection
│   │   ├── cache.py                 # Redis cache
│   │   ├── exceptions.py            # Custom exceptions
│   │   ├── middleware.py            # Custom middleware
│   │   └── logging.py               # Logging configuration
│   │
│   ├── integrations/                # External service integrations
│   │   ├── __init__.py
│   │   ├── osm/                     # OpenStreetMap integration
│   │   │   ├── __init__.py
│   │   │   ├── nominatim.py
│   │   │   └── osrm.py
│   │   ├── mapbox/
│   │   │   ├── __init__.py
│   │   │   └── client.py
│   │   ├── weather/
│   │   │   ├── __init__.py
│   │   │   └── openweather.py
│   │   ├── currency/
│   │   │   ├── __init__.py
│   │   │   └── exchange_rate.py
│   │   ├── payment/
│   │   │   ├── __init__.py
│   │   │   ├── stripe_client.py
│   │   │   └── iyzico_client.py
│   │   ├── notification/
│   │   │   ├── __init__.py
│   │   │   ├── fcm_client.py
│   │   │   ├── twilio_client.py
│   │   │   └── sendgrid_client.py
│   │   └── n8n/
│   │       ├── __init__.py
│   │       └── webhook_client.py
│   │
│   ├── ai/                          # AI and ML components
│   │   ├── __init__.py
│   │   ├── courier_assignment.py    # ML-based courier matching
│   │   ├── route_optimization.py    # Route optimization algorithms
│   │   ├── demand_forecasting.py    # Demand prediction
│   │   ├── pricing_model.py         # Dynamic pricing ML
│   │   └── models/                  # Trained ML models
│   │
│   ├── tasks/                       # Background tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── currency_update.py
│   │   ├── weather_update.py
│   │   ├── analytics_jobs.py
│   │   └── notification_jobs.py
│   │
│   └── utils/                       # Utility functions
│       ├── __init__.py
│       ├── validators.py
│       ├── helpers.py
│       ├── constants.py
│       └── enums.py
│
├── alembic/                         # Database migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_auth.py
│   │   ├── test_orders.py
│   │   └── test_pricing.py
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   └── test_external_services.py
│   └── load/
│       └── locustfile.py
│
├── scripts/                         # Utility scripts
│   ├── seed_database.py
│   ├── generate_test_data.py
│   └── backup_database.sh
│
├── docker/                          # Docker configurations
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── nginx.conf
│
├── docs/                            # Documentation
│   ├── API.md
│   ├── SETUP.md
│   ├── DEPLOYMENT.md
│   └── CONTRIBUTING.md
│
├── .env.example                     # Environment variables template
├── .env.dev
├── .env.prod
├── .gitignore
├── docker-compose.yml
├── docker-compose.dev.yml
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── pytest.ini
├── alembic.ini
├── README.md
├── ARCHITECTURE.md
└── LICENSE
```

## Directory Descriptions

### `/app`
Ana uygulama dizini. Tüm backend kodları burada bulunur.

### `/app/api`
API endpoint'leri versiyonlanmış şekilde organize edilmiştir. Her endpoint dosyası ilgili resource'un CRUD operasyonlarını içerir.

### `/app/models`
SQLAlchemy ORM modelleri. Veritabanı tablolarının Python class karşılıkları.

### `/app/schemas`
Pydantic schemas. API request/response validation ve serialization için kullanılır.

### `/app/services`
Business logic katmanı. Karmaşık iş mantığı, hesaplamalar ve orchestration burada yapılır.

### `/app/repositories`
Data access layer. Veritabanı operasyonlarını soyutlar ve repository pattern uygular.

### `/app/core`
Çekirdek utilities. Güvenlik, veritabanı bağlantısı, cache, exception handling gibi temel işlevler.

### `/app/integrations`
Harici servis entegrasyonları. Her servis için ayrı modül ve client implementasyonları.

### `/app/ai`
AI ve ML bileşenleri. Kurye atama, rota optimizasyonu, talep tahmini gibi ML modelleri.

### `/app/tasks`
Celery background tasks. Asenkron işlemler, scheduled jobs, queue işlemleri.

### `/alembic`
Veritabanı migration dosyaları. Alembic kullanılarak veritabanı şema değişiklikleri yönetilir.

### `/tests`
Test suite. Unit, integration ve load testleri için ayrı dizinler.

### `/scripts`
Yardımcı scriptler. Database seeding, test data generation, backup scriptleri.

### `/docker`
Docker konfigürasyonları. Dockerfile'lar ve nginx configuration.

### `/docs`
Proje dokümantasyonu. API docs, setup guides, deployment instructions.
