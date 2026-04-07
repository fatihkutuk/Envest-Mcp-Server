"""
Track MCP SSE session IDs after the authenticated GET /sse handshake so that
POST /.../messages?session_id=... can succeed without repeating the bearer token.

The MCP protocol sends clients a relative POST URI without auth; LM Studio does not
attach Authorization to those POSTs, so BearerAuthMiddleware would reject them otherwise.

Also tracks which ASGI app owns each session so multi-instance dispatch can forward
POST /messages to the correct app (regular instance or merged MCP).
"""

from __future__ import annotations

import contextvars
import logging
import threading
import time
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

logger = logging.getLogger("scada_mcp.sse_session")

_lock = threading.Lock()
_sessions: dict[str, float] = {}          # hex -> expiry monotonic
_session_apps: dict[str, object] = {}     # hex -> ASGI app that owns this session
_DEFAULT_TTL_SEC = 900.0

_hook_installed = False

# Context variable: set by dispatch before forwarding GET /sse to an app.
# The SSE hook reads it to associate the session with the dispatching app.
current_dispatch_app: contextvars.ContextVar[object | None] = contextvars.ContextVar(
    "current_dispatch_app", default=None
)


def register_sse_session(session_id: UUID, *, ttl_sec: float = _DEFAULT_TTL_SEC) -> None:
    ttl = max(60.0, float(ttl_sec))
    key = session_id.hex
    app = current_dispatch_app.get(None)
    with _lock:
        _sessions[key] = time.monotonic() + ttl
        if app is not None:
            _session_apps[key] = app
    logger.debug("Registered SSE session %s (ttl=%.0fs, app=%s)", key, ttl, "yes" if app else "no")


def is_sse_session_authorized(session_id_hex: str | None) -> bool:
    if not session_id_hex:
        return False
    key = session_id_hex.strip().lower()
    if len(key) != 32:
        return False
    now = time.monotonic()
    with _lock:
        exp = _sessions.get(key)
        if exp is None:
            return False
        if now > exp:
            del _sessions[key]
            _session_apps.pop(key, None)
            logger.debug("SSE session %s expired", key)
            return False
        return True


def get_session_app(session_id_hex: str | None) -> object | None:
    """Return the ASGI app that owns this session, or None."""
    if not session_id_hex:
        return None
    key = session_id_hex.strip().lower()
    with _lock:
        return _session_apps.get(key)


def install_sse_session_hook() -> None:
    """Monkey-patch SseServerTransport.connect_sse once (mcp package)."""
    global _hook_installed
    if _hook_installed:
        return

    import mcp.server.sse as sse_mod

    _orig_connect = sse_mod.SseServerTransport.connect_sse
    _real_uuid4 = sse_mod.uuid4

    @asynccontextmanager
    async def _connect_sse_register(self: Any, scope: Any, receive: Any, send: Any):
        def uuid4_tracing() -> Any:
            sid = _real_uuid4()
            register_sse_session(sid)
            return sid

        sse_mod.uuid4 = uuid4_tracing
        try:
            async with _orig_connect(self, scope, receive, send) as streams:
                yield streams
        finally:
            sse_mod.uuid4 = _real_uuid4

    sse_mod.SseServerTransport.connect_sse = _connect_sse_register  # type: ignore[method-assign]
    _hook_installed = True
    logger.debug("SSE session hook installed")
