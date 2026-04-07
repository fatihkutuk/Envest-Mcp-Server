#!/bin/bash
# ============================================
# SSL Sertifika Kurulumu
# ============================================
# Kullanim: bash scripts/ssl-setup.sh [cloudflare|letsencrypt]

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSL_MODE="${1:-}"
DOMAIN="mcp.envest.com.tr"

if [ -z "$SSL_MODE" ]; then
    echo "Kullanim: bash scripts/ssl-setup.sh [cloudflare|letsencrypt]"
    echo ""
    echo "  cloudflare   - Cloudflare Origin Certificate kurulumu"
    echo "  letsencrypt  - Let's Encrypt (Certbot) kurulumu"
    exit 1
fi

case "$SSL_MODE" in
    cloudflare)
        echo "========================================"
        echo "  Cloudflare Origin Certificate"
        echo "========================================"
        echo ""
        echo "1. Cloudflare Dashboard'a gidin:"
        echo "   SSL/TLS > Origin Server > Create Certificate"
        echo ""
        echo "2. Olusturulan sertifika dosyalarini kaydedin:"
        echo "   - origin.pem (Certificate)"
        echo "   - origin.key (Private Key)"
        echo ""
        echo "3. Dosyalari kopyalayin:"
        echo "   cp origin.pem $PROJECT_DIR/certs/origin.pem"
        echo "   cp origin.key $PROJECT_DIR/certs/origin.key"
        echo ""
        echo "4. Nginx'i yeniden baslatin:"
        echo "   docker compose restart nginx"
        echo ""
        echo "5. Cloudflare SSL modunu 'Full (Strict)' yapin."
        echo ""

        # Sertifika dosyalari var mi kontrol et
        if [ -f "$PROJECT_DIR/certs/origin.pem" ] && [ -f "$PROJECT_DIR/certs/origin.key" ]; then
            echo "Sertifika dosyalari mevcut. Nginx yeniden baslatilabilir."
        else
            echo "UYARI: Sertifika dosyalari henuz $PROJECT_DIR/certs/ altinda degil!"
            mkdir -p "$PROJECT_DIR/certs"
        fi
        ;;

    letsencrypt)
        echo "========================================"
        echo "  Let's Encrypt (Certbot)"
        echo "========================================"

        # Nginx config'de Let's Encrypt satirlarini etkinlestir
        echo "[1/3] Nginx config guncelleniyor..."
        NGINX_CONF="$PROJECT_DIR/nginx/conf.d/mcp.envest.com.tr.conf"

        # Once HTTP-only nginx ile certbot challenge icin baslat
        echo "[2/3] Ilk sertifika alinacak..."
        echo "  DNS A kaydi $DOMAIN -> sunucu IP'si gostermeli!"
        echo ""

        # E-posta
        read -p "Let's Encrypt e-posta adresi: " LE_EMAIL

        # Certbot ile sertifika al
        docker compose --profile letsencrypt run --rm certbot certonly \
            --webroot \
            --webroot-path=/var/www/certbot \
            --email "$LE_EMAIL" \
            --agree-tos \
            --no-eff-email \
            -d "$DOMAIN"

        echo "[3/3] Sertifika alindi!"
        echo ""
        echo "Nginx config'de Let's Encrypt satirlarini etkinlestirin:"
        echo "  $NGINX_CONF"
        echo ""
        echo "Sonra Nginx'i yeniden baslatin:"
        echo "  docker compose restart nginx"
        echo ""
        echo "Otomatik yenileme icin certbot servisini baslatin:"
        echo "  docker compose --profile letsencrypt up -d certbot"
        ;;

    *)
        echo "Bilinmeyen mod: $SSL_MODE"
        echo "Kullanim: bash scripts/ssl-setup.sh [cloudflare|letsencrypt]"
        exit 1
        ;;
esac
