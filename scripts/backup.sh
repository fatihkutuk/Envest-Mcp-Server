#!/bin/bash
# ============================================
# Envest MCP Server - Yedekleme
# ============================================
# Kullanim: bash scripts/backup.sh [hedef-dizin]
# Cron:     0 2 * * * /opt/envest-mcp/scripts/backup.sh /backups/envest-mcp

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${1:-/tmp/envest-mcp-backup}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/envest-mcp-$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "Yedekleme basliyor..."
echo "  Kaynak: $PROJECT_DIR"
echo "  Hedef:  $BACKUP_FILE"

# Yedeklenecek dosyalar (kaynak kod haric - git'te zaten var)
tar -czf "$BACKUP_FILE" \
    -C "$PROJECT_DIR" \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='*/exports/*' \
    .env \
    mcps/scada/instances/ \
    mcps/korucaps/.env \
    certs/ \
    2>/dev/null || true

BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
echo "Yedekleme tamamlandi: $BACKUP_FILE ($BACKUP_SIZE)"

# 30 gunden eski yedekleri sil
find "$BACKUP_DIR" -name "envest-mcp-*.tar.gz" -mtime +30 -delete 2>/dev/null || true
echo "30 gunden eski yedekler temizlendi."
