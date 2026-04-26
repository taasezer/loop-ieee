# LOOP Logistics Platform - Deployment Guide

Bu proje, esneklik ve performans sağlamak amacıyla **İkili Dağıtım (Dual-Deployment)** stratejisi kullanacak şekilde yapılandırılmıştır.

1. **Staging / Test Ortamı:** Render (PaaS) üzerinden otomatik CI/CD.
2. **Production / Canlı Ortam:** Oracle Cloud VPS üzerinden Docker Compose.

---

## Bölüm 1: STAGING (Render - Test Ortamı)

Geliştirme sürecindeki kodlarınızı hızlıca test etmek için Render kullanılır. Projede bulunan `render.yaml` dosyası bu ortam için optimize edilmiştir.

### Render Dağıtım Adımları
1. **GitHub'a Push:**
   ```bash
   git add .
   git commit -m "Test deploy"
   git push origin main
   ```
2. **Render Dashboard:**
   - [render.com](https://render.com) adresine gidin.
   - **"New" -> "Blueprint"** seçeneğine tıklayın.
   - GitHub deponuzu bağlayın. Render, `render.yaml` dosyasını otomatik algılayıp veritabanı, Redis ve FastAPI servisini kuracaktır.
3. **Environment Variables:**
   - Render Dashboard üzerinden ilgili servise (Web Service) tıklayın.
   - `Environment` sekmesinden `.env.example` içerisindeki dış servis API anahtarlarını (SendGrid, Twilio vb.) ekleyin.

> **Not:** Render'ın ücretsiz planında 15 dakika inaktivite sonrası servis uykuya geçer (Cold Start). Bu sadece test içindir. Ayrıca **n8n** Render üzerinde çalışmaz, kendi bilgisayarınızda çalıştırıp bağlamanız gerekir.

---

## Bölüm 2: PRODUCTION (Oracle Cloud - Canlı Ortam)

Müşterileriniz için kesintisiz, sıfır gecikmeli ve n8n dahil tüm servisleri barındıran gerçek canlı ortam kurulumudur.

### Adım 1: Oracle Cloud Sunucusu Oluşturma
1. Oracle Cloud panelinden **"Create a VM instance"** deyin.
2. Image olarak **Ubuntu 22.04**, Shape olarak **Ampere (ARM) A1 Compute** (4 OCPU, 24 GB RAM) seçin. (Ücretsiz katman).
3. SSH anahtarlarınızı indirmeyi unutmayın.
4. **VCN Security List (Güvenlik Duvarı):** Ağ ayarlarından Ingress Rules kısmına `TCP 8000` (FastAPI) ve `TCP 5678` (n8n) portları için `0.0.0.0/0` kuralını ekleyin.

### Adım 2: Sunucuya Bağlanma ve Docker Kurulumu
Bilgisayarınızın terminalinden sunucuya bağlanın:
```bash
ssh -i /path/to/your/private_key ubuntu@SUNUCU_IP_ADRESI
```

Sunucuya Docker ve Git kurun:
```bash
sudo apt update
sudo apt install -y docker.io docker-compose git
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
```
*(Grup ayarının geçerli olması için SSH'dan çıkıp tekrar girmeniz gerekebilir)*

### Adım 3: Projeyi Klonlama ve Ayarlar
```bash
git clone https://github.com/kullaniciadi/loop-ieee.git
cd loop-ieee
```

`.env` dosyanızı oluşturun:
```bash
cp .env.example .env
nano .env
```
Buradaki tüm API anahtarlarınızı (`SENDGRID_API_KEY`, `TWILIO`, vb.) dikkatlice doldurun. Çıkmak için `CTRL+X`, `Y`, `Enter`.

### Adım 4: Sistemi Başlatma
Tüm servisleri (Backend, Postgres, Redis ve n8n) tek komutla canlıya alın:
```bash
docker-compose up -d --build
```

### Adım 5: Doğrulama ve Kullanım
- **API (FastAPI):** `http://SUNUCU_IP_ADRESI:8000/docs`
- **Otomasyon (n8n):** `http://SUNUCU_IP_ADRESI:5678`

Her iki servise de tarayıcı üzerinden erişebilirsiniz. `docker-compose.yml` dosyamız, Veritabanı (5432) ve Redis (6379) portlarını güvenlik sebebiyle dış dünyaya kapatmıştır.

> **Önemli:** Production ortamında Domain bağlayıp SSL sertifikası (HTTPS) almak için Nginx Reverse Proxy kullanılması önerilir. Kurulum tamamlandıktan sonra Nginx ve Certbot kurulumu yapılabilir.
