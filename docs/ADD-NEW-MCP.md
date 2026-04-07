# Yeni MCP Sunucusu Ekleme Rehberi

Bu rehber, Envest MCP altyapisina yeni bir MCP sunucusu eklemeyi adim adim aciklar.

## Onkosullar

- Docker ve Docker Compose kurulu
- Projenin calisan bir deployment'i mevcut
- Yeni MCP'nin ihtiyac duydugu veritabani/servisler erisilebilir durumda

## Adim 1: Sablon Olustur

```bash
cd /opt/envest-mcp
bash scripts/add-mcp.sh <mcp-adi> <python|node>
```

Ornek:
```bash
bash scripts/add-mcp.sh enerji-izleme python
bash scripts/add-mcp.sh hava-api node
```

Bu komut `mcps/<mcp-adi>/` altinda secilen dile uygun bir sablon olusturur.

## Adim 2: MCP Sunucusunu Implement Et

### Python (FastMCP)

```python
# mcps/<mcp-adi>/src/main.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("enerji-izleme")

@mcp.tool()
def get_energy_data(station_id: int, date: str) -> dict:
    """Belirtilen istasyon icin enerji verisini getirir."""
    # DB sorgusu ve is mantigi
    return {"station_id": station_id, "date": date, "kwh": 1234.5}

if __name__ == "__main__":
    import uvicorn
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount

    sse = SseServerTransport("/messages/")
    app = Starlette(routes=[
        Route("/sse", endpoint=sse.handle_sse_connection),
        Mount("/messages/", app=sse.handle_post_message),
        Route("/", endpoint=lambda r: JSONResponse({"service": "enerji-izleme"})),
    ])
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### Node.js (@modelcontextprotocol/sdk)

```typescript
// mcps/<mcp-adi>/src/index.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { z } from "zod";
import http from "http";

const server = new McpServer({ name: "hava-api", version: "1.0.0" });

server.tool("get_weather", { city: z.string() }, async ({ city }) => ({
  content: [{ type: "text", text: JSON.stringify({ city, temp: 22 }) }],
}));

// HTTP SSE server setup...
```

## Adim 3: Ortam Degiskenleri

```bash
nano mcps/<mcp-adi>/.env
```

Minimum:
```
# Veritabani (gerekiyorsa)
DB_HOST=xxx
DB_PORT=3306
DB_NAME=xxx
DB_USER=xxx
DB_PASSWORD=xxx

# Kimlik dogrulama
BEARER_TOKEN=<guclu-token>

# Port
MCP_PORT=8080
```

## Adim 4: docker-compose.yml'a Ekle

`docker-compose.yml` dosyasina yeni servis ekleyin:

```yaml
services:
  # ... mevcut servisler ...

  enerji-izleme:
    build:
      context: ./mcps/enerji-izleme
      dockerfile: Dockerfile
    container_name: envest-enerji-izleme
    env_file:
      - ./mcps/enerji-izleme/.env
    ports:
      - "127.0.0.1:8003:8080"
    restart: unless-stopped
    networks:
      - envest-net
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

Port numarasini mevcut servislerle cakismayacak sekilde secin (8003, 8004, ...).

## Adim 5: Nginx Location Blogu

`nginx/conf.d/mcp.envest.com.tr.conf` dosyasina ekleyin:

```nginx
# --- Enerji Izleme MCP ---
location /enerji-izleme/ {
    proxy_pass http://enerji-izleme:8080/;
    proxy_http_version 1.1;
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding on;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Authorization $http_authorization;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
    proxy_connect_timeout 10s;
}
```

## Adim 6: Deploy

```bash
# Yeni servisi build et ve baslat
docker compose up -d --build enerji-izleme

# Nginx'i yeniden baslat (yeni location icin)
docker compose restart nginx

# Kontrol et
docker compose ps
curl https://mcp.envest.com.tr/enerji-izleme/
```

## Adim 7: MCP Client Yapilandirmasi

```json
{
  "mcpServers": {
    "envest-enerji-izleme": {
      "url": "https://mcp.envest.com.tr/enerji-izleme/sse",
      "headers": {
        "Authorization": "Bearer <token>"
      }
    }
  }
}
```

## Kontrol Listesi

- [ ] MCP sunucusu implement edildi
- [ ] .env dosyasi olusturuldu (hassas bilgiler)
- [ ] Dockerfile calisiyor (`docker build` basarili)
- [ ] docker-compose.yml'a servis eklendi
- [ ] Nginx config'e location eklendi
- [ ] `docker compose up -d --build` basarili
- [ ] Health check endpointi calisiyor
- [ ] SSE baglantisi calisiyor
- [ ] Bearer token dogrulamasi calisiyor
- [ ] MCP client'tan araclar gorunuyor
