# LOOP Lojistik Platformu - Deployment Rehberi

## İçindekiler
1. [Giriş](#giriş)
2. [Gereksinimler](#gereksinimler)
3. [Hazırlık](#hazırlık)
4. [Kurulum](#kurulum)
5. [Yapılandırma](#yapılandırma)
6. [Deploy](#deploy)
7. [Monitoring](#monitoring)
8. [Sorun Giderme](#sorun-giderme)

## Giriş

Bu rehber, LOOP Lojistik Platformu'nun üretim ortamına deploy edilmesi için adım adım talimatlar içerir. Platform, modern mikroservis mimarisi ile tasarlanmıştır ve Docker konteynerleri kullanarak ölçeklenebilirlik sağlar.

## Gereksinimler

### Minimum Sistem Gereksinimleri
- **CPU**: 4 çekirdek (8 çekirdek önerilir)
- **RAM**: 8 GB (16 GB önerilir)
- **Disk**: 100 GB SSD
- **İşletim Sistemi**: Ubuntu 20.04 LTS veya üzeri

### Yazılım Gereksinimleri
- Docker 24.0+
- Docker Compose 2.0+
- Git
- OpenSSL (SSL sertifikaları için)

### Network Gereksinimleri
- Port 80 (HTTP)
- Port 443 (HTTPS)
- Port 8000 (API - internal)
- Port 5432 (PostgreSQL - internal)
- Port 6379 (Redis - internal)
- Port 5678 (n8n - internal)

## Hazırlık

### 1. Sunucu Hazırlığı

```bash
# Sistemi güncelle
sudo apt update && sudo apt upgrade -y

# Gerekli araçları kur
sudo apt install -y docker.io docker-compose git openssl curl wget

# Docker servisini başlat
sudo systemctl enable docker
sudo systemctl start docker

# Kullanıcıyı docker grubuna ekle
sudo usermod -aG docker $USER
```

### 2. SSL Sertifikası Hazırlığı

```bash
# SSL dizini oluştur
mkdir -p ~/loop/ssl

# Self-signed sertifika oluştur (test için)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ~/loop/ssl/loop.key \
  -out ~/loop/ssl/loop.crt \
  -subj "/C=TR/ST=Istanbul/L=Istanbul/O=LOOP/CN=loop.com"
```

## Kurulum

### 1. Projeyi Klonlayın

```bash
# Proje dizini oluştur
mkdir -p ~/loop
cd ~/loop

# Projeyi klonla
git clone https://github.com/your-org/loop-logistics.git .
```

### 2. Çevre Değişkenlerini Yapılandırın

```bash
# .env dosyasını oluştur
cp .env.example .env

# .env dosyasını düzenle
nano .env
```

### 3. Gerekli Ayarları Yapın

#### Veritabanı Şifresi
```bash
# Güçlü bir şifre oluştur
DB_PASSWORD=$(openssl rand -base64 32)
echo "DATABASE_URL=postgresql+asyncpg://loop_user:${DB_PASSWORD}@db:5432/loop_db" >> .env
```

#### Secret Key
```bash
# JWT secret key oluştur
SECRET_KEY=$(openssl rand -hex 32)
echo "SECRET_KEY=${SECRET_KEY}" >> .env
```

#### API Anahtarları
```bash
# Mapbox API anahtarı (zorunlu)
echo "MAPBOX_ACCESS_TOKEN=your-mapbox-token" >> .env

# Diğer API anahtarları (opsiyonel)
echo "OPENWEATHER_API_KEY=your-weather-key" >> .env
echo "CURRENCY_API_KEY=your-currency-key" >> .env
```

## Yapılandırma

### 1. Docker Compose Yapılandırması

```yaml
# docker-compose.yml dosyasını gözden geçirin
version: '3.8'

services:
  api:
    environment:
      - DATABASE_URL=postgresql+asyncpg://loop_user:${DB_PASSWORD}@db:5432/loop_db
      - SECRET_KEY=${SECRET_KEY}
      - MAPBOX_ACCESS_TOKEN=${MAPBOX_ACCESS_TOKEN}
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 2. Nginx Yapılandırması

```nginx
# nginx.conf
upstream api {
    server api:8000;
}

server {
    listen 80;
    server_name loop.com;
    
    location / {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Monitoring Yapılandırması

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'loop-api'
    static_configs:
      - targets: ['api:8000']
```

## Deploy

### 1. İlk Deploy

```bash
# Docker Compose ile servisleri başlat
docker-compose up -d

# Logları kontrol et
docker-compose logs -f api
```

### 2. Health Check

```bash
# API health check
curl http://localhost:8000/health

# Veritabanı bağlantısını kontrol et
docker-compose exec db pg_isready -U loop_user

# Redis bağlantısını kontrol et
docker-compose exec redis redis-cli ping
```

### 3. Veritabanını Başlat

```bash
# Alembic migrasyonlarını çalıştır
docker-compose exec api alembic upgrade head

# İlk kullanıcıyı oluştur (opsiyonel)
docker-compose exec api python -c "
from app.core.database import init_db
import asyncio
asyncio.run(init_db())
"
```

## Monitoring

### 1. Prometheus ve Grafana

```bash
# Monitoring servislerini başlat
docker-compose up -d prometheus grafana

# Grafana'ya bağlan
# URL: http://your-server-ip:3000
# Kullanıcı adı: admin
# Şifre: .env dosyasındaki GRAFANA_PASSWORD
```

### 2. Log Yönetimi

```bash
# Tüm servislerin loglarını görüntüle
docker-compose logs -f

# Spesifik servis logu
docker-compose logs -f api

# Logları dosyaya yaz
docker-compose logs --no-color > logs/loop-logs-$(date +%Y%m%d).log
```

### 3. Monitoring Dashboard'ları

#### Sistem Metrikleri
- CPU kullanımı
- Memory kullanımı
- Disk I/O
- Network trafiği

#### Uygulama Metrikleri
- API response times
- Database query performance
- Courier activity metrics
- Order completion rates

## Backup ve Recovery

### 1. Veritabanı Backup

```bash
# PostgreSQL backup
docker-compose exec db pg_dump -U loop_user loop_db > backup/loop-db-$(date +%Y%m%d).sql

# Otomatik backup için cron job
# crontab -e
0 2 * * * /path/to/backup-script.sh
```

### 2. Redis Backup

```bash
# Redis backup
docker-compose exec redis redis-cli BGSAVE

# Backup dosyasını kopyala
docker cp loop_redis:/data/dump.rdb backup/redis-dump-$(date +%Y%m%d).rdb
```

### 3. Recovery

```bash
# PostgreSQL restore
docker-compose exec -T db psql -U loop_user loop_db < backup/loop-db-latest.sql

# Redis restore
docker-compose down
docker volume rm loop_redis_data
docker-compose up -d redis
docker cp backup/redis-dump-latest.rdb loop_redis:/data/dump.rdb
docker-compose restart redis
```

## Güncelleme (Update)

### 1. Zero-Downtime Deploy

```bash
# Yeni versiyonu çek
git pull origin main

# Yeni image'ları build et
docker-compose build

# Yeni servisleri başlat (rolling update)
docker-compose up -d --no-deps api

# Eski container'ları temizle
docker system prune -f
```

### 2. Database Migration

```bash
# Migration kontrolü
docker-compose exec api alembic current

# Yeni migration'ları uygula
docker-compose exec api alembic upgrade head

# Migration geri alma (gerekirse)
docker-compose exec api alembic downgrade -1
```

## Güvenlik

### 1. SSL/TLS Sertifikaları

```bash
# Let's Encrypt ile sertifika al
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d loop.com -d www.loop.com

# Otomatik yenileme
echo "0 12 * * * root certbot renew --quiet" | sudo tee -a /etc/crontab
```

### 2. Firewall Yapılandırması

```bash
# UFW firewall kuralları
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 3. Secret Management

```bash
# Docker secret'ları kullan
echo "db_password" | docker secret create db_password -
echo "jwt_secret" | docker secret create jwt_secret -
```

## Performance Optimizasyonu

### 1. Database Optimizasyonu

```sql
-- Index oluşturma
CREATE INDEX idx_couriers_location ON couriers USING GIST(current_location);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at);

-- Database maintenance
VACUUM ANALYZE;
```

### 2. Redis Optimizasyonu

```bash
# Redis configuration
docker-compose exec redis redis-cli CONFIG SET maxmemory 1gb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 3. API Optimizasyonu

```python
# FastAPI caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

FastAPICache.init(RedisBackend(), prefix="loop-cache")
```

## Sorun Giderme

### 1. Container Başlatma Hataları

```bash
# Container durumunu kontrol et
docker-compose ps

# Container loglarını incele
docker-compose logs [service-name]

# Container içine gir
docker-compose exec [service-name] /bin/bash
```

### 2. Veritabanı Bağlantı Hataları

```bash
# PostgreSQL loglarını kontrol et
docker-compose logs db

# Veritabanı bağlantısını test et
docker-compose exec api python -c "
import asyncio
from app.core.database import engine
async def test():
    async with engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print(result.scalar())
asyncio.run(test())
"
```

### 3. Memory ve CPU Sorunları

```bash
# Sistem kaynaklarını kontrol et
docker stats

# Container resource limitlerini ayarla
docker-compose up -d --scale api=2
```

### 4. Network Sorunları

```bash
# Network bağlantılarını kontrol et
docker network ls
docker network inspect loop_network

# Container'lar arası iletişimi test et
docker-compose exec api ping db
docker-compose exec api ping redis
```

## Ölçeklenebilirlik

### 1. Horizontal Scaling

```yaml
# docker-compose.yml
deploy:
  replicas: 3
  update_config:
    parallelism: 1
    delay: 10s
  restart_policy:
    condition: on-failure
```

### 2. Load Balancing

```nginx
# nginx.conf
upstream api {
    least_conn;
    server api1:8000 weight=3;
    server api2:8000 weight=2;
    server api3:8000 weight=1;
}
```

### 3. Database Scaling

```yaml
# PostgreSQL read replicas
version: '3.8'
services:
  db-primary:
    image: postgis/postgis:15-3.3
    environment:
      - POSTGRES_DB=loop_db
      - POSTGRES_USER=loop_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_HOST_AUTH_METHOD=trust
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8
    command: >
      postgres 
      -c wal_level=replica 
      -c max_replication_slots=2 
      -c max_wal_senders=2
```

## İletişim ve Destek

- **Dokümantasyon**: [https://docs.loop.com](https://docs.loop.com)
- **API Referansı**: [https://api.loop.com/docs](https://api.loop.com/docs)
- **Destek**: support@loop.com
- **GitHub Issues**: [https://github.com/your-org/loop-logistics/issues](https://github.com/your-org/loop-logistics/issues)

## Lisans

Bu proje MIT Lisansı ile lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

---

**LOOP Lojistik Platformu** - Modern, ölçeklenebilir ve güvenli lojistik çözümleri 🚚✨