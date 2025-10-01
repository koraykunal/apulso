#!/usr/bin/env python
"""
N8N Debug Script - Bağlantı sorunlarını teşhis eder
"""

import requests
import ssl
import socket
from urllib.parse import urlparse

N8N_URL = "https://n8n.srv1011837.hstgr.cloud/"

def test_domain_resolution():
    """Domain çözümlemesi test et"""
    print("🔍 Domain çözümlemesi test ediliyor...")

    try:
        parsed = urlparse(N8N_URL)
        hostname = parsed.hostname

        ip = socket.gethostbyname(hostname)
        print(f"✅ Domain çözümlendi: {hostname} -> {ip}")
        return True
    except Exception as e:
        print(f"❌ Domain çözümleme hatası: {e}")
        return False

def test_port_connection():
    """Port bağlantısı test et"""
    print("🔍 Port bağlantısı test ediliyor...")

    try:
        parsed = urlparse(N8N_URL)
        hostname = parsed.hostname
        port = 443 if parsed.scheme == 'https' else 80

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((hostname, port))
        sock.close()

        if result == 0:
            print(f"✅ Port {port} açık")
            return True
        else:
            print(f"❌ Port {port} kapalı veya erişilemiyor")
            return False
    except Exception as e:
        print(f"❌ Port test hatası: {e}")
        return False

def test_ssl_certificate():
    """SSL sertifika test et"""
    print("🔍 SSL sertifikası test ediliyor...")

    try:
        parsed = urlparse(N8N_URL)
        hostname = parsed.hostname

        context = ssl.create_default_context()
        sock = socket.create_connection((hostname, 443), timeout=10)
        ssock = context.wrap_socket(sock, server_hostname=hostname)

        cert = ssock.getpeercert()
        print(f"✅ SSL sertifikası geçerli")
        print(f"   Subject: {dict(x[0] for x in cert['subject'])}")
        print(f"   Issuer: {dict(x[0] for x in cert['issuer'])}")

        ssock.close()
        return True
    except Exception as e:
        print(f"❌ SSL test hatası: {e}")
        return False

def test_http_with_different_settings():
    """Farklı HTTP ayarlarıyla test et"""
    print("🔍 Farklı HTTP ayarlarıyla test ediliyor...")

    # Test 1: SSL doğrulama olmadan
    try:
        print("  Test 1: SSL doğrulama olmadan...")
        response = requests.get(
            N8N_URL,
            verify=False,
            timeout=15,
            allow_redirects=True
        )
        print(f"  ✅ SSL olmadan başarılı: {response.status_code}")
        print(f"  Headers: {dict(response.headers)}")
        return True
    except Exception as e:
        print(f"  ❌ SSL olmadan hata: {e}")

    # Test 2: User-Agent ile
    try:
        print("  Test 2: User-Agent ile...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(
            N8N_URL,
            headers=headers,
            timeout=15,
            verify=False
        )
        print(f"  ✅ User-Agent ile başarılı: {response.status_code}")
        return True
    except Exception as e:
        print(f"  ❌ User-Agent ile hata: {e}")

    # Test 3: HTTP yerine HTTPS
    try:
        print("  Test 3: HTTP protokolü ile...")
        http_url = N8N_URL.replace('https://', 'http://')
        response = requests.get(
            http_url,
            timeout=15,
            allow_redirects=True
        )
        print(f"  ✅ HTTP ile başarılı: {response.status_code}")
        return True
    except Exception as e:
        print(f"  ❌ HTTP ile hata: {e}")

    return False

def test_n8n_specific_endpoints():
    """N8N özel endpoint'lerini test et"""
    print("🔍 N8N endpoint'leri test ediliyor...")

    base_url = N8N_URL.rstrip('/')
    endpoints = [
        '/healthz',
        '/rest/login',
        '/api/v1/workflows',
        '/webhook-test/test',
        ''  # Ana sayfa
    ]

    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            print(f"  Test: {url}")

            response = requests.get(
                url,
                timeout=10,
                verify=False,
                allow_redirects=True
            )

            print(f"    ✅ {response.status_code}: {response.reason}")
            if response.status_code == 200:
                print(f"    Content-Type: {response.headers.get('content-type', 'N/A')}")

        except Exception as e:
            print(f"    ❌ Hata: {e}")

def main():
    print("🚨 N8N Bağlantı Debug Scripti")
    print("=" * 50)

    # 1. Domain çözümlemesi
    if not test_domain_resolution():
        print("❌ Domain sorunu var, devam edilemiyor")
        return

    print()

    # 2. Port bağlantısı
    if not test_port_connection():
        print("❌ Port sorunu var, devam edilemiyor")
        return

    print()

    # 3. SSL sertifika
    test_ssl_certificate()
    print()

    # 4. HTTP testleri
    if test_http_with_different_settings():
        print("\n✅ HTTP bağlantısı başarılı!")
        print()

        # 5. N8N endpoint testleri
        test_n8n_specific_endpoints()
    else:
        print("\n❌ Tüm HTTP testleri başarısız")
        print("💡 Olası sebepler:")
        print("   - Firewall/IP kısıtlaması")
        print("   - N8N servis durmuş")
        print("   - Proxy/VPN sorunu")

if __name__ == "__main__":
    main()