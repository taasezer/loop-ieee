# LOOP Lojistik Platformu - Dockerfile
# Python 3.11 tabanlı FastAPI uygulaması

FROM python:3.11-slim

# Sistem paketlerini güncelle ve gerekli bağımlılıkları yükle
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libgeos-dev \
    proj-bin \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizinini ayarla
WORKDIR /app

# Python path'i ayarla
ENV PYTHONPATH=/app

# Gereksiz Python dosyalarını kaldır (image boyutunu küçült)
RUN find /usr/local/lib/python3.11 -name "test" -type d -exec rm -rf {} + || true

# requirements.txt dosyasını kopyala ve bağımlılıkları yükle
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# FastAPI uygulaması için ortam değişkenleri
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Uygulamanın çalışacağı port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Uygulamayı başlat
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]