# Render Deployment Kontrol Listesi

## Durum: HAZIR

Sistem Render uzerinden deploy edilmeye tamamen hazir.

## Mevcut Konfigurasyon

### 1. Render Blueprint (`render.yaml`)
- Web servisi (FastAPI)
- PostgreSQL veritabani
- Redis cache
- Otomatik environment variable yonetimi

### 2. Build Script (`build.sh`)
- Dependency yukleme
- PDF kutuphaneleri (reportlab, matplotlib)
- Database migration

### 3. Dockerfile
- Python 3.11
- Production hazir konfigurasyon

## Deployment Adimlari

### Adim 1: GitHub Repository
```bash
# Repoyu GitHub'a push edin
git add .
git commit -m "Production ready: Full testing and optimization complete"
git push origin main
```

### Adim 2: Render Dashboard
1. [render.com](https://render.com) adresine gidin
2. "New" -> "Blueprint" secin
3. GitHub repository'nizi baglayin
4. `render.yaml` otomatik algilanacak

### Adim 3: Environment Variables
Asagidaki API anahtarlarini Render dashboard'dan ekleyin:
- `GOOGLE_MAPS_API_KEY`
- `OPENWEATHER_API_KEY`
- `EXCHANGE_RATE_API_KEY`

### Adim 4: Deploy
"Apply" butonuna tiklayin. Render otomatik olarak:
- PostgreSQL database olusturur
- Redis instance baslatir
- Backend'i deploy eder
- Database migration'lari calistirir

## Deployment Sonrasi Kontrol

### Health Check
```bash
curl https://your-app.onrender.com/health
```

### API Documentation
```
https://your-app.onrender.com/docs
```

### Test Endpoints
```bash
# Root endpoint
curl https://your-app.onrender.com/

# Analytics
curl https://your-app.onrender.com/api/analytics/dashboard
```

## Onemli Notlar

1. **Ucretsiz Plan Sinirlari**
   - 15 dakika inaktiviteden sonra sleep modu
   - Aylik 750 saat calisma
   - Shared resources

2. **Production Onerileri**
   - Paid plan'a gecis onerilir (7$/ay)
   - Database backup'lari etkinlestirin
   - Monitoring ekleyin

3. **CORS Ayarlari**
   - Frontend URL'ini `CORS_ORIGINS` environment variable'ina ekleyin

## Sorun Giderme

### Build Hatasi
- `build.sh` dosyasinin calistirilabilir oldugunu kontrol edin
- Dependency cakismalarini inceleyin

### Database Baglanti Hatasi
- `DATABASE_URL` environment variable'inin dogru ayarlandigini dogrulayin
- Migration'larin calistigini kontrol edin

### Redis Baglanti Hatasi
- Redis service'inin aktif oldugunu dogrulayin
- `REDIS_URL` environment variable'ini kontrol edin

## Destek

Deployment sirasinda sorun yasarsaniz:
1. Render logs'lari inceleyin
2. Environment variables'i kontrol edin
3. Build script'i gozden gecirin
