# LOOP LOJİSTİK - TEKNİK MİMARİ DÖKÜMANASYONU

## Proje Özeti

LOOP, modern lojistik yönetimi için tasarlanmış kapsamlı bir dijital platformdur. Gerçek zamanlı GPS takibi, AI destekli kurye atamaları, çoklu API entegrasyonları ve gelişmiş raporlama özellikleri sunar.

## Teknoloji Stack'i

### Backend Framework
- **FastAPI**: Modern, async Python web framework
- **Python 3.11+**: Yüksek performanslı runtime
- **Pydantic**: Veri doğrulama ve serileştirme
- **SQLAlchemy**: ORM ve veritabanı yönetimi

### Veritabanı Sistemi
- **PostgreSQL 15+**: Ana veritabanı
- **PostGIS**: Coğrafi veri işleme ve spatial sorgular
- **Redis**: Önbellekleme ve session yönetimi
- **Alembic**: Veritabanı migrasyonları

### API Entegrasyonları
- **Mapbox API**: Harita, rota planlama ve GPS takibi
- **OpenWeatherMap API**: Hava durumu verisi
- **CurrencyAPI**: Gerçek zamanlı döviz kurları
- **n8n**: AI karar motoru ve otomasyon

### Altyapı ve Deployment
- **Docker**: Konteynerizasyon
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy ve load balancer
- **Uvicorn**: ASGI server

## Sistem Mimarisi

### Mikroservis Yapısı
```
LOOP Lojistik Platformu
├── API Gateway (Nginx)
├── Authentication Service
├── GPS Tracking Service
├── Route Optimization Service
├── Courier Management Service
├── Order Management Service
├── Notification Service
├── Weather Integration Service
├── Currency Service
└── AI Decision Engine (n8n)
```

### Veri Akışı
1. **Client Request** → API Gateway
2. **Authentication** → Auth Service
3. **Business Logic** → İlgili mikroservis
4. **Data Processing** → PostgreSQL/Redis
5. **External APIs** → Harita, hava durumu, döviz
6. **AI Decisions** → n8n otomasyonu

## API Entegrasyon Detayları

### 1. Mapbox API Entegrasyonu
```python
# Route Optimization API
POST https://api.mapbox.com/directions/v5/mapbox/driving/{coordinates}
Headers: {
    "Authorization": "Bearer {MAPBOX_ACCESS_TOKEN}"
}

# Matrix API - Çoklu lokasyon mesafe hesaplama
POST https://api.mapbox.com/directions-matrix/v1/mapbox/driving/{coordinates}

# Geocoding API - Adres koordinata çevirme
GET https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json
```

**Kullanım Alanları:**
- Rota optimizasyonu
- Gerçek zamanlı GPS takibi
- Mesafe ve süre hesaplamaları
- Adres doğrulama

### 2. OpenWeatherMap API Entegrasyonu
```python
# Current Weather Data
GET https://api.openweathermap.org/data/2.5/weather
Params: {
    "lat": {latitude},
    "lon": {longitude},
    "appid": {API_KEY}
}

# Weather Forecast
GET https://api.openweathermap.org/data/2.5/forecast
```

**Kullanım Alanları:**
- Teslimat rotalarında hava durumu analizi
- Gecikme tahminleri
- Kurye güvenliği optimizasyonu

### 3. CurrencyAPI Entegrasyonu
```python
# Real-time Exchange Rates
GET https://currencyapi.net/api/v1/rates
Params: {
    "key": {API_KEY},
    "base": "USD",
    "output": "JSON"
}

# Currency Conversion
GET https://currencyapi.net/api/v1/convert
```

**Kullanım Alanları:**
- Çok para birimli fiyatlandırma
- Uluslararası gönderiler
- Maliyet analizleri

### 4. n8n AI Karar Motoru
```json
{
  "workflow": {
    "name": "Courier Assignment AI",
    "nodes": [
      {
        "id": "1",
        "type": "webhook",
        "name": "Order Trigger",
        "parameters": {
          "path": "order-assignment"
        }
      },
      {
        "id": "2", 
        "type": "function",
        "name": "ML Prediction",
        "parameters": {
          "model": "courier-assignment-v2"
        }
      }
    ]
  }
}
```

**AI Karar Süreçleri:**
- En uygun kurye ataması
- Rota optimizasyonu
- Tahmini varış süreleri
- Gecikme analizi

## Veritabanı Tasarımı

### Ana Tablolar

#### 1. Couriers (Kuryeler)
```sql
CREATE TABLE couriers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    status courier_status NOT NULL DEFAULT 'available',
    current_location GEOGRAPHY(POINT, 4326),
    vehicle_type vehicle_type NOT NULL,
    rating DECIMAL(3,2) DEFAULT 5.0,
    total_deliveries INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. Orders (Siparişler)
```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    pickup_address TEXT NOT NULL,
    pickup_location GEOGRAPHY(POINT, 4326) NOT NULL,
    delivery_address TEXT NOT NULL,
    delivery_location GEOGRAPHY(POINT, 4326) NOT NULL,
    status order_status NOT NULL DEFAULT 'pending',
    assigned_courier_id UUID REFERENCES couriers(id),
    priority priority_level DEFAULT 'normal',
    estimated_distance FLOAT,
    estimated_duration INTEGER,
    actual_distance FLOAT,
    actual_duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. Routes (Rotalar)
```sql
CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id),
    courier_id UUID REFERENCES couriers(id),
    optimized_path GEOGRAPHY(LINESTRING, 4326),
    waypoints GEOGRAPHY[] DEFAULT ARRAY[]::GEOGRAPHY[],
    traffic_conditions JSONB,
    weather_conditions JSONB,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexler ve Optimizasyon
```sql
-- Spatial indexler
CREATE INDEX idx_couriers_location ON couriers USING GIST(current_location);
CREATE INDEX idx_orders_pickup ON orders USING GIST(pickup_location);
CREATE INDEX idx_orders_delivery ON orders USING GIST(delivery_location);

-- Performans indexleri
CREATE INDEX idx_couriers_status ON couriers(status);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at);
```

## API Endpoint Tasarımı

### Authentication Endpoints
```
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

### Courier Management
```
GET    /api/v1/couriers              # Tüm kuryeler
GET    /api/v1/couriers/{id}         # Kurye detayı
POST   /api/v1/couriers              # Yeni kurye
PUT    /api/v1/couriers/{id}         # Kurye güncelle
DELETE /api/v1/couriers/{id}         # Kurye sil
GET    /api/v1/couriers/nearby       # Yakındaki kuryeler
```

### Order Management
```
GET    /api/v1/orders
GET    /api/v1/orders/{id}
POST   /api/v1/orders
PUT    /api/v1/orders/{id}
DELETE /api/v1/orders/{id}
POST   /api/v1/orders/{id}/assign    # Kurye ataması
POST   /api/v1/orders/{id}/complete  # Teslimat tamamlandı
```

### GPS Tracking
```
GET    /api/v1/tracking/{courier_id}     # Kurye konumu
POST   /api/v1/tracking/update           # Konum güncelleme
GET    /api/v1/tracking/route/{order_id} # Sipariş rotası
```

### Analytics & Reporting
```
GET    /api/v1/analytics/dashboard       # Dashboard verileri
GET    /api/v1/analytics/deliveries      # Teslimat istatistikleri
GET    /api/v1/analytics/performance     # Performans metrikleri
```

## Güvenlik ve Authentication

### JWT Token Sistemi
```python
# Token yapısı
{
  "sub": "user_id",
  "exp": 1234567890,
  "iat": 1234567890,
  "scope": "courier|admin|customer"
}
```

### Rate Limiting
- API başına rate limit: 1000 request/saat
- IP başına rate limit: 100 request/dakika
- Authentication endpoint'leri: 10 request/dakika

### Güvenlik Başlıkları
- HTTPS zorunlu
- CORS konfigürasyonu
- Input validation
- SQL injection koruma
- XSS koruma

## Performans Optimizasyonu

### Caching Stratejileri
```python
# Redis caching örnekleri
@cache(expire=300)  # 5 dakika
async def get_courier_location(courier_id: str):
    return await redis.get(f"courier:{courier_id}:location")

@cache(expire=3600)  # 1 saat
async def get_weather_data(location: tuple):
    return await redis.get(f"weather:{location[0]}:{location[1]}")
```

### Database Optimizasyonu
- Connection pooling
- Query optimization
- Index kullanımı
- Read replicas (yüksek trafik için)

### Async İşlemler
```python
# Async/await kullanımı
async def optimize_route(courier_id: str, orders: List[str]):
    # Paralel API çağrıları
    weather_task = get_weather_async()
    traffic_task = get_traffic_async()
    
    weather, traffic = await asyncio.gather(weather_task, traffic_task)
    
    return calculate_optimal_route(weather, traffic)
```

## Flutter Frontend Entegrasyonu

### API Client Yapısı
```dart
class LoopApiClient {
  final Dio _dio = Dio();
  
  Future<List<Courier>> getNearbyCouriers(LatLng location) async {
    final response = await _dio.get('/api/v1/couriers/nearby', 
      queryParameters: {
        'lat': location.latitude,
        'lng': location.longitude,
        'radius': 5000
      }
    );
    
    return (response.data as List)
      .map((json) => Courier.fromJson(json))
      .toList();
  }
}
```

### WebSocket Bağlantısı
```dart
// Gerçek zamanlı GPS takibi için
final channel = WebSocketChannel.connect(
  Uri.parse('wss://api.loop.com/ws/tracking'),
);

channel.stream.listen((message) {
  final data = jsonDecode(message);
  updateCourierLocation(data['courier_id'], data['location']);
});
```

## Deployment ve DevOps

### Docker Konfigürasyonu
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/loop_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgis/postgis:15-3.3
    environment:
      - POSTGRES_DB=loop_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=password
```

### Monitoring ve Logging
- **Prometheus**: Metrik toplama
- **Grafana**: Görselleştirme
- **ELK Stack**: Log yönetimi
- **Sentry**: Hata takibi

### CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/
      - name: Run linting
        run: flake8 src/
```

## Ölçeklenebilirlik Stratejisi

### Horizontal Scaling
- Load balancer (Nginx)
- Multiple API instances
- Database read replicas
- Redis cluster

### Vertical Partitioning
- Servis başına database
- Coğrafi bölge bazlı veri dağılımı
- CDN kullanımı

### Performance Hedefleri
- API response time: < 200ms
- Database query time: < 50ms
- Concurrent users: 10,000+
- Uptime: 99.9%

## Geliştirme Planı

### Faz 1: Core Backend (2-3 hafta)
- FastAPI altyapısı
- Temel veritabanı modelleri
- Authentication sistemi
- Temel CRUD operasyonları

### Faz 2: GPS ve Harita Entegrasyonu (2 hafta)
- Mapbox API entegrasyonu
- GPS tracking sistemi
- Rota optimizasyonu
- Spatial sorgular

### Faz 3: API Entegrasyonları (1-2 hafta)
- Hava durumu API
- Döviz kuru API
- External servis entegrasyonları

### Faz 4: AI ve Otomasyon (2-3 hafta)
- n8n kurulumu
- AI karar motorları
- Otomatik kurye atama
- Predictive analytics

### Faz 5: Testing ve Optimization (1-2 hafta)
- Unit testler
- Integration testler
- Performance testleri
- Güvenlik testleri

## Sonuç

LOOP lojistik platformu, modern mikroservis mimarisi ile ölçeklenebilir, güvenli ve yüksek performanslı bir çözüm sunar. FastAPI tabanlı backend, çeşitli API entegrasyonları ve AI destekli karar motorları ile lojistik operasyonların verimliliğini artırır.

Platform, Flutter frontend ile tam entegre çalışacak şekilde tasarlanmıştır ve gerçek zamanlı veri işleme, konum takibi ve akıllı otomasyon özellikleri ile rekabetçi bir lojistik çözümü sunar.