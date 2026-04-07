# Ubuntu Sunucu Deployment Rehberi

## Gereksinimler

- Ubuntu 22.04 LTS veya 24.04 LTS
- Minimum 2 GB RAM, 2 CPU
- 20 GB disk alani
- Domain DNS: `mcp.envest.com.tr` -> sunucu public IP

## Adim 1: Sunucu Hazirligi

```bash
# Sistem guncelleme
sudo apt update && sudo apt upgrade -y

# Projeyi klonla
sudo git clone <repo-url> /opt/envest-mcp
cd /opt/envest-mcp

# Kurulum scriptini calistir
sudo bash scripts/setup.sh
```

Bu script sunlari yapar:
- Docker Engine ve Docker Compose kurar
- UFW firewall yapilandirir (22, 80, 443 portlari acik)
- .env sablonlarini olusturur

## Adim 2: Yapilandirma

### Global (.env)
```bash
cd /opt/envest-mcp
nano .env
```

### SCADA MCP
```bash
cp mcps/scada/instances/_template/.env.example mcps/scada/instances/korubin_main/.env
nano mcps/scada/instances/korubin_main/.env
```

Zorunlu degerler:
```
DB_HOST=<mysql-sunucu-ip>
DB_PORT=3306
DB_NAME=kbindb
DB_USERNAME=<kullanici>
DB_PASSWORD=<sifre>
MCP_ADMIN_SECRET=<guclu-rastgele-anahtar>
MCP_TOKEN_SECRET=<guclu-rastgele-anahtar>
MCP_PUBLIC_BASE_URL=https://mcp.envest.com.tr/scada
```

Guclu anahtar olusturmak icin:
```bash
openssl rand -hex 32
```

### SCADA Instance YAML
```bash
nano mcps/scada/instances/korubin_main/instance.yaml
```

`mcp_public_base_url` degerini `https://mcp.envest.com.tr/scada` olarak ayarlayin.

### KoruCAPS MCP
```bash
cp mcps/korucaps/.env.example mcps/korucaps/.env
nano mcps/korucaps/.env
```

Zorunlu degerler:
```
WINCAPS_DB_HOST=<mysql-sunucu-ip>
WINCAPS_DB_PORT=3306
WINCAPS_DB_NAME=wincaps72
WINCAPS_DB_USER=<kullanici>
WINCAPS_DB_PASSWORD=<sifre>
KORUCAPS_TOKEN=<guclu-bearer-token>
MCP_PORT=8002
```

## Adim 3: SSL Sertifikasi

### Cloudflare (Onerilen)

1. Cloudflare Dashboard > DNS:
   - A kaydi: `mcp` -> `<sunucu-ip>` (Proxied/turuncu bulut)

2. SSL/TLS > Origin Server > Create Certificate:
   - Hostnames: `mcp.envest.com.tr`
   - Certificate Validity: 15 yil

3. Sertifika dosyalarini kaydedin:
   ```bash
   mkdir -p /opt/envest-mcp/certs
   nano /opt/envest-mcp/certs/origin.pem   # Certificate icerigi yapistir
   nano /opt/envest-mcp/certs/origin.key   # Private Key icerigi yapistir
   chmod 600 /opt/envest-mcp/certs/origin.key
   ```

4. Cloudflare SSL/TLS > Overview:
   - SSL mode: **Full (Strict)**

### Let's Encrypt

```bash
bash scripts/ssl-setup.sh letsencrypt
```

Nginx config'de:
- Cloudflare satirlarini yoruma alin
- Let's Encrypt satirlarini etkinlestirin

```bash
nano nginx/conf.d/mcp.envest.com.tr.conf
```

## Adim 4: Servisleri Baslat

```bash
cd /opt/envest-mcp

# Build ve baslat
docker compose up -d --build

# Durumu kontrol et
docker compose ps

# Log'lari izle
docker compose logs -f
```

## Adim 5: Dogrulama

```bash
# Gateway
curl https://mcp.envest.com.tr/
# Beklenen: {"service":"Envest MCP Gateway","endpoints":["/scada/","/korucaps/"]}

# SCADA health
curl https://mcp.envest.com.tr/scada/
# Beklenen: 200 OK

# KoruCAPS health
curl https://mcp.envest.com.tr/korucaps/
# Beklenen: JSON info response

# SCADA token al
curl -X POST https://mcp.envest.com.tr/scada/auth/mint \
  -H "X-Admin-Secret: <admin-secret>"
# Beklenen: {"token":"v1...","ttl_sec":900}
```

## Adim 6: Otomatik Baslama

Docker servislerinin sunucu yeniden basladiginda otomatik baslamasini saglayin:

```bash
sudo systemctl enable docker
```

`docker compose` servisleri `restart: unless-stopped` ile tanimlanmistir, Docker basladiginda otomatik baslar.

## Adim 7: Yedekleme Cron'u

```bash
# Yedekleme dizini olustur
sudo mkdir -p /backups/envest-mcp

# Her gece 02:00'de yedekle
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/envest-mcp/scripts/backup.sh /backups/envest-mcp") | crontab -
```

## Guncelleme

```bash
cd /opt/envest-mcp

# Yeni kodu cek
git pull

# Yeniden build ve deploy
docker compose up -d --build

# Sadece belirli bir servisi guncelle
docker compose up -d --build scada-mcp
```

## Izleme

### Container durumlari
```bash
docker compose ps
```

### Canli loglar
```bash
# Tum servisler
docker compose logs -f

# Belirli servis
docker compose logs -f scada-mcp
docker compose logs -f korucaps-mcp
docker compose logs -f nginx
```

### Kaynak kullanimi
```bash
docker stats
```

### Disk kullanimi
```bash
docker system df
# Temizlik icin:
docker system prune -f
```
