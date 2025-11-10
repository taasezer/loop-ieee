# LOOP Lojistik Platformu 🚚

Modern, ölçeklenebilir ve AI destekli lojistik yönetim platformu. GPS takibi, rota optimizasyonu, kurye yönetimi ve gerçek zamanlı analizler sunar.

## Özellikler ✨

- 🗺️ **GPS Takibi** - Gerçek zamanlı kurye konum takibi
- 🧠 **AI Karar Motoru** - Akıllı kurye ataması ve rota optimizasyonu
- 🌤️ **Hava Durumu Entegrasyonu** - Teslimatları hava durumuna göre optimize etme
- 💱 **Çoklu Para Birimi** - Uluslararası gönderiler için otomatik döviz çevirimi
- 📱 **Flutter Uyumlu** - Mobil uygulama ile tam entegrasyon
- 🔒 **Güvenlik** - JWT authentication ve rate limiting
- 📊 **Analitik** - Detaylı raporlama ve performans metrikleri

## Teknoloji Stack'i 🛠️

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL + PostGIS** - Coğrafi veri yönetimi
- **Redis** - Önbellekleme ve session yönetimi
- **SQLAlchemy** - ORM ve veritabanı yönetimi
- **Pydantic** - Veri doğrulama ve serileştirme

### API Entegrasyonları
- **Mapbox API** - Harita, rota planlama ve GPS takibi
- **OpenWeatherMap API** - Hava durumu verisi
- **CurrencyAPI** - Gerçek zamanlı döviz kurları
- **n8n** - AI karar motoru ve otomasyon

### Altyapı
- **Docker & Docker Compose** - Konteynerizasyon
- **Nginx** - Reverse proxy ve load balancer
- **Prometheus + Grafana** - Monitoring ve metrik toplama

## Hızlı Başlangıç 🚀

### Gereksinimler
- Docker ve Docker Compose
- Python 3.11+ (geliştirme için)
- Mapbox API anahtarı

### Kurulum

1. **Projeyi klonlayın**
```bash
git clone https://github.com/your-org/loop-logistics.git
cd loop-logistics
```

2. **Çevre değişkenlerini ayarlayın**
```bash
cp .env.example .env
# .env dosyasını düzenleyin - API anahtarlarını girin
```

3. **Docker ile başlatın**
```bash
docker-compose up -d
```

4. **API'yi test edin**
```bash
curl http://localhost:8000/api-info
```

### Geliştirme Ortamı

1. **Sanal ortam oluşturun**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Bağımlılıkları yükleyin**
```bash
pip install -r requirements.txt
```

3. **Veritabanını başlatın**
```bash
alembic upgrade head
```

4. **Uygulamayı başlatın**
```bash
uvicorn app.main:app --reload
```

## API Dokümantasyonu 📚

### Ana Endpoint'ler

- `GET /` - API durumu
- `GET /health` - Sağlık kontrolü
- `GET /docs` - Swagger UI dokümantasyonu
- `GET /redoc` - ReDoc dokümantasyonu

### Kurye Yönetimi
- `GET /api/v1/couriers` - Tüm kuryeler
- `GET /api/v1/couriers/nearby` - Yakındaki kuryeler
- `POST /api/v1/couriers` - Yeni kurye oluştur
- `PATCH /api/v1/couriers/{id}/location` - Konum güncelle

### Sipariş Yönetimi
- `GET /api/v1/orders` - Tüm siparişler
- `POST /api/v1/orders` - Yeni sipariş oluştur
- `POST /api/v1/orders/{id}/assign` - Kurye ata
- `POST /api/v1/orders/{id}/complete` - Teslimat tamamla

### GPS Takibi
- `GET /api/v1/tracking/{courier_id}` - Kurye konumu
- `POST /api/v1/tracking/update` - Konum güncelle

## Flutter Entegrasyonu 📱

### API Client Örneği
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

## AI Karar Motoru 🤖

n8n ile entegre AI karar motoru:

### Özellikler
- **Kurye Ataması** - En uygun kuryeyi otomatik seç
- **Rota Optimizasyonu** - En kısa ve ekonomik rotayı bul
- **Gecikme Tahmini** - Hava durumu ve trafik analizi
- **Performans Analizi** - Kurye verimliliğini ölç

### Örnek Workflow
```json
{
  "name": "Courier Assignment AI",
  "nodes": [
    {
      "type": "webhook",
      "name": "Order Trigger",
      "parameters": {
        "path": "order-assignment"
      }
    },
    {
      "type": "function",
      "name": "ML Prediction", 
      "parameters": {
        "model": "courier-assignment-v2"
      }
    }
  ]
}
```

## Monitoring ve Logging 📊

### Prometheus Metrikleri
- API response times
- Database query performance
- Courier activity metrics
- Order completion rates

### Grafana Dashboard'ları
- Sistem sağlığı
- Kurye performansı
- Sipariş istatistikleri
- Kullanıcı aktivitesi

### Log Yapılandırması
```python
# Loguru ile yapılandırma
logger.add("logs/loop_{time}.log", 
          rotation="500 MB", 
          retention="10 days",
          level="INFO")
```

## Güvenlik 🔒

### JWT Authentication
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
- API başına: 1000 request/saat
- IP başına: 100 request/dakika
- Auth endpoint'leri: 10 request/dakika

### Güvenlik Başlıkları
- HTTPS zorunlu
- CORS koruması
- Input validation
- SQL injection koruma

## Ölçeklenebilirlik 🚀

### Horizontal Scaling
- Load balancer (Nginx)
- Multiple API instances
- Database read replicas
- Redis cluster

### Performance Hedefleri
- API response time: < 200ms
- Database query time: < 50ms
- Concurrent users: 10,000+
- Uptime: 99.9%

## Geliştirme Planı 📋

### Faz 1: Core Backend (2-3 hafta)
- [x] FastAPI altyapısı
- [x] Temel veritabanı modelleri
- [x] Authentication sistemi
- [ ] Temel CRUD operasyonları

### Faz 2: GPS ve Harita Entegrasyonu (2 hafta)
- [ ] Mapbox API entegrasyonu
- [ ] GPS tracking sistemi
- [ ] Rota optimizasyonu
- [ ] Spatial sorgular

### Faz 3: API Entegrasyonları (1-2 hafta)
- [ ] Hava durumu API
- [ ] Döviz kuru API
- [ ] External servis entegrasyonları

### Faz 4: AI ve Otomasyon (2-3 hafta)
- [ ] n8n kurulumu
- [ ] AI karar motorları
- [ ] Otomatik kurye atama
- [ ] Predictive analytics

### Faz 5: Testing ve Optimization (1-2 hafta)
- [ ] Unit testler
- [ ] Integration testler
- [ ] Performance testleri
- [ ] Güvenlik testleri

## Katkıda Bulunma 🤝

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Commit yapın (`git commit -m 'Add some AmazingFeature'`)
4. Branch'e push yapın (`git push origin feature/AmazingFeature`)
5. Pull Request oluşturun

## Lisans 📄

Bu proje MIT Lisansı ile lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## İletişim 📧

LOOP Development Team - dev@loop.com

Project Link: [https://github.com/your-org/loop-logistics](https://github.com/your-org/loop-logistics)

## Teşekkürler 🙏

- [FastAPI](https://fastapi.tiangolo.com/) - Harika web framework'ü için
- [Mapbox](https://www.mapbox.com/) - Harita ve rota planlama servisleri için
- [n8n](https://n8n.io/) - Açık kaynak otomasyon platformu için
- Tüm katkıda bulunanlar ve destekçiler için

---

**LOOP Lojistik Platformu** - Modern lojistik çözümleri için kapsamlı backend sistemi. 🚚✨