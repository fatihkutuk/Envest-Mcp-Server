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
            "\n\n=== KARAR AKIŞI (dinamik tool/skill seçimi) ==="
            "\nHer yeni görev için:"
            "\n1) **list_skills** çağır → skill description'larını gör."
            "\n   Skill'ler: core-rules (zorunlu ilk okuma), korubin-scada, aqua-devices, "
            "envest-urunler, database-best-practices. Açıklama/keyword'lerden uygun olanı SEÇ."
            "\n2) **get_skill('core-rules')** — birim, yuvarlama, tag semantiği, pompa seçimi, çoklu instance."
            "\n3) Konu spesifikse ilgili skill'i oku (skill description ve keywords eşleşmesiyle)."
            "\n4) Sadece CANLI SCADA verisi gerekiyorsa SCADA tool'u çağır. Aksi halde skill yeterli."
            "\n\n=== TEMEL TOOL'LAR (dinamik prefix) ==="
            "\n- **find_node_everywhere(keywords)** — node ismi (tüm instance'lar), selected_tool_prefix döner"
            "\n- **list_scada_instances** — mevcut SCADA instance'larını ve prefix'lerini listele"
            "\n- **pump_select_for_node(node_id)** — node_id biliniyorsa pompa akışı için tek çağrı"
            "\n- `<prefix>_prepare_pump_selection(nodeId)` — canlı Q/H + hidrolik ağ + çalışma modu + mevcut pompa"
            "\n- `<prefix>_get_installed_pump_info(nodeId)` — takılı pompa (pump_eff + node_param)"
            "\n- `<prefix>_analyze_pump_at_frequency(...)` — frekans projeksiyonu (sistem eğrisi + annexa)"
            "\n- `<prefix>_get_active_alarms`, `<prefix>_export_*` — tipik SCADA operasyonları"
            "\n\nPrefix'i HARDCODE etme. find_node_everywhere veya pump_select_for_node'un "
            "response'unda dönen `selected_tool_prefix`'i kullan."
            "\n\n=== ÖZET KURALLAR ==="
            "\n- Cihaz/ürün sorusu (AQUA, PLC modeli, modem status, alarm kodu, register, vs) → **skill**"
            "\n- Canlı durum sorusu (şu an X ne) → **SCADA tool**"
            "\n- Ürün tanıtımı/katalog → **envest-urunler skill'i** (SCADA'daki node_product_type DEĞİL)"
            "\n- Pompa seçimi: canlı tag (ToplamHm, Debimetre). YASAK: XD_BasmaYukseklik, np_*, X*. P_hid=(Q×H)/367."
        )
        instructions = "\n".join(routing_lines)

        merged_mcp = FastMCP(
            f"merged-{'_'.join(instance_ids[:3])}",
            instructions=instructions,
            json_response=True,
        )

        scada_cfgs: list = []
        for cfg in configs:
            if cfg.toolpacks:
                from .toolpacks import resolve_packs
                packs = resolve_packs(cfg.toolpacks)
            else:
                from .toolpacks import default_scada_packs
                packs = default_scada_packs()
            pack_ids = {getattr(spec.pack, "id", "") for spec in packs}
            if "scada" in pack_ids:
                scada_cfgs.append(cfg)
            for spec in packs:
                spec.pack.register(merged_mcp, cfg)

        # Server-side cross-instance node search — LLM'in prefix'leri
        # hatirlamasina gerek kalmadan TUM SCADA instance'larinda tek seferde arar.
        if len(scada_cfgs) >= 1:
            _register_cross_instance_tools(merged_mcp, scada_cfgs)

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


def _register_cross_instance_tools(mcp: Any, scada_cfgs: list) -> None:
    """
    Register server-side cross-instance search tools on a merged MCP.

    These tools fan out to all SCADA instances in the token's scope,
    so the LLM does not need to remember to try different prefixes.
    """
    from .db import connect as _db_connect

    @mcp.tool(name="find_node_everywhere")
    def find_node_everywhere(keywords: str, limit_per_instance: int = 5) -> Any:
        """ANY SCADA node arama — TUM instance'larda aynı anda arar.

        Kullanıcı bir node adı söyledi ama hangi SCADA olduğunu belirtmediyse
        (ör. "selafur kuyu 4", "akkent terfi") BUNU ÇAĞIR. Prefix hatırlamana gerek yok.

        Returns: Her instance için ayrı sonuç bloğu. Sonraki çağrılarda
        sonucun `instance_prefix` alanını kullanarak ilgili instance'ın
        tool'larını çağır (ör. `<selected_tool_prefix>get_node`, `<selected_tool_prefix>get_device_tag_values`).
        """
        kw = (keywords or "").strip()
        if not kw:
            return {"error": "keywords parametresi zorunlu", "ornek": "selafur kuyu 4"}

        kw_norm = kw.lower()
        lim = max(1, min(int(limit_per_instance), 50))
        results: list[dict[str, Any]] = []
        total_found = 0
        errors: list[dict[str, Any]] = []

        for cfg in scada_cfgs:
            if not cfg.db:
                continue
            block: dict[str, Any] = {
                "instance_id": cfg.instance_id,
                "instance_prefix": cfg.tool_prefix.rstrip("_"),
                "mcp_name": cfg.mcp_name,
                "tool_prefix": cfg.tool_prefix,
                "nodes": [],
            }
            try:
                with _db_connect(cfg.db) as conn:
                    with conn.cursor() as cur:
                        # Case-insensitive, ascii-normalize friendly LIKE
                        like = f"%{kw_norm}%"
                        cur.execute(
                            """
                            SELECT n.id, n.nName, n.nView, n.nType, n.nState
                            FROM node n
                            WHERE LOWER(n.nName) LIKE %s
                               OR LOWER(n.nView) LIKE %s
                            ORDER BY CHAR_LENGTH(n.nName) ASC
                            LIMIT %s
                            """,
                            (like, like, lim),
                        )
                        rows = list(cur.fetchall())
                        block["nodes"] = rows
                        total_found += len(rows)
            except Exception as exc:
                block["error"] = f"{type(exc).__name__}: {exc}"
                errors.append({"instance": cfg.instance_id, "error": block["error"]})
            results.append(block)

        out: dict[str, Any] = {
            "keywords": kw,
            "total_found": total_found,
            "instances_searched": len(results),
            "results": results,
        }
        if errors:
            out["errors"] = errors

        if total_found == 0:
            prefixes = [r["instance_prefix"] for r in results]
            out["hint_tr"] = (
                f"'{kw}' hicbir SCADA instance'inda ({', '.join(prefixes)}) bulunamadi. "
                "Kullaniciya yazim hatasi olabilir mi diye sor, TAHMIN YURUTME."
            )
        elif total_found > 0:
            # Auto-pick hint: if only one instance returned results, suggest it
            non_empty = [r for r in results if r["nodes"]]
            if len(non_empty) == 1:
                winner = non_empty[0]
                out["selected_instance"] = winner["instance_prefix"]
                out["selected_tool_prefix"] = winner["tool_prefix"]
                out["hint_tr"] = (
                    f"Sadece '{winner['instance_prefix']}' instance'inda bulundu. "
                    f"Sonraki tool cagrilarinda '{winner['tool_prefix']}' prefix'ini kullan "
                    f"(ornek: {winner['tool_prefix']}get_node, {winner['tool_prefix']}get_device_tag_values)."
                )
            else:
                out["hint_tr"] = (
                    "Birden fazla instance'da esleyen node var — kullaniciya hangisi "
                    "oldugunu sor, tahmin yurutme. Sectikten sonra o instance'in "
                    "'tool_prefix' degerini kullan."
                )
        return out

    @mcp.tool(name="pump_select_for_node")
    def pump_select_for_node(node_id: int) -> Any:
        """Node ID için pompa seç — TEK ÇAĞRI, tüm SCADA'larda bakar, nView'dan kuyu/terfi anlar.

        Kullanıcı sadece node_id verdiyse (örn. 'Serbest Bölge Kuyu 1192 için pompa seç'):
        bu tool'u çağır. Hangi instance'ta olduğunu bulur, canlı tag'leri okur, Q/H hazır döner.
        Sonra response'taki 'next_action' ile korucaps_search_pumps çağır.
        """
        nid = int(node_id)
        if nid <= 0:
            return {"error": "node_id > 0 olmali"}

        # Her instance'ta node var mi diye bak
        found_cfg = None
        found_node = None
        errors: list[dict[str, Any]] = []
        for cfg in scada_cfgs:
            if not cfg.db:
                continue
            try:
                with _db_connect(cfg.db) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT id, nName, nView, nType, nState FROM node WHERE id = %s",
                            (nid,),
                        )
                        row = cur.fetchone()
                        if row:
                            found_cfg = cfg
                            found_node = row
                            break
            except Exception as exc:
                errors.append({
                    "instance": cfg.instance_id,
                    "error": f"{type(exc).__name__}: {exc}",
                })

        if found_cfg is None:
            if errors and len(errors) == len([c for c in scada_cfgs if c.db]):
                return {
                    "error": "Tüm SCADA DB bağlantıları hata verdi.",
                    "errors": errors,
                    "hint_tr": "DB erişim sorunu — kullanıcıya bildir, tekrar denemesini söyle.",
                }
            return {
                "error": f"Node {nid} hiçbir SCADA'da bulunamadi.",
                "errors": errors or None,
                "hint_tr": "Node ID yanlış olabilir. Kullanıcıya teyit ettir.",
            }

        # nView'dan pompa tipi + korucaps parametreleri
        nv = str(found_node.get("nView") or "").lower()
        nname = str(found_node.get("nName") or "").lower()
        is_well = ("kuyu" in nv) or ("kuyu" in nname) or ("well" in nv)
        is_booster = ("terfi" in nv) or ("terfi" in nname) or ("booster" in nv) or ("hidro" in nv)
        if is_well:
            kc_app, kc_sub, series = "groundwater", "WELLINS", "SP"
            pump_type = "kuyu (dalgıç)"
        elif is_booster:
            kc_app, kc_sub, series = "booster", "BOOSPUMP", "CR"
            pump_type = "terfi/booster"
        else:
            kc_app, kc_sub, series = None, None, None
            pump_type = f"belirsiz (nView={found_node.get('nView')})"

        prefix = found_cfg.tool_prefix

        return {
            "selected_instance": found_cfg.instance_id,
            "selected_tool_prefix": prefix,
            "node": {
                "id": nid,
                "nName": found_node.get("nName"),
                "nView": found_node.get("nView"),
                "nType": found_node.get("nType"),
            },
            "pump_type": pump_type,
            "pump_series_hint": series,
            "korucaps_app": kc_app,
            "korucaps_sub_app": kc_sub,
            "next_action": (
                f"{prefix}prepare_pump_selection(nodeId={nid})"
            ),
            "hint_tr": (
                f"Node {nid} → {found_cfg.instance_id} instance'ında bulundu. "
                f"Pompa tipi: {pump_type}. Şimdi next_action'ı çağır — "
                f"canlı Q/H alıp korucaps_search_pumps'a verecek."
            ),
        }

    @mcp.tool(name="list_scada_instances")
    def list_scada_instances() -> Any:
        """Bu token icin erisilebilir SCADA instance'larini listele.

        find_node_everywhere otomatik olarak hepsinde arama yapar, ama hangi
        SCADA'lar mevcut oldugunu gormek istersen bu tool'u cagir."""
        return {
            "instances": [
                {
                    "instance_id": cfg.instance_id,
                    "mcp_name": cfg.mcp_name,
                    "tool_prefix": cfg.tool_prefix,
                    "panel_base_url": cfg.panel_base_url,
                    "description": cfg.mcp_description or "",
                }
                for cfg in scada_cfgs
            ],
            "hint_tr": (
                "Node ararken prefix hatirlamana gerek yok: find_node_everywhere "
                "otomatik hepsinde arar."
            ),
        }
