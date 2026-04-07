#!/bin/bash
# ============================================
# Envest MCP Server - Ubuntu Sunucu Kurulum
# ============================================
# Kullanim: sudo bash scripts/setup.sh
# Ubuntu 22.04+ uzerinde test edilmistir.

set -euo pipefail

echo "========================================"
echo "  Envest MCP Server - Sunucu Kurulum"
echo "========================================"

# --- Gerekli Paketler ---
echo "[1/5] Sistem paketleri guncelleniyor..."
apt-get update
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw

# --- Docker ---
echo "[2/5] Docker kuruluyor..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
    echo "Docker kuruldu."
else
    echo "Docker zaten kurulu."
fi

# --- Docker Compose ---
echo "[3/5] Docker Compose kontrol ediliyor..."
if ! docker compose version &> /dev/null; then
    apt-get install -y docker-compose-plugin
    echo "Docker Compose kuruldu."
else
    echo "Docker Compose zaten kurulu."
fi

# --- Firewall ---
echo "[4/5] Firewall yapilandiriliyor..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable
echo "Firewall yapilandirildi (22, 80, 443 acik)."

# --- Proje Dizini ---
echo "[5/5] Proje dizini hazirlaniyor..."
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# .env dosyalari kontrol
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "UYARI: .env dosyasi olusturuldu. Lutfen degerleri doldurun!"
fi

# certs dizini
mkdir -p "$PROJECT_DIR/certs"

echo ""
echo "========================================"
echo "  Kurulum tamamlandi!"
echo "========================================"
echo ""
echo "Sonraki adimlar:"
echo "  1. .env dosyalarini doldurun:"
echo "     - $PROJECT_DIR/.env"
echo "     - $PROJECT_DIR/mcps/scada/instances/korubin_main/.env"
echo "     - $PROJECT_DIR/mcps/korucaps/.env"
echo ""
echo "  2. SSL sertifikalarini yukleyin:"
echo "     - Cloudflare: certs/origin.pem ve certs/origin.key"
echo "     - Let's Encrypt: bash scripts/ssl-setup.sh"
echo ""
echo "  3. Servisleri baslatin:"
echo "     docker compose up -d --build"
echo ""
echo "  4. Durumu kontrol edin:"
echo "     docker compose ps"
echo "     curl https://mcp.envest.com.tr/"
