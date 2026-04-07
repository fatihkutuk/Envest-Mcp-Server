# Envest MCP Server - Canli Sunucu Deploy Rehberi

## Gereksinimler

- Ubuntu 22.04+
- Python 3.10+
- pip3
- pm2 (Node.js ile kurulu)
- Nginx (CloudPanel veya mevcut)
- Cloudflare Tunnel (sunucu disariya kapali ise)

## Adim 1: Dosyalari Sunucuya Kopyala

Windows'tan:
```bash
scp -r D:/LiveProject/Envest-Mcp-Server/mcps/scada root@SUNUCU_IP:/home/envest-mcp/htdocs/mcp.envest.com.tr/mcps/scada
```

Veya rsync ile (sadece degisen dosyalar):
```bash
rsync -avz --exclude='__pycache__' --exclude='node_modules' --exclude='*.pyc' \
  D:/LiveProject/Envest-Mcp-Server/mcps/scada/ \
  root@SUNUCU_IP:/home/envest-mcp/htdocs/mcp.envest.com.tr/mcps/scada/
```

## Adim 2: Python Bagimliliklari Kur

```bash
ssh root@SUNUCU_IP
cd /home/envest-mcp/htdocs/mcp.envest.com.tr/mcps/scada
pip3 install -e .
pip3 install bcrypt
```

## Adim 3: Log ve Data Dizinleri

```bash
cd /home/envest-mcp/htdocs/mcp.envest.com.tr
mkdir -p logs data
```

## Adim 4: ecosystem.config.js Olustur

```bash
cat > /home/envest-mcp/htdocs/mcp.envest.com.tr/ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: "envest-mcp",
      script: "python3",
      args: "-m scada_mcp.combined --host 127.0.0.1 --port 8001 --require-token",
      cwd: "/home/envest-mcp/htdocs/mcp.envest.com.tr/mcps/scada",
      interpreter: "none",
      env: {
        LOG_LEVEL: "info",
      },
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
      error_file: "/home/envest-mcp/htdocs/mcp.envest.com.tr/logs/error.log",
      out_file: "/home/envest-mcp/htdocs/mcp.envest.com.tr/logs/out.log",
      merge_logs: true,
      log_date_format: "YYYY-MM-DD HH:mm:ss",
    },
  ],
};
EOF
```

## Adim 5: pm2 ile Baslat

```bash
cd /home/envest-mcp/htdocs/mcp.envest.com.tr
pm2 delete envest-mcp 2>/dev/null
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Sunucu reboot'ta otomatik baslasin
```

## Adim 6: Calistigini Dogrula

```bash
# pm2 durumu
pm2 status

# Log kontrol
pm2 logs envest-mcp --lines 20

# Localhost test
curl http://127.0.0.1:8001/
# HTML donmeli (login sayfasina redirect)

curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/login
# 200 donmeli
```

## Adim 7: Nginx Ayari

CloudPanel zaten mcp.envest.com.tr icin config olusturmus.
Vhost'ta `proxy_buffering off` ekli olmali (SSE icin zorunlu):

```bash
# CloudPanel > Sites > mcp.envest.com.tr > Vhost
# location / blogunda su satirlarin oldugundan emin ol:
#   proxy_buffering off;
#   proxy_cache off;
#   proxy_set_header Authorization $http_authorization;
```

## Adim 8: Cloudflare Tunnel (Sunucu Disariya Kapali ise)

Tunnel zaten kuruluysa:
```bash
pm2 restart mcp-tunnel
```

Yoksa:
```bash
# Tunnel olustur (bir kere yapilir)
cloudflared tunnel create envest-mcp

# Config yaz
cat > /root/.cloudflared/config.yml << 'EOF'
tunnel: <TUNNEL_ID>
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: mcp.envest.com.tr
    service: http://127.0.0.1:8001
  - service: http_status:404
EOF

# pm2 ile baslat
pm2 start cloudflared --name "mcp-tunnel" -- tunnel --config /root/.cloudflared/config.yml run envest-mcp
pm2 save
```

Cloudflare Dashboard > Zero Trust > Tunnels > envest-mcp > Public Hostname:
- Subdomain: mcp
- Domain: envest.com.tr
- Service: http://127.0.0.1:8001

## Adim 9: Dis Erisim Testi

```bash
curl https://mcp.envest.com.tr/
# Login sayfasina redirect olmali
```

Tarayicidan: https://mcp.envest.com.tr/login
- Kullanici: admin
- Sifre: admin (ilk giriste degistir!)

## Adim 10: Token Olustur ve MCP Client Test

1. Admin panele gir: https://mcp.envest.com.tr/login
2. Tokens > Yeni Token Olustur
3. Instance sec (korubin_main, korucaps, vs.)
4. Token Olustur > JWT kopyala

LM Studio / Claude Desktop / Cursor config:
```json
{
  "mcpServers": {
    "envest": {
      "url": "https://mcp.envest.com.tr/mcp/sse",
      "headers": {
        "Authorization": "Bearer <JWT_TOKEN>"
      }
    }
  }
}
```

## Guncelleme

Kod degistiginde:
```bash
# Dosyalari kopyala (rsync ile sadece degisen)
rsync -avz --exclude='__pycache__' --exclude='*.pyc' --exclude='data/' --exclude='logs/' \
  D:/LiveProject/Envest-Mcp-Server/mcps/scada/ \
  root@SUNUCU_IP:/home/envest-mcp/htdocs/mcp.envest.com.tr/mcps/scada/

# Sunucuda restart
ssh root@SUNUCU_IP "pm2 restart envest-mcp"
```

## pm2 Komutlari

```bash
pm2 status              # Durum
pm2 logs envest-mcp     # Canli log
pm2 restart envest-mcp  # Yeniden baslat
pm2 stop envest-mcp     # Durdur
pm2 delete envest-mcp   # Sil
pm2 monit               # Izleme paneli
```

## Sorun Giderme

### Sunucu baslamiyor
```bash
pm2 logs envest-mcp --lines 50
# Python hata mesajina bak
```

### Port kullaniliyor
```bash
ss -tlnp | grep 8001
# Baska process varsa oldur
kill -9 <PID>
```

### Token calismiyor
Admin panelden yeni token olustur. Eski /auth/mint token'lari artik gecersiz.

### DB baglantisi basarisiz
Instance .env dosyasindaki DB bilgilerini kontrol et:
```bash
cat /home/envest-mcp/htdocs/mcp.envest.com.tr/mcps/scada/instances/<instance_name>/.env
```

### Nginx 502 Bad Gateway
pm2 calisiyor mu kontrol et:
```bash
pm2 status
curl http://127.0.0.1:8001/
```
