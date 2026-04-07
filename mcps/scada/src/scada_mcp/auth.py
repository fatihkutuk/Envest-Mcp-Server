from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass
from typing import Any


logger = logging.getLogger("scada_mcp.auth")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("ascii"))


@dataclass(frozen=True)
class TokenClaims:
    sub: str
    iat: int
    exp: int
    aud: str = "scada-mcp"


class TokenError(Exception):
    pass


def mint_file_download_token(*, token_secret: str, sub: str, filename: str, ttl_sec: int = 3600) -> str:
    """
    Scope=file_download token for GET /files/.../filename.
    Browser-clickable URL (?download_token=).
    """
    token_secret = token_secret.strip()
    if not token_secret:
        raise TokenError("token_secret is empty")
    fn = (filename or "").strip()
    if not fn or "/" in fn or "\\" in fn:
        raise TokenError("invalid filename for download token")
    now = int(time.time())
    ttl = max(60, int(ttl_sec))
    exp = now + ttl
    claims = {
        "sub": sub,
        "iat": now,
        "exp": exp,
        "aud": "scada-mcp",
        "scope": "file_download",
        "fn": fn,
    }
    payload = json.dumps(claims, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sig = hmac.new(token_secret.encode("utf-8"), payload, hashlib.sha256).digest()
    return f"v1.{_b64url(payload)}.{_b64url(sig)}"


def mint_token(*, token_secret: str, sub: str, ttl_sec: int) -> str:
    token_secret = token_secret.strip()
    if not token_secret:
        raise TokenError("token_secret is empty")
    now = int(time.time())
    ttl = int(ttl_sec)
    # ttl_sec <= 0: long-lived token (e.g. 10 years).
    if ttl <= 0:
        exp = now + (10 * 365 * 86400)
    else:
        exp = now + max(30, ttl)
    claims = {
        "sub": sub,
        "iat": now,
        "exp": exp,
        "aud": "scada-mcp",
    }
    payload = json.dumps(claims, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sig = hmac.new(token_secret.encode("utf-8"), payload, hashlib.sha256).digest()
    return f"v1.{_b64url(payload)}.{_b64url(sig)}"


def peek_sub_unverified(token: str) -> str:
    """Read JWT payload.sub without verifying signature (used to pick the signing secret)."""
    token = token.strip()
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != "v1":
        raise TokenError("invalid token format")
    payload_b = _b64url_decode(parts[1])
    claims = json.loads(payload_b.decode("utf-8"))
    if not isinstance(claims, dict):
        raise TokenError("invalid claims")
    return str(claims.get("sub") or "").strip()


def verify_token_with_registry(*, token: str, registry: dict[str, str]) -> dict[str, Any]:
    """Verify HMAC using the secret for claims.sub (each SCADA instance has its own MCP_TOKEN_SECRET)."""
    sub = peek_sub_unverified(token)
    if not sub:
        raise TokenError("missing sub")
    secret = registry.get(sub)
    if not secret:
        raise TokenError("unknown instance")
    return verify_token(token_secret=secret, token=token)


def verify_token(*, token_secret: str, token: str) -> dict[str, Any]:
    token_secret = token_secret.strip()
    token = token.strip()
    if not token_secret:
        raise TokenError("token_secret is empty")
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != "v1":
        raise TokenError("invalid token format")
    payload_b = _b64url_decode(parts[1])
    sig_b = _b64url_decode(parts[2])
    expect = hmac.new(token_secret.encode("utf-8"), payload_b, hashlib.sha256).digest()
    if not hmac.compare_digest(expect, sig_b):
        raise TokenError("bad signature")
    claims = json.loads(payload_b.decode("utf-8"))
    if not isinstance(claims, dict):
        raise TokenError("invalid claims")
    now = int(time.time())
    exp = int(claims.get("exp") or 0)
    if exp <= now:
        raise TokenError("token expired")
    if claims.get("aud") != "scada-mcp":
        raise TokenError("bad audience")
    return claims
