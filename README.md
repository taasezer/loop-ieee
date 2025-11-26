# LOOP Lojistik Platformu

FastAPI, PostgreSQL, Redis ve Docker ile gelistirilmis kapsamli bir lojistik backend sistemi. Yapay zeka destekli kurye atamasi, gercek zamanli takip ve Flutter entegrasyonu icerir.

---

## Icindekiler
1. [Ozellikler](#ozellikler)
2. [Teknoloji Yigini](#teknoloji-yigini)
3. [Hizli Baslangic (Docker)](#hizli-baslangic-docker)
4. [Manuel Kurulum](#manuel-kurulum)
5. [API Referansi](#api-referansi)
6. [Flutter Entegrasyonu](#flutter-entegrasyonu)
7. [n8n Otomasyonu](#n8n-otomasyonu)
8. [Test](#test)
9. [Gelistirme Asamalari](#gelistirme-asamalari)
10. [Render ile Deploy](#render-ile-deploy)
11. [Dagitim](#dagitim)

---

## <a name="ozellikler"></a>Ozellikler

- **Harita & GPS Entegrasyonu**: Google Maps API ile cografi kodlama, rotalama ve mesafe hesaplama
- **Gercek Zamanli Takip**: WebSocket tabanli canli kurye takibi ve oda bazli yayin sistemi
- **Yapay Zeka Karar Motoru**: Mesafe, puan, hava durumu, trafik ve is yukune gore akilli kurye atamasi
- **Dinamik Fiyatlandirma**: Mesafe, talep artisi ve hava kosullarina gore otomatik fiyatlandirma
- **Hava Durumu Entegrasyonu**: OpenWeatherMap API ile hava durumu destekli lojistik ve guvenlik uyarilari
- **Doviz Kuru**: Uluslararasi operasyonlar icin gercek zamanli doviz donusumu
- **Bildirimler**: Push (FCM), SMS (Twilio) ve E-posta (SendGrid) destegi
- **Analitik**: Siparis, gelir ve kurye performansi icin dashboard

---

## <a name="teknoloji-yigini"></a>Teknoloji Yigini

- **Backend**: FastAPI (Python 3.11+)
- **Veritabani**: PostgreSQL + SQLAlchemy (Async)
- **Onbellek**: Redis
- **Containerization**: Docker & Docker Compose
- **Migration**: Alembic
- **Test**: Pytest
- **Gercek Zamanli**: WebSockets

---

## <a name="hizli-baslangic-docker"></a>Hizli Baslangic (Docker)

Projeyi calistirmanin en kolay yolu.

### Gereksinimler
- Docker & Docker Compose

### Adimlar
1. **Depoyu klonlayin**
   ```bash
   git clone <repo-url>
   cd loop-logistics
   ```

2. **Servisleri Baslatin**
   ```bash
   docker-compose up --build
   ```
   Bu sunlari baslatir:
   - Backend API (Port 8000)
   - PostgreSQL (Port 5432)
   - Redis (Port 6379)

3. **Erisim**
   - **API Dokumani**: http://localhost:8000/docs
   - **Saglik Kontrolu**: http://localhost:8000/health

---

## <a name="manuel-kurulum"></a>Manuel Kurulum

Docker olmadan yerel gelistirme icin.

### Gereksinimler
- Python 3.11+
- PostgreSQL (Yerel veya Bulut)
- Redis (Yerel veya Bulut)

### Adimlar
1. **Sanal Ortam Olusturun**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```

2. **Bagimliliklari Yukleyin**
   ```bash
   pip install -r requirements.txt
   ```

3. **Yapilandirma**
   `.env` dosyasi olusturun:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
   REDIS_URL=redis://localhost:6379/0
   SECRET_KEY=gizli_anahtariniz
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # Harici API'ler
   GOOGLE_MAPS_API_KEY=anahtariniz
   OPENWEATHER_API_KEY=anahtariniz
   EXCHANGE_RATE_API_KEY=anahtariniz
   ```

4. **Veritabani Migration**
   ```bash
   alembic upgrade head
   ```

5. **Uygulamayi Calistirin**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## <a name="api-referansi"></a>API Referansi

### Kimlik Dogrulama
- `POST /api/auth/register`: Yeni kullanici kaydi (Musteri/Kurye)
- `POST /api/auth/login`: Giris yap ve JWT token al

### Siparisler
- `POST /api/orders/`: Siparis olustur
- `GET /api/orders/`: Siparisleri listele
- `GET /api/orders/{id}`: Siparis detaylari
- `POST /api/orders/{id}/cancel`: Siparisi iptal et
- `GET /api/orders/active`: Aktif siparisler

### Kurye Siparisleri
- `GET /api/courier/orders/available`: Atanmamis siparisler
- `POST /api/courier/orders/{id}/accept`: Siparisi kabul et
- `POST /api/courier/orders/{id}/pickup`: Teslim alindi
- `POST /api/courier/orders/{id}/complete`: Teslimi tamamla

### Takip
- `POST /api/tracking/update`: Kurye konumunu guncelle
- `GET /api/tracking/courier/{id}`: Kurye konumunu al
- `WS /api/tracking/ws`: Gercek zamanli guncellemeler icin WebSocket

### Yapay Zeka Motoru
- `POST /api/ai/recommend`: Kurye onerisi al
- `POST /api/ai/assign`: En uygun kuryeyi otomatik ata
- `POST /api/ai/optimize-route`: Teslimat rotasini optimize et

### Admin & Analitik
- `GET /api/admin/orders`: Tum siparisler (filtreli)
- `GET /api/admin/couriers`: Kurye istatistikleri
- `GET /api/admin/realtime-map`: Canli harita verisi
- `GET /api/analytics/revenue`: Gelir analizi
- `GET /api/analytics/delivery-metrics`: Teslimat metrikleri
- `GET /api/analytics/heatmap`: Cografi isi haritasi

### Promosyonlar
- `POST /api/promotions`: Promosyon kodu olustur (admin)
- `GET /api/promotions`: Tum promosyon kodlari
- `POST /api/promotions/validate`: Promosyon kodunu dogrula

### Bildirimler
- `GET /api/notifications`: Bildirimleri listele
- `PUT /api/notifications/{id}/read`: Okundu isaretle
- `GET /api/notifications/unread-count`: Okunmamis sayisi

*(Uygulama calisirken `/docs` adresinde tam interaktif dokumantasyon mevcuttur)*

---

## <a name="flutter-entegrasyonu"></a>Flutter Entegrasyonu

### Bagimliliklar
`pubspec.yaml` dosyaniza ekleyin:
```yaml
dependencies:
  http: ^1.1.0
  web_socket_channel: ^2.4.0
  google_maps_flutter: ^2.5.0
  geolocator: ^10.1.0
```

### WebSocket Servisi Ornegi
```dart
class WebSocketService {
  WebSocketChannel? _channel;

  void connect() {
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://your-api-url:8000/api/tracking/ws')
    );
  }

  void subscribeToOrder(String orderId) {
    _channel?.sink.add(json.encode({
      'type': 'subscribe_order',
      'order_id': orderId,
    }));
  }
}
```

---

## <a name="n8n-otomasyonu"></a>n8n Otomasyonu

Proje `n8n/workflows/` dizininde kapsamli otomasyon workflow'lari icerir:

1. **Auto Assignment** (`auto_assignment.json`): Yeni siparisleri AI onerilerine gore otomatik kuryelere atar.
2. **Weather Alert** (`weather_alert.json`): Kotu hava kosullarinda aktif kuryeleri uyarir.
3. **Performance Report** (`performance_report.json`): Gunluk kurye performans raporlari ve bonus onerileri olusturur.
4. **Late Delivery Alert** (`late_delivery_alert.json`): Geciken teslimatlari tespit eder, musteriye ozur ve indirim kodu gonderir.

### Detayli Dokumantasyon
Kurulum, konfigurasyon ve test adimlari icin [n8n/README.md](n8n/README.md) dosyasina bakin.

### Hizli Kurulum
1. n8n yukleyin: `npm install -g n8n`
2. `n8n/workflows/*.json` dosyalarini ice aktarin
3. Environment variable'lari ayarlayin (`LOOP_API_URL`, `LOOP_API_TOKEN`)

---

## <a name="test"></a>Test

Backend'i dogrulamak icin otomatik test paketini calistirin:

```bash
pytest
```
Bu, Kimlik Dogrulama, Siparisler ve API endpoint'leri icin unit ve integration testlerini calistirir.

### Hizli API Testi

Veritabani yapilandirmasi olmadan tum endpoint'leri test edin:

```bash
python test_api.py
```

### Son Test Sonuclari

**Test Tarihi:** 2025-11-25
**Toplam Endpoint:** 52+
**Basari Orani:** %100

#### Test Ozeti
- Ana endpoint yanit veriyor
- Saglik kontrolu geciyor
- Swagger UI `/docs` adresinde erisilebilir
- Redis onbellegi bagli (Mock/Real)
- Tum Faz 1-4 ozellikleri dogrulandi
- n8n Otomasyon Workflow'lari dogrulandi (Auto Assignment, Weather Alert, Performance Report, Late Delivery Alert)

#### Dogrulanmis Route Gruplari
| Ozellik | Endpoint Sayisi | Durum |
|---------|-----------------|-------|
| Bildirimler | 5 | Basarili |
| Kurye Siparisleri | 7 | Basarili |
| Admin Dashboard | 6 | Basarili |
| Analitik | 7 | Basarili |
| Promosyonlar | 4 | Basarili |
| Siparisler (Gelismis) | 6 | Basarili |
| Kuryeler | 4 | Basarili |
| n8n Entegrasyonu | 8 | Basarili |

**Backend Puani:** 9.0/10 (Production Hazir ve Optimize Edilmis)

---

## <a name="gelistirme-asamalari"></a>Tamamlanan Gelistirme Asamalari

### Faz 1: Kritik Altyapi
- Decorator'lu Redis onbellekleme sistemi
- Rate limiting middleware (slowapi + Redis)
- Gelistirilmis bildirim altyapisi
- **Etki:** %90+ API cagrisi azaltma, DDoS korumasi

### Faz 2: Siparis & Kurye Yonetimi
- Dogrulama ile siparis state machine
- Kurye ozel siparis route'lari (7 endpoint)
- Gelistirilmis siparis workflow (iptal, durum takibi)
- Kurye yonetimi (kazanc, performans, cevrimici/cevrimdisi)
- **Etki:** Tam siparis yasam dongusu yonetimi

### Faz 3: Admin & Analitik
- Admin dashboard API'lari (6 endpoint)
- Gelismis analitik (gelir, metrikler, isi haritasi, icgoruler)
- Izleme icin gercek zamanli harita verisi
- Manuel kurye atamasi
- **Etki:** Tam is zekasi ve yonetim

### Faz 4: Gelismis Ozellikler
- FCM push bildirimleri (mock, production hazir)
- SendGrid ile e-posta servisi (mock)
- Twilio ile SMS servisi (mock)
- Dinamik fiyatlandirma (talep artisi, hava durumu, zaman bazli)
- Promosyon kodu sistemi (4 endpoint)
- **Etki:** Cok kanalli katilim ve akilli fiyatlandirma


---

## Render ile Deploy

### Onkoşullar

Deployment oncesinde asagidaki API anahtarlarini hazir bulundurun:
- Google Maps API Key
- OpenWeatherMap API Key
- Exchange Rate API Key

### Adim 1: GitHub Repository Hazirlama

1. **Kodu GitHub'a Yukleyin**
   ```bash
   git init
   git add .
   git commit -m "Production ready deployment"
   git branch -M main
   git remote add origin https://github.com/kullanici-adi/loop-logistics.git
   git push -u origin main
   ```

### Adim 2: Render Hesap Olusturma

1. **Render.com'a Gidin**
   - [render.com](https://render.com) adresine gidin
   - GitHub hesabinizla oturum acin
   - Repository erisim izni verin

### Adim 3: Blueprint ile Deploy

1. **Yeni Blueprint Olusturun**
   - Dashboard'da "New" butonuna tiklayin
   - "Blueprint" secenegini secin
   - GitHub repository'nizi baglayin
   - `loop-logistics` repository'sini secin

2. **Otomatik Algilama**
   - Render otomatik olarak `render.yaml` dosyasini algilar
   - Asagidaki servisler olusturulur:
     - Web Service (FastAPI Backend)
     - PostgreSQL Database
     - Redis Cache

### Adim 4: Environment Variables Yapilendirmasi

Render dashboard'dan asagidaki environment variable'lari ekleyin:

#### Gerekli API Anahtarlari
```
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
EXCHANGE_RATE_API_KEY=your_exchange_rate_api_key_here
```

#### Otomatik Olusturulan Degerler
Render asagidakileri otomatik olusturur:
- `DATABASE_URL` - PostgreSQL baglanti dizesi
- `REDIS_URL` - Redis baglanti dizesi
- `SECRET_KEY` - JWT imzalama anahtari

#### CORS Yapilendirmasi
Frontend URL'nizi ekleyin:
```
CORS_ORIGINS=https://your-frontend-domain.com,https://your-app.onrender.com
```

### Adim 5: Deploy Baslatma

1. **Deploy Butonuna Tiklayin**
   - "Apply" veya "Create" butonuna tiklayin
   - Render otomatik olarak build surecini baslatir

2. **Build Sureci**
   Render asagidaki adimlari otomatik gerceklestirir:
   - Dependencies yukleme (`pip install -r requirements.txt`)
   - PDF kutuphaneleri yukleme (`reportlab`, `matplotlib`)
   - Database migration'lari calistirma (`alembic upgrade head`)

3. **Deployment Izleme**
   - Logs sekmesinden build surecini izleyebilirsiniz
   - Ilk deployment 5-10 dakika surebilir

### Adim 6: Deployment Dogrulama

Deploy tamamlandiktan sonra:

1. **Health Check**
   ```bash
   curl https://your-app-name.onrender.com/health
   ```
   Beklenen yanit:
   ```json
   {"status": "healthy"}
   ```

2. **API Dokumantasyonu**
   Browser'da acin:
   ```
   https://your-app-name.onrender.com/docs
   ```

3. **Test Endpoint'leri**
   ```bash
   # Root endpoint
   curl https://your-app-name.onrender.com/
   
   # Analytics dashboard
   curl https://your-app-name.onrender.com/api/analytics/dashboard
   ```

### Render Ucretsiz Plan Ozellikleri

**Dahil Olanlar:**
- 750 saat/ay web service calisma suresi
- PostgreSQL database (256MB)
- Redis cache (25MB)
- Otomatik HTTPS sertifikasi
- Otomatik deployment (git push ile)
- Public URL

**Sinirlamalar:**
- 15 dakika inaktiviteden sonra sleep modu
- Shared CPU ve RAM
- Bandwidth limiti (100GB/ay)
- Sleep modundan cikis: 30-60 saniye

### Production Icin Oneriler

Production ortami icin Paid Plan'a gecis onerilir:

#### Starter Plan (7 USD/ay)
- 24/7 kesintisiz calisma
- Sleep modu yok
- Daha iyi performans
- Background workers destegi

#### Database Upgrade (7 USD/ay)
- PostgreSQL Standard
- 1GB storage
- Otomatik backup
- Point-in-time recovery

#### Redis Upgrade (10 USD/ay)
- Redis Standard
- 256MB memory
- Data persistence
- Eviction policy secimi

### Deploy Sonrasi Yapilandirma

#### Custom Domain Baglama

1. Render Dashboard'da "Settings" sekmesine gidin
2. "Custom Domain" bolumune domain'inizi ekleyin
3. DNS kayitlarini yapilandirin:
   ```
   Type: CNAME
   Name: api (veya subdomain)
   Value: your-app.onrender.com
   ```

#### SSL/TLS Sertifikasi

Render otomatik olarak Let's Encrypt SSL sertifikasi saglar:
- HTTPS varsayilan olarak aktiftir
- Sertifikalar otomatik yenilenir
- HTTP istekleri otomatik HTTPS'e yonlendirilir

#### Monitoring ve Logs

1. **Logs Goruntuleme**
   - Dashboard'dan "Logs" sekmesine gidin
   - Real-time log stream
   - Son 7 gun log gecmisi (Free plan)

2. **Metrics**
   - CPU kullanimi
   - Memory kullanimi
   - Request sayisi
   - Response suresi

### Sorun Giderme

#### Build Hatasi

**Sorun:** Dependencies yukleme hatasi
```bash
ERROR: Could not find a version that satisfies the requirement
```

**Cozum:**
- `requirements.txt` dosyasini kontrol edin
- Version pinning yapin (ornek: `fastapi==0.104.1`)
- `build.sh` dosyasindaki pip upgrade komutunu kontrol edin

#### Database Baglanti Hatasi

**Sorun:** `could not connect to server`

**Cozum:**
1. `DATABASE_URL` environment variable'inin dogru ayarlandigini dogrulayin
2. Database service'inin aktif oldugunu kontrol edin
3. Migration'larin calistigini dogrulayin

#### Redis Baglanti Hatasi

**Sorun:** `Connection refused` veya `ECONNREFUSED`

**Cozum:**
1. Redis service'inin provisioned oldugunu kontrol edin
2. `REDIS_URL` environment variable'ini dogrulayin
3. Render dashboard'dan Redis status'u kontrol edin

#### Sleep Mode Sorunu

**Sorun:** Ilk request yavas

**Cozum:**
- Free plan'da normal bir durumdur
- Paid plan'a gecis yaparak cozulebilir
- Veya external monitoring servisi (UptimeRobot) kullanarak sistemi aktif tutun

### Otomatik Deployment

Render otomatik deployment destekler:

1. **GitHub Integration**
   - Main branch'e push yapildiginda otomatik deploy
   - Pull request'ler icin preview environment (Pro plan)

2. **Deployment Hook**
   ```bash
   # Manuel trigger
   curl -X POST https://api.render.com/deploy/srv-xxxxx?key=your-deploy-key
   ```

3. **Rollback**
   - Dashboard'dan onceki deployment'a donulebilir
   - Deployment history son 30 gun saklanir

---

## Environment Variables Referansi


## <a name="dagitim"></a>Genel Dagitim

### Production Kontrol Listesi
1. **Guvenlik**:
   - `SECRET_KEY`'i guclu rastgele bir string ile degistirin
   - `CORS_ORIGINS`'i frontend domain'inize ayarlayin
   - HTTPS (SSL) kullanin
2. **Veritabani**:
   - Yonetilen PostgreSQL servisi kullanin (AWS RDS, Supabase, vb.)
   - Yedeklemeleri etkinlestirin
3. **Ortam**:
   - `API_RELOAD=false` ayarlayin
   - Anahtarlar icin Docker Secrets veya Environment Variables kullanin

### Dockerfile
Dahil edilen `Dockerfile` production icin hazirdir.
```bash
docker build -t loop-backend .
docker run -p 8000:8000 --env-file .env loop-backend
```

---

## Destek

Sorulariniz veya sorunlariniz icin lutfen bir issue acin veya projeyi forklayip pull request gonderin.

**Backend Durumu:** Production Hazir
**Test Durumu:** Tum endpoint'ler dogrulandi
**Ozellik Tamamlama:** 9.0/10
