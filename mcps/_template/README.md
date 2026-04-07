# Yeni MCP Ekleme Sablonu

Bu dizini kopyalayarak yeni bir MCP servisi olusturabilirsiniz.

## Adimlar

1. Bu dizini kopyalayin:
   ```bash
   cp -r mcps/_template mcps/yeni-mcp-ismi
   ```

2. Dil secimine gore Dockerfile'i secin:
   - Python: `mv Dockerfile.python Dockerfile && rm Dockerfile.node`
   - Node.js: `mv Dockerfile.node Dockerfile && rm Dockerfile.python`

3. MCP sunucunuzu implement edin (`src/` altinda)

4. `.env` dosyasini olusturun (gerekli credentials)

5. `docker-compose.yml`'a servisinizi ekleyin:
   ```yaml
   yeni-mcp:
     build: ./mcps/yeni-mcp-ismi
     env_file: ./mcps/yeni-mcp-ismi/.env
     ports:
       - "127.0.0.1:800X:8080"
     restart: unless-stopped
     networks:
       - envest-net
   ```

6. Nginx config'e location blogu ekleyin (`nginx/conf.d/mcp.envest.com.tr.conf`):
   ```nginx
   location /yeni-mcp/ {
       proxy_pass http://yeni-mcp:8080/;
       proxy_buffering off;
       proxy_cache off;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_read_timeout 300s;
       proxy_send_timeout 300s;
   }
   ```

7. Servisleri yeniden baslatin:
   ```bash
   docker-compose up -d --build yeni-mcp
   docker-compose restart nginx
   ```
