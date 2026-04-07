"""
HTTP GET download handler for instance exports/ files (Web UI download_url).
Security: basename only; no path traversal; Bearer or ?access_token= (same JWT as MCP).
"""

from __future__ import annotations

import logging
import mimetypes
import re
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response

logger = logging.getLogger("scada_mcp.exports_http")

_SAFE_EXPORT_NAME = re.compile(r"^[a-zA-Z0-9._\-]+$")


def is_safe_export_basename(name: str) -> bool:
    if not name or len(name) > 255 or "/" in name or "\\" in name or name.startswith("."):
        return False
    return bool(_SAFE_EXPORT_NAME.match(name))


def export_file_path(*, exports_root: Path, filename: str) -> Path | None:
    if not is_safe_export_basename(filename):
        return None
    p = (exports_root / filename).resolve()
    try:
        p.relative_to(exports_root.resolve())
    except ValueError:
        return None
    return p if p.is_file() else None


def encode_download_token_for_path(token: str) -> str:
    """Encode v1... signature as a single path segment (no dot/query loss)."""
    import base64

    return base64.urlsafe_b64encode(token.encode("ascii")).decode("ascii").rstrip("=")


def decode_download_token_from_path(enc: str) -> str:
    import base64

    pad = "=" * (-len(enc) % 4)
    return base64.urlsafe_b64decode((enc + pad).encode("ascii")).decode("ascii")


def public_download_signed_path(*, public_base: str, instance_id: str, filename: str, token: str) -> str:
    """Recommended: /files/{id}/dt/{enc}/{filename} -- browser-safe (no ? trimming)."""
    from urllib.parse import quote

    enc = encode_download_token_for_path(token)
    b = public_base.rstrip("/")
    f = quote(filename, safe="")
    return f"{b}/files/{instance_id}/dt/{enc}/{f}"


def download_path(*, instance_id: str, filename: str) -> str:
    """Relative path: /files/{instance_id}/{filename} (without public_base)."""
    from urllib.parse import quote

    f = quote(filename, safe="")
    return f"/files/{instance_id}/{f}"


def download_signed_path(*, instance_id: str, filename: str, token: str) -> str:
    """Relative path: /files/{instance_id}/dt/{enc}/{filename} (without public_base)."""
    from urllib.parse import quote

    enc = encode_download_token_for_path(token)
    f = quote(filename, safe="")
    return f"/files/{instance_id}/dt/{enc}/{f}"


def make_export_download_handler(*, instance_id: str, exports_dir: Path):
    async def download(request: Request) -> Response:
        from urllib.parse import unquote

        iid = request.path_params.get("instance_id") or ""
        fn = unquote(request.path_params.get("filename") or "")
        if iid != instance_id:
            logger.warning("Export download: instance mismatch (expected=%s, got=%s)", instance_id, iid)
            return JSONResponse({"error": "instance mismatch"}, status_code=404)
        path = export_file_path(exports_root=exports_dir, filename=fn)
        if path is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        media_type, _ = mimetypes.guess_type(fn)
        return FileResponse(
            path,
            filename=fn,
            media_type=media_type or "application/octet-stream",
        )

    return download


def public_download_url(*, public_base: str, instance_id: str, filename: str) -> str:
    from urllib.parse import quote

    b = public_base.rstrip("/")
    f = quote(filename, safe="")
    return f"{b}/files/{instance_id}/{f}"


def parse_files_path(path: str) -> tuple[str, str] | None:
    """Parse '/files/{instance_id}/{filename}' path into parts (excluding query string)."""
    from urllib.parse import unquote

    p = (path or "").split("?", 1)[0].strip()
    if not p.startswith("/"):
        p = "/" + p
    parts = [x for x in p.split("/") if x]
    if len(parts) < 3 or parts[0] != "files":
        return None
    return parts[1], unquote(parts[2])


def append_download_token(url: str, token: str) -> str:
    """Signed download token; browser GET without Bearer required."""
    from urllib.parse import urlencode

    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{urlencode({'download_token': token})}"
