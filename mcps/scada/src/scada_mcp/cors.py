"""Optional CORS for browser Web UI -> MCP /files (cross-origin fetch + Bearer)."""

from __future__ import annotations

import logging
import os

from starlette.applications import Starlette

logger = logging.getLogger("scada_mcp.cors")


def add_cors_if_configured(app: Starlette) -> None:
    raw = (os.getenv("MCP_CORS_ORIGINS") or "").strip()
    if not raw:
        return
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if not origins:
        return
    from starlette.middleware.cors import CORSMiddleware

    logger.info("CORS enabled for origins: %s", origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
