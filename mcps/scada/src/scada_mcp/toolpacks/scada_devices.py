"""Device profile / phtml viewer tools: list_point_display_templates, read_point_display_template,
summarize_point_display_template, list_point_display_files, search_point_display_templates,
get_panel_url_for_template, extract_menu_links.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..tools.core import guard, prefixed_name
from ..types import InstanceConfig

log = logging.getLogger(__name__)

_FOLDER_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_WS_RE = re.compile(r"\s+")
_HTML_ENTITY_RE = re.compile(r"&(?:nbsp|amp|lt|gt|quot|apos);", flags=re.IGNORECASE)
_PHTML_TAG_CANDIDATE_RE = re.compile(r"\b[A-Z]{1,4}_[A-Za-z0-9_]{2,64}\b")


def _strip_html(text: str) -> str:
    t = _HTML_TAG_RE.sub(" ", text)
    t = _HTML_ENTITY_RE.sub(" ", t)
    t = t.replace("\u00a0", " ")
    t = _HTML_WS_RE.sub(" ", t)
    return t.strip()


def _validate_rel_path(rel: str) -> str | None:
    rel = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not rel or ".." in rel:
        return None
    for part in rel.split("/"):
        if not part or part in {".", ".."} or not _FOLDER_RE.fullmatch(part):
            return None
    return rel


def _safe_resolve_under(base: Path, *parts: str) -> Path | None:
    try:
        target = (base.joinpath(*parts)).resolve()
    except Exception:
        return None
    if not str(target).startswith(str(base) + os.sep):
        return None
    return target


class ScadaDevicesPack:
    """Device profiles, Kepware info, PLC data, phtml viewer tools."""

    id = "scada_devices"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix

        def _panel_base_url() -> str:
            u = (cfg.panel_base_url or "").strip()
            if not u:
                return ""
            u = u.rstrip("/")
            if not re.match(r"^https?://", u, flags=re.IGNORECASE):
                u = "https://" + u.lstrip("/")
            return u

        def _point_display_root() -> str:
            return (os.getenv("KORUBIN_POINT_DISPLAY_ROOT") or "").strip()

        # --- list_point_display_templates ---
        tool = prefixed_name(prefix, "list_point_display_templates")

        def _list_point_display_templates_impl(limit: int = 200) -> Any:
            root = _point_display_root()
            if not root or not Path(root).is_dir():
                return {
                    "error": "point_display_root tanımlı değil veya erişilemiyor",
                    "hint": "Ortam değişkeni KORUBIN_POINT_DISPLAY_ROOT ayarlayın (örn. .../app/views/point/display/common)",
                }
            lim = max(1, min(500, int(limit)))
            dirs: list[str] = []
            for name in sorted(os.listdir(root)):
                full = Path(root) / name
                if full.is_dir() and _FOLDER_RE.fullmatch(name):
                    dirs.append(name)
            return {"count": len(dirs), "folders": dirs[:lim], "panel_base_configured": _panel_base_url() != ""}

        @mcp.tool(name=tool)
        def list_point_display_templates(limit: int = 200) -> str:
            """Nokta görüntü şablonları listesi."""
            return guard(tool, _list_point_display_templates_impl)(limit)

        # --- read_point_display_template ---
        tool = prefixed_name(prefix, "read_point_display_template")

        def _read_point_display_template_impl(
            n_view_folder: str,
            relative_path: str,
            node_id: int | None = None,
            max_chars: int = 0,
        ) -> Any:
            root = _point_display_root()
            if not root or not Path(root).is_dir():
                return {"error": "point_display_root tanımlı değil"}
            folder = (n_view_folder or "").strip()
            if not folder or not _FOLDER_RE.fullmatch(folder):
                return {"error": "Geçersiz n_view_folder"}
            rel = _validate_rel_path(relative_path or "")
            if not rel:
                return {"error": "Geçersiz relative_path"}
            base = Path(root).resolve()
            target = _safe_resolve_under(base, folder, rel)
            if not target:
                return {"error": "Erişim reddedildi"}
            if not target.is_file():
                return {"error": "Dosya bulunamadı"}
            if target.stat().st_size > 262144:
                return {"error": "Dosya çok büyük", "max_bytes": 262144, "file_bytes": target.stat().st_size}
            content = target.read_text(encoding="utf-8", errors="replace")
            mc = int(max_chars or 0)
            if mc < 0:
                mc = 0
            mc = min(mc, 200_000)
            truncated = False
            if mc > 0 and len(content) > mc:
                content = content[:mc]
                truncated = True
            payload: dict[str, Any] = {
                "n_view_folder": folder,
                "relative_path": rel,
                "bytes": len(content.encode("utf-8", errors="ignore")),
                "content": content,
                "content_truncated": truncated,
                "content_max_chars": mc if mc > 0 else None,
            }
            base_url = _panel_base_url()
            if base_url and node_id and int(node_id) > 0:
                node_id_i = int(node_id)
                point_url = f"{base_url}/panel/point/{node_id_i}/"
                payload["panel"] = {"base_url": base_url, "node_id": node_id_i, "point_url": point_url}
            return payload

        @mcp.tool(name=tool)
        def read_point_display_template(
            n_view_folder: str,
            relative_path: str,
            node_id: int | None = None,
            max_chars: int = 0,
        ) -> str:
            """Şablon dosya içeriği okuma. Yol: {KORUBIN_POINT_DISPLAY_ROOT}/{n_view_folder}/{relative_path}."""
            return guard(tool, _read_point_display_template_impl)(n_view_folder, relative_path, node_id, max_chars)

        # --- summarize_point_display_template ---
        tool = prefixed_name(prefix, "summarize_point_display_template")

        def _summarize_point_display_template_impl(
            n_view_folder: str,
            relative_path: str,
            node_id: int | None = None,
            max_excerpt_chars: int = 1800,
        ) -> Any:
            payload = _read_point_display_template_impl(n_view_folder, relative_path, node_id)
            if isinstance(payload, dict) and payload.get("error"):
                return payload
            if not isinstance(payload, dict) or "content" not in payload:
                return {"error": "Şablon okunamadı"}
            content = str(payload.get("content") or "")
            rel = str(payload.get("relative_path") or relative_path)
            folder = str(payload.get("n_view_folder") or n_view_folder)

            headings: list[dict[str, Any]] = []
            for m in re.finditer(r"(?is)<h([1-6])[^>]*>(.*?)</h\\1>", content):
                lvl = int(m.group(1))
                txt = _strip_html(m.group(2))
                if txt:
                    headings.append({"level": lvl, "text": txt})
                if len(headings) >= 20:
                    break

            links: list[dict[str, Any]] = []
            for m in re.finditer(r"""(?is)\bhref\s*=\s*["']([^"']+)["']""", content):
                href = (m.group(1) or "").strip()
                if not href or len(href) > 240:
                    continue
                label_ctx = content[max(0, m.start() - 120) : min(len(content), m.end() + 240)]
                label = _strip_html(label_ctx)
                links.append({"href": href, "label_hint": label[:120] if label else ""})
                if len(links) >= 60:
                    break

            controls: list[dict[str, Any]] = []
            for m in re.finditer(r"(?is)<(input|select|textarea)\\b([^>]*)>", content):
                tag = (m.group(1) or "").lower()
                attrs = m.group(2) or ""
                def _attr(name: str) -> str | None:
                    pat = r"(?is)\b" + re.escape(name) + r"\s*=\s*['\"]([^'\"]+)['\"]"
                    mm = re.search(pat, attrs)
                    if not mm:
                        return None
                    v = (mm.group(1) or "").strip()
                    return v[:180] if v else None

                name = _attr("name")
                cid = _attr("id")
                ctype = _attr("type") or (tag if tag != "input" else "input")
                if not (name or cid):
                    continue
                controls.append({"tag": tag, "type": ctype, "name": name, "id": cid})
                if len(controls) >= 120:
                    break

            tables: list[dict[str, Any]] = []
            for tm in re.finditer(r"(?is)<table\\b[^>]*>(.*?)</table>", content):
                t_html = tm.group(1) or ""
                ths = [
                    _strip_html(x)
                    for x in re.findall(r"(?is)<th\\b[^>]*>(.*?)</th>", t_html)
                ]
                ths = [x for x in ths if x]
                row_count = len(re.findall(r"(?is)<tr\\b", t_html))
                tables.append({"headers": ths[:20], "row_count": row_count})
                if len(tables) >= 12:
                    break

            tag_candidates = list(dict.fromkeys(_PHTML_TAG_CANDIDATE_RE.findall(content)))
            if len(tag_candidates) > 250:
                tag_candidates = tag_candidates[:250]

            excerpt_lim = min(max(int(max_excerpt_chars), 0), 4000)
            excerpt = ""
            if excerpt_lim > 0:
                excerpt = _strip_html(content)[:excerpt_lim]

            out: dict[str, Any] = {
                "n_view_folder": folder,
                "relative_path": rel,
                "bytes": payload.get("bytes"),
                "headings": headings,
                "links": links,
                "controls": controls,
                "tables": tables,
                "tag_candidates": tag_candidates,
                "excerpt": excerpt,
            }
            if "panel" in payload:
                out["panel"] = payload["panel"]
            return out

        @mcp.tool(name=tool)
        def summarize_point_display_template(
            n_view_folder: str,
            relative_path: str,
            node_id: int | None = None,
            max_excerpt_chars: int = 1800,
        ) -> str:
            """Şablon özeti: tag referansları, menü yapısı, tablo ve form alanları."""
            return guard(prefixed_name(prefix, "summarize_point_display_template"), _summarize_point_display_template_impl)(
                n_view_folder, relative_path, node_id, max_excerpt_chars
            )

        # --- list_point_display_files ---
        tool = prefixed_name(prefix, "list_point_display_files")

        def _list_point_display_files_impl(
            n_view_folder: str,
            relative_dir: str = "",
            recursive: bool = True,
            limit: int = 500,
        ) -> Any:
            root = _point_display_root()
            if not root or not Path(root).is_dir():
                return {"error": "point_display_root tanımlı değil"}
            folder = (n_view_folder or "").strip()
            if not folder or not _FOLDER_RE.fullmatch(folder):
                return {"error": "Geçersiz n_view_folder"}
            lim = min(max(int(limit), 1), 2000)
            rel_dir = (relative_dir or "").strip()
            rel_dir_clean = ""
            if rel_dir:
                rel_dir_clean = _validate_rel_path(rel_dir)
                if not rel_dir_clean:
                    return {"error": "Geçersiz relative_dir"}
            base = Path(root).resolve()
            start = _safe_resolve_under(base, folder, rel_dir_clean) if rel_dir_clean else _safe_resolve_under(base, folder)
            if not start or not start.is_dir():
                return {"error": "Klasör bulunamadı", "n_view_folder": folder, "relative_dir": rel_dir_clean}

            out: list[str] = []
            truncated = False
            it = start.rglob("*") if bool(recursive) else start.glob("*")
            for p in it:
                if not p.is_file():
                    continue
                relp = str(p.relative_to(Path(root).resolve() / folder)).replace("\\", "/")
                fl = relp.lower()
                if fl.endswith(".phtml") or fl.endswith(".js"):
                    out.append(relp)
                    if len(out) >= lim:
                        truncated = True
                        break
            out.sort()
            return {
                "n_view_folder": folder,
                "relative_dir": rel_dir_clean,
                "recursive": bool(recursive),
                "limit": lim,
                "count": len(out),
                "truncated": truncated,
                "files": out,
            }

        @mcp.tool(name=tool)
        def list_point_display_files(n_view_folder: str, relative_dir: str = "", recursive: bool = True, limit: int = 500) -> str:
            """Şablon klasöründeki dosyalar. KORUBIN_POINT_DISPLAY_ROOT/{n_view_folder} altında .phtml/.js listeler."""
            return guard(tool, _list_point_display_files_impl)(n_view_folder, relative_dir, recursive, limit)

        # --- search_point_display_templates ---
        tool = prefixed_name(prefix, "search_point_display_templates")

        def _search_point_display_templates_impl(
            n_view_folder: str,
            query: str,
            case_insensitive: bool = True,
            limit: int = 50,
        ) -> Any:
            root = _point_display_root()
            if not root or not Path(root).is_dir():
                return {"error": "point_display_root tanımlı değil"}
            folder = (n_view_folder or "").strip()
            if not folder or not _FOLDER_RE.fullmatch(folder):
                return {"error": "Geçersiz n_view_folder"}
            q = (query or "").strip()
            if not q:
                return {"error": "query gerekli"}
            lim = min(max(int(limit), 1), 200)

            base = Path(root).resolve()
            start = _safe_resolve_under(base, folder)
            if not start or not start.is_dir():
                return {"error": "Klasör bulunamadı", "n_view_folder": folder}

            q_cmp = q.casefold() if case_insensitive else q
            max_files_scanned = 800
            max_total_bytes = 2_000_000
            total_bytes = 0
            scanned = 0
            matches: list[dict[str, Any]] = []
            skipped_too_big: list[str] = []

            for p in start.rglob("*.phtml"):
                if scanned >= max_files_scanned or len(matches) >= lim:
                    break
                if not p.is_file():
                    continue
                scanned += 1
                try:
                    sz = int(p.stat().st_size)
                except Exception:
                    continue
                if sz > 262144:
                    relp = str(p.relative_to(start)).replace("\\", "/")
                    skipped_too_big.append(relp)
                    continue
                if total_bytes + sz > max_total_bytes:
                    break
                try:
                    txt = p.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                total_bytes += sz

                hay = txt.casefold() if case_insensitive else txt
                if q_cmp not in hay:
                    continue
                relp = str(p.relative_to(start)).replace("\\", "/")
                idx = hay.find(q_cmp)
                start_i = max(0, idx - 80)
                end_i = min(len(txt), idx + len(q) + 160)
                excerpt = txt[start_i:end_i].replace("\n", " ").replace("\r", " ")
                matches.append({"relative_path": relp, "bytes": sz, "excerpt": excerpt})

            return {
                "n_view_folder": folder,
                "query": q,
                "case_insensitive": bool(case_insensitive),
                "limit": lim,
                "matched": len(matches),
                "files_scanned": scanned,
                "total_bytes_scanned": total_bytes,
                "results": matches,
                "skipped_too_big": skipped_too_big[:25],
            }

        @mcp.tool(name=tool)
        def search_point_display_templates(n_view_folder: str, query: str, case_insensitive: bool = True, limit: int = 50) -> str:
            """Şablonlarda metin arama. nView klasöründeki .phtml dosyalarında substring arar."""
            return guard(tool, _search_point_display_templates_impl)(n_view_folder, query, case_insensitive, limit)

        # --- get_panel_url_for_template ---
        tool = prefixed_name(prefix, "get_panel_url_for_template")

        def _get_panel_url_for_template_impl(
            node_id: int,
            relative_path: str,
            panel_base_url_override: str = "",
        ) -> Any:
            nid = int(node_id)
            if nid <= 0:
                return {"error": "node_id > 0 olmalı"}
            rel = _validate_rel_path(relative_path or "")
            if not rel:
                return {"error": "Geçersiz relative_path"}
            rel_norm = rel.replace("\\", "/")
            rel_lower = rel_norm.lower()
            if rel_lower.endswith(".phtml"):
                rel_norm = rel_norm[: -len(".phtml")]
                rel_lower = rel_lower[: -len(".phtml")]
            segment = rel_norm.strip("/").lstrip("/")
            if not segment:
                return {"error": "Segment üretilemedi"}
            base = (panel_base_url_override or "").strip().rstrip("/")
            if not base:
                base = _panel_base_url()
            if base and not re.match(r"^https?://", base, flags=re.IGNORECASE):
                base = "https://" + base.lstrip("/")

            basename = segment.split("/")[-1].strip().lower()
            is_default_like = basename in {"genel", "main"}
            if is_default_like:
                panel_path = f"/panel/point/{nid}/{segment}"
                return {
                    "node_id": nid,
                    "relative_path": rel,
                    "segment": segment,
                    "panel_path": panel_path,
                    "panel_link": (f"{base}{panel_path}" if base else None),
                    "panel_base": base or None,
                    "warning_tr": "GENEL/MAIN gibi dosyalar bazı kurulumlarda 'varsayılan ekran' olabilir; doğru segment panel uygulamasına göre değişebilir. Gerekirse MENU.phtml içindeki linkleri çıkarın.",
                }
            panel_path = f"/panel/point/{nid}/{segment}"
            return {
                "node_id": nid,
                "relative_path": rel,
                "segment": segment,
                "panel_path": panel_path,
                "panel_link": (f"{base}{panel_path}" if base else None),
                "panel_base": base or None,
            }

        @mcp.tool(name=tool)
        def get_panel_url_for_template(node_id: int, relative_path: str, panel_base_url_override: str = "") -> str:
            """Şablon için panel URL oluşturma. `.phtml` yolunu panel segment/URL'ye dönüştürür; varlık doğrulamaz."""
            return guard(prefixed_name(prefix, "get_panel_url_for_template"), _get_panel_url_for_template_impl)(
                node_id, relative_path, panel_base_url_override
            )

        # --- extract_menu_links ---
        tool = prefixed_name(prefix, "extract_menu_links")

        def _extract_menu_links_impl(n_view_folder: str, menu_path: str = "MENU.phtml", limit: int = 200) -> Any:
            root = _point_display_root()
            if not root or not Path(root).is_dir():
                return {"error": "point_display_root tanımlı değil"}
            folder = (n_view_folder or "").strip()
            if not folder or not _FOLDER_RE.fullmatch(folder):
                return {"error": "Geçersiz n_view_folder"}
            mp = _validate_rel_path(menu_path or "")
            if not mp:
                return {"error": "Geçersiz menu_path"}
            base = Path(root).resolve()
            target = _safe_resolve_under(base, folder, mp)
            if not target or not target.is_file():
                return {"error": "MENU dosyası bulunamadı", "menu_path": mp}
            if target.stat().st_size > 262144:
                return {"error": "Dosya çok büyük", "max_bytes": 262144, "file_bytes": target.stat().st_size}
            content = target.read_text(encoding="utf-8", errors="replace")
            lim = min(max(int(limit), 1), 1000)

            raw: list[str] = []
            for m in re.finditer(r"""(?i)\b(?:href|src)\s*=\s*["']([^"']+)["']""", content):
                raw.append(m.group(1))
            for m in re.finditer(r"""(?i)(\./[a-zA-Z0-9_./-]+)""", content):
                raw.append(m.group(1))
            raw = [r.strip() for r in raw if r and len(r.strip()) <= 200]

            candidates: list[dict[str, Any]] = []
            seen: set[str] = set()
            for r in raw:
                if len(candidates) >= lim:
                    break
                rr = r.strip()
                if rr in seen:
                    continue
                seen.add(rr)
                seg = None
                relp = None
                if rr.startswith("./"):
                    seg = rr[2:].lstrip("/")
                    relp = f"{seg}.phtml" if seg and not seg.endswith(".phtml") else seg
                elif rr.startswith("/panel/point/"):
                    parts = rr.split("/")
                    if len(parts) >= 5:
                        seg = "/".join(parts[5:]).strip("/")
                        relp = f"{seg}.phtml" if seg else None
                else:
                    guess = rr.lstrip("/").strip()
                    if guess and _validate_rel_path(guess.replace("?", "/").split("#")[0]) is not None:
                        seg = guess.split("?")[0].split("#")[0].strip("/")
                        if seg:
                            relp = f"{seg}.phtml" if not seg.lower().endswith(".phtml") else seg
                candidates.append({"raw": rr, "segment_guess": seg, "relative_path_guess": relp})

            return {"n_view_folder": folder, "menu_path": mp, "count": len(candidates), "candidates": candidates}

        @mcp.tool(name=tool)
        def extract_menu_links(n_view_folder: str, menu_path: str = "MENU.phtml", limit: int = 200) -> str:
            """Şablondaki menü linkleri. MENU.phtml içinden panel segment/link adaylarını çıkarır."""
            return guard(tool, _extract_menu_links_impl)(n_view_folder, menu_path, limit)

    def manifest_groups(self, *, prefix: str) -> list[dict]:
        p = prefix
        return [
            {
                "id": "semantics",
                "title_tr": "Panel semantik / şablon",
                "tools": [
                    p + "list_point_display_templates",
                    p + "read_point_display_template",
                    p + "list_point_display_files",
                    p + "search_point_display_templates",
                    p + "get_panel_url_for_template",
                    p + "extract_menu_links",
                    p + "summarize_point_display_template",
                ],
            },
        ]
