#!/bin/bash
# ============================================
# Yeni MCP Servisi Ekleme
# ============================================
# Kullanim: bash scripts/add-mcp.sh <mcp-ismi> <dil>
# Ornek:    bash scripts/add-mcp.sh energy-monitor python
#           bash scripts/add-mcp.sh weather-api node

set -euo pipefail

MCP_NAME="${1:-}"
MCP_LANG="${2:-}"

if [ -z "$MCP_NAME" ] || [ -z "$MCP_LANG" ]; then
    echo "Kullanim: bash scripts/add-mcp.sh <mcp-ismi> <dil>"
    echo ""
    echo "  mcp-ismi  - Yeni MCP'nin adi (ornek: energy-monitor)"
    echo "  dil       - 'python' veya 'node'"
    echo ""
    echo "Ornek:"
    echo "  bash scripts/add-mcp.sh energy-monitor python"
    echo "  bash scripts/add-mcp.sh weather-api node"
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="$PROJECT_DIR/mcps/$MCP_NAME"

if [ -d "$TARGET_DIR" ]; then
    echo "HATA: $TARGET_DIR dizini zaten mevcut!"
    exit 1
fi

echo "Yeni MCP olusturuluyor: $MCP_NAME ($MCP_LANG)"

# Template'i kopyala
cp -r "$PROJECT_DIR/mcps/_template" "$TARGET_DIR"

# Dil secimi
case "$MCP_LANG" in
    python)
        mv "$TARGET_DIR/Dockerfile.python" "$TARGET_DIR/Dockerfile"
        rm -f "$TARGET_DIR/Dockerfile.node"
        mkdir -p "$TARGET_DIR/src"
        echo "# $MCP_NAME MCP Server" > "$TARGET_DIR/src/__init__.py"
        echo "Python MCP sablonu olusturuldu."
        ;;
    node)
        mv "$TARGET_DIR/Dockerfile.node" "$TARGET_DIR/Dockerfile"
        rm -f "$TARGET_DIR/Dockerfile.python"
        mkdir -p "$TARGET_DIR/src"
        echo "// $MCP_NAME MCP Server" > "$TARGET_DIR/src/index.ts"
        echo "Node.js MCP sablonu olusturuldu."
        ;;
    *)
        echo "HATA: Bilinmeyen dil '$MCP_LANG'. 'python' veya 'node' kullanin."
        rm -rf "$TARGET_DIR"
        exit 1
        ;;
esac

# Port hesapla (mevcut MCP sayisina gore)
EXISTING_COUNT=$(find "$PROJECT_DIR/mcps" -maxdepth 1 -mindepth 1 -type d ! -name "_template" | wc -l)
NEW_PORT=$((8000 + EXISTING_COUNT))

echo ""
echo "========================================"
echo "  $MCP_NAME olusturuldu!"
echo "========================================"
echo ""
echo "Dizin: $TARGET_DIR"
echo "Port:  $NEW_PORT (onerilir)"
echo ""
echo "Sonraki adimlar:"
echo ""
echo "1. MCP sunucunuzu implement edin:"
echo "   $TARGET_DIR/src/"
echo ""
echo "2. .env dosyasi olusturun:"
echo "   $TARGET_DIR/.env"
echo ""
echo "3. docker-compose.yml'a ekleyin:"
echo ""
echo "   $MCP_NAME:"
echo "     build: ./mcps/$MCP_NAME"
echo "     env_file: ./mcps/$MCP_NAME/.env"
echo "     ports:"
echo "       - \"127.0.0.1:$NEW_PORT:8080\""
echo "     restart: unless-stopped"
echo "     networks:"
echo "       - envest-net"
echo ""
echo "4. Nginx config'e location ekleyin:"
echo "   nginx/conf.d/mcp.envest.com.tr.conf"
echo ""
echo "   location /$MCP_NAME/ {"
echo "       proxy_pass http://$MCP_NAME:8080/;"
echo "       proxy_buffering off;"
echo "       proxy_cache off;"
echo "       ..."
echo "   }"
echo ""
echo "5. Build ve deploy:"
echo "   docker compose up -d --build $MCP_NAME"
echo "   docker compose restart nginx"
