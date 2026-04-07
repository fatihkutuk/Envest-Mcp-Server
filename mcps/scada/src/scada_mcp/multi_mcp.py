"""
Serve multiple FastMCP streamable-http apps on one URL (/mcp). JWT claim sub = instance_id;
each instance uses its own MCP_TOKEN_SECRET for HMAC.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from .auth import TokenError, peek_sub_unverified, verify_token, verify_token_with_registry
from .sse_session import current_dispatch_app, get_session_app, is_sse_session_authorized

logger = logging.getLogger("scada_mcp.dispatch")


def _extract_bearer_token(request: Request) -> str:
    token = ""
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
    else:
        for hdr in ("x-access-token", "X-Access-Token"):
            xt = (request.headers.get(hdr) or "").strip()
            if xt:
                token = xt.split(" ", 1)[1].strip() if xt.lower().startswith("bearer ") else xt
                break
        if not token:
            qp = request.query_params
            token = (qp.get("access_token") or qp.get("token") or "").strip()
            if token.lower().startswith("bearer "):
                token = token.split(" ", 1)[1].strip()
    while token.lower().startswith("bearer "):
        token = token[7:].strip()
    return token


def discover_instance_paths(instances_dir: Any) -> list[Any]:
    from pathlib import Path

    p = Path(instances_dir)
    out: list[Any] = []
    if not p.is_dir():
        return out
    for child in sorted(p.iterdir()):
        if not child.is_dir() or child.name.startswith(".") or child.name == "_template":
            continue
        if (child / "instance.yaml").exists() or (child / "instance.yml").exists() or (child / "instance.json").exists():
            out.append(child)
    return out


class MultiMcpDispatchASGI:
    """One ASGI app: verify Bearer JWT (registry by sub) and forward to the matching streamable_http app."""

    def __init__(
        self,
        *,
        apps_by_sub: dict[str, ASGIApp],
        secret_registry: dict[str, str],
        token_store: Any | None = None,
        instances_dir: Any | None = None,
        max_concurrency_by_sub: dict[str, int] | None = None,
        wait_ms_by_sub: dict[str, int] | None = None,
    ) -> None:
        # Dict references are updated in-place (combined hot-reload); do not reassign.
        self._apps = apps_by_sub
        self._registry = secret_registry
        self._token_store = token_store
        self._instances_dir = instances_dir
        self._merged_cache: dict[str, object] = {}
        self._merged_lock = asyncio.Lock()
        self._locks: dict[str, asyncio.Semaphore] = {}
        self._max_by_sub = max_concurrency_by_sub or {}
        self._wait_ms_by_sub = wait_ms_by_sub or {}
        # Default: behave like a normal web backend (handle bursts without errors).
        self._default_max_concurrency = 16
        # Default: no timeout -> queue instead of returning 429.
        self._default_wait_ms = 0

    def _post_messages_authorized_by_session(self, request: Request) -> bool:
        """Allow POST /messages with a registered SSE session_id (no bearer needed)."""
        if request.method != "POST":
            return False
        path = request.url.path
        if "/messages" not in path:
            return False
        sid = request.query_params.get("session_id")
        if is_sse_session_authorized(sid):
            logger.debug("SSE session auth OK session_id=%s", sid)
            return True
        return False

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            logger.warning("dispatch: non-http scope type=%s, rejecting", scope["type"])
            resp = JSONResponse({"error": "unsupported"}, status_code=500)
            await resp(scope, receive, send)
            return

        request = Request(scope)
        method = request.method
        path = scope.get("path") or ""
        t0 = time.monotonic()

        logger.debug(
            "dispatch: %s %s content-type=%s",
            method, path,
            request.headers.get("content-type", "-"),
        )

        if method == "OPTIONS":
            logger.debug("dispatch: OPTIONS -> 200")
            await Response(status_code=200)(scope, receive, send)
            return

        # --- Path normalization: Mount("/mcp") strips prefix, path may be "" or "/" ---
        if not path or path == "":
            scope = dict(scope)
            scope["path"] = "/"
            scope["raw_path"] = b"/"
            logger.debug("dispatch: normalized empty path -> /")

        # --- SSE session auth bypass for POST /messages ---
        if self._post_messages_authorized_by_session(request):
            sid = request.query_params.get("session_id", "")
            # Look up which app owns this session
            owner_app = get_session_app(sid)
            if owner_app is not None:
                logger.debug("dispatch: SSE session POST -> owner app (session=%s)", sid[:12])
                await owner_app(scope, receive, send)
                return
            # Fallback: try all regular apps (backward compat for sessions without app tracking)
            for sub, inner in self._apps.items():
                logger.debug("dispatch: SSE session POST fallback to sub=%s", sub)
                await inner(scope, receive, send)
                return
            resp = JSONResponse({"error": "no instance available"}, status_code=503)
            await resp(scope, receive, send)
            return

        token = _extract_bearer_token(request)
        if not token:
            logger.warning(
                "dispatch: missing bearer token method=%s path=%s user-agent=%s",
                method, path,
                request.headers.get("user-agent", "-"),
            )
            resp = JSONResponse({"error": "missing bearer token"}, status_code=401)
            await resp(scope, receive, send)
            return

        # --- New flow: token_id (tok_) based routing ---
        sub_hint = peek_sub_unverified(token)
        if self._token_store and sub_hint.startswith("tok_"):
            record = self._token_store.get_token(sub_hint)
            if record is not None:
                if record.get("revoked"):
                    logger.warning("dispatch: revoked token sub=%s", sub_hint)
                    resp = JSONResponse({"error": "token revoked"}, status_code=401)
                    await resp(scope, receive, send)
                    return

                if record.get("expires_at"):
                    from datetime import datetime, timezone as _tz

                    exp = datetime.fromisoformat(record["expires_at"])
                    if exp.replace(tzinfo=_tz.utc) < datetime.now(_tz.utc):
                        logger.warning("dispatch: expired token sub=%s", sub_hint)
                        resp = JSONResponse({"error": "token expired"}, status_code=401)
                        await resp(scope, receive, send)
                        return

                # Valid record - verify signature with per-token secret
                try:
                    claims = verify_token(token_secret=record["token_secret"], token=token)
                except TokenError as e:
                    logger.warning("dispatch: token verification failed sub=%s: %s", sub_hint, e)
                    resp = JSONResponse({"error": "invalid token", "detail": str(e)}, status_code=401)
                    await resp(scope, receive, send)
                    return

                allowed = record["allowed_instances"]
                valid_instances = [iid for iid in allowed if iid in self._apps]

                if not valid_instances:
                    logger.warning("dispatch: no valid instances for token sub=%s allowed=%s", sub_hint, allowed)
                    resp = JSONResponse(
                        {"error": "no valid instances", "detail": "none of the allowed instances are available"},
                        status_code=404,
                    )
                    await resp(scope, receive, send)
                    return

                if len(valid_instances) == 1:
                    inner = self._apps[valid_instances[0]]
                    logger.debug("dispatch: tok_ single instance %s -> %s", sub_hint, valid_instances[0])
                    token_cd = current_dispatch_app.set(inner)
                    try:
                        await inner(scope, receive, send)
                    finally:
                        current_dispatch_app.reset(token_cd)
                    return
                else:
                    merged = await self._get_or_create_merged(valid_instances)
                    logger.debug("dispatch: tok_ merged instances %s -> %s", sub_hint, valid_instances)
                    token_cd = current_dispatch_app.set(merged)
                    try:
                        await merged(scope, receive, send)
                    finally:
                        current_dispatch_app.reset(token_cd)
                    return
            # record is None -> fall through to legacy flow
            logger.debug("dispatch: tok_ sub=%s not in token_store, falling through to legacy", sub_hint)

        # --- Legacy flow: sub = instance_id, verified via secret registry ---
        try:
            claims = verify_token_with_registry(token=token, registry=self._registry)
        except TokenError as e:
            logger.warning("dispatch: invalid token: %s", e)
            resp = JSONResponse({"error": "invalid token", "detail": str(e)}, status_code=401)
            await resp(scope, receive, send)
            return

        sub = str(claims.get("sub") or "").strip()
        inner = self._apps.get(sub)
        if inner is None:
            logger.warning("dispatch: unknown sub=%r, available=%s", sub, list(self._apps.keys()))
            resp = JSONResponse(
                {"error": "unknown instance", "detail": f"no MCP for sub={sub!r}"},
                status_code=404,
            )
            await resp(scope, receive, send)
            return

        sem = self._locks.get(sub)
        if sem is None:
            mc = int(self._max_by_sub.get(sub) or 0) or self._default_max_concurrency
            # Keep bounded, but allow meaningful parallelism under load.
            mc = max(1, min(64, mc))
            sem = asyncio.Semaphore(mc)
            self._locks[sub] = sem

        # Concurrency guard:
        # - wait_ms <= 0: queue (no errors)
        # - wait_ms  > 0: wait up to that time, then 429
        wait_ms = int(self._wait_ms_by_sub.get(sub) or 0) or self._default_wait_ms
        wait_ms = max(0, min(120_000, wait_ms))

        # Try immediate acquire.
        acquired = False
        if getattr(sem, "_value", 0) > 0:
            try:
                await asyncio.wait_for(sem.acquire(), timeout=0.01)
                acquired = True
            except asyncio.TimeoutError:
                acquired = False
        if not acquired:
            if wait_ms > 0:
                timeout = wait_ms / 1000.0
                try:
                    await asyncio.wait_for(sem.acquire(), timeout=timeout)
                    acquired = True
                except asyncio.TimeoutError:
                    acquired = False
            else:
                await sem.acquire()
                acquired = True
        if not acquired:
            logger.warning("dispatch: 429 busy sub=%s", sub)
            resp = JSONResponse(
                {
                    "error": "busy",
                    "detail": "MCP instance is busy handling another request. Please retry.",
                    "sub": sub,
                },
                status_code=429,
            )
            await resp(scope, receive, send)
            return
        try:
            logger.debug("dispatch: forwarding %s %s -> sub=%s", method, path, sub)
            token_cd = current_dispatch_app.set(inner)
            try:
                await inner(scope, receive, send)
            finally:
                current_dispatch_app.reset(token_cd)
        except Exception:
            logger.exception("dispatch: unhandled exception sub=%s method=%s path=%s", sub, method, path)
            raise
        finally:
            if acquired:
                sem.release()
            elapsed = time.monotonic() - t0
            logger.debug("dispatch: done sub=%s %s %s elapsed=%.3fs", sub, method, path, elapsed)

    # ------------------------------------------------------------------
    # Merged MCP helpers (for tok_ tokens spanning multiple instances)
    # ------------------------------------------------------------------

    async def _get_or_create_merged(self, instance_ids: list[str]) -> ASGIApp:
        key = "|".join(sorted(instance_ids))
        if key in self._merged_cache:
            return self._merged_cache[key][1]  # type: ignore[return-value]

        async with self._merged_lock:
            # Double-check after acquiring lock
            if key in self._merged_cache:
                return self._merged_cache[key][1]  # type: ignore[return-value]
            return await self._create_merged(key, instance_ids)

    async def _create_merged(self, key: str, instance_ids: list[str]) -> ASGIApp:
        from mcp.server.fastmcp import FastMCP

        from .cli import _HybridMcpASGI
        from .config import load_instance

        # Create a merged FastMCP with tools from all instances
        # Build routing instructions so the model knows which prefix to use
        routing_lines = [
            "IMPORTANT: This MCP serves MULTIPLE systems. Use the correct tool prefix based on what the user is asking about:\n"
        ]
        configs = []
        for iid in instance_ids:
            if self._instances_dir:
                cfg = load_instance(self._instances_dir / iid)
                configs.append(cfg)
                desc = cfg.mcp_description or cfg.mcp_name or iid
                routing_lines.append(
                    f"- {cfg.tool_prefix}* tools → {cfg.mcp_name} ({desc})"
                )

        routing_lines.append(
            "\nWhen the user mentions a specific system/site name, use the matching prefix. "
            "If unclear, ask which system they mean before calling a tool. "
            "NEVER mix prefixes in a single query - each tool call must use the prefix of the target system."
        )
        instructions = "\n".join(routing_lines)

        merged_mcp = FastMCP(
            f"merged-{'_'.join(instance_ids[:3])}",
            instructions=instructions,
            json_response=True,
        )

        for cfg in configs:
            if cfg.toolpacks:
                from .toolpacks import resolve_packs
                packs = resolve_packs(cfg.toolpacks)
            else:
                from .toolpacks import default_scada_packs
                packs = default_scada_packs()
            for spec in packs:
                spec.pack.register(merged_mcp, cfg)

        merged_mcp.settings.streamable_http_path = "/"
        merged_mcp.settings.mount_path = "/"

        # Must create apps first (session_manager is lazily initialized)
        sh_app = merged_mcp.streamable_http_app()
        sse_app = merged_mcp.sse_app()

        # Start the session manager so SSE sessions work
        sm_ctx = merged_mcp.session_manager.run()
        await sm_ctx.__aenter__()

        hybrid = _HybridMcpASGI(
            mcp_base="/mcp",
            streamable_http_app=sh_app,
            sse_app=sse_app,
        )

        self._merged_cache[key] = (merged_mcp, hybrid, sm_ctx)
        return hybrid

    async def clear_merged_cache(self) -> None:
        """Drop all cached merged-MCP apps (call on hot-reload)."""
        for key, (mcp, hybrid, sm_ctx) in list(self._merged_cache.items()):
            try:
                await sm_ctx.__aexit__(None, None, None)
            except Exception:
                pass
        self._merged_cache.clear()
