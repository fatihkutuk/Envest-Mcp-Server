# Ubuntu Sunucu Deploy Rehberi

## Gereksinimler

- Ubuntu 22.04+
- Python 3.10+
- pip3
- pm2 (`npm install -g pm2`)
- Cloudflare hesabi (tunnel icin)
- cloudflared (`apt install cloudflared` veya https://github.com/cloudflare/cloudflared)

## Adim 1: Dosyalari Sunucuya Kopyala

```bash
# Ilk kurulum
git clone <repo-url> /home/envest-mcp/htdocs/mcp.envest.com.tr

# Guncelleme (rsync ile sadece degisen dosyalar)
rsync -avz --exclude='__pycache__' --exclude='*.pyc' --exclude='data/' --exclude='logs/' \
  D:/LiveProject/Envest-Mcp-Server/mcps/scada/ \
  root@SUNUCU_IP:/home/envest-mcp/htdocs/mcp.envest.com.tr/mcps/scada/
```

## Adim 2: Python Bagimliliklari

```bash
cd /home/envest-mcp/htdocs/mcp.envest.com.tr/mcps/scada
pip3 install -e .
pip3 install bcrypt
```

## Adim 3: Dizinler

```bash
cd /home/envest-mcp/htdocs/mcp.envest.com.tr
mkdir -p logs data
```

## Adim 4: ecosystem.config.js

```bash
cat > /home/envest-mcp/htdocs/mcp.envest.com.tr/ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: "envest-mcp",
    script: "python3",
    args: "-m scada_mcp.combined --host 127.0.0.1 --port 8001 --require-token",
    cwd: "/home/envest-mcp/htdocs/mcp.envest.com.tr/mcps/scada",
    interpreter: "none",
    env: { LOG_LEVEL: "info" },
    autorestart: true,
    max_restarts: 10,
    restart_delay: 3000,
    error_file: "/home/envest-mcp/htdocs/mcp.envest.com.tr/logs/error.log",
    out_file: "/home/envest-mcp/htdocs/mcp.envest.com.tr/logs/out.log",
    merge_logs: true,
    log_date_format: "YYYY-MM-DD HH:mm:ss",
  }],
};
EOF
```

## Adim 5: pm2 ile Baslat

```bash
cd /home/envest-mcp/htdocs/mcp.envest.com.tr
pm2 delete envest-mcp 2>/dev/null
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Reboot'ta otomatik baslasin
```

## Adim 6: Dogrula

```bash
pm2 status
pm2 logs envest-mcp --lines 10
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/login
# 200 donmeli
```

## Adim 7: Cloudflare Tunnel

### Tunnel yoksa ilk kez olustur:

```bash
cloudflared tunnel login
cloudflared tunnel create envest-mcp
# TUNNEL_ID not et (ornek: aecfac20-88e8-42c9-82ad-537ce60ef0ce)
```

### Tunnel config:

```bash
cat > /root/.cloudflared/config.yml << 'EOF'
tunnel: <TUNNEL_ID>
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: mcp.envest.com.tr
    service: http://127.0.0.1:8001
    originRequest:
      httpHostHeader: "127.0.0.1:8001"
      noTLSVerify: true
  - service: http_status:404
EOF
```

**ONEMLI:** `httpHostHeader: "127.0.0.1:8001"` satirini MUTLAKA ekleyin.
Bu olmadan MCP SSE baglantisi `421 Misdirected Request` veya `Invalid Host header` hatasi verir.

### Tunnel'i pm2 ile baslat:

```bash
pm2 start cloudflared --name "mcp-tunnel" -- tunnel --config /root/.cloudflared/config.yml run envest-mcp
pm2 save
```

### Cloudflare Dashboard'dan hostname ekle:

Zero Trust > Networks > Tunnels > envest-mcp > Public Hostname:
- Subdomain: `mcp`
- Domain: `envest.com.tr`
- Service Type: HTTP
- URL: `127.0.0.1:8001`

### DNS ayari:

Cloudflare DNS'te `mcp` subdomain'i icin A kaydi varsa silin.
Tunnel otomatik CNAME olusturur. Olusturmazsa manuel ekleyin:
- Type: CNAME
- Name: mcp
- Target: `<TUNNEL_ID>.cfargotunnel.com`
- Proxy: ON

## Adim 8: Cloudflare Ayarlari

**Rocket Loader KAPALI olmali** (Tailwind CSS'i bozar):
- Cloudflare > envest.com.tr > Speed > Optimization > Rocket Loader > OFF

Veya template'lerde `data-cfasync="false"` attribute'u ekli (zaten eklendi).

## Adim 9: Nginx (CloudPanel) Ayarlari

CloudPanel > Sites > mcp.envest.com.tr > Vhost:

```nginx
location / {
    proxy_pass http://127.0.0.1:8001/;
    proxy_http_version 1.1;
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding on;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Authorization $http_authorization;
    proxy_connect_timeout 900;
    proxy_send_timeout 900;
    proxy_read_timeout 900;
}
```

**ONEMLI:** `proxy_buffering off;` olmadan SSE calismaz.

Static dosyalar icin symlink:
```bash
ln -sf /home/envest-mcp/htdocs/mcp.envest.com.tr/mcps/scada/src/scada_mcp/admin/static \
       /home/envest-mcp/htdocs/mcp.envest.com.tr/static
```

## Adim 10: Test

```bash
# Sunucudan
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/login
# 200

# Tunnel uzerinden
timeout 3 curl -s -N https://mcp.envest.com.tr/mcp/sse \
  -H "Authorization: Bearer <TOKEN>" 2>&1
# event: endpoint
# data: /mcp/messages/?session_id=...
```

Tarayicidan: `https://mcp.envest.com.tr/login`
- Kullanici: admin / admin (ilk giriste degistir!)

## Guncelleme

```bash
# Dosyalari rsync ile kopyala
rsync -avz --exclude='__pycache__' --exclude='*.pyc' --exclude='data/' --exclude='logs/' \
  D:/LiveProject/Envest-Mcp-Server/mcps/scada/ \
  root@SUNUCU_IP:/home/envest-mcp/htdocs/mcp.envest.com.tr/mcps/scada/

# Restart
ssh root@SUNUCU_IP "pm2 restart envest-mcp"
```

**NOT:** `data/` ve `logs/` dizinleri rsync'ten haric - tokens.json ve users.json korunur.

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

### 421 Misdirected Request
Cloudflare tunnel config'inde `httpHostHeader` eksik:
```yaml
originRequest:
  httpHostHeader: "127.0.0.1:8001"
```

### CSS bozuk
Cloudflare Rocket Loader'i kapat veya `data-cfasync="false"` attribute'u ekle.
Static symlink kontrol: `ls -la /home/envest-mcp/htdocs/mcp.envest.com.tr/static/`

### Token calismsiyor
Admin panelden yeni token olustur. Eski `/auth/mint` token'lari artik gecersiz.

### Sunucu baslamiyor
```bash
pm2 logs envest-mcp --lines 30
```

### Port kullaniliyor
```bash
ss -tlnp | grep 8001
kill -9 <PID>
```

### DB baglantisi basarisiz
Instance .env dosyasini kontrol et:
```bash
cat /home/envest-mcp/htdocs/mcp.envest.com.tr/mcps/scada/instances/<instance>/.env
```
