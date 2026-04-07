# Mimari Belgeleri

## Genel Bakis

Envest MCP Server, birden fazla Model Context Protocol (MCP) sunucusunu tek bir domain altinda birlestiren bir gateway mimarisi kullanir.

```
Internet
    |
Cloudflare (opsiyonel DDoS + SSL)
    |
Nginx (SSL sonlandirma + reverse proxy)
    |
Docker Network (envest-net)
    |
+---+---+---+---+
|       |       |
SCADA  CAPS  Yeni...
:8001  :8002  :800X
```

## Bilesenler

### Nginx (Gateway)

- SSL sonlandirma (Cloudflare Origin Cert veya Let's Encrypt)
- Path-based routing: `/scada/` -> SCADA MCP, `/korucaps/` -> KoruCAPS MCP
- SSE/streaming desteği: `proxy_buffering off`
- WebSocket upgrade desteği (gelecek streamable-http icin)
- 300 saniye proxy timeout (uzun sureli sorgular icin)

### SCADA MCP (Python)

**Teknoloji**: FastMCP + Starlette + Uvicorn + PyMySQL
**Port**: 8001
**Transport**: SSE + Streamable HTTP (hybrid)

**Coklu Instance**:
- Her instance kendi DB, token secret, tool prefix'ine sahip
- JWT `sub` claim'i ile dogru instance'a yonlendirilir
- `instances/` dizininde yapilandirma

**Tool Organizasyonu**:
```
toolpacks/
├── scada_core.py       # Manifest, routing, lexicon
├── scada_nodes.py      # Node CRUD + arama
├── scada_tags.py       # Tag islemleri
├── scada_logs.py       # Log sorgulama
├── scada_devices.py    # Device profilleri
├── scada_alarms.py     # Alarm yonetimi
├── scada_dashboard.py  # Dashboard ozet
├── scada_charts.py     # Chart verileri
├── scada_dma.py        # DMA analizi
├── scada_exports.py    # Rapor export
├── scada_analytics.py  # Trend analizi
└── ai_registry.py      # AI modul registry
```

**Kimlik Dogrulama**:
- JWT v1 format: `v1.{payload}.{signature}`
- HMAC-SHA256 imzalama
- Admin secret ile token olusturma (`/auth/mint`)
- Dosya indirme tokenleri (query param olarak)

### KoruCAPS MCP (TypeScript)

**Teknoloji**: @modelcontextprotocol/sdk + mysql2 + Zod
**Port**: 8002
**Transport**: SSE

**Toollar**:
- `search_pumps` - Pompa arama (WinCAPS algoritma)
- `calculate_operating_point` - Calisma noktasi hesaplama
- `get_pump_details` - Teknik ozellikler
- `get_pump_curve_data` - Q-H, Q-P, Q-eta egrileri
- `list_applications` - Uygulama kategorileri
- `list_pump_families` - Pompa aileleri

**Algoritma**: Grundfos WinCAPS DLL'den reverse-engineered pompa secim algoritmasi:
- Filtre tablosu sorgusu → Aday secimi
- Polinom egri degerlendirmesi
- Iteratif motor slip hesaplama
- Tolerans harmanlamasi (SP serisi %80/%20)
- Enerji bazli siralama

**Kimlik Dogrulama**: Bearer token (environment variable)

## Docker Agi

Tum containerlar `envest-net` bridge aginda iletisim kurar:
- Nginx → `scada-mcp:8001`, `korucaps-mcp:8002`
- Sadece Nginx disariya acik (80, 443)
- MCP containerlar `127.0.0.1` uzerinde (dis erisim yok)

## Veri Akisi

```
MCP Client (Claude/Cursor)
    |
    | HTTPS + Bearer Token
    v
Nginx (SSL + /path routing)
    |
    | HTTP + Authorization header
    v
MCP Server (SCADA veya KoruCAPS)
    |
    | PyMySQL / mysql2
    v
MySQL/MariaDB (dis sunucu)
```

## Yeni MCP Ekleme Akisi

1. `mcps/_template/` kopyala
2. Dockerfile, kaynak kod, .env olustur
3. `docker-compose.yml`'a servis ekle
4. `nginx/conf.d/mcp.envest.com.tr.conf`'a location ekle
5. `docker compose up -d --build <yeni-mcp> && docker compose restart nginx`

Her yeni MCP bagimsiz bir container olarak calisir. Dil kisitlamasi yoktur.
