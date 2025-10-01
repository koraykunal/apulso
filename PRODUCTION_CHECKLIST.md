# 🚀 Production Deployment Checklist

## 📝 Yapılan Değişiklikler

### ✅ Tamamlanan İyileştirmeler

#### 1. **Settings.py - Production Ready**
- ✅ SECRET_KEY environment variable'a taşındı
- ✅ DEBUG environment variable'dan okunuyor
- ✅ ALLOWED_HOSTS yapılandırıldı
- ✅ PostgreSQL desteği eklendi (development'ta SQLite, production'da PostgreSQL)
- ✅ Database connection pooling (CONN_MAX_AGE=600)
- ✅ Static files yapılandırması (WhiteNoise)
- ✅ CORS güvenlik ayarları (production'da whitelist)
- ✅ Security headers eklendi (HSTS, SSL Redirect, XSS Protection)
- ✅ Cookie security (SECURE, HTTPONLY)
- ✅ Logging yapılandırması
- ✅ Email configuration
- ✅ Celery/Redis setup

#### 2. **Docker & Deployment**
- ✅ Dockerfile oluşturuldu
- ✅ docker-compose.yml (PostgreSQL, Redis, Django, Celery, Nginx)
- ✅ Nginx configuration
- ✅ .dockerignore
- ✅ .gitignore güncellendi

#### 3. **Environment Variables**
- ✅ .env.example güncellendi (detaylı açıklamalar)
- ✅ .env.production şablonu oluşturuldu
- ✅ Hassas bilgiler environment variable'lara taşındı

#### 4. **Celery Setup**
- ✅ celery.py oluşturuldu
- ✅ __init__.py güncellendi
- ✅ Docker compose'da worker ve beat servisleri

#### 5. **Documentation**
- ✅ DEPLOYMENT.md - Detaylı deployment guide
- ✅ Bu checklist dosyası

---

## 🔧 Production'a Geçmeden Önce Yapılması Gerekenler

### 1. Environment Variables Setup

```bash
# .env.production dosyasını düzenle
cp .env.example .env.production

# Yeni SECRET_KEY oluştur
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

**Güncellenecek değerler:**
- [ ] `SECRET_KEY` - Yukarıdaki komuttan alınan değer
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` - Domain adınız
- [ ] `DB_NAME, DB_USER, DB_PASSWORD, DB_HOST` - PostgreSQL bilgileri
- [ ] `CORS_ALLOWED_ORIGINS` - Frontend URL'i
- [ ] `CSRF_TRUSTED_ORIGINS` - Frontend URL'i
- [ ] `FAL_KEY` - Mevcut production key
- [ ] `EMAIL_HOST_USER` ve `EMAIL_HOST_PASSWORD` - Production email
- [ ] `N8N_WEBHOOK_URL` ve `N8N_API_KEY` - Production N8N

### 2. Database Migration

```bash
# Development verisini PostgreSQL'e taşı (opsiyonel)
python manage.py dumpdata > backup.json

# Production PostgreSQL'de
python manage.py migrate
python manage.py loaddata backup.json  # Eğer veri taşınacaksa
```

### 3. Static Files

```bash
# Static files'ları topla
python manage.py collectstatic --noinput
```

### 4. Superuser Oluştur

```bash
python manage.py createsuperuser
```

---

## 🔒 Güvenlik Kontrolleri

- [ ] SECRET_KEY değiştirildi mi?
- [ ] DEBUG=False production'da?
- [ ] ALLOWED_HOSTS doğru mu?
- [ ] SSL sertifikası var mı?
- [ ] Database şifreleri güçlü mü?
- [ ] .env.production git'e commitlenmemiş mi?
- [ ] CORS sadece güvenilir domain'lere açık mı?
- [ ] Email credentials doğru mu?
- [ ] FAL_KEY production key mi?

---

## 📦 Deployment Seçenekleri

### Seçenek 1: Docker ile Deployment (Önerilen)

```bash
# 1. Dosyaları sunucuya aktar
scp -r . user@server:/app/apulso_backend/

# 2. Sunucuda
cd /app/apulso_backend
docker-compose -f docker-compose.yml up -d

# 3. Migration
docker-compose exec web python manage.py migrate

# 4. Superuser
docker-compose exec web python manage.py createsuperuser

# 5. Static files
docker-compose exec web python manage.py collectstatic --noinput
```

### Seçenek 2: Manuel Deployment

```bash
# DEPLOYMENT.md'de detaylı anlatıldı
# Gunicorn + Systemd + Nginx kullanarak
```

---

## 🎯 Önerilen Hosting Seçenekleri

1. **DigitalOcean Droplet** - $12/month (2GB RAM, 1 CPU)
2. **AWS EC2** - t3.small (~$15/month)
3. **Heroku** - Kolay ama pahalı
4. **Railway.app** - Yeni, modern, kolay
5. **Render.com** - PostgreSQL dahil, $7/month

### En Kolay Deployment: Railway.app

```bash
# 1. Railway CLI yükle
npm install -g @railway/cli

# 2. Login
railway login

# 3. Yeni proje oluştur
railway init

# 4. PostgreSQL ekle
railway add postgresql

# 5. Deploy
railway up

# 6. Environment variables ekle (Railway dashboard'dan)
```

---

## 📊 Production Monitoring (İsteğe Bağlı)

### Sentry - Error Tracking

```bash
# requirements.txt'e ekle
pip install sentry-sdk

# settings.py
import sentry_sdk
sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)
```

### Prometheus/Grafana - Metrics

```yaml
# docker-compose.yml'e eklenebilir
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

---

## 🔄 Güncellemeler

### Code Update Süreci

```bash
# 1. Yeni kodu çek
git pull origin main

# 2. Docker rebuild
docker-compose down
docker-compose build
docker-compose up -d

# 3. Migration
docker-compose exec web python manage.py migrate

# 4. Static files
docker-compose exec web python manage.py collectstatic --noinput

# 5. Restart
docker-compose restart web
```

---

## ⚠️ Önemli Notlar

### Ödeme Sistemi Hakkında

- Payment app şu an aktif ancak frontend'de kullanılmıyor
- Production'da payments app'i devre dışı bırakılabilir:
  ```python
  # settings.py - INSTALLED_APPS
  # 'payments',  # Devre dışı
  ```

### FAL AI Try-On

- Try-on özelliği aktif ve production ready
- Demo invitation sistemi çalışıyor
- Cost tracking mevcut ($0.07/request)

### Media Files

- Development: Local storage
- Production: AWS S3'e taşınması önerilir
  ```python
  # settings.py
  if not DEBUG:
      DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
  ```

---

## 🎉 Deployment Sonrası Test

- [ ] Admin panel erişilebiliyor mu? `/admin/`
- [ ] API docs çalışıyor mu? `/api/docs/`
- [ ] Static files yükleniyor mu?
- [ ] Media upload çalışıyor mu?
- [ ] Email gönderimi test edildi mi?
- [ ] Try-on feature çalışıyor mu?
- [ ] Celery worker çalışıyor mu?
- [ ] Database bağlantısı sorunsuz mu?
- [ ] CORS frontend ile çalışıyor mu?

---

## 📞 Sorun Giderme

### Sık Karşılaşılan Hatalar

1. **Static files yüklenmiyor**
   ```bash
   python manage.py collectstatic --noinput
   # Nginx'te static path'i kontrol et
   ```

2. **Database bağlantı hatası**
   ```bash
   # .env.production'daki DB bilgilerini kontrol et
   docker-compose exec web python manage.py dbshell
   ```

3. **CORS hatası**
   ```bash
   # settings.py - CORS_ALLOWED_ORIGINS kontrol et
   ```

4. **500 Internal Server Error**
   ```bash
   # Logları kontrol et
   docker-compose logs web
   tail -f logs/django.log
   ```

---

## ✨ Sonuç

Backend artık **production ready**!

Yapılan tüm değişiklikler:
- ✅ Security hardened
- ✅ PostgreSQL ready
- ✅ Docker containerized
- ✅ Logging configured
- ✅ Celery integrated
- ✅ Static files optimized
- ✅ Environment-based config
- ✅ Deployment documented

**Bir sonraki adım:** Production sunucusuna deploy etmek! 🚀
