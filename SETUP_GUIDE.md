# LOOP Logistics - Setup Guide

## API Keys Rehberi

Bu projede kullanılan tüm API'leri nasıl edinebileceğiniz:

### 1. Google Maps API Key

**Adım 1:** [Google Cloud Console](https://console.cloud.google.com/) adresine gidin

**Adım 2:** Yeni bir proje oluşturun veya mevcut projeyi seçin

**Adım 3:** Sol menüden "APIs & Services" > "Library" seçin

**Adım 4:** Aşağıdaki API'leri aktifleştirin:
- Maps JavaScript API
- Geocoding API
- Directions API
- Distance Matrix API

**Adım 5:** "APIs & Services" > "Credentials" seçin

**Adım 6:** "Create Credentials" > "API Key" tıklayın

**Adım 7:** API anahtarını kopyalayın ve `.env` dosyasına ekleyin

**Maliyet:** Aylık $200 ücretsiz kullanım kredisi

---

### 2. OpenWeatherMap API Key

**Adım 1:** [OpenWeatherMap](https://openweathermap.org/api) adresine gidin

**Adım 2:** "Sign Up" butonuna tıklayın ve ücretsiz hesap oluşturun

**Adım 3:** Email doğrulaması yapın

**Adım 4:** "API Keys" sekmesine gidin

**Adım 5:** Default API key'i kopyalayın veya yeni bir tane oluşturun

**Adım 6:** `.env` dosyasına ekleyin

**Maliyet:** Ücretsiz plan - 60 istek/dakika, 1,000,000 istek/ay

**Not:** API key aktif olması 1-2 saat sürebilir

---

### 3. ExchangeRate-API Key

**Adım 1:** [ExchangeRate-API](https://www.exchangerate-api.com/) adresine gidin

**Adım 2:** "Get Free Key" butonuna tıklayın

**Adım 3:** Email adresinizi girin ve hesap oluşturun

**Adım 4:** Email'inizden doğrulama yapın

**Adım 5:** Dashboard'dan API key'inizi kopyalayın

**Adım 6:** `.env` dosyasına ekleyin

**Maliyet:** Ücretsiz plan - 1,500 istek/ay

---

## Kurulum Adımları

### 1. Gereksinimler

- Python 3.9 veya üzeri
- pip (Python package manager)
- Git

### 2. Projeyi İndirin

```bash
cd loop-logistics
```

### 3. Virtual Environment Oluşturun

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 5. Environment Variables Ayarlayın

`.env.example` dosyasını `.env` olarak kopyalayın:

```bash
cp .env.example .env
```

`.env` dosyasını düzenleyin ve API anahtarlarınızı ekleyin:

```env
# Supabase (Zaten yapılandırılmış)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key

# Google Maps API (Yukarıdan aldığınız key)
GOOGLE_MAPS_API_KEY=AIzaSy...

# Weather API (Yukarıdan aldığınız key)
OPENWEATHER_API_KEY=abc123...

# Currency API (Yukarıdan aldığınız key)
EXCHANGE_RATE_API_KEY=xyz789...

# n8n (Opsiyonel)
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook

# Redis (Opsiyonel - local kullanım için)
REDIS_URL=redis://localhost:6379
```

### 6. Database'i Kontrol Edin

Supabase database zaten oluşturuldu ve aşağıdaki tablolar hazır:
- `couriers` - Kurye bilgileri
- `courier_locations` - Anlık konum verileri
- `orders` - Teslimat siparişleri
- `assignment_history` - Atama geçmişi
- `location_history` - Konum geçmişi

### 7. Uygulamayı Çalıştırın

```bash
python run.py
```

Uygulama çalışmaya başladığında:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## Test Etme

### 1. Health Check Testi

```bash
curl http://localhost:8000/health
```

Beklenen yanıt:
```json
{"status": "healthy"}
```

### 2. Geocoding Testi

```bash
curl -X POST http://localhost:8000/api/maps/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "Taksim Square, Istanbul"}'
```

### 3. Weather Testi

```bash
curl -X POST http://localhost:8000/api/weather/current \
  -H "Content-Type: application/json" \
  -d '{"latitude": 41.0082, "longitude": 28.9784}'
```

### 4. Currency Testi

```bash
curl http://localhost:8000/api/currency/popular
```

---

## Sorun Giderme

### Problem: "Module not found" hatası

**Çözüm:**
```bash
pip install -r requirements.txt
```

### Problem: Google Maps API hatası

**Çözüm:**
- API key'in doğru kopyalandığını kontrol edin
- Google Cloud Console'da gerekli API'lerin aktif olduğunu doğrulayın
- Billing bilgilerinin eklendiğini kontrol edin

### Problem: OpenWeatherMap API "Invalid API key"

**Çözüm:**
- API key'in aktif olması için 1-2 saat bekleyin
- Email doğrulamasının yapıldığını kontrol edin

### Problem: Port 8000 zaten kullanımda

**Çözüm:**
`.env` dosyasında portu değiştirin:
```env
API_PORT=8001
```

### Problem: Supabase connection hatası

**Çözüm:**
- `.env` dosyasındaki Supabase URL ve Key'lerin doğru olduğunu kontrol edin
- İnternet bağlantınızı kontrol edin

---

## Üretim Ortamına Alma

### 1. Security Ayarları

- `API_RELOAD=false` yapın
- Güçlü API authentication ekleyin
- HTTPS kullanın
- Rate limiting ekleyin

### 2. Environment Variables

Üretim ortamında environment variables'ı güvenli şekilde saklayın:
- Heroku: Config Vars
- AWS: Parameter Store / Secrets Manager
- Docker: Secrets

### 3. Monitoring

Aşağıdaki servisleri kurun:
- Error tracking: Sentry
- Logging: CloudWatch / ELK
- Uptime monitoring: UptimeRobot
- Performance: New Relic

---

## Flutter Entegrasyonu

Flutter uygulamanızı bu API'ye bağlamak için:

1. `docs/FLUTTER_INTEGRATION.md` dosyasını okuyun
2. API base URL'ini Flutter config'inizde ayarlayın
3. Örnek servisleri kullanarak entegrasyon yapın

---

## n8n Workflow Kurulumu

Otomasyonları aktifleştirmek için:

1. `n8n/README.md` dosyasını okuyun
2. n8n'i kurun (Docker veya npm)
3. Workflow JSON dosyalarını import edin
4. Webhook URL'lerini ayarlayın

---

## Destek

Sorularınız için:
- API Dokumentasyonu: http://localhost:8000/docs
- Flutter Guide: `docs/FLUTTER_INTEGRATION.md`
- n8n Guide: `n8n/README.md`
- README: `README.md`

---

## Hızlı Başlangıç Özeti

```bash
# 1. Virtual environment
python -m venv venv
source venv/bin/activate  # veya Windows'ta: venv\Scripts\activate

# 2. Bağımlılıklar
pip install -r requirements.txt

# 3. Environment dosyası
cp .env.example .env
# .env dosyasını düzenle ve API keylerini ekle

# 4. Çalıştır
python run.py

# 5. Test et
curl http://localhost:8000/health
```

Başarılar!
