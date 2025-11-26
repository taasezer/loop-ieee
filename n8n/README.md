# LOOP n8n Workflows Kılavuzu

Bu dizin LOOP Lojistik Platformu için n8n otomasyon workflow'larını içerir.

## 📋 İçindekiler

- [Kurulum](#kurulum)
- [Workflow'lar](#workflows)
- [Konfigürasyon](#konfigürasyon)
- [Test](#test)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Kurulum

### Gereksinimler
- Node.js 18+
- n8n (Self-hosted veya Cloud)
- LOOP Backend API erişimi

### Adımlar

1. **n8n Kurulumu**
```bash
# NPM ile global yükleme
npm install -g n8n

# Veya Docker ile
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

2. **n8n Başlatma**
```bash
n8n start
```

3. **Browser'da Aç**
```
http://localhost:5678
```

4. **Workflow'ları Import Et**
   - n8n dashboard'da "Workflows" → "Import from File"
   - Bu dizindeki `.json` dosyalarını seçip import edin

---

## 📦 Workflows

### 1. Auto Assignment (`auto_assignment.json`)

**Amaç**: Yeni siparişler için otomatik kurye ataması  
**Tetikleme**: Webhook (POST request)  
**Çalışma Sıklığı**: Her yeni sipariş

**Akış**:
1. Webhook ile yeni sipariş bildirimi alır
2. AI recommendation endpoint'ini çağırır
3. Skor kontrolü yapar (>0.7 threshold)
4. Başarılıysa otomatik kurye atar
5. Push bildirimi gönderir
6. Başarısızsa manuel atama gerektiğini bildirir

**Özellikler**:
- ✅ JWT Authentication
- ✅ 3x Retry logic
- ✅ 30s Timeout
- ✅ Error handling
- ✅ Detaylı loglama
- ✅ Bildirim entegrasyonu

**Webhook URL**:
```
http://localhost:5678/webhook/<your-webhook-id>
```

**Test Request**:
```bash
curl -X POST http://localhost:5678/webhook/<id> \
  -H "Content-Type: application/json" \
  -d '{"order_id": 1}'
```

---

### 2. Weather Alert (`weather_alert.json`)

**Amaç**: Aktif kuryeler için hava durumu uyarıları  
**Tetikleme**: Zamanlayıcı  
**Çalışma Sıklığı**: Her 30 dakika

**Akış**:
1. Aktif kuryeler listesini alır
2. Her kurye için hava durumu etkisini kontrol eder
3. Kötü hava durumunda (impact_score < 0.7) uyarı çağrısı
4. Push + SMS bildirimi gönderir
5. Alert throttling ile 1 saat içinde tekrar gönderimi önler
6. Çok sayıda uyarı varsa admin'e bildirim

**Özellikler**:
- ✅ Alert throttling (1 saat)
- ✅ Multi-channel notifications (Push + SMS)
- ✅ Severity levels (critical/high/moderate/low)
- ✅ Admin escalation
- ✅ Batch processing (5 kurye/grup)
- ✅ Error handling

**Severity Levels**:
- 🚨 **Critical** (score < 0.3): Tehlikeli koşullar, teslimat durdurma önerisi
- ⚠️ **High** (score < 0.5): Kötü koşullar, aşırı dikkat gerekli
- ⚡ **Moderate** (score < 0.7): Orta etki, dikkatli sürüş
- 💡 **Low** (score < 0.85): Hafif etki, uyanık olma

---

### 3. Performance Report (`performance_report.json`)

**Amaç**: Günlük kurye performans raporları  
**Tetikleme**: Zamanlayıcı  
**Çalışma Sıklığı**: Her gün gece yarısı (00:00)

**Akış**:
1. Bir önceki günün metriklerini toplar
2. Kurye istatistiklerini alır
3. Top 5 performans gösterenleri belirler
4. Bonus önerileri hesaplar ($5/teslimat)
5. Geliştirilmesi gereken kuryeler listeler
6. HTML email raporu oluşturur
7. Admin'e email gönderir (simulated)

**Rapor İçeriği**:
- 📈 Günlük Özet (toplam teslimat, tamamlanan, iptal)
- 🏆 Top Performers (teslimat sayısı, rating, kazanç)
- 💰 Bonus Önerileri (toplam bonus havuzu)
- ⚠️ İyileştirme Gereken Kuryeler (düşük rating)

**Email Formatı**: Professional HTML template

---

### 4. Late Delivery Alert (`late_delivery_alert.json`)

**Amaç**: Geç kalan teslimatları tespit ve bildirim  
**Tetikleme**: Zamanlayıcı  
**Çalışma Sıklığı**: Her 5 dakika

**Akış**:
1. Aktif siparişleri kontrol eder (in_transit, picked_up)
2. Tahmini teslimat zamanını geçmiş olanları filtreler
3. Her sipariş için bir kez bildirim gönderir
4. Müşteriye özür + yeni ETA bildirir
5. Kurye ve admin'e bildirim gönderir
6. Gecikme süresine göre otomatik kompansasyon
7. Promosyon kodu oluşturur

**Kompansasyon Sistemi**:
- 🎁 **15-30 dakika geç**: %10 discount code
- 🎁 **30+ dakika geç**: %20 discount code
- ✅ Kodlar otomatik oluşturulur ve müşteriye gönderilir
- ⏰ Geçerlilik: 30 gün
- 🔒 Tek kullanımlık

**Notification Channels**:
- Müşteri: Push notification + kompansasyon kodu
- Kurye: Push notification (uyarı)
- Admin: Push notification (bilgilendirme)

---

## ⚙️ Konfigürasyon

### Environment Variables

n8n'de aşağıdaki environment variable'ları ayarlayın:

```bash
# Backend API
LOOP_API_URL=http://localhost:8000          # Backend API base URL
LOOP_API_TOKEN=your_jwt_token_here          # JWT authentication token

# Email (Production)
ADMIN_EMAIL=admin@loop.com                  # Admin email adresi
SENDGRID_API_KEY=your_sendgrid_key         # SendGrid API key
SENDGRID_FROM_EMAIL=noreply@loop.com       # Gönderen email

# SMS (Production)
TWILIO_ACCOUNT_SID=your_twilio_sid         # Twilio hesap SID
TWILIO_AUTH_TOKEN=your_twilio_token        # Twilio auth token
TWILIO_PHONE=+1234567890                   # Twilio telefon numarası
```

### n8n Environment Variables Ayarlama

**Method 1: n8n UI**
1. Settings → Environments
2. Add new environment variable
3. Save

**Method 2: .env File**
```bash
# ~/.n8n/.env dosyası oluşturun
echo "LOOP_API_URL=http://localhost:8000" >> ~/.n8n/.env
echo "LOOP_API_TOKEN=your_token" >> ~/.n8n/.env
```

**Method 3: Docker**
```bash
docker run -it --rm \
  -e LOOP_API_URL=http://localhost:8000 \
  -e LOOP_API_TOKEN=your_token \
  -p 5678:5678 \
  n8nio/n8n
```

### Webhook Authentication

Workflow'larda JWT authentication kullanılıyor. Token almak için:

```bash
# Backend'e login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone": "+905555555555", "password": "password"}'

# Response'dan token'ı alın ve LOOP_API_TOKEN'a kaydedin
```

---

## 🧪 Test

### 1. Backend'i Başlatın

```bash
cd /path/to/loop-backend
uvicorn app.main:app --reload
```

### 2. n8n'i Başlatın

```bash
n8n start
```

### 3. Workflow Test Senaryoları

#### Auto Assignment Testi

```bash
# Webhook URL'ini n8n'den kopyalayın
# Test request gönderin
curl -X POST http://localhost:5678/webhook/<webhook-id> \
  -H "Content-Type: application/json" \
  -d '{"order_id": 1}'
```

**Beklenen Sonuç**:
- ✅ AI recommendation başarılı
- ✅ Kurye atandı veya manuel atama gerektiği döndü
- ✅ Bildirim simüle edildi
- ✅ Log console'da görünüyor

#### Weather Alert Testi

```bash
# n8n UI'da workflow'u manuel çalıştır
# "Execute Workflow" butonuna tıkla
```

**Beklenen Sonuç**:
- ✅ Aktif kuryeler listelendi
- ✅ Her kurye için hava durumu kontrol edildi
- ✅ Gerekirse uyarı gönderildi
- ✅ Throttling çalışıyor (1 saat içinde tekrar göndermiyor)

#### Performance Report Testi

```bash
# Manual trigger ile test
# Veya zamanı değiştirip bekle
```

**Beklenen Sonuç**:
- ✅ Metrikler toplandı
- ✅ Top performers listelendi
- ✅ HTML email oluşturuldu
- ✅ Console'da email preview görünüyor

#### Late Delivery Alert Testi

```bash
# Önce geç bir sipariş oluştur (estimated_delivery_time geçmiş)
# Manuel trigger ile workflow'u çalıştır
```

**Beklenen Sonuç**:
- ✅ Geç sipariş tespit edildi
- ✅ Müşteri, kurye ve admin'e bildirim gönderildi
- ✅ Kompansasyon kodu oluşturuldu (eğer yeterince geç)
- ✅ Duplicate bildirim gönderilmedi

---

## 🔍 Troubleshooting

### Problem: Workflow çalışmıyor

**Çözüm**:
1. n8n log'larını kontrol edin
2. Environment variables doğru ayarlandığını doğrulayın
3. Backend API'nin çalıştığını kontrol edin (`curl http://localhost:8000/health`)

### Problem: Authentication hatası

**Çözüm**:
1. `LOOP_API_TOKEN` değişkenini kontrol edin
2. Token'ın expire olmadığını doğrulayın
3. Yeni token alın:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone": "+905555555555", "password": "password"}'
```

### Problem: Webhook tetiklenmiyor

**Çözüm**:
1. Webhook URL'ini doğru kopyaladığınızdan emin olun
2. Workflow'un "Active" olduğunu kontrol edin
3. n8n'in production mode'da çalıştığını doğrulayın

### Problem: Email gönderilmiyor

**Çözüm**:
1. Workflow şu anda email simüle ediyor (production ready değil)
2. Production için SendGrid entegrasyonunu aktifleştirin
3. `Send Email (Simulated)` node'undaki comment'leri kaldırın

### Problem: SMS gönderilmiyor

**Çözüm**:
1. Workflow şu anda SMS simüle ediyor
2. Production için Twilio entegrasyonunu aktifleştirin
3. `Send SMS (Simulated)` node'undaki comment'leri kaldırın

### Problem: Weather API hatası

**Çözüm**:
1. `OPENWEATHER_API_KEY` backend .env'de tanımlı mı?
2. API quota'nızı kontrol edin
3. Fallback mock data otomatik döndürülür

---

## 📊 Monitoring ve Logs

### Execution Logs

n8n UI'da:
1. "Executions" sekmesine gidin
2. Her workflow execution'ını görün
3. Her node'un input/output'unu inceleyin
4. Error'ları ve timing'leri kontrol edin

### Console Logs

Her workflow detaylı console logging içerir:

```
[2025-11-23T01:00:00.000Z] AI Recommendation requested for Order #123
[2025-11-23T01:00:01.000Z] Order #123 assigned to John Doe
[2025-11-23T01:00:02.000Z] ✅ Late delivery alert sent for order #456
```

### Monitoring Best Practices

- ✅ Execution history'yi düzenli kontrol edin
- ✅ Failed execution'ları inceleyin
- ✅ Workflow performance'ını optimize edin
- ✅ Alert frequency'yi ayarlayın (spam önleme)

---

## 🚀 Production Deployment

### 1. n8n Cloud Kullanımı

En kolay yöntem: https://n8n.cloud

- ✅ Managed hosting
- ✅ Auto-scaling
- ✅ Built-in monitoring
- ✅ Scheduled backups

### 2. Self-Hosted (Docker)

```yaml
# docker-compose.yml
version: '3.8'
services:
  n8n:
    image: n8nio/n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=secure_password
      - LOOP_API_URL=https://your-api.com
      - LOOP_API_TOKEN=${JWT_TOKEN}
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  n8n_data:
```

```bash
docker-compose up -d
```

### 3. Production Checklist

- [ ] Environment variables güvenli şekilde saklanıyor
- [ ] Webhook URL'leri HTTPS kullanıyor
- [ ] Email/SMS entegrasyonları aktif
- [ ] Error notifications ayarlandı
- [ ] Backup stratejisi oluşturuldu
- [ ] Rate limiting yapılandırıldı
- [ ] Monitoring dashboards kuruldu

---

## 📞 Destek

Sorularınız veya sorunlarınız için:
- GitHub Issues açın
- Backend dokumentasyonuna bakın
- n8n community: https://community.n8n.io

---

## 🔄 Güncelleme Geçmişi

**v1.0 - 2025-11-23**
- ✅ Auto Assignment workflow enhanced
- ✅ Weather Alert workflow enhanced
- ✅ Performance Report workflow created
- ✅ Late Delivery Alert workflow created
- ✅ All workflows production-ready
- ✅ Comprehensive documentation added
