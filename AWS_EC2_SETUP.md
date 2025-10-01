# 🚀 AWS EC2 + S3 Setup Guide - Apulso Backend

## ✅ EC2'da IAM Role Kullanmanın Avantajları

- 🔒 **Daha güvenli**: Access key'ler code/env'de yok
- 🔄 **Otomatik rotation**: AWS halleder
- 🚫 **Key leak riski yok**: Hard-coded credentials yok
- ⚡ **Kolay yönetim**: IAM'den izinleri değiştir

---

## 📋 Adım 1: S3 Bucket Oluştur (Zaten Yaptın ✅)

AWS Console → S3 → Create bucket

```
Bucket name: apulso-bucket
Region: EU (Frankfurt) eu-west-1  # veya en yakın region
Block all public access: ❌ (KAPALI - media files için)
```

### Bucket Policy

Permissions → Bucket Policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::apulso-bucket/*"
        }
    ]
}
```

### CORS Configuration

Permissions → CORS:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["https://apulso.io", "https://www.apulso.io"],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3000
    }
]
```

---

## 📋 Adım 2: IAM Role Oluştur

### 2.1. IAM Role oluştur

AWS Console → IAM → Roles → Create role

1. **Trusted entity type**: AWS service
2. **Use case**: EC2
3. **Next**

### 2.2. Permissions ekle

Policy seçimi için **Custom Policy** oluştur:

**Create policy** → JSON:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::apulso-bucket",
                "arn:aws:s3:::apulso-bucket/*"
            ]
        }
    ]
}
```

Policy name: `ApulsoS3Access`

### 2.3. Role ismini belirle

Role name: `ApulsoEC2S3Role`

**Create role**

---

## 📋 Adım 3: EC2 Instance Oluştur

### 3.1. EC2 Launch

AWS Console → EC2 → Launch Instance

**Instance ayarları:**
```
Name: apulso-backend
AMI: Ubuntu Server 22.04 LTS
Instance type: t3.small (2 vCPU, 2GB RAM) - başlangıç için yeterli
                veya t3.medium (daha iyi performans)
```

**Key pair:** Yeni oluştur veya mevcut bir key kullan
```
Key pair name: apulso-ec2-key
Type: RSA
Format: .pem (Mac/Linux) veya .ppk (Windows/PuTTY)
```

**Network settings:**
```
Auto-assign public IP: Enable
Firewall (Security Groups):
  ✅ SSH (22) - My IP
  ✅ HTTP (80) - Anywhere
  ✅ HTTPS (443) - Anywhere
  ✅ Custom TCP (8000) - Anywhere (geçici - test için)
```

**Storage:**
```
Root volume: 30 GB gp3
```

**Advanced details → IAM instance profile:**
```
IAM role: ApulsoEC2S3Role  ✅ BURADA SEÇ!
```

**Launch instance**

---

## 📋 Adım 4: EC2'ya Bağlan ve Kurulum

### 4.1. SSH ile bağlan

```bash
# Linux/Mac
chmod 400 apulso-ec2-key.pem
ssh -i apulso-ec2-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# Windows (PuTTY kullan veya WSL)
```

### 4.2. Sistem güncellemesi

```bash
sudo apt update && sudo apt upgrade -y
```

### 4.3. Docker kurulumu

```bash
# Docker yükle
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker compose yükle
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# User'ı docker grubuna ekle (sudo olmadan çalıştırmak için)
sudo usermod -aG docker $USER
newgrp docker

# Test
docker --version
docker-compose --version
```

### 4.4. Git kurulumu

```bash
sudo apt install git -y
```

---

## 📋 Adım 5: Backend Kodunu Deploy Et

### 5.1. Repository clone

```bash
# Home directory'de
cd ~

# Git clone (private repo ise SSH key eklemen gerekir)
git clone https://github.com/KULLANICI_ADIN/apulso_backend.git
# veya
git clone git@github.com:KULLANICI_ADIN/apulso_backend.git

cd apulso_backend
```

### 5.2. .env.production dosyasını oluştur

```bash
# Mevcut .env.production'ı düzenle
nano .env.production
```

**ÖNEMLİ:** AWS credentials'ı **boş bırak**! IAM Role kullanıyorsun:

```bash
SECRET_KEY="&n_+)ll&qs@ej^30)et#1bp32vfp_xd=qj%6#-%ef+@boie1dx"
DEBUG=False
ALLOWED_HOSTS=apulso.io,www.apulso.io,YOUR_EC2_IP

DB_NAME=apulso_production
DB_USER=apulso_prod_user
DB_PASSWORD=zscAXD1423.
DB_HOST=db
DB_PORT=5432

CORS_ALLOWED_ORIGINS=https://apulso.io,https://www.apulso.io
CSRF_TRUSTED_ORIGINS=https://apulso.io,https://www.apulso.io

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_FROM_ADDRESS=noreply@apulso.io

FAL_KEY=699df8fb-4e2e-4cfc-a327-c30eb0b325fc:18e189b926db491a970cff0d67c4d34e
N8N_WEBHOOK_URL=https://n8n.srv1011837.hstgr.cloud/webhook/
N8N_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

REDIS_URL=redis://redis:6379/0

# S3 - IAM Role kullanıyoruz, credentials boş!
USE_S3=True
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=apulso-bucket
AWS_S3_REGION_NAME=eu-west-1
```

Kaydet: `Ctrl+O`, `Enter`, `Ctrl+X`

### 5.3. Docker ile başlat

```bash
# Containers oluştur ve başlat
docker-compose up -d

# Logları izle
docker-compose logs -f

# Migration
docker-compose exec web python manage.py migrate

# Superuser oluştur
docker-compose exec web python manage.py createsuperuser

# Static files
docker-compose exec web python manage.py collectstatic --noinput
```

### 5.4. Test

```bash
# EC2 IP ile test
curl http://YOUR_EC2_IP:8000/api/v1/

# Browser'da aç
http://YOUR_EC2_IP:8000/admin/
http://YOUR_EC2_IP:8000/api/docs/
```

---

## 📋 Adım 6: Domain Ayarları (apulso.io)

### 6.1. DNS Kayıtları

Domain sağlayıcında (GoDaddy, Namecheap, Route53, vs.):

```
Type    Name    Value                       TTL
A       @       YOUR_EC2_PUBLIC_IP          300
A       www     YOUR_EC2_PUBLIC_IP          300
A       api     YOUR_EC2_PUBLIC_IP          300
```

Test: `ping apulso.io` (EC2 IP'yi görmeli)

### 6.2. SSL Sertifikası (Let's Encrypt)

```bash
# Certbot yükle
sudo apt install certbot python3-certbot-nginx -y

# Nginx container'ını durdur (certbot için)
docker-compose stop nginx

# SSL sertifikası al
sudo certbot certonly --standalone -d apulso.io -d www.apulso.io -d api.apulso.io
# Email gir, ToS kabul et

# Sertifikalar:
# /etc/letsencrypt/live/apulso.io/fullchain.pem
# /etc/letsencrypt/live/apulso.io/privkey.pem
```

### 6.3. Nginx SSL ayarları

```bash
# SSL dizini oluştur
mkdir -p nginx/ssl

# Sertifikaları kopyala
sudo cp /etc/letsencrypt/live/apulso.io/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/apulso.io/privkey.pem nginx/ssl/key.pem
sudo chown -R $USER:$USER nginx/ssl
```

`nginx/nginx.conf` dosyasını düzenle - HTTPS kısmını aktif et:

```bash
nano nginx/nginx.conf
```

HTTPS server bloğundaki comment'leri kaldır ve düzenle:

```nginx
server {
    listen 443 ssl http2;
    server_name apulso.io www.apulso.io;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # ... rest of config
}
```

```bash
# Nginx'i yeniden başlat
docker-compose up -d nginx
```

### 6.4. Auto-renewal

```bash
# Cron job ekle
sudo crontab -e

# En alta ekle (her gün 2:00'de kontrol eder)
0 2 * * * certbot renew --quiet && cp /etc/letsencrypt/live/apulso.io/*.pem /home/ubuntu/apulso_backend/nginx/ssl/ && docker-compose -f /home/ubuntu/apulso_backend/docker-compose.yml restart nginx
```

---

## 📋 Adım 7: S3 Test

### 7.1. Django shell'de test

```bash
docker-compose exec web python manage.py shell
```

```python
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# S3'e dosya yükle
file_content = ContentFile(b"Test content from EC2")
file_path = default_storage.save('test.txt', file_content)

print(f"Uploaded to: {file_path}")
print(f"URL: {default_storage.url(file_path)}")

# Browser'da URL'yi aç - dosya görünmeli!
```

---

## 🔍 IAM Role Çalışıyor mu Kontrol Et

```bash
# EC2 içinde
docker-compose exec web bash

# Boto3 ile test
python3 << EOF
import boto3

# Credentials otomatik IAM Role'den gelir
s3 = boto3.client('s3', region_name='eu-west-1')
buckets = s3.list_buckets()

print("Buckets:", [b['Name'] for b in buckets['Buckets']])
# ['apulso-bucket', ...] görmelisin
EOF
```

**Başarılıysa:** IAM Role çalışıyor! ✅

---

## 🔧 Güncellemeler

```bash
# Kod güncellemesi
cd ~/apulso_backend
git pull origin main

# Rebuild
docker-compose down
docker-compose build
docker-compose up -d

# Migration
docker-compose exec web python manage.py migrate

# Static files
docker-compose exec web python manage.py collectstatic --noinput
```

---

## 🐛 Sorun Giderme

### S3 upload hatası

```bash
# IAM Role kontrolü
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/ApulsoEC2S3Role

# Credentials görmeli (geçici access key/secret)
```

### Permission denied

IAM Role policy'sini kontrol et - bucket ARN doğru mu?

### HTTPS çalışmıyor

```bash
# Nginx logs
docker-compose logs nginx

# SSL sertifika path'i doğru mu?
ls -la nginx/ssl/
```

---

## ✅ Checklist

Production'da:

- [ ] EC2 instance oluşturuldu
- [ ] IAM Role (ApulsoEC2S3Role) atandı
- [ ] S3 bucket policy yapılandırıldı
- [ ] Docker kuruldu
- [ ] Backend deploy edildi
- [ ] Database migration çalıştırıldı
- [ ] S3 upload test edildi
- [ ] Domain DNS ayarları yapıldı
- [ ] SSL sertifikası kuruldu
- [ ] HTTPS çalışıyor
- [ ] .env.production'da AWS_ACCESS_KEY boş

---

## 🎯 Sonuç

✅ **IAM Role kullanarak S3'e erişim sağlandı**
- Access key'e gerek yok!
- Daha güvenli
- AWS best practice

🌐 **Production URLs:**
- API: https://api.apulso.io
- Admin: https://api.apulso.io/admin/
- Docs: https://api.apulso.io/api/docs/
- Media: https://apulso-bucket.s3.eu-west-1.amazonaws.com/
