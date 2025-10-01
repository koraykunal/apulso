# Apulso Backend - Production Deployment Guide

## 📋 Prerequisites

- Docker & Docker Compose installed
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (if not using Docker)
- Domain name configured
- SSL certificate (for HTTPS)

## 🚀 Quick Start with Docker

### 1. Environment Setup

```bash
# Copy production environment template
cp .env.example .env.production

# Generate a new SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Edit .env.production and update:
# - SECRET_KEY (from above)
# - DEBUG=False
# - ALLOWED_HOSTS (your domain)
# - Database credentials
# - CORS_ALLOWED_ORIGINS (your frontend URL)
# - FAL_KEY (for AI Try-On feature)
# - Email settings
```

### 2. Build and Run

```bash
# Build containers
docker-compose build

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f web

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### 3. Verify Deployment

```bash
# Check if all services are running
docker-compose ps

# Test API health
curl http://localhost:8000/api/v1/

# Access admin panel
http://localhost:8000/admin/
```

## 🔧 Manual Deployment (Without Docker)

### 1. System Requirements

```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Install Redis
sudo apt-get install redis-server

# Install Python 3.11+
sudo apt-get install python3.11 python3.11-venv
```

### 2. Application Setup

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env.production
# Edit .env.production with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### 3. Setup Gunicorn Service

Create `/etc/systemd/system/apulso.service`:

```ini
[Unit]
Description=Apulso Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/apulso_backend
Environment="PATH=/path/to/apulso_backend/.venv/bin"
ExecStart=/path/to/apulso_backend/.venv/bin/gunicorn --workers 4 --bind 0.0.0.0:8000 apulso_backend.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start apulso
sudo systemctl enable apulso
```

### 4. Setup Celery Workers

Create `/etc/systemd/system/celery.service`:

```ini
[Unit]
Description=Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/apulso_backend
Environment="PATH=/path/to/apulso_backend/.venv/bin"
ExecStart=/path/to/apulso_backend/.venv/bin/celery -A apulso_backend worker --loglevel=info

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl start celery
sudo systemctl enable celery
```

## 🌐 Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/apulso_backend/staticfiles/;
    }

    location /media/ {
        alias /path/to/apulso_backend/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔒 SSL Setup (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## 📊 Database Management

### Backup

```bash
# Docker
docker-compose exec db pg_dump -U apulso_user apulso_production > backup.sql

# Manual
pg_dump -U apulso_user -h localhost apulso_production > backup.sql
```

### Restore

```bash
# Docker
cat backup.sql | docker-compose exec -T db psql -U apulso_user apulso_production

# Manual
psql -U apulso_user -h localhost apulso_production < backup.sql
```

## 🔍 Monitoring & Logs

### Docker Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery_worker
```

### Application Logs

```bash
# Django logs
tail -f logs/django.log

# Gunicorn logs
journalctl -u apulso -f

# Celery logs
journalctl -u celery -f
```

## ⚙️ Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | ✅ |
| `DEBUG` | Debug mode (False in production) | ✅ |
| `ALLOWED_HOSTS` | Allowed host domains | ✅ |
| `DB_NAME` | PostgreSQL database name | ✅ |
| `DB_USER` | PostgreSQL username | ✅ |
| `DB_PASSWORD` | PostgreSQL password | ✅ |
| `DB_HOST` | Database host | ✅ |
| `DB_PORT` | Database port | ✅ |
| `CORS_ALLOWED_ORIGINS` | Frontend URLs | ✅ |
| `FAL_KEY` | FAL AI API key (for Try-On) | ✅ |
| `EMAIL_HOST_USER` | SMTP email | ❌ |
| `EMAIL_HOST_PASSWORD` | SMTP password | ❌ |
| `N8N_WEBHOOK_URL` | N8N webhook URL | ❌ |
| `REDIS_URL` | Redis connection URL | ✅ |

## 🚨 Security Checklist

- [ ] Change SECRET_KEY to a strong random value
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS correctly
- [ ] Setup SSL/HTTPS
- [ ] Update CORS_ALLOWED_ORIGINS
- [ ] Use strong database passwords
- [ ] Enable firewall (UFW)
- [ ] Setup fail2ban
- [ ] Regular security updates
- [ ] Monitor logs regularly
- [ ] Setup automated backups

## 🔄 Updates & Maintenance

```bash
# Pull latest code
git pull origin main

# Rebuild Docker containers
docker-compose down
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

## 📞 Support

For issues or questions:
- Check logs first
- Review Django error pages (if DEBUG=True locally)
- Check Docker container status
- Verify all environment variables

## 🎯 Performance Optimization

1. **Database Indexing**: Already configured in models
2. **Redis Caching**: Setup for Celery
3. **Static Files**: Served via WhiteNoise/Nginx
4. **Gunicorn Workers**: 4 workers (adjust based on CPU cores: 2 × CPU + 1)
5. **PostgreSQL Connection Pooling**: Enabled (CONN_MAX_AGE=600)

## 📈 Scaling Recommendations

- **Horizontal Scaling**: Add more Gunicorn workers
- **Database**: Setup PostgreSQL replication
- **Media Files**: Move to AWS S3/DigitalOcean Spaces
- **CDN**: Use Cloudflare for static assets
- **Monitoring**: Add Sentry for error tracking
- **Load Balancer**: Use Nginx or cloud load balancer
