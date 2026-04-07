# Envest MCP Server

Birden fazla MCP (Model Context Protocol) sunucusunu tek bir Python sureci uzerinden, JWT token ile ayirarak sunan profesyonel platform.

## Mimari

```
mcp.envest.com.tr
        |
   Cloudflare Tunnel
        |
   Python Sunucu (:8001)
   FastMCP + Multi-Instance
        |
   +----+----------+-----------+-----------+
   |               |           |           |
SCADA          KoruCAPS     Database    Yeni MCP...
(korubin_main) (korucaps)  (test_db)   (instance)
   |               |           |           |
JWT token      JWT token    JWT token   JWT token
```

- **Tek sunucu, tek port** - tum MCP'ler ayni Python sureci uzerinde calisir
- **JWT token ile ayrim** - her instance'in kendi token'i var, ayni `/mcp/sse` endpoint'i
- **Admin panel** - web tabanli yonetim (kullanici, token, instance, skill yonetimi)
- **Toolpack sistemi** - SCADA, KoruCAPS, Database, Skills toolpack'leri
- **Skill sistemi** - domain bilgisi markdown paketleri (progressive disclosure)

## Toolpack Katalogu

| Toolpack | Aciklama | Tool Sayisi |
|----------|----------|-------------|
| `scada` | SCADA verileri (node, tag, log, alarm, DMA analizi) | ~40+ |
| `korucaps` | Grundfos pompa secimi, performans hesaplama | 6 |
| `database` | Genel DB analizi (sema, sorgu, istatistik, procedure, trigger, view) | 15 |
| `skills` | Domain bilgi paketleri (markdown) | 2 |

## Hizli Baslangic (Ubuntu)

Detayli rehber: [DEPLOY.md](DEPLOY.md)

```bash
# 1. Projeyi klonla
git clone <repo-url> /home/envest-mcp/htdocs/mcp.envest.com.tr
cd /home/envest-mcp/htdocs/mcp.envest.com.tr

# 2. Python bagimliliklar
cd mcps/scada && pip3 install -e . && pip3 install bcrypt && cd ../..

# 3. Dizinler
mkdir -p logs data

# 4. pm2 ile baslat
pm2 start ecosystem.config.js
pm2 save && pm2 startup

# 5. Cloudflare Tunnel ayarla (DEPLOY.md'ye bak)

# 6. Admin panele gir
# https://mcp.envest.com.tr/login
# Varsayilan: admin / admin (hemen degistir!)
```

## MCP Client Baglantisi

Admin panelden token olustur, LM Studio / Claude Desktop / Cursor'a ekle:

```json
{
  "mcpServers": {
    "envest": {
      "url": "https://mcp.envest.com.tr/mcp/sse",
      "headers": {
        "Authorization": "Bearer <TOKEN>"
      }
    }
  }
}
```

## Admin Panel

`https://mcp.envest.com.tr/login` adresinden erisim.

| Sayfa | Aciklama |
|-------|----------|
| Dashboard | Instance, token, kullanici sayilari |
| Instances | MCP instance listesi, olustur, duzenle, sil |
| Tokens | Token yonetimi (olustur, duzenle, sil, JWT goster, config ornekleri) |
| Skills | Domain bilgi dosyalari yonetimi (olustur, duzenle, sil) |
| Users | Kullanici yonetimi, profil, sifre degistirme |

## Yeni MCP Ekleme

1. Admin panel > Instances > Yeni Instance
2. Toolpack sec (scada, korucaps, database, vb.)
3. DB bilgilerini gir
4. Tokens > Yeni Token Olustur, instance sec
5. Token'i MCP client'a ekle

## Proje Yapisi

```
mcps/scada/
├── src/scada_mcp/
│   ├── combined.py          # Ana giris noktasi (multi-instance)
│   ├── multi_mcp.py         # JWT token routing
│   ├── auth.py              # JWT mint/verify
│   ├── db.py                # DB baglanti havuzu
│   ├── config.py            # Instance config yukleme
│   ├── server_factory.py    # FastMCP server olusturma
│   ├── admin/               # Admin panel (Starlette + Jinja2)
│   │   ├── app.py           # Route handler'lar
│   │   ├── store.py         # users.json + tokens.json CRUD
│   │   ├── auth_session.py  # Session yonetimi
│   │   ├── templates/       # HTML template'ler
│   │   └── static/          # CSS, JS, Tailwind
│   ├── toolpacks/           # SCADA tool paketleri
│   ├── korucaps/            # KoruCAPS pompa secim
│   ├── database_tools/      # Database analiz
│   └── skills/              # Skill sistemi
├── instances/               # MCP instance yapilandirmalari
│   ├── korubin_main/        # SCADA instance
│   ├── korucaps/            # KoruCAPS instance
│   ├── CorumScada/          # Corum SCADA instance
│   └── test_database/       # Database instance
├── skills/                  # Global skill dosyalari
│   └── korubin-scada/       # SCADA domain bilgisi
├── data/                    # users.json, tokens.json
└── pyproject.toml
```

## Lisans

Envest Enerji - Tum haklari saklidir.
