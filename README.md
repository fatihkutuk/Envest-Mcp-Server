# Envest MCP Server

Envest SCADA ve KoruCAPS MCP sunucularini tek bir domain altinda (`mcp.envest.com.tr`) birlestiren, Docker tabanli, production-ready altyapi.

## Mimari

```
mcp.envest.com.tr
        |
   Nginx (SSL + Reverse Proxy)
        |
   Tek Python Sunucu (:8001)
   FastMCP + Multi-Instance
        |
   +----+----------+-----------+
   |               |           |
SCADA          KoruCAPS     Yeni MCP...
(korubin_main) (korucaps)   (yeni_instance)
   |               |           |
JWT token      JWT token    JWT token
sub=korubin_main sub=korucaps sub=yeni_instance
```

- **Tek sunucu, tek port** - tum MCP'ler ayni Python sureci uzerinde calisir
- **JWT token ile ayrim** - her instance'in kendi token'i var, ayni `/mcp/` endpointi
- **SCADA** instance: node/tag/log sorgulama, DMA analizi, alarm yonetimi, rapor export
- **KoruCAPS** instance: Grundfos pompa secimi, performans hesaplama, egri analizi
- **Yeni MCP eklemek**: `instances/` altina klasor kopyala, config degistir, sunucuyu yeniden baslat

## Hizli Baslangic

### Gereksinimler

- Ubuntu 22.04+ (veya Docker destekleyen herhangi bir Linux)
- Docker Engine 24+
- Docker Compose v2+
- Domain DNS kaydi (mcp.envest.com.tr -> sunucu IP)

### Kurulum

```bash
# 1. Projeyi klonlayin
git clone <repo-url> /opt/envest-mcp
cd /opt/envest-mcp

# 2. Sunucu kurulumu (Docker, firewall, vb.)
sudo bash scripts/setup.sh

# 3. Ortam degiskenlerini yapilandirin
cp .env.example .env
nano .env

# SCADA instance
cp mcps/scada/instances/_template/.env.example mcps/scada/instances/korubin_main/.env
nano mcps/scada/instances/korubin_main/.env

# KoruCAPS
cp mcps/korucaps/.env.example mcps/korucaps/.env
nano mcps/korucaps/.env

# 4. SSL sertifikasi
# Cloudflare icin:
bash scripts/ssl-setup.sh cloudflare
# veya Let's Encrypt icin:
bash scripts/ssl-setup.sh letsencrypt

# 5. Servisleri baslatin
docker compose up -d --build

# 6. Durumu kontrol edin
docker compose ps
curl https://mcp.envest.com.tr/
```

## Endpoint Tablosu

Tum MCP'ler ayni URL uzerinden, farkli JWT token'larla erisilir:

| Endpoint | Aciklama | Kimlik Dogrulama |
|----------|----------|-----------------|
| `https://mcp.envest.com.tr/` | Instance yonetim paneli | - |
| `https://mcp.envest.com.tr/mcp/sse` | MCP SSE endpoint (tum instance'lar) | Bearer Token |
| `https://mcp.envest.com.tr/auth/mint` | Token olusturma | X-Admin-Secret |
| `https://mcp.envest.com.tr/files/...` | Export dosya indirme | Bearer/Download Token |

## MCP Client Yapilandirma Ornekleri

### Claude Desktop / Cursor / LM Studio - SCADA

```json
{
  "mcpServers": {
    "envest-scada": {
      "url": "https://mcp.envest.com.tr/mcp/sse",
      "headers": {
        "Authorization": "Bearer <scada-token>"
      }
    }
  }
}
```

### Claude Desktop / Cursor / LM Studio - KoruCAPS

```json
{
  "mcpServers": {
    "envest-korucaps": {
      "url": "https://mcp.envest.com.tr/mcp/sse",
      "headers": {
        "Authorization": "Bearer <korucaps-token>"
      }
    }
  }
}
```

> **NOT:** URL ayni (`/mcp/sse`). Fark sadece Bearer token'da. Token'daki `sub` claim'i hangi instance'a yonlendirilecegini belirler.

### Token Alma

```bash
# SCADA token
curl -X POST https://mcp.envest.com.tr/auth/mint \
  -H "X-Admin-Secret: <scada-admin-secret>" \
  -d '{"instance":"korubin_main"}'

# KoruCAPS token
curl -X POST https://mcp.envest.com.tr/auth/mint \
  -H "X-Admin-Secret: <korucaps-admin-secret>" \
  -d '{"instance":"korucaps"}'
```

## Ortam Degiskenleri

### Global (.env)

| Degisken | Aciklama | Varsayilan |
|----------|----------|-----------|
| `DOMAIN` | Domain adi | mcp.envest.com.tr |
| `SSL_MODE` | SSL modu | cloudflare |

### SCADA MCP (mcps/scada/instances/<instance>/.env)

| Degisken | Aciklama |
|----------|----------|
| `DB_HOST` | MySQL sunucu adresi |
| `DB_PORT` | MySQL port |
| `DB_NAME` | Veritabani adi |
| `DB_USERNAME` | DB kullanici adi |
| `DB_PASSWORD` | DB sifre |
| `MCP_ADMIN_SECRET` | Admin kimlik dogrulama anahtari |
| `MCP_TOKEN_SECRET` | JWT imzalama anahtari |
| `MCP_PUBLIC_BASE_URL` | Public URL (export linkleri icin) |

### KoruCAPS MCP (mcps/korucaps/.env)

| Degisken | Aciklama |
|----------|----------|
| `WINCAPS_DB_HOST` | WinCaps MySQL sunucu |
| `WINCAPS_DB_PORT` | MySQL port |
| `WINCAPS_DB_NAME` | Veritabani adi (wincaps72) |
| `WINCAPS_DB_USER` | DB kullanici |
| `WINCAPS_DB_PASSWORD` | DB sifre |
| `KORUCAPS_TOKEN` | Bearer kimlik dogrulama tokeni |
| `MCP_PORT` | Sunucu portu (8002) |

## Yeni MCP Ekleme

Yeni bir MCP sunucusu eklemek 5 adimda yapilir:

```bash
# 1. Sablon olustur
bash scripts/add-mcp.sh enerji-izleme python
# veya
bash scripts/add-mcp.sh hava-durumu node

# 2. MCP'nizi implement edin
#    mcps/enerji-izleme/src/ altinda

# 3. .env dosyasi olusturun
#    mcps/enerji-izleme/.env

# 4. docker-compose.yml'a servis ekleyin
# 5. nginx config'e location blogu ekleyin

# 6. Deploy
docker compose up -d --build enerji-izleme
docker compose restart nginx
```

Detayli rehber: [docs/ADD-NEW-MCP.md](docs/ADD-NEW-MCP.md)

## SCADA Instance Yonetimi

SCADA MCP coklu instance destekler. Yeni bir SCADA instance eklemek icin:

```bash
# Template'i kopyala
cp -r mcps/scada/instances/_template mcps/scada/instances/yeni-saha

# Yapilandirma dosyalarini duzenle
nano mcps/scada/instances/yeni-saha/instance.yaml
nano mcps/scada/instances/yeni-saha/.env

# Container'i yeniden baslat
docker compose restart scada-mcp
```

Her instance kendi DB baglantisi, token secret'i ve tool prefix'ine sahiptir.

## SSL Yapilandirmasi

### Secenek 1: Cloudflare (Onerilen)

1. Cloudflare'de DNS A kaydi ekleyin: `mcp.envest.com.tr` -> sunucu IP
2. Cloudflare proxy'yi etkinlestirin (turuncu bulut)
3. SSL/TLS > Origin Server > Create Certificate
4. Sertifikayi `certs/origin.pem` ve `certs/origin.key` olarak kaydedin
5. SSL modunu "Full (Strict)" yapin

### Secenek 2: Let's Encrypt

```bash
bash scripts/ssl-setup.sh letsencrypt
```

Nginx config'de Let's Encrypt satirlarini etkinlestirin (Cloudflare satirlarini yoruma alin).

## Yedekleme

```bash
# Manuel yedekleme
bash scripts/backup.sh /backups/envest-mcp

# Cron ile otomatik (her gece 02:00)
echo "0 2 * * * /opt/envest-mcp/scripts/backup.sh /backups/envest-mcp" | crontab -
```

## Sorun Giderme

### Container durumu kontrol
```bash
docker compose ps
docker compose logs scada-mcp --tail 50
docker compose logs korucaps-mcp --tail 50
docker compose logs nginx --tail 50
```

### Container'i yeniden baslat
```bash
docker compose restart scada-mcp
docker compose restart korucaps-mcp
```

### Tamamen yeniden build
```bash
docker compose down
docker compose up -d --build
```

### SSE baglantisi test
```bash
# SCADA
curl -N -H "Authorization: Bearer <token>" \
  https://mcp.envest.com.tr/scada/mcp/sse

# KoruCAPS
curl -N -H "Authorization: Bearer <token>" \
  https://mcp.envest.com.tr/korucaps/sse
```

### Port cakismasi
```bash
# Hangi portlar kullaniliyor
ss -tlnp | grep -E '800[0-9]'
```

## Dizin Yapisi

```
Envest-Mcp-Server/
├── README.md                       # Bu dosya
├── docker-compose.yml              # Tum servisler
├── docker-compose.dev.yml          # Dev override
├── .env.example                    # Global ortam degiskenleri
├── .gitignore
├── nginx/                          # Reverse proxy
│   ├── nginx.conf
│   └── conf.d/
│       └── mcp.envest.com.tr.conf
├── mcps/                           # MCP sunuculari
│   ├── scada/                      # SCADA MCP (Python)
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── src/scada_mcp/         # Kaynak kod
│   │   └── instances/              # SCADA instance'lari
│   ├── korucaps/                   # KoruCAPS MCP (TypeScript)
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── src/                    # Kaynak kod
│   └── _template/                  # Yeni MCP sablonu
├── scripts/                        # Otomasyon
│   ├── setup.sh                    # Sunucu kurulum
│   ├── ssl-setup.sh                # SSL kurulum
│   ├── add-mcp.sh                  # Yeni MCP ekleme
│   └── backup.sh                   # Yedekleme
├── certs/                          # SSL sertifikalari (git-ignored)
└── docs/                           # Belgeler
    ├── DEPLOYMENT.md
    ├── ADD-NEW-MCP.md
    └── ARCHITECTURE.md
```

## Lisans

Envest Enerji - Tum haklari saklidir.
