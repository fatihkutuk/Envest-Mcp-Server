from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import mimetypes
import os
import sys
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Mount, Route

from .auth import TokenError, peek_sub_unverified, verify_token, verify_token_with_registry
from .cli import BearerAuthMiddleware, McpPathTokenRewriteMiddleware, _HybridMcpASGI
from .cors import add_cors_if_configured
from .config import load_instance
from .exports_http import decode_download_token_from_path, export_file_path, make_export_download_handler
from .multi_mcp import _extract_bearer_token
from .admin.app import build_admin_app
from .admin.store import DataStore
from .multi_mcp import MultiMcpDispatchASGI, discover_instance_paths
from .server_factory import create_mcp_server
from .sse_session import install_sse_session_hook

logger = logging.getLogger("scada_mcp.combined")

# SSE session hook must be installed early (before any SSE transport usage).
install_sse_session_hook()


def _configure_logging() -> None:
    """Apply LOG_LEVEL env to all scada_mcp loggers (not just uvicorn)."""
    level_name = os.getenv("LOG_LEVEL", "info").upper()
    level = getattr(logging, level_name, logging.INFO)
    # Set the root scada_mcp namespace so all child loggers inherit.
    pkg_logger = logging.getLogger("scada_mcp")
    pkg_logger.setLevel(level)
    # Ensure at least one handler so messages are visible.
    if not pkg_logger.handlers and not logging.root.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s"))
        pkg_logger.addHandler(handler)


class _NormalizeMcpPathMiddleware:
    """
    Ensure /mcp (no trailing slash) is rewritten to /mcp/ before Starlette routing.
    Starlette Mount("/mcp") with redirect_slashes=False only matches /mcp/* not /mcp.
    Some providers (OpenRouter, etc.) send requests to /mcp without trailing slash.
    """

    def __init__(self, app, *, mcp_prefix: str = "/mcp"):
        self._app = app
        self._bare = mcp_prefix.rstrip("/") or "/mcp"
        self._target = self._bare + "/"

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path") or ""
            if path == self._bare:
                scope = dict(scope)
                scope["path"] = self._target
                scope["raw_path"] = self._target.encode("utf-8")
                logger.debug("NormalizePath: %s -> %s", path, self._target)
        await self._app(scope, receive, send)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="scada-mcp-combined")
    p.add_argument(
        "--instance",
        default="",
        help="Single instance dir (legacy). Leave empty to serve ALL instances under <root>/instances on one /mcp URL (HF-style: Bearer + sub).",
    )
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--root", default="", help="Project root folder; defaults to auto-detect")
    p.add_argument("--require-token", action="store_true", help="Require bearer token for /mcp/*")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    _configure_logging()
    ns = _parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(ns.root).resolve() if ns.root else _project_root()
    if ns.instance.strip():
        return _run_single(ns, root=root)
    return _run_multi(ns, root=root)


def _run_single(ns: argparse.Namespace, *, root: Path) -> int:
    instance_dir = Path(ns.instance).expanduser().resolve()
    cfg = load_instance(instance_dir)
    mcp = create_mcp_server(cfg)

    manager_app = build_manager_app(root=root)

    # Auto-generate a token_secret for legacy BearerAuthMiddleware compatibility
    import secrets as _secrets
    token_secret = _secrets.token_hex(32)

    logger.info("mode=single instance_dir=%s", instance_dir)

    mcp.settings.streamable_http_path = "/"
    mcp.settings.mount_path = "/"

    hybrid_app = _HybridMcpASGI(
        mcp_base="/mcp",
        streamable_http_app=mcp.streamable_http_app(),
        sse_app=mcp.sse_app(),
    )

    exports_dir = cfg.base_dir / "exports"
    export_dl = make_export_download_handler(instance_id=cfg.instance_id, exports_dir=exports_dir)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        async with mcp.session_manager.run():
            yield

    app = Starlette(
        routes=[
            Route("/files/{instance_id}/dt/{download_token_enc}/{filename}", export_dl, methods=["GET"]),
            Route("/files/{instance_id}/{filename}", export_dl, methods=["GET"]),
            Mount("/mcp", app=hybrid_app),
            Mount("/", app=manager_app),
        ],
        lifespan=lifespan,
    )
    app.router.redirect_slashes = False

    app.add_middleware(
        BearerAuthMiddleware,
        token_secret=token_secret,
        require=bool(ns.require_token),
        exempt_paths=set(),
        protected_prefixes=("/mcp", "/mcp/", "/files", "/files/"),
    )
    app.add_middleware(McpPathTokenRewriteMiddleware, mcp_prefix="/mcp", rewrite_target="/mcp/")
    app.add_middleware(_NormalizeMcpPathMiddleware, mcp_prefix="/mcp")
    add_cors_if_configured(app)

    import uvicorn

    uvicorn.run(app, host=ns.host, port=ns.port, log_level=os.getenv("LOG_LEVEL", "info"))
    return 0


def _scan_instances_into_registry(
    instances_dir: Path,
    *,
    secret_registry: dict[str, str],
    apps_by_sub: dict[str, object],
    max_concurrency_by_sub: dict[str, int],
    wait_ms_by_sub: dict[str, int],
    mcps: list,
) -> None:
    """Populate dicts and list in-place (MultiMcpDispatchASGI uses the same references)."""
    secret_registry.clear()
    apps_by_sub.clear()
    max_concurrency_by_sub.clear()
    wait_ms_by_sub.clear()
    mcps.clear()
    paths = discover_instance_paths(instances_dir)
    import secrets as _secrets

    for p in paths:
        try:
            cfg = load_instance(p)
        except Exception as e:
            logger.warning("skip %s: %s", p.name, e)
            continue
        if not cfg.auth or not cfg.auth.enabled:
            logger.info("skip %s: auth disabled", p.name)
            continue
        # Legacy fallback flow için ve download signed-URL için kullanilan secret.
        # config.py artik cfg.auth.token_secret'i kalici dosyadan okuyup sagliyor —
        # burada ayni secret'i secret_registry'ye aynen yaziyoruz ki sign+verify uyussun.
        # Admin panel tokenlari (tok_ prefix) kendi per-token secret'leriyle calisir.
        if cfg.auth and (cfg.auth.token_secret or "").strip():
            auto_secret = cfg.auth.token_secret
        else:
            auto_secret = _secrets.token_hex(32)
        if cfg.instance_id in secret_registry:
            logger.warning("duplicate instance_id %r, skipping %s", cfg.instance_id, p)
            continue
        mcp = create_mcp_server(cfg)
        mcp.settings.streamable_http_path = "/"
        mcp.settings.mount_path = "/"

        hybrid_app = _HybridMcpASGI(
            mcp_base="/mcp",
            streamable_http_app=mcp.streamable_http_app(),
            sse_app=mcp.sse_app(),
        )

        secret_registry[cfg.instance_id] = auto_secret
        apps_by_sub[cfg.instance_id] = hybrid_app
        if int(cfg.mcp_max_concurrency or 0) > 0:
            max_concurrency_by_sub[cfg.instance_id] = int(cfg.mcp_max_concurrency)
        if int(cfg.mcp_concurrency_wait_ms or 0) > 0:
            wait_ms_by_sub[cfg.instance_id] = int(cfg.mcp_concurrency_wait_ms)
        mcps.append(mcp)
        logger.info("registered instance %s (id=%s)", p.name, cfg.instance_id)


def _run_multi(ns: argparse.Namespace, *, root: Path) -> int:
    if not ns.require_token:
        logger.error(
            "scada-mcp-combined: multi-instance mode requires --require-token (JWT routes by sub)."
        )
        return 2

    instances_dir = root / "instances"
    secret_registry: dict[str, str] = {}
    apps_by_sub: dict[str, object] = {}
    max_concurrency_by_sub: dict[str, int] = {}
    wait_ms_by_sub: dict[str, int] = {}
    mcps: list = []
    _scan_instances_into_registry(
        instances_dir,
        secret_registry=secret_registry,
        apps_by_sub=apps_by_sub,
        max_concurrency_by_sub=max_concurrency_by_sub,
        wait_ms_by_sub=wait_ms_by_sub,
        mcps=mcps,
    )

    if not apps_by_sub:
        logger.error(
            "scada-mcp-combined: no instances with auth under %s. "
            "Use --instance <path> for single-instance mode.",
            instances_dir,
        )
        return 2

    logger.info("mode=multi instances_dir=%s subjects=%s", instances_dir, list(apps_by_sub.keys()))

    session_tasks: list[asyncio.Task] = []
    reload_lock = asyncio.Lock()

    async def _run_mcp_session(mcp: object) -> None:
        try:
            async with mcp.session_manager.run():  # type: ignore[attr-defined]
                await asyncio.Future()
        except asyncio.CancelledError:
            raise

    async def rebuild_mcp_instances() -> None:
        """Hot-reload: rebuild MCP registrations from disk (no restart needed)."""
        async with reload_lock:
            for t in session_tasks:
                t.cancel()
            if session_tasks:
                await asyncio.gather(*session_tasks, return_exceptions=True)
            session_tasks.clear()
            _scan_instances_into_registry(
                instances_dir,
                secret_registry=secret_registry,
                apps_by_sub=apps_by_sub,
                max_concurrency_by_sub=max_concurrency_by_sub,
                wait_ms_by_sub=wait_ms_by_sub,
                mcps=mcps,
            )
            logger.info("MCP reload subjects=%s", list(apps_by_sub.keys()))
            # Coklu-instance tokenlari icin cache'lenmis merged MCP'leri dusur —
            # aksi halde guncel DB credentials eski instance'ta kilitli kalir.
            try:
                if hasattr(dispatch, "clear_merged_cache"):
                    await dispatch.clear_merged_cache()
            except Exception as exc:
                logger.warning("clear_merged_cache failed: %s", exc)
            if not apps_by_sub:
                logger.warning("no valid auth instances left; /mcp will return 404")
                return
            for m in mcps:
                session_tasks.append(asyncio.create_task(_run_mcp_session(m)))

    # Data store for admin panel (users, tokens)
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)
    store = DataStore(data_dir)
    store.ensure_default_admin()

    admin_app = build_admin_app(root=root, store=store, on_instances_changed=rebuild_mcp_instances)

    dispatch = MultiMcpDispatchASGI(
        apps_by_sub=apps_by_sub,
        secret_registry=secret_registry,
        token_store=store,
        instances_dir=instances_dir,
        max_concurrency_by_sub=max_concurrency_by_sub,
        wait_ms_by_sub=wait_ms_by_sub,
    )

    def _resolve_secret_for_sub(sub: str) -> str | None:
        """Legacy instance_id -> secret_registry, tok_ -> token_store lookup."""
        secret = secret_registry.get(sub)
        if secret:
            return secret
        if sub.startswith("tok_"):
            rec = store.get_token(sub)
            if rec and not rec.get("revoked"):
                return rec.get("token_secret")
        return None

    def _tok_targets_instance(sub: str, instance_id: str) -> bool:
        """For tok_ tokens, check instance_id is in allowed_instances."""
        if not sub.startswith("tok_"):
            return True  # legacy tokens are scoped via sub == instance_id check
        rec = store.get_token(sub)
        if not rec or rec.get("revoked"):
            return False
        allowed = rec.get("allowed_instances") or []
        return instance_id in allowed

    async def export_download_multi(request: Request) -> Response:
        from urllib.parse import unquote

        instance_id = request.path_params.get("instance_id", "")
        fn = unquote(request.path_params.get("filename", ""))
        enc = request.path_params.get("download_token_enc")
        if enc is not None:
            try:
                dt = decode_download_token_from_path(enc)
            except Exception:
                return JSONResponse({"error": "invalid download token encoding"}, status_code=400)
            try:
                sub = peek_sub_unverified(dt)
                secret = _resolve_secret_for_sub(sub)
                if not secret:
                    return JSONResponse({"error": "unknown instance"}, status_code=401)
                claims = verify_token(token_secret=secret, token=dt)
                if claims.get("scope") != "file_download":
                    return JSONResponse({"error": "invalid download token"}, status_code=401)
                claim_sub = str(claims.get("sub") or "")
                if claim_sub.startswith("tok_"):
                    if not _tok_targets_instance(claim_sub, instance_id):
                        return JSONResponse({"error": "forbidden"}, status_code=403)
                elif claim_sub != instance_id:
                    return JSONResponse({"error": "forbidden"}, status_code=403)
                if str(claims.get("fn") or "") != fn:
                    return JSONResponse({"error": "forbidden"}, status_code=403)
            except TokenError as e:
                return JSONResponse({"error": "invalid download token", "detail": str(e)}, status_code=401)
        else:
            dt = (request.query_params.get("download_token") or "").strip()
            if dt:
                try:
                    sub = peek_sub_unverified(dt)
                    secret = _resolve_secret_for_sub(sub)
                    if not secret:
                        return JSONResponse({"error": "unknown instance"}, status_code=401)
                    claims = verify_token(token_secret=secret, token=dt)
                    if claims.get("scope") != "file_download":
                        return JSONResponse({"error": "invalid download token"}, status_code=401)
                    claim_sub = str(claims.get("sub") or "")
                    if claim_sub.startswith("tok_"):
                        if not _tok_targets_instance(claim_sub, instance_id):
                            return JSONResponse({"error": "forbidden"}, status_code=403)
                    elif claim_sub != instance_id:
                        return JSONResponse({"error": "forbidden"}, status_code=403)
                    if str(claims.get("fn") or "") != fn:
                        return JSONResponse({"error": "forbidden"}, status_code=403)
                except TokenError as e:
                    return JSONResponse({"error": "invalid download token", "detail": str(e)}, status_code=401)
            else:
                token = _extract_bearer_token(request)
                if not token:
                    return JSONResponse({"error": "missing bearer token"}, status_code=401)
                try:
                    sub = peek_sub_unverified(token)
                    secret = _resolve_secret_for_sub(sub)
                    if not secret:
                        return JSONResponse({"error": "unknown instance"}, status_code=401)
                    claims = verify_token(token_secret=secret, token=token)
                except TokenError as e:
                    return JSONResponse({"error": "invalid token", "detail": str(e)}, status_code=401)
                claim_sub = str(claims.get("sub") or "")
                if claim_sub.startswith("tok_"):
                    if not _tok_targets_instance(claim_sub, instance_id):
                        return JSONResponse({"error": "forbidden"}, status_code=403)
                elif claim_sub != instance_id:
                    return JSONResponse({"error": "forbidden"}, status_code=403)

        ex_root = instances_dir / instance_id / "exports"
        path = export_file_path(exports_root=ex_root, filename=fn)
        if path is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        media_type, _ = mimetypes.guess_type(fn)
        return FileResponse(
            path,
            filename=fn,
            media_type=media_type or "application/octet-stream",
        )

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        for m in mcps:
            session_tasks.append(asyncio.create_task(_run_mcp_session(m)))
        yield
        for t in session_tasks:
            t.cancel()
        if session_tasks:
            await asyncio.gather(*session_tasks, return_exceptions=True)
        session_tasks.clear()

    app = Starlette(
        routes=[
            Route("/files/{instance_id}/dt/{download_token_enc}/{filename}", export_download_multi, methods=["GET"]),
            Route("/files/{instance_id}/{filename}", export_download_multi, methods=["GET"]),
            Mount("/mcp", app=dispatch),
            Mount("/", app=admin_app),
        ],
        lifespan=lifespan,
    )
    app.router.redirect_slashes = False

    # McpPathTokenRewrite: support /mcp/k/<hex-token>/ URL pattern (LM Studio style).
    app.add_middleware(McpPathTokenRewriteMiddleware, mcp_prefix="/mcp", rewrite_target="/mcp/")
    # Normalize /mcp -> /mcp/ so Starlette Mount("/mcp") can match.
    app.add_middleware(_NormalizeMcpPathMiddleware, mcp_prefix="/mcp")

    add_cors_if_configured(app)

    import uvicorn

    uvicorn.run(app, host=ns.host, port=ns.port, log_level=os.getenv("LOG_LEVEL", "info"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
