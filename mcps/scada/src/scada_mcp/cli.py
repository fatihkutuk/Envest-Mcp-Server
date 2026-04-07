from __future__ import annotations

import argparse
import base64
import contextlib
import logging
import os
import re
import sys
import time
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.routing import Route, Mount

from .auth import TokenError, mint_token, verify_token
from .cors import add_cors_if_configured
from .config import load_instance
from .exports_http import decode_download_token_from_path, make_export_download_handler, parse_files_path
from .server_factory import create_mcp_server
from .sse_session import install_sse_session_hook, is_sse_session_authorized

logger = logging.getLogger("scada_mcp.middleware")

# MCP POST /messages never includes bearer token; session_id is registered on GET /sse.
install_sse_session_hook()


def encode_token_for_mcp_url_path(token: str) -> str:
    """Single path segment: h + hex(JWT). Safe for /mcp/k/<segment>/ (no slashes)."""
    return "h" + token.encode("utf-8").hex()


def decode_token_from_mcp_url_path(segment: str) -> str:
    segment = segment.strip()
    if not segment:
        raise ValueError("empty segment")
    # h + hex(utf-8 jwt) -- never fall through to base64 (would corrupt the JWT and yield bad signature).
    if segment.startswith("h") and len(segment) > 1:
        rest = segment[1:]
        if not all(c in "0123456789abcdefABCDEF" for c in rest):
            raise ValueError("invalid hex after h")
        if len(rest) % 2 != 0:
            raise ValueError("odd hex length (truncated URL?)")
        return bytes.fromhex(rest).decode("utf-8")
    pad = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + pad).decode("utf-8")


class McpPathTokenRewriteMiddleware:
    """
    LM Studio remote MCP often omits config headers and strips ?access_token= on EventSource.
    Accept /{mcp}/k/<h+hex(jwt)>/[/...] and rewrite to the real MCP path with Authorization.
    """

    def __init__(self, app: Starlette, *, mcp_prefix: str = "/mcp", rewrite_target: str = "/mcp/"):
        self._app = app
        self._prefix = (mcp_prefix or "/mcp").rstrip("/") or "/mcp"
        self._target = rewrite_target
        self._pat = re.compile("^" + re.escape(self._prefix) + r"/k/([^/]+)(/.*)?$")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        path = scope.get("path") or ""
        m = self._pat.match(path)
        if not m:
            await self._app(scope, receive, send)
            return
        try:
            token = decode_token_from_mcp_url_path(m.group(1))
        except Exception as e:
            logger.warning("McpPathTokenRewrite: invalid token encoding in URL path=%s: %s", path, e)
            resp = JSONResponse({"error": "invalid token encoding in URL path"}, status_code=401)
            await resp(scope, receive, send)
            return
        suffix = m.group(2) or ""
        base = (self._target or "/mcp/").rstrip("/")
        new_path = (base + suffix) if suffix else (self._target if self._target.endswith("/") else self._target + "/")
        if not new_path.startswith("/"):
            new_path = "/" + new_path
        logger.debug("McpPathTokenRewrite: rewriting %s -> %s (token injected)", path, new_path)
        scope = dict(scope)
        scope["path"] = new_path
        scope["raw_path"] = new_path.encode("utf-8")
        hdrs: list[tuple[bytes, bytes]] = []
        replaced = False
        for k, v in scope.get("headers") or []:
            if k.lower() == b"authorization":
                hdrs.append((b"authorization", f"Bearer {token}".encode()))
                replaced = True
            else:
                hdrs.append((k, v))
        if not replaced:
            hdrs.append((b"authorization", f"Bearer {token}".encode()))
        scope["headers"] = hdrs
        await self._app(scope, receive, send)


class _RewritePathASGI:
    def __init__(self, app, *, rewrite_map: dict[str, str]):
        self._app = app
        self._rewrite_map = rewrite_map

    async def __call__(self, scope, receive, send):
        if scope["type"] in {"http", "websocket"}:
            path = scope.get("path") or ""
            if path in self._rewrite_map:
                scope = dict(scope)
                scope["path"] = self._rewrite_map[path]
        await self._app(scope, receive, send)


class _HybridMcpASGI:
    """
    Serve Streamable HTTP and SSE under the same configured MCP base path.

    LM Studio may attempt SSE (EventSource) for a remote MCP URL; if the server is
    running in streamable-http mode only, that results in 404. We route GET requests
    under the MCP base path to the SSE app (with / -> /sse rewrite), while leaving
    non-GET requests to the streamable-http app.

    Distinguishes streamable-http GET (notification stream, has Mcp-Session-Id header)
    from SSE handshake GET (no session header).
    """

    def __init__(self, *, mcp_base: str, streamable_http_app, sse_app):
        # Allow mcp_base="/" for inner-mount usage (combined.py multi-instance).
        stripped = (mcp_base or "/mcp").rstrip("/")
        self._base = stripped if stripped else ""
        self._match_root = True if self._base == "" else False
        self._stream = streamable_http_app
        self._sse = _RewritePathASGI(sse_app, rewrite_map={"/": "/sse", "": "/sse"})

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self._stream(scope, receive, send)
            return
        path = scope.get("path") or ""
        method = (scope.get("method") or "").upper()

        # --- Path normalization: empty path -> "/" ---
        if not path:
            scope = dict(scope)
            scope["path"] = "/"
            scope["raw_path"] = b"/"
            path = "/"

        is_under_base = self._match_root or path == self._base or path.startswith(self._base + "/")

        # Compute inner path (after stripping mount prefix)
        inner_path = path[len(self._base):] if not self._match_root else path

        # SSE POST: /messages/ path goes to SSE app (session_id in query string)
        if method == "POST" and (inner_path.startswith("/messages") or inner_path.startswith("/messages/")):
            logger.debug("Hybrid: POST %s -> SSE messages", path)
            await self._sse._app(scope, receive, send)
            return

        if method == "GET" and is_under_base:
            # Distinguish streamable-http GET (has Mcp-Session-Id) from SSE handshake GET.
            has_session = any(
                k.lower() == b"mcp-session-id"
                for k, _ in (scope.get("headers") or [])
            )
            if has_session:
                logger.debug("Hybrid: GET %s with Mcp-Session-Id -> streamable-http", path)
                await self._stream(scope, receive, send)
                return

            scope2 = dict(scope)
            scope2["path"] = inner_path or ""
            logger.debug("Hybrid: GET %s -> SSE (inner_path=%s)", path, inner_path or "/")
            await self._sse(scope2, receive, send)
            return
        logger.debug("Hybrid: %s %s -> streamable-http", method, path)
        await self._stream(scope, receive, send)


def _file_download_token_ok(request: Request, token_secret: str) -> bool:
    """GET /files/.../dt/{enc}/... or ?download_token= (browser; no Bearer needed)."""
    if request.method != "GET" or not token_secret.strip():
        return False
    from urllib.parse import unquote

    path = request.url.path or ""
    # Path: /files/{iid}/dt/{base64url(v1...)}/{filename}
    m = re.match(r"^/files/([^/]+)/dt/([^/]+)/([^/]+)$", path)
    if m:
        iid, enc, fn_raw = m.group(1), m.group(2), unquote(m.group(3))
        try:
            dt = decode_download_token_from_path(enc)
        except Exception:
            return False
        try:
            claims = verify_token(token_secret=token_secret, token=dt)
        except TokenError:
            return False
        if claims.get("scope") != "file_download":
            return False
        return str(claims.get("sub") or "") == iid and str(claims.get("fn") or "") == fn_raw

    dt = (request.query_params.get("download_token") or "").strip()
    if not dt:
        return False
    parsed = parse_files_path(path)
    if not parsed:
        return False
    iid, fn = parsed
    try:
        claims = verify_token(token_secret=token_secret, token=dt)
    except TokenError:
        return False
    if claims.get("scope") != "file_download":
        return False
    return str(claims.get("sub") or "") == iid and str(claims.get("fn") or "") == fn


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
            # EventSource / LM Studio: query survives when headers do not.
            qp = request.query_params
            token = (qp.get("access_token") or qp.get("token") or "").strip()
            if token.lower().startswith("bearer "):
                token = token.split(" ", 1)[1].strip()
    # Postman: Auth type Bearer + raw value starting with "Bearer " -> duplicate prefix.
    while token.lower().startswith("bearer "):
        token = token[7:].strip()
    return token


def _post_messages_authorized_by_session(request: Request) -> bool:
    if request.method != "POST":
        return False
    path = request.url.path
    if "/messages" not in path:
        return False
    return is_sse_session_authorized(request.query_params.get("session_id"))


class BearerAuthMiddleware:
    def __init__(
        self,
        app: Starlette,
        *,
        token_secret: str,
        require: bool,
        exempt_paths: set[str],
        protected_prefixes: tuple[str, ...],
    ):
        self._app = app
        self._secret = token_secret
        self._require = require
        self._exempt = exempt_paths
        self._protected_prefixes = protected_prefixes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        request = Request(scope, receive)
        method = request.method
        path = request.url.path
        t0 = time.monotonic()

        if not self._require:
            await self._app(scope, receive, send)
            return
        if path in self._exempt:
            await self._app(scope, receive, send)
            return
        if self._protected_prefixes and not any(path.startswith(p) for p in self._protected_prefixes):
            await self._app(scope, receive, send)
            return
        if method == "OPTIONS":
            await self._app(scope, receive, send)
            return
        if self._require and not self._secret:
            logger.error("BearerAuth: token_secret empty but --require-token set")
            resp = JSONResponse(
                {"error": "auth misconfigured", "detail": "token_secret is empty but --require-token is set"},
                status_code=503,
            )
            await resp(scope, receive, send)
            return
        if _post_messages_authorized_by_session(request):
            logger.debug("BearerAuth: SSE session bypass %s %s", method, path)
            await self._app(scope, receive, send)
            return
        if _file_download_token_ok(request, self._secret):
            logger.debug("BearerAuth: file download token OK %s", path)
            await self._app(scope, receive, send)
            return
        token = _extract_bearer_token(request)
        if not token:
            logger.warning(
                "BearerAuth: 401 missing token %s %s user-agent=%s content-type=%s",
                method, path,
                request.headers.get("user-agent", "-"),
                request.headers.get("content-type", "-"),
            )
            resp = JSONResponse({"error": "missing bearer token"}, status_code=401)
            await resp(scope, receive, send)
            return
        try:
            verify_token(token_secret=self._secret, token=token)
        except TokenError as e:
            logger.warning("BearerAuth: 401 invalid token %s %s: %s", method, path, e)
            resp = JSONResponse({"error": "invalid token", "detail": str(e)}, status_code=401)
            await resp(scope, receive, send)
            return
        elapsed = time.monotonic() - t0
        logger.debug("BearerAuth: OK %s %s (auth %.3fs)", method, path, elapsed)
        await self._app(scope, receive, send)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="scada-mcp")
    p.add_argument("--instance", required=True, help="Path to instances/<name> directory")
    p.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="MCP transport",
    )
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--mcp-path", default="/mcp/", help="Mount path for MCP over HTTP (use trailing slash to avoid redirects)")
    p.add_argument("--require-token", action="store_true", help="Require bearer token for HTTP MCP endpoint")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(sys.argv[1:] if argv is None else argv)
    instance_dir = Path(ns.instance).expanduser().resolve()
    cfg = load_instance(instance_dir)
    mcp = create_mcp_server(cfg)

    if ns.transport == "stdio":
        # Local/ephemeral: intended to be launched by Cursor/LM Studio with command/args.
        mcp.run(transport="stdio")
        return 0

    # HTTP server with optional ephemeral auth.
    auth_cfg = cfg.auth
    token_secret = ""
    admin_secret = ""
    ttl = 900
    enabled = False
    if auth_cfg and auth_cfg.enabled:
        enabled = True
        token_secret = auth_cfg.token_secret
        admin_secret = auth_cfg.admin_secret
        ttl = auth_cfg.token_ttl_sec

    mcp_path = ns.mcp_path
    if not mcp_path.startswith("/"):
        mcp_path = "/" + mcp_path
    if mcp_path != "/" and mcp_path.endswith("/"):
        mcp_path = mcp_path.rstrip("/")

    # Configure FastMCP to serve transports at this path.
    if ns.transport == "streamable-http":
        mcp.settings.streamable_http_path = mcp_path
    else:
        # We mount the SSE ASGI app ourselves (see routing below). Keep FastMCP's internal
        # mount_path at root so we don't end up with doubled prefixes like /mcp/mcp/...
        mcp.settings.mount_path = "/"

    lifespan = None
    if ns.transport == "streamable-http":
        @contextlib.asynccontextmanager
        async def lifespan(app: Starlette):
            async with mcp.session_manager.run():
                yield

    async def mint(request: Request) -> Response:
        if not enabled:
            return JSONResponse({"error": "auth disabled"}, status_code=404)
        provided = request.headers.get("x-admin-secret") or ""
        if not admin_secret or provided != admin_secret:
            return JSONResponse({"error": "forbidden"}, status_code=403)
        token = mint_token(token_secret=token_secret, sub=cfg.instance_id, ttl_sec=ttl)
        return JSONResponse({"token": token, "ttl_sec": ttl})

    def root(_: Request) -> Response:
        return PlainTextResponse(
            "SCADA MCP server is running.\n"
            f"Transport={ns.transport}\n"
            f"MCP path={mcp_path}\n",
            status_code=200,
        )

    exports_dir = cfg.base_dir / "exports"
    export_dl = make_export_download_handler(instance_id=cfg.instance_id, exports_dir=exports_dir)
    routes = [
        Route("/files/{instance_id}/dt/{download_token_enc}/{filename}", export_dl, methods=["GET"]),
        Route("/files/{instance_id}/{filename}", export_dl, methods=["GET"]),
        Route("/", root, methods=["GET"]),
        Route("/favicon.ico", lambda request: Response(status_code=204), methods=["GET"]),
        Route("/auth/mint", mint, methods=["POST"]),
    ]
    if ns.transport == "streamable-http":
        # Serve MCP app at root; FastMCP routes it under configured streamable_http_path.
        routes.append(
            Mount(
                "/",
                app=_HybridMcpASGI(
                    mcp_base=mcp_path,
                    streamable_http_app=mcp.streamable_http_app(),
                    sse_app=mcp.sse_app(),
                ),
            )
        )
    else:
        # For SSE, FastMCP's SSE app exposes endpoints like /sse and /messages.
        base = mcp_path.rstrip("/") or "/"
        sse_app = _RewritePathASGI(mcp.sse_app(), rewrite_map={"/": "/sse", "": "/sse"})
        routes.append(Mount(base, app=sse_app))

    app = Starlette(routes=routes, lifespan=lifespan)
    app.router.redirect_slashes = False

    exempt = {"/auth/mint"}
    mp = mcp_path.rstrip("/") or "/"
    app.add_middleware(
        BearerAuthMiddleware,
        token_secret=token_secret,
        require=bool(ns.require_token),
        exempt_paths=exempt,
        protected_prefixes=(mp, mp + "/", "/files", "/files/"),
    )
    if ns.transport == "streamable-http":
        base = mcp_path.rstrip("/") or "/mcp"
        app.add_middleware(
            McpPathTokenRewriteMiddleware,
            mcp_prefix=base,
            rewrite_target=base,
        )

    add_cors_if_configured(app)

    import uvicorn  # local import to keep CLI lightweight

    uvicorn.run(app, host=ns.host, port=ns.port, log_level=os.getenv("LOG_LEVEL", "info"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
