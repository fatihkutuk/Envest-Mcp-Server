FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config libcairo2-dev curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ src/

VOLUME /app/instances
EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/ || exit 1

# Multi-instance mode: tum instances/ altindaki MCP'leri yukler
# Token ile ayrim: SCADA token -> SCADA tools, KoruCAPS token -> KoruCAPS tools
CMD ["python", "-m", "scada_mcp.combined", "--host", "0.0.0.0", "--port", "8001", "--require-token"]
