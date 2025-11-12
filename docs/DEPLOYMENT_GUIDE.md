# LOOP - Production Deployment Guide

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- Domain name configured
- SSL certificate (Let's Encrypt recommended)
- Minimum 4GB RAM, 2 CPU cores, 50GB storage

## Deployment Steps

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create app user
sudo useradd -m -s /bin/bash loop
sudo usermod -aG docker loop
```

### 2. Clone and Configure

```bash
# Clone repository
cd /home/loop
git clone https://github.com/yourusername/loop.git
cd loop

# Copy environment file
cp .env.example .env

# Edit production environment variables
nano .env
```

### 3. Configure Environment Variables

Edit `.env` with production values:

```env
# Application
APP_ENV=production
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://loop_user:STRONG_PASSWORD@postgres:5432/loop_db

# Redis
REDIS_URL=redis://redis:6379/0

# External Services
OPENWEATHER_API_KEY=your-api-key
MAPBOX_ACCESS_TOKEN=your-token
STRIPE_API_KEY=your-stripe-key
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# Domain
DOMAIN=yourdomain.com
```

### 4. SSL Certificate Setup

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/
sudo chown loop:loop ./ssl/*
```

### 5. Build and Deploy

```bash
# Build Docker images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 6. Database Migration

```bash
# Run migrations
docker-compose exec app alembic upgrade head

# Create admin user (optional)
docker-compose exec app python scripts/create_admin.py
```

### 7. Nginx Configuration

Update `docker/nginx.conf` with your domain:

```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 8. Monitoring Setup

```bash
# Access Prometheus
http://yourdomain.com:9090

# Access Flower (Celery monitoring)
http://yourdomain.com:5555

# Access n8n (Workflow automation)
http://yourdomain.com:5678
```

### 9. Backup Configuration

```bash
# Create backup script
cat > /home/loop/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/loop/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec -T postgres pg_dump -U loop_user loop_db > $BACKUP_DIR/db_$DATE.sql

# Backup uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz ./uploads/

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /home/loop/backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/loop/backup.sh") | crontab -
```

### 10. Firewall Configuration

```bash
# Allow necessary ports
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Health Checks

```bash
# Check API health
curl https://yourdomain.com/health

# Check database connection
docker-compose exec app python -c "from app.core.database import engine; print('DB OK')"

# Check Redis connection
docker-compose exec redis redis-cli ping
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  app:
    deploy:
      replicas: 3
    
  worker:
    deploy:
      replicas: 5
```

### Load Balancer

Use Nginx or HAProxy for load balancing:

```nginx
upstream app_servers {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    location / {
        proxy_pass http://app_servers;
    }
}
```

## Monitoring and Logging

### Centralized Logging

```bash
# Install ELK Stack or use cloud logging
docker-compose -f docker-compose.logging.yml up -d
```

### Application Monitoring

- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Sentry**: Error tracking
- **New Relic**: APM (optional)

## Troubleshooting

### Application Won't Start

```bash
# Check logs
docker-compose logs app

# Check environment variables
docker-compose exec app env | grep DATABASE

# Restart services
docker-compose restart
```

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec app python -c "from app.core.database import test_connection; test_connection()"
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Limit container memory
docker-compose.yml:
  services:
    app:
      mem_limit: 2g
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Enable SSL/TLS
- [ ] Configure firewall
- [ ] Set up fail2ban
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable database encryption
- [ ] Set up regular backups
- [ ] Configure monitoring and alerts
- [ ] Update dependencies regularly
- [ ] Enable audit logging

## Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec app alembic upgrade head
```

### Database Maintenance

```bash
# Vacuum database
docker-compose exec postgres psql -U loop_user -d loop_db -c "VACUUM ANALYZE;"

# Check database size
docker-compose exec postgres psql -U loop_user -d loop_db -c "SELECT pg_size_pretty(pg_database_size('loop_db'));"
```

## Performance Optimization

1. **Database Indexing**: Ensure all foreign keys and frequently queried columns are indexed
2. **Connection Pooling**: Configure appropriate pool sizes
3. **Caching**: Use Redis for frequently accessed data
4. **CDN**: Serve static files through CDN
5. **Compression**: Enable gzip compression in Nginx
6. **Database Read Replicas**: For read-heavy workloads

## Support

For production support:
- Email: devops@loop-logistics.com
- Slack: #loop-production
- On-call: +1-XXX-XXX-XXXX

---

**Last Updated**: November 2025
