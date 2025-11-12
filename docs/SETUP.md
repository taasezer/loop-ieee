# LOOP - Setup Guide

This guide will help you set up the LOOP logistics backend system from scratch.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11 or higher**
- **PostgreSQL 15 or higher**
- **Redis 7 or higher**
- **Docker and Docker Compose** (optional, for containerized deployment)
- **Git**

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/loop.git
cd loop
```

## Step 2: Environment Setup

### Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

For development dependencies:

```bash
pip install -r requirements-dev.txt
```

## Step 3: Configure Environment Variables

### Copy Environment Template

```bash
cp .env.example .env
```

### Edit .env File

Open `.env` and configure the following essential variables:

#### Application Settings
```env
SECRET_KEY=your-very-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-change-this
DEBUG=True
APP_ENV=development
```

#### Database Configuration
```env
DATABASE_URL=postgresql+asyncpg://loop_user:loop_password@localhost:5432/loop_db
```

#### Redis Configuration
```env
REDIS_URL=redis://localhost:6379/0
```

## Step 4: Database Setup

### Create PostgreSQL Database

```bash
# Login to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE loop_db;
CREATE USER loop_user WITH PASSWORD 'loop_password';
GRANT ALL PRIVILEGES ON DATABASE loop_db TO loop_user;
\q
```

### Run Database Migrations

```bash
alembic upgrade head
```

## Step 5: External Service Configuration

### OpenWeatherMap API

1. Sign up at https://openweathermap.org/api
2. Get your API key
3. Add to `.env`:
```env
OPENWEATHER_API_KEY=your-api-key
```

### Mapbox (Optional)

1. Sign up at https://www.mapbox.com/
2. Get your access token
3. Add to `.env`:
```env
MAPBOX_ACCESS_TOKEN=your-token
```

### Firebase Cloud Messaging

1. Create a Firebase project
2. Download service account credentials JSON
3. Save as `firebase-credentials.json` in project root
4. Add to `.env`:
```env
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
FIREBASE_PROJECT_ID=your-project-id
```

### Stripe Payment

1. Sign up at https://stripe.com
2. Get API keys from dashboard
3. Add to `.env`:
```env
STRIPE_API_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### Twilio SMS (Optional)

1. Sign up at https://www.twilio.com
2. Get account SID and auth token
3. Add to `.env`:
```env
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

## Step 6: Run the Application

### Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or using the main module:

```bash
python -m app.main
```

### Access the Application

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Step 7: Docker Deployment (Optional)

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services Available

- **API**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **n8n**: http://localhost:5678
- **Flower**: http://localhost:5555
- **Prometheus**: http://localhost:9090

## Step 8: Initialize Data (Optional)

### Seed Database

```bash
python scripts/seed_database.py
```

### Create Admin User

```bash
python scripts/create_admin.py
```

## Step 9: Run Background Workers

### Start Celery Worker

```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

### Start Celery Beat (Scheduler)

```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

### Monitor with Flower

```bash
celery -A app.tasks.celery_app flower --port=5555
```

## Step 10: Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test
pytest tests/unit/test_auth.py -v
```

### View Coverage Report

```bash
open htmlcov/index.html  # On macOS
# Or navigate to htmlcov/index.html in your browser
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U loop_user -d loop_db -h localhost
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping

# Should return PONG
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Migration Issues

```bash
# Reset migrations (CAUTION: This will drop all data)
alembic downgrade base
alembic upgrade head
```

## Development Tools

### Code Formatting

```bash
# Format with black
black app/

# Sort imports
isort app/

# Lint with flake8
flake8 app/
```

### Type Checking

```bash
mypy app/
```

### Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

## Next Steps

1. Read the [API Documentation](API.md)
2. Review the [Architecture](../ARCHITECTURE.md)
3. Check the [Contributing Guidelines](CONTRIBUTING.md)
4. Explore the [Deployment Guide](DEPLOYMENT.md)

## Support

If you encounter any issues:

1. Check the [FAQ](FAQ.md)
2. Search existing [GitHub Issues](https://github.com/yourusername/loop/issues)
3. Create a new issue with detailed information
4. Contact support at support@loop-logistics.com

---

**Happy coding! 🚀**
