"""Tag-related tools: search_tags, get_device_tag_values, list_live_tag_across_nodes,
get_scada_system_stats, get_korubin_data_concepts, get_device_data,
get_nview_equipment_profile, get_scada_semantics, get_view_tag_meanings,
get_counter_semantics, resolve_semantic_tag_candidates.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..tools.core import guard, prefixed_name
from ..types import InstanceConfig
from .. import db as dbmod

log = logging.getLogger(__name__)

_TAG_RE = re.compile(r"^[a-zA-Z0-9_]+$")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _php_data_scada_path(name: str) -> Path:
    return _project_root() / "eskiprojeornekicin" / "data" / "scada" / name


def _load_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _try_load_json_file(path: Path) -> tuple[Any | None, dict[str, Any] | None]:
    if not path.exists():
        return None, {
            "type": "missing_json",
            "message": f"JSON dosyası bulunamadı: {path.name}",
            "expected_path": str(path),
        }
    try:
        return _load_json_file(path), None
    except Exception as e:
        return None, {
            "type": "invalid_json",
            "message": f"JSON okunamadı: {path.name} ({e.__class__.__name__})",
            "expected_path": str(path),
        }


def _normalize_turkish_text(text: str) -> str:
    tr = ["ç", "Ç", "ğ", "Ğ", "ı", "İ", "ö", "Ö", "ş", "Ş", "ü", "Ü"]
    en = ["c", "C", "g", "G", "i", "I", "o", "O", "s", "S", "u", "U"]
    for a, b in zip(tr, en, strict=False):
        text = text.replace(a, b)
    text = re.sub(r"[^\w\s\.\-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text, flags=re.UNICODE)
    return text.strip()


def _normalize_nview(nview: str) -> str:
    if nview.startswith("_a-multi"):
        return nview.replace("_a-multi", "a-system", 1)
    return nview


class ScadaTagsPack:
    """Tag/semantic tools ported from PHP ScadaTools + ScreenSemanticsTools."""

    id = "scada_tags"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix

        # --- get_scada_system_stats ---
        tool = prefixed_name(prefix, "get_scada_system_stats")

        def _get_scada_system_stats_impl(top_nodes: int = 15) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            top_nodes = min(max(int(top_nodes), 0), 50)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) AS c FROM kbindb._tagoku")
                    total_rows = int(cur.fetchone()["c"])
                    cur.execute("SELECT COUNT(DISTINCT devId) AS c FROM kbindb._tagoku")
                    device_count = int(cur.fetchone()["c"])
                    cur.execute("SELECT COUNT(DISTINCT tagName) AS c FROM kbindb._tagoku")
                    distinct_tag_names = int(cur.fetchone()["c"])

                    counter_rows = 0
                    counter_devices = 0
                    try:
                        cur.execute("SELECT COUNT(*) AS c FROM kbindb._servercounters")
                        counter_rows = int(cur.fetchone()["c"])
                        cur.execute("SELECT COUNT(DISTINCT devId) AS c FROM kbindb._servercounters")
                        counter_devices = int(cur.fetchone()["c"])
                    except Exception:
                        pass

                    cur.execute("SELECT MIN(readTime) AS en_eski, MAX(readTime) AS en_guncel FROM kbindb._tagoku")
                    read_bounds = cur.fetchone()

                    top_list: list[dict[str, Any]] = []
                    if top_nodes > 0:
                        cur.execute(
                            f"""
                            SELECT t.devId AS node_id, n.nName AS node_adi, COUNT(*) AS tag_satir_sayisi
                            FROM kbindb._tagoku t
                            LEFT JOIN kbindb.node n ON n.id = t.devId
                            GROUP BY t.devId, n.nName
                            ORDER BY tag_satir_sayisi DESC
                            LIMIT {top_nodes}
                            """
                        )
                        top_list = list(cur.fetchall())

            return {
                "sozluk_tr": {
                    "_tagoku": "Bellekte tutulan anlık PLC/OPC tag değerleri. Her satır = bir cihaz (devId) + bir tag adı (tagName). devId genelde node.id ile aynıdır.",
                    "toplam_tag_satiri": "Tüm sistemdeki _tagoku satır sayısı = tüm noktalardaki canlı tag kayıtlarının toplamı (aynı isimli tag farklı noktalarda ayrı satırdır).",
                    "cihaz_sayisi": "En az bir canlı tag satırı olan farklı devId (nokta) sayısı.",
                    "benzersiz_tag_adi": "Sistem genelinde kaç farklı tagName kullanıldığı (ad çeşitliliği).",
                    "tek_nokta": "Bir noktanın tüm tagları için get_device_data(deviceId) veya get_device_tag_values.",
                },
                "istatistik": {
                    "tagoku_toplam_satir": total_rows,
                    "tagoku_farkli_cihaz": device_count,
                    "tagoku_benzersiz_tag_adi": distinct_tag_names,
                    "servercounters_toplam_satir": counter_rows,
                    "servercounters_farkli_cihaz": counter_devices,
                    "tagoku_okuma_zamani": {
                        "en_eski": (read_bounds or {}).get("en_eski"),
                        "en_guncel": (read_bounds or {}).get("en_guncel"),
                    },
                },
                "en_cok_tagi_olan_noktalar": top_list,
                "ilgili_araclar_tr": "Tam kurumsal özet: get_scada_summary. Aynı tag tüm noktalar: list_live_tag_across_nodes. LIKE arama: search_tags. Şema: get_database_schema.",
            }

        @mcp.tool(name=tool)
        def get_scada_system_stats(top_nodes: int = 15) -> str:
            """Sistem istatistikleri: tag sayıları, cihaz dağılımı, en çok tag'e sahip node'lar."""
            return guard(tool, _get_scada_system_stats_impl)(top_nodes)

        # --- get_korubin_data_concepts ---
        tool = prefixed_name(prefix, "get_korubin_data_concepts")

        def _get_korubin_data_concepts_impl() -> Any:
            path = _php_data_scada_path("korubin_data_concepts.json")
            if not path.exists():
                raise RuntimeError("korubin_data_concepts.json bulunamadı")
            return _load_json_file(path)

        @mcp.tool(name=tool)
        def get_korubin_data_concepts() -> str:
            """SCADA veri kavramları: tag, node, alarm, log ilişkileri."""
            return guard(tool, _get_korubin_data_concepts_impl)()

        # --- get_device_data ---
        tool = prefixed_name(prefix, "get_device_data")

        def _get_device_data_impl(deviceId: int, limit_tags: int = 0, limit_counters: int = 0) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            did = int(deviceId)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, nName, nType, nPath FROM node WHERE id = %s", (did,))
                    node = cur.fetchone()
                    lim_tags = int(limit_tags or 0)
                    lim_cnt = int(limit_counters or 0)
                    if lim_tags < 0:
                        lim_tags = 0
                    if lim_cnt < 0:
                        lim_cnt = 0
                    lim_tags = min(lim_tags, 5000)
                    lim_cnt = min(lim_cnt, 5000)

                    tag_sql = "SELECT tagName, tagValue, readTime FROM _tagoku WHERE devId = %s ORDER BY tagName"
                    cnt_sql = "SELECT tagName, tagValue, readTime FROM _servercounters WHERE devId = %s ORDER BY tagName"
                    if lim_tags > 0:
                        tag_sql = tag_sql + " LIMIT %s"
                        cur.execute(tag_sql, (did, lim_tags))
                    else:
                        cur.execute(tag_sql, (did,))
                    tags = list(cur.fetchall())

                    if lim_cnt > 0:
                        cnt_sql = cnt_sql + " LIMIT %s"
                        cur.execute(cnt_sql, (did, lim_cnt))
                    else:
                        cur.execute(cnt_sql, (did,))
                    counters = list(cur.fetchall())
            return {
                "device_id": did,
                "node": node or None,
                "tag_sayisi": len(tags),
                "tags": tags,
                "counter_sayisi": len(counters),
                "counters": counters,
                "limits": {
                    "limit_tags": lim_tags,
                    "limit_counters": lim_cnt,
                    "note_tr": "limit_* = 0 ise LIMIT uygulanmaz. Büyük node'larda LM Studio context taşmasını önlemek için limit kullanın.",
                },
            }

        @mcp.tool(name=tool)
        def get_device_data(deviceId: int, limit_tags: int = 0, limit_counters: int = 0) -> str:
            """Cihaz detayı: channel, device, connection bilgileri."""
            return guard(tool, _get_device_data_impl)(deviceId, limit_tags, limit_counters)

        # --- get_device_tag_values ---
        tool = prefixed_name(prefix, "get_device_tag_values")

        def _get_device_tag_values_impl(deviceId: int, tag_names: str) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            did = int(deviceId)
            raw = re.split(r"[\s,]+", (tag_names or "").strip())
            names: list[str] = []
            for t in raw:
                t = t.strip()
                if t and len(t) <= 128 and _TAG_RE.fullmatch(t):
                    names.append(t)
            names = list(dict.fromkeys(names))
            if not names:
                return {"error": "Geçerli tag_names gerekli", "device_id": did}
            if len(names) > 80:
                names = names[:80]
            placeholders = ",".join(["%s"] * len(names))
            sql = f"SELECT tagName, tagValue, readTime FROM _tagoku WHERE devId = %s AND tagName IN ({placeholders}) ORDER BY tagName"
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, tuple([did] + names))
                    rows = list(cur.fetchall())
            found = {r["tagName"]: r for r in rows if "tagName" in r}
            missing = [n for n in names if n not in found]
            return {
                "device_id": did,
                "requested": names,
                "found_count": len(found),
                "tags": list(found.values()),
                "not_in_tagoku": missing,
            }

        @mcp.tool(name=tool)
        def get_device_tag_values(deviceId: int, tag_names: str) -> str:
            """Cihazın anlık tag değerleri (_tagoku)."""
            return guard(tool, _get_device_tag_values_impl)(deviceId, tag_names)

        # --- list_live_tag_across_nodes ---
        tool = prefixed_name(prefix, "list_live_tag_across_nodes")

        def _list_live_tag_across_nodes_impl(
            tag_name: str = "",
            preset: str = "",
            match: str = "exact",
            limit: int = 500,
        ) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 2000)
            match_l = (match or "").strip().lower()
            if match_l not in {"exact", "like"}:
                match_l = "exact"

            presets = {
                "hidrolik_verim": "YaklasikHidrolikVerim",
                "yaklasik_verim": "YaklasikHidrolikVerim",
                "verim": "YaklasikHidrolikVerim",
                "debimetre": "Debimetre",
                "t_su_sayac": "T_SuSayac",
                "su_sayac": "T_SuSayac",
            }
            tag = (tag_name or "").strip()
            p = (preset or "").strip().lower()
            if not tag and p and p in presets:
                tag = presets[p]
            if not tag:
                return {
                    "error": "tag_name veya preset gerekli",
                    "preset_ornekleri": list(presets.keys()),
                    "ornek_tag": "YaklasikHidrolikVerim",
                }
            if not _TAG_RE.fullmatch(tag):
                return {"error": "tag_name yalnız harf, rakam ve _ içerebilir"}

            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    if match_l == "exact":
                        cur.execute(
                            """
                            SELECT t.devId AS node_id, n.nName AS node_adi, n.nView AS n_view, t.tagName, t.tagValue, t.readTime
                            FROM kbindb._tagoku t
                            LEFT JOIN kbindb.node n ON n.id = t.devId
                            WHERE t.tagName = %s
                            ORDER BY n.nName ASC, t.devId ASC
                            LIMIT %s
                            """,
                            (tag, limit),
                        )
                    else:
                        cur.execute(
                            """
                            SELECT t.devId AS node_id, n.nName AS node_adi, n.nView AS n_view, t.tagName, t.tagValue, t.readTime
                            FROM kbindb._tagoku t
                            LEFT JOIN kbindb.node n ON n.id = t.devId
                            WHERE t.tagName LIKE %s
                            ORDER BY n.nName ASC, t.devId ASC, t.tagName ASC
                            LIMIT %s
                            """,
                            (f"%{tag}%", limit),
                        )
                    rows = list(cur.fetchall())
            return {
                "tag_sorgusu": tag,
                "match": match_l,
                "satir_sayisi": len(rows),
                "limit": limit,
                "satirlar": rows,
            }

        @mcp.tool(name=tool)
        def list_live_tag_across_nodes(tag_name: str = "", preset: str = "", match: str = "exact", limit: int = 500) -> str:
            """Birden fazla node'da aynı tag adının anlık değerleri."""
            return guard(tool, _list_live_tag_across_nodes_impl)(tag_name, preset, match, limit)

        # --- search_tags ---
        tool = prefixed_name(prefix, "search_tags")

        def _search_tags_impl(tagName: str, limit: int = 100) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 500)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT t.devId, n.nName AS node_adi, t.tagName, t.tagValue, t.readTime
                        FROM _tagoku t
                        LEFT JOIN node n ON t.devId = n.id
                        WHERE t.tagName LIKE %s
                        ORDER BY t.devId, t.tagName
                        LIMIT %s
                        """,
                        (f"%{tagName}%", limit),
                    )
                    results = list(cur.fetchall())
            return {"search": tagName, "count": len(results), "results": results}

        @mcp.tool(name=tool)
        def search_tags(tagName: str, limit: int = 100) -> str:
            """_tagoku canlı tag arama. Ürün dokümanı için get_product_specs kullanın."""
            return guard(tool, _search_tags_impl)(tagName, limit)

        # --- get_nview_equipment_profile ---
        tool = prefixed_name(prefix, "get_nview_equipment_profile")

        def _get_nview_equipment_profile_impl(n_view: str) -> Any:
            n_view = (n_view or "").strip()
            if not n_view:
                return {"error": "n_view gerekli"}
            p = _php_data_scada_path("nview_equipment_hints.json")
            data, warn = _try_load_json_file(p)
            if warn:
                return {
                    "n_view": n_view,
                    "matched": False,
                    "match_type": None,
                    "warning": warn,
                    "note_tr": "İpucu JSON'u yoksa bu araç yalnızca 'missing' uyarısı döndürür.",
                }
            header = {"global_note_tr": data.get("global_note_tr"), "aqua_rule_tr": data.get("aqua_rule_tr")}
            v = n_view.strip().lower()
            exact = data.get("exact") or {}
            for k, row in exact.items():
                if str(k).lower() == v and isinstance(row, dict):
                    out = {**header, "matched": True, "match_type": "exact", "n_view": n_view}
                    out.update(row)
                    return out
            prefixes = list(data.get("prefix_match") or [])
            prefixes.sort(key=lambda r: len(str(r.get("prefix", ""))), reverse=True)
            for row in prefixes:
                if not isinstance(row, dict):
                    continue
                pfx = str(row.get("prefix", "")).strip().lower()
                if pfx and v.startswith(pfx):
                    out = {**header, "matched": True, "match_type": "prefix", "matched_prefix": pfx, "n_view": n_view}
                    copy = dict(row)
                    copy.pop("prefix", None)
                    out.update(copy)
                    return out
            suffixes = list(data.get("suffix_match") or [])
            suffixes.sort(key=lambda r: len(str(r.get("suffix", ""))), reverse=True)
            for row in suffixes:
                if not isinstance(row, dict):
                    continue
                sfx = str(row.get("suffix", "")).strip().lower()
                if sfx and v.endswith(sfx):
                    out = {**header, "matched": True, "match_type": "suffix", "matched_suffix": sfx, "n_view": n_view}
                    copy = dict(row)
                    copy.pop("suffix", None)
                    out.update(copy)
                    return out
            default = data.get("default") or {}
            out = {**header, "matched": True, "match_type": "default", "n_view": n_view}
            if isinstance(default, dict):
                out.update(default)
            return out

        @mcp.tool(name=tool)
        def get_nview_equipment_profile(n_view: str) -> str:
            """nView ekipman profili: tag şablonları."""
            return guard(prefixed_name(prefix, "get_nview_equipment_profile"), _get_nview_equipment_profile_impl)(n_view)

        # --- get_scada_semantics ---
        tool = prefixed_name(prefix, "get_scada_semantics")

        def _get_scada_semantics_impl(section: str = "all") -> Any:
            cfg_json = _load_json_file(_php_data_scada_path("tag_semantic_defaults.json"))
            s = (section or "all").strip().lower()
            if s == "all":
                return cfg_json
            if s == "meta":
                return {
                    "version": cfg_json.get("version"),
                    "description": cfg_json.get("description"),
                    "resolution_order": cfg_json.get("resolution_order"),
                }
            if s in cfg_json:
                return cfg_json[s]
            return {
                "error": "Geçersiz section",
                "allowed": ["all", "prefix_rules", "semantic_aliases", "views", "nview_overrides", "meta"],
            }

        @mcp.tool(name=tool)
        def get_scada_semantics(section: str = "all") -> str:
            """SCADA semantik tanımları."""
            return guard(tool, _get_scada_semantics_impl)(section)

        # --- get_view_tag_meanings ---
        tool = prefixed_name(prefix, "get_view_tag_meanings")

        def _resolve_view_description_key(normalized_view: str, views_data: dict) -> str:
            lower_map = {str(k).lower(): str(k) for k in views_data.keys()}
            k = normalized_view.lower()
            if k in lower_map:
                return lower_map[k]
            if "dma" in k and "a-dma-envest" in lower_map:
                return lower_map["a-dma-envest"]
            if k.startswith("a-system"):
                fallback = "a-system-kalecik" if k == "a-system-kalecik" else "a-system"
                return lower_map.get(fallback, fallback)
            return lower_map.get("default", "default")

        def _get_view_tag_meanings_impl(nView: str) -> Any:
            p = _php_data_scada_path("view_tag_descriptions.json")
            data, warn = _try_load_json_file(p)
            views = (data or {}).get("views") or {}
            normalized = _normalize_nview((nView or "").strip())
            if not isinstance(views, dict) or not views:
                return {
                    "n_view_input": nView,
                    "normalized_n_view": normalized,
                    "description_key": None,
                    "tag_count": 0,
                    "tags": {},
                    "warning": warn
                    or {
                        "type": "empty_json",
                        "message": "view_tag_descriptions.json içinde views boş veya geçersiz",
                        "expected_path": str(p),
                    },
                }
            key = _resolve_view_description_key(normalized, views)
            tags = views.get(key) or {}
            return {
                "n_view_input": nView,
                "normalized_n_view": normalized,
                "description_key": key,
                "tag_count": len(tags) if isinstance(tags, dict) else 0,
                "tags": tags,
            }

        @mcp.tool(name=tool)
        def get_view_tag_meanings(nView: str) -> str:
            """View'a özel tag anlamları."""
            return guard(prefixed_name(prefix, "get_view_tag_meanings"), _get_view_tag_meanings_impl)(nView)

        # --- get_counter_semantics ---
        tool = prefixed_name(prefix, "get_counter_semantics")

        def _get_counter_semantics_impl(group: str = "") -> Any:
            data = _load_json_file(_php_data_scada_path("counter_semantic_defaults.json"))
            g = (group or "").strip().lower()
            if not g:
                return data
            if g not in data:
                return {"error": "Grup yok", "allowed": list(data.keys())}
            return {g: data[g]}

        @mcp.tool(name=tool)
        def get_counter_semantics(group: str = "") -> str:
            """Sayaç semantikleri."""
            return guard(tool, _get_counter_semantics_impl)(group)

        # --- resolve_semantic_tag_candidates ---
        tool = prefixed_name(prefix, "resolve_semantic_tag_candidates")

        def _resolve_view_group(view_lower: str) -> str:
            if not view_lower:
                return "default"
            if "dma" in view_lower:
                return "dma"
            if ("kuyu" in view_lower) or ("well" in view_lower):
                return "kuyu"
            if ("depo" in view_lower) or ("tank" in view_lower) or ("store" in view_lower):
                return "depo"
            if ("terfi" in view_lower) or ("riser" in view_lower) or ("pump" in view_lower):
                return "terfi"
            return "default"

        def _unique_case_insensitive(tags: list[str]) -> list[str]:
            out: list[str] = []
            seen: set[str] = set()
            for t in tags:
                t = str(t).strip()
                if not t:
                    continue
                k = t.lower()
                if k in seen:
                    continue
                seen.add(k)
                out.append(t)
            return out

        def _resolve_semantic_key_from_text(text: str, semantic_aliases: dict) -> str | None:
            normalized = _normalize_turkish_text((text or "").lower())
            for sk, aliases in semantic_aliases.items():
                for alias in (aliases or []):
                    alias_norm = _normalize_turkish_text(str(alias).strip().lower())
                    if alias_norm and alias_norm in normalized:
                        return str(sk)
            return None

        def _merge_semantic_candidates(cfg_json: dict, exact_view_lower: str, group_key: str, semantic_key: str) -> list[str]:
            views = {str(k).lower(): v for k, v in (cfg_json.get("views") or {}).items()}
            nview_overrides_raw = cfg_json.get("nview_overrides") or {}
            nview_overrides = {str(k).lower(): v for k, v in (nview_overrides_raw or {}).items()}
            exact_map = (nview_overrides.get(exact_view_lower) or {}) if isinstance(nview_overrides.get(exact_view_lower), dict) else {}
            group_map = (views.get(group_key) or {}) if isinstance(views.get(group_key), dict) else {}
            default_map = (views.get("default") or {}) if isinstance(views.get("default"), dict) else {}
            tags = []
            tags.extend(list((exact_map.get(semantic_key) or [])))
            tags.extend(list((group_map.get(semantic_key) or [])))
            tags.extend(list((default_map.get(semantic_key) or [])))
            return _unique_case_insensitive([str(t) for t in tags])

        def _resolve_semantic_tag_candidates_impl(node_id: int, query_text: str = "", semantic_key: str = "", n_view_override: str = "") -> Any:
            cfg_json = _load_json_file(_php_data_scada_path("tag_semantic_defaults.json"))
            semantic_aliases = cfg_json.get("semantic_aliases") or {}
            key = (semantic_key or "").strip()
            if not key and (query_text or "").strip():
                resolved = _resolve_semantic_key_from_text(query_text, semantic_aliases if isinstance(semantic_aliases, dict) else {})
                key = resolved or ""
            if not key:
                return {
                    "error": "semantic_key veya eşleşen query_text gerekli",
                    "semantic_keys_sample": list((semantic_aliases or {}).keys())[:15] if isinstance(semantic_aliases, dict) else [],
                }
            exact = (n_view_override or "").strip().lower()
            if int(node_id) > 0 and not exact:
                if not cfg.db:
                    raise RuntimeError("DB config is missing for this instance.")
                with dbmod.connect(cfg.db) as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT nView FROM node WHERE id = %s LIMIT 1", (int(node_id),))
                        row = cur.fetchone() or {}
                        exact = str(row.get("nView") or "").strip().lower()
            group = _resolve_view_group(exact)
            candidates = _merge_semantic_candidates(cfg_json, exact, group, key)
            return {
                "semantic_key": key,
                "node_id": int(node_id),
                "n_view_exact_lower": exact,
                "view_group": group,
                "tag_candidates": candidates,
                "resolution_order": cfg_json.get("resolution_order"),
            }

        @mcp.tool(name=tool)
        def resolve_semantic_tag_candidates(node_id: int, query_text: str = "", semantic_key: str = "", n_view_override: str = "") -> str:
            """Semantik tag aday çözümleme."""
            return guard(tool, _resolve_semantic_tag_candidates_impl)(node_id, query_text, semantic_key, n_view_override)

    def manifest_groups(self, *, prefix: str) -> list[dict]:
        p = prefix
        return [
            {
                "id": "scada_live",
                "title_tr": "SCADA canlı veri (_tagoku)",
                "tools": [
                    p + "get_scada_system_stats",
                    p + "get_device_data",
                    p + "get_device_tag_values",
                    p + "list_live_tag_across_nodes",
                    p + "search_tags",
                ],
            },
            {
                "id": "concepts",
                "title_tr": "Kavram rehberi",
                "tools": [p + "get_korubin_data_concepts"],
            },
            {
                "id": "semantics",
                "title_tr": "Panel semantik",
                "tools": [
                    p + "get_nview_equipment_profile",
                    p + "get_scada_semantics",
                    p + "get_view_tag_meanings",
                    p + "get_counter_semantics",
                    p + "resolve_semantic_tag_candidates",
                ],
            },
        ]
