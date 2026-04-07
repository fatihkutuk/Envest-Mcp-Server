from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..tools.core import guard, prefixed_name
from ..types import InstanceConfig
from .. import db as dbmod


_TAG_RE = re.compile(r"^[a-zA-Z0-9_]+$")
_FOLDER_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_WS_RE = re.compile(r"\s+")
_HTML_ENTITY_RE = re.compile(r"&(?:nbsp|amp|lt|gt|quot|apos);", flags=re.IGNORECASE)
_PHTML_TAG_CANDIDATE_RE = re.compile(r"\b[A-Z]{1,4}_[A-Za-z0-9_]{2,64}\b")


def _strip_html(text: str) -> str:
    # Very small HTML-ish normalizer (good enough for phtml snapshots).
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


def _project_root() -> Path:
    # toolpacks/ -> scada_mcp/ -> src/ -> py-scada-mcp/
    return Path(__file__).resolve().parents[3]


def _php_data_scada_path(name: str) -> Path:
    return _project_root() / "eskiprojeornekicin" / "data" / "scada" / name


def _load_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _try_load_json_file(path: Path) -> tuple[Any | None, dict[str, Any] | None]:
    """
    Return (data, warning_payload). Never raises.
    warning_payload shape is stable for MCP clients.
    """
    if not path.exists():
        return None, {
            "type": "missing_json",
            "message": f"JSON dosyası bulunamadı: {path.name}",
            "expected_path": str(path),
        }
    try:
        return _load_json_file(path), None
    except Exception as e:  # noqa: BLE001
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


class ScadaPortedPack:
    """
    Direct port of PHP tools from `eskiprojeornekicin/src/Tools/*.php`.

    Goal: preserve base tool names and JSON shapes; prefixing is applied via InstanceConfig.tool_prefix.
    """

    id = "scada_ported"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix

        # --- ScadaTools.php ---
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

        # --- NodeTools.php ---
        tool = prefixed_name(prefix, "get_node_counts")

        def _get_node_counts_impl() -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT n.nState,
                               CASE n.nState
                                   WHEN -1 THEN 'silinmis'
                                   WHEN 0 THEN 'deaktif'
                                   WHEN 5 THEN 'test'
                                   WHEN 10 THEN 'demo'
                                   WHEN 100 THEN 'aktif'
                                   ELSE 'diger'
                               END AS anahtar,
                               COUNT(*) AS sayi
                        FROM node n
                        GROUP BY n.nState
                        ORDER BY n.nState
                        """
                    )
                    by_state_all = list(cur.fetchall())

                    cur.execute("SELECT COUNT(*) AS c FROM node")
                    toplam = int(cur.fetchone()["c"])
                    cur.execute("SELECT COUNT(*) AS c FROM node WHERE nState >= 0")
                    silinmis_haric = int(cur.fetchone()["c"])

                    def counts_by_state_for_ntype(nt: int) -> dict[str, Any]:
                        cur.execute(
                            """
                            SELECT n.nState,
                                   CASE n.nState
                                       WHEN -1 THEN 'silinmis'
                                       WHEN 0 THEN 'deaktif'
                                       WHEN 5 THEN 'test'
                                       WHEN 10 THEN 'demo'
                                       WHEN 100 THEN 'aktif'
                                       ELSE 'diger'
                                   END AS anahtar,
                                   COUNT(*) AS sayi
                            FROM node n
                            WHERE n.nType = %s
                            GROUP BY n.nState
                            ORDER BY n.nState
                            """,
                            (nt,),
                        )
                        rows = list(cur.fetchall())
                        m = {int(r["nState"]): int(r["sayi"]) for r in rows}
                        st_rows = [{"nState": int(r["nState"]), "anahtar": str(r["anahtar"]), "sayi": int(r["sayi"])} for r in rows]
                        return {
                            "nstate_dagilimi": st_rows,
                            "toplam": int(sum(m.values())),
                            "aktif_100": int(m.get(100, 0)),
                            "deaktif_0": int(m.get(0, 0)),
                            "silinmis": int(m.get(-1, 0)),
                        }

                    nokta777 = counts_by_state_for_ntype(777)
                    sistem666 = counts_by_state_for_ntype(666)

                    cur.execute("SELECT n.nType, COUNT(*) AS sayi FROM node n GROUP BY n.nType ORDER BY n.nType")
                    ntype_ozet = list(cur.fetchall())
                    ntype_panel = {
                        "1": "Ulke",
                        "2": "Sehir",
                        "3": "Kurum",
                        "4": "Birim",
                        "666": "Sistem",
                        "777": "Nokta",
                    }
                    for r in ntype_ozet:
                        k = str(r.get("nType", "")).strip()
                        r["panel_etiket_tr"] = ntype_panel.get(k, "Diger")
                        r["sayi"] = int(r["sayi"])

            kisa = (
                f"Panel «Nokta» (nType 777): toplam {nokta777['toplam']}; aktif (nState 100) {nokta777['aktif_100']}; "
                f"deaktif (0) {nokta777['deaktif_0']}; silinmiş (-1) {nokta777['silinmis']}. "
                f"«Sistem» (666): toplam {sistem666['toplam']}; aktif {sistem666['aktif_100']}. Tüm node tablosu satırı: {toplam}."
            )
            return {
                "_kisa_cevap": kisa,
                "soru_nokta_sayisi_ntype_777": {
                    "toplam": nokta777["toplam"],
                    "aktif_nstate_100": nokta777["aktif_100"],
                    "deaktif_nstate_0": nokta777["deaktif_0"],
                    "silinmis_nstate_minus1": nokta777["silinmis"],
                    "nstate_dagilimi": nokta777["nstate_dagilimi"],
                },
                "soru_sistem_sayisi_ntype_666": {
                    "toplam": sistem666["toplam"],
                    "aktif_nstate_100": sistem666["aktif_100"],
                    "deaktif_nstate_0": sistem666["deaktif_0"],
                    "silinmis_nstate_minus1": sistem666["silinmis"],
                    "nstate_dagilimi": sistem666["nstate_dagilimi"],
                },
                "tum_node_tablosu_ozet": {
                    "toplam_satir": toplam,
                    "silinmis_haric": silinmis_haric,
                    "nstate_dagilimi": by_state_all,
                },
                "ntype_dagilimi_panel": ntype_ozet,
                "not_tr": "Korubin arayüzünde «Nokta» seçeneği nType=777; «Sistem»=666. «Kaç nokta var» sorusu genelde 777 toplamını ifade eder. nState 100=aktif, 0=deaktif.",
            }

        @mcp.tool(name=tool)
        def get_node_counts() -> str:
            """Node sayıları: nType ve nView bazında."""
            return guard(tool, _get_node_counts_impl)()

        tool = prefixed_name(prefix, "list_nodes")

        def _list_nodes_impl(
            nType: str = "",
            nState: int = -999,
            search: str = "",
            limit: int = 50,
            offset: int = 0,
            *,
            sort_by_name_len: bool = False,
        ) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 200)
            offset = max(int(offset), 0)
            where: list[str] = []
            params: list[Any] = []
            if nType:
                where.append("n.nType = %s")
                params.append(nType)
            if int(nState) != -999:
                where.append("n.nState = %s")
                params.append(int(nState))
            # nView + ürün tipi (pt.name): isimde «dma» geçmeyen DMA istasyonları için (ör. Koru1000 Aqua CNT DMA)
            def _search_or_cols(pat: str) -> tuple[str, list[Any]]:
                clause = (
                    "(n.nName LIKE %s OR n.nPath LIKE %s OR n.nDev LIKE %s "
                    "OR LOWER(IFNULL(n.nView,'')) LIKE LOWER(%s) "
                    "OR LOWER(TRIM(IFNULL(pt.name,''))) LIKE LOWER(%s))"
                )
                return clause, [pat, pat, pat, pat, pat]

            if search:
                q = search.strip()
                parts = [p for p in q.split() if p]
                if len(parts) > 1:
                    for p in parts:
                        pat = f"%{p}%"
                        c, ps = _search_or_cols(pat)
                        where.append(c)
                        params.extend(ps)
                else:
                    pat = f"%{q}%"
                    c, ps = _search_or_cols(pat)
                    where.append(c)
                    params.extend(ps)
            where_sql = ("WHERE " + " AND ".join(where)) if where else ""
            order_clause = (
                "ORDER BY LENGTH(n.nName) ASC, n.id DESC" if sort_by_name_len else "ORDER BY n.id DESC"
            )
            from_join = """
                FROM node n
                LEFT JOIN node_product_type pt ON n.nView = pt.nView
            """
            sql = f"""
                SELECT n.id, n.nName, n.nNo, n.nType, n.nBase, n.nView, n.nPath, n.nDev,
                       n.nState, n.nTags, n.nTime,
                       pt.name AS urun_tipi
                {from_join}
                {where_sql}
                {order_clause}
                LIMIT %s OFFSET %s
            """
            sql_count = f"SELECT COUNT(*) AS total {from_join} {where_sql}"
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, tuple(params + [limit, offset]))
                    nodes = list(cur.fetchall())
                    cur.execute(sql_count, tuple(params))
                    total = int(cur.fetchone()["total"])
            return {"total": total, "count": len(nodes), "limit": limit, "offset": offset, "nodes": nodes}

        @mcp.tool(name=tool)
        def list_nodes(
            nType: str = "",
            nState: int = -999,
            search: str = "",
            ara: str = "",
            limit: int = 50,
            offset: int = 0,
        ) -> str:
            """Node listesi (filtreleme ve sayfalama). Arama: nName, nPath, nDev, nView, ürün tipi; birden fazla kelime AND ile daraltılır."""
            merged = (search or ara or "").strip()
            return guard(tool, _list_nodes_impl)(nType, nState, merged, limit, offset)

        tool = prefixed_name(prefix, "find_nodes_by_keywords")

        def _find_nodes_by_keywords_impl(
            keywords: str = "",
            nType: str = "",
            limit: int = 20,
            anahtar_kelime: str = "",
            ara: str = "",
        ) -> Any:
            kw = (keywords or anahtar_kelime or ara or "").strip()
            if not kw:
                return {"error": "keywords veya ara veya anahtar_kelime gerekli", "ornek": "dma, Serbest Bölge Kuyu"}
            lim = min(max(int(limit), 1), 100)
            out = _list_nodes_impl(nType, -999, kw, lim, 0, sort_by_name_len=True)
            if isinstance(out, dict) and "nodes" in out:
                out["hint_tr"] = (
                    "İlk satırlar genelde en kısa ve en iyi isim eşleşmesidir; birden fazla satır varsa "
                    "nName ve urun_tipi ile seçin (kuyu: genelde «Koru1000 Well» / nView a-kuyu-envest)."
                )
            return out

        @mcp.tool(name=tool)
        def find_nodes_by_keywords(
            keywords: str = "",
            nType: str = "",
            limit: int = 20,
            anahtar_kelime: str = "",
            ara: str = "",
        ) -> str:
            """Node arama (isim, nView, nType). nView alt dizgesi ve ürün tipi adı dahil aranır."""
            return guard(tool, _find_nodes_by_keywords_impl)(
                keywords, nType, limit, anahtar_kelime, ara
            )

        tool = prefixed_name(prefix, "get_node")

        def _get_node_impl(nodeId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            nid = int(nodeId)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT n.*, pt.name AS urun_tipi, pt.category AS urun_kategori
                        FROM node n
                        LEFT JOIN node_product_type pt ON n.nView = pt.nView
                        WHERE n.id = %s
                        """,
                        (nid,),
                    )
                    node = cur.fetchone()
                    if not node:
                        return {"error": f"Node ID {nid} bulunamadı."}
                    cur.execute("SELECT pKey, pVal, edit_uid, edit_time FROM node_param WHERE nodeId = %s ORDER BY pKey", (nid,))
                    node["parametreler"] = list(cur.fetchall())
                    cur.execute("SELECT COUNT(*) AS c FROM alarmparameters WHERE nid = %s", (nid,))
                    node["alarm_sayisi"] = int(cur.fetchone()["c"])
                    cur.execute("SELECT COUNT(*) AS c FROM logparameters WHERE nid = %s AND state = 1", (nid,))
                    node["aktif_log_sayisi"] = int(cur.fetchone()["c"])
                    cur.execute("SELECT id, nName, nType, nState FROM node WHERE nBase = %s ORDER BY nName LIMIT 100", (nid,))
                    node["alt_nodeler"] = list(cur.fetchall())
            return node

        @mcp.tool(name=tool)
        def get_node(nodeId: int) -> str:
            """Tek node detayı (nView, nType, parametreler vb.). Panel şablon/menü için nView kritik alandır."""
            return guard(tool, _get_node_impl)(nodeId)

        tool = prefixed_name(prefix, "list_product_types")

        def _list_product_types_impl() -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT pt.id, pt.nView, pt.name, pt.category,
                               COUNT(n.id) AS kullanan_node_sayisi
                        FROM node_product_type pt
                        LEFT JOIN node n ON n.nView = pt.nView
                        GROUP BY pt.id
                        ORDER BY kullanan_node_sayisi DESC
                        """
                    )
                    types = list(cur.fetchall())
            return {"count": len(types), "product_types": types}

        @mcp.tool(name=tool)
        def list_product_types() -> str:
            """Ürün tipleri (node_product_type)."""
            return guard(tool, _list_product_types_impl)()

        # --- AlarmTools.php ---
        tool = prefixed_name(prefix, "list_alarms")

        def _list_alarms_impl(nodeId: int = 0, limit: int = 50, offset: int = 0) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 200)
            offset = max(int(offset), 0)
            params: list[Any] = []
            where = ""
            if int(nodeId) > 0:
                where = "WHERE ap.nid = %s"
                params.append(int(nodeId))
            sql = f"""
                SELECT ap.pId, ap.name, ap.nid, n.nName AS node_adi, ap.tagPath,
                       ap.minVal, ap.maxVal, ap.scanRate, ap.stayTime,
                       ap.alType, ap.alGroup, ap.alGroupPath,
                       CASE WHEN ap.alertAlarm = 1 THEN 'Evet' ELSE 'Hayır' END AS bildirim_alarm,
                       CASE WHEN ap.logAlarm = 1 THEN 'Evet' ELSE 'Hayır' END AS log_alarm,
                       ap.comment,
                       ast.state AS aktif_mi, ast.lastVal, ast.time AS son_durum_zamani
                FROM alarmparameters ap
                LEFT JOIN node n ON ap.nid = n.id
                LEFT JOIN alarmstate ast ON ap.pId = ast.pId
                {where}
                ORDER BY ap.pId DESC
                LIMIT %s OFFSET %s
            """
            count_sql = f"SELECT COUNT(*) AS total FROM alarmparameters ap {where}"
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, tuple(params + [limit, offset]))
                    alarms = list(cur.fetchall())
                    cur.execute(count_sql, tuple(params))
                    total = int(cur.fetchone()["total"])
            return {"total": total, "count": len(alarms), "alarms": alarms}

        @mcp.tool(name=tool)
        def list_alarms(nodeId: int = 0, limit: int = 50, offset: int = 0) -> str:
            """Alarm parametreleri listesi."""
            return guard(tool, _list_alarms_impl)(nodeId, limit, offset)

        tool = prefixed_name(prefix, "get_active_alarms")

        def _get_active_alarms_impl(limit: int = 100) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 500)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT ast.pId, ap.name, ap.nid, n.nName AS node_adi, ap.tagPath,
                               ap.minVal, ap.maxVal, ast.lastVal, ast.time AS alarm_zamani,
                               ap.alType, ap.alGroup, ap.alGroupPath, ap.comment,
                               CASE WHEN ast.isLoud = 1 THEN 'Sesli' ELSE 'Sessiz' END AS ses_durumu
                        FROM alarmstate ast
                        JOIN alarmparameters ap ON ast.pId = ap.pId
                        LEFT JOIN node n ON ap.nid = n.id
                        WHERE ast.state = 1
                        ORDER BY ast.time DESC
                        LIMIT %s
                        """,
                        (limit,),
                    )
                    alarms = list(cur.fetchall())
            return {"count": len(alarms), "active_alarms": alarms}

        @mcp.tool(name=tool)
        def get_active_alarms(limit: int = 100) -> str:
            """Aktif alarm listesi (state=1)."""
            return guard(tool, _get_active_alarms_impl)(limit)

        tool = prefixed_name(prefix, "get_alarm_subscribers")

        def _get_alarm_subscribers_impl(alarmId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            aid = int(alarmId)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT pId, name, nid, tagPath, minVal, maxVal, comment FROM alarmparameters WHERE pId = %s",
                        (aid,),
                    )
                    alarm = cur.fetchone()
                    if not alarm:
                        return {"error": f"Alarm ID {aid} bulunamadı."}
                    cur.execute(
                        """
                        SELECT ua.uid, u.uFirstName, u.uLastName, u.uName, u.uTel, u.uMail,
                               ua.stype,
                               CASE ua.stype WHEN 0 THEN 'Alarm' WHEN 1 THEN 'SMS' WHEN 2 THEN 'Mail' WHEN 3 THEN 'SMS+Mail' END AS bildirim_tipi
                        FROM user_alarm ua
                        JOIN users u ON ua.uid = u.id
                        WHERE ua.al_Id = %s
                        ORDER BY u.uFirstName
                        """,
                        (aid,),
                    )
                    subscribers = list(cur.fetchall())
                    cur.execute(
                        "SELECT type, msgTo, title, toUrl, server FROM user_notifications WHERE alarmParameterId = %s",
                        (aid,),
                    )
                    notifications = list(cur.fetchall())
            alarm["abone_sayisi"] = len(subscribers)
            alarm["aboneler"] = subscribers
            alarm["bildirimler"] = notifications
            return alarm

        @mcp.tool(name=tool)
        def get_alarm_subscribers(alarmId: int) -> str:
            """Alarm abonelikleri."""
            return guard(tool, _get_alarm_subscribers_impl)(alarmId)

        # --- SchemaTools.php ---
        tool = prefixed_name(prefix, "get_database_schema")

        def _get_database_schema_impl() -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT TABLE_NAME, TABLE_ROWS, ENGINE, TABLE_COMMENT
                        FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_SCHEMA = 'kbindb'
                        ORDER BY TABLE_NAME
                        """
                    )
                    tables = list(cur.fetchall())
                    cur.execute(
                        """
                        SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME, CONSTRAINT_NAME
                        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                        WHERE TABLE_SCHEMA = 'kbindb' AND REFERENCED_TABLE_NAME IS NOT NULL
                        ORDER BY TABLE_NAME
                        """
                    )
                    fks = list(cur.fetchall())
            fk_map: dict[str, list[dict[str, str]]] = {}
            for fk in fks:
                t = fk.get("TABLE_NAME")
                if not t:
                    continue
                fk_map.setdefault(str(t), []).append(
                    {
                        "column": str(fk.get("COLUMN_NAME")),
                        "references": f"{fk.get('REFERENCED_TABLE_NAME')}.{fk.get('REFERENCED_COLUMN_NAME')}",
                    }
                )
            result: list[dict[str, Any]] = []
            for t in tables:
                name = str(t.get("TABLE_NAME"))
                entry: dict[str, Any] = {
                    "table": name,
                    "rows": int(t.get("TABLE_ROWS") or 0),
                    "engine": t.get("ENGINE"),
                }
                if name in fk_map and fk_map[name]:
                    entry["foreign_keys"] = fk_map[name]
                result.append(entry)

            relationships = [
                "users.gid -> user_groups.id : Kullanıcı hangi gruba ait",
                "user_auths(uid -> users.id, nid -> node.id) : Kullanıcının node üzerindeki bireysel yetkileri",
                "user_group_auths(gid -> user_groups.id, nid -> node.id) : Grubun node üzerindeki yetkileri",
                "user_alarm(uid -> users.id, al_Id -> alarmparameters.pId) : Kullanıcının alarm abonelikleri",
                "user_node_rel(uid -> users.id, nid -> node.id) : Kullanıcı-node ilişkileri",
                "alarmparameters.nid -> node.id : Alarm hangi node'a ait",
                "alarmstate.pId -> alarmparameters.pId : Alarm anlık durum bilgisi",
                "node_param.nodeId -> node.id : Node parametreleri (key-value)",
                "node.nView -> node_product_type.nView : Node ürün tipi",
                "logparameters.nid -> node.id : Log parametreleri hangi node'a ait",
                "tag_link(srcDid, destDid -> node.id) : Cihazlar arası tag bağlantıları",
                "tag_clone(src_nid, dest_nid -> node.id) : Node'lar arası tag klonlama",
                "tag_clone_tags.cid -> tag_clone.id : Klonlanan tag detayları",
                "tag_clone.type -> tag_clone_type.id : Klonlama tipleri",
                "user_notifications.alarmParameterId -> alarmparameters.pId : Alarm bildirim ayarları",
                "_tagoku.devId -> node.id : Anlık SCADA tag okuma değerleri (MEMORY)",
                "_servercounters.devId -> node.id : Sunucu sayaçları",
            ]
            return {"database": "kbindb", "table_count": len(result), "tables": result, "relationships": relationships}

        @mcp.tool(name=tool)
        def get_database_schema() -> str:
            """Veritabanı şema bilgisi: tablolar, kolonlar."""
            return guard(tool, _get_database_schema_impl)()

        tool = prefixed_name(prefix, "get_table_info")

        def _get_table_info_impl(tableName: str) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            t = (tableName or "").strip()
            if not t:
                return {"error": "tableName gerekli"}
            forbidden_fields = {"uPass", "passMD5", "passText"}
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'kbindb' AND TABLE_NAME = %s",
                        (t,),
                    )
                    if not cur.fetchone():
                        return {"error": f"'{t}' tablosu kbindb'de bulunamadı."}
                    cur.execute(
                        """
                        SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY, COLUMN_COMMENT, EXTRA
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = 'kbindb' AND TABLE_NAME = %s
                        ORDER BY ORDINAL_POSITION
                        """,
                        (t,),
                    )
                    cols = [c for c in cur.fetchall() if str(c.get("COLUMN_NAME")) not in forbidden_fields]
                    cur.execute(
                        """
                        SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                        WHERE TABLE_SCHEMA = 'kbindb' AND TABLE_NAME = %s AND REFERENCED_TABLE_NAME IS NOT NULL
                        """,
                        (t,),
                    )
                    fks = list(cur.fetchall())
                    cur.execute(
                        """
                        SELECT INDEX_NAME, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS idx_columns, NON_UNIQUE
                        FROM INFORMATION_SCHEMA.STATISTICS
                        WHERE TABLE_SCHEMA = 'kbindb' AND TABLE_NAME = %s
                        GROUP BY INDEX_NAME, NON_UNIQUE
                        """,
                        (t,),
                    )
                    idx = list(cur.fetchall())
            return {"table": t, "columns": cols, "foreign_keys": fks, "indexes": idx}

        @mcp.tool(name=tool)
        def get_table_info(tableName: str) -> str:
            """Tablo detayı: kolonlar ve örnek veri."""
            return guard(tool, _get_table_info_impl)(tableName)

        tool = prefixed_name(prefix, "run_safe_query")

        def _run_safe_query_impl(query: str) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            normalized = re.sub(r"\s+", " ", (query or "").strip())
            if not re.match(r"^\s*SELECT\b", normalized, flags=re.IGNORECASE):
                return {"error": "Yalnızca SELECT sorguları çalıştırılabilir."}
            forbidden_keywords = [
                "INSERT",
                "UPDATE",
                "DELETE",
                "DROP",
                "ALTER",
                "TRUNCATE",
                "CREATE",
                "GRANT",
                "REVOKE",
                "EXEC",
                "EXECUTE",
                "INTO OUTFILE",
                "INTO DUMPFILE",
                "LOAD_FILE",
            ]
            forbidden_fields = ["uPass", "passMD5", "passText"]
            for w in forbidden_keywords:
                if w.lower() in normalized.lower():
                    return {"error": f"Güvenlik: '{w}' ifadesi kullanılamaz."}
            for f in forbidden_fields:
                if f.lower() in normalized.lower():
                    return {"error": f"Güvenlik: '{f}' alanı sorgulanamaz."}
            if " limit " not in (" " + normalized.lower() + " "):
                normalized = normalized + " LIMIT 100"
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(normalized)
                    results = list(cur.fetchall())
            return {"query": normalized, "row_count": len(results), "results": results}

        @mcp.tool(name=tool)
        def run_safe_query(query: str) -> str:
            """Güvenli SELECT sorgusu (sadece okuma)."""
            return guard(tool, _run_safe_query_impl)(query)

        # --- ScreenSemanticsTools.php (static JSON + optional disk templates) ---
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
                    "note_tr": "İpucu JSON'u yoksa bu araç yalnızca 'missing' uyarısı döndürür. SCADA ekran çözümlemeleri yine de şablon dosyalarından (MENU.phtml vb.) yapılabilir.",
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

        tool = prefixed_name(prefix, "get_view_tag_meanings")

        def _normalize_nview(nview: str) -> str:
            if nview.startswith("_a-multi"):
                return nview.replace("_a-multi", "a-system", 1)
            return nview

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

        tool = prefixed_name(prefix, "get_node_scada_context")

        def _panel_base_url() -> str:
            u = (cfg.panel_base_url or "").strip()
            if not u:
                return ""
            u = u.rstrip("/")
            if not re.match(r"^https?://", u, flags=re.IGNORECASE):
                u = "https://" + u.lstrip("/")
            return u

        def _resolve_process_adapter(nType: str, nViewRaw: str) -> str:
            v = _normalize_nview(nViewRaw)
            lower = v.lower()
            t = str(nType).strip()
            if t == "666" or lower.startswith("a-system") or nViewRaw.lower().startswith("_a-multi"):
                return "system"
            if t == "777" or ("kuyu" in lower) or ("well" in lower):
                return "well"
            if ("depo" in lower) or ("tank" in lower) or ("store" in lower):
                return "tank"
            if ("terfi" in lower) or ("riser" in lower):
                return "riser"
            return "generic"

        def _get_node_scada_context_impl(node_id: int) -> Any:
            if int(node_id) <= 0:
                return {"error": "node_id > 0 olmalı"}
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, nName, nType, nView FROM node WHERE id = %s LIMIT 1", (int(node_id),))
                    row = cur.fetchone()
            if not row:
                return {"error": "Node bulunamadı"}
            nView = str(row.get("nView") or "")
            nType = str(row.get("nType") or "")
            normalized = _normalize_nview(nView)
            adapter = _resolve_process_adapter(nType, nView)
            profiles = {
                "system": {"process_name": "Sistem / çoklu nokta görünümü", "metrics_summary": "debi (m³/h), güç (kW), basınç (bar), faz voltaj/akım, depo seviyeleri, dozaj"},
                "well": {"process_name": "Kuyu istasyonu (yeraltı suyu pompaj)", "metrics_summary": "debi (m³/h), güç (kW), basınç (bar), frekans (Hz), su sıcaklığı (°C)"},
                "tank": {"process_name": "Depo istasyonu", "metrics_summary": "seviye (cm), debi (m³/h), basınç (bar)"},
                "riser": {"process_name": "Terfi istasyonu", "metrics_summary": "debi (m³/h), güç (kW), basınç (bar)"},
                "generic": {"process_name": "Genel nokta", "metrics_summary": "ekran tipine göre değişir; tag sözlüğü ve semantic eşleme kullanın"},
            }
            view_group = _resolve_view_group(nView.lower())
            warnings: list[dict[str, Any]] = []
            meanings_path = _php_data_scada_path("view_tag_descriptions.json")
            meanings, warn = _try_load_json_file(meanings_path)
            if warn:
                warnings.append(warn)
            views = (meanings or {}).get("views") or {}
            desc_key = _resolve_view_description_key(normalized, views if isinstance(views, dict) else {})
            tags = (views.get(desc_key) if isinstance(views, dict) else {}) or {}
            panel_nav = None
            hints_path = _php_data_scada_path("panel_navigation_hints.json")
            hints, warn2 = _try_load_json_file(hints_path)
            if warn2:
                warnings.append(warn2)
            by_view = (hints or {}).get("views") or {}
            nv_key = nView.lower()
            if isinstance(by_view, dict) and nv_key in by_view and isinstance(by_view[nv_key], dict):
                panel_nav = {"has_hints": True, "topics": list(by_view[nv_key].keys()), "use_tool": "get_node_panel_settings_guide"}
            return {
                "node_id": int(row["id"]),
                "n_name": row.get("nName"),
                "n_type": nType,
                "n_view": nView,
                "normalized_n_view": normalized,
                "view_group": view_group,
                "process_adapter": adapter,
                "process_name": profiles[adapter]["process_name"],
                "metrics_summary": profiles[adapter]["metrics_summary"],
                "tag_meanings_key": desc_key,
                "tag_meanings": tags,
                "panel_navigation": panel_nav,
                "n_view_equipment_profile": _get_nview_equipment_profile_impl(nView),
                "warnings": warnings,
            }

        @mcp.tool(name=tool)
        def get_node_scada_context(node_id: int) -> str:
            """Node SCADA bağlamı: tag’ler, alarmlar, loglar. Sözlükler eksikse `warnings` döner."""
            return guard(prefixed_name(prefix, "get_node_scada_context"), _get_node_scada_context_impl)(node_id)

        tool = prefixed_name(prefix, "get_node_panel_settings_guide")

        def _get_node_panel_settings_guide_impl(node_id: int, topic: str = "") -> Any:
            if int(node_id) <= 0:
                return {"error": "node_id > 0 olmalı"}
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, nName, nView FROM node WHERE id = %s LIMIT 1", (int(node_id),))
                    row = cur.fetchone()
            if not row:
                return {"error": "Node bulunamadı"}
            n_view = str(row.get("nView") or "")
            n_view_equipment = _get_nview_equipment_profile_impl(n_view)
            nv_key = n_view.lower()
            hints_path = _php_data_scada_path("panel_navigation_hints.json")
            hints_file, warn = _try_load_json_file(hints_path)
            by_view = (hints_file or {}).get("views") or {}
            view_hints = by_view.get(nv_key) if isinstance(by_view, dict) else None

            root = (os.getenv("KORUBIN_POINT_DISPLAY_ROOT") or "").strip()
            disk_files: list[str] = []
            disk_files_recursive: list[str] = []
            if root and Path(root).is_dir():
                dpath = Path(root) / n_view
                if dpath.is_dir():
                    for fn in sorted(os.listdir(dpath)):
                        fl = fn.lower()
                        if fl.endswith(".phtml") or fl.endswith(".js"):
                            disk_files.append(fn)
                    # recursive list (relative_path style), capped
                    base = Path(root).resolve()
                    folder_ok = _FOLDER_RE.fullmatch(n_view) is not None
                    if folder_ok:
                        start = _safe_resolve_under(base, n_view)
                        if start and start.is_dir():
                            max_files = 800
                            for p in start.rglob("*"):
                                if not p.is_file():
                                    continue
                                rel_path = str(p.relative_to(start)).replace("\\", "/")
                                fl = rel_path.lower()
                                if fl.endswith(".phtml") or fl.endswith(".js"):
                                    disk_files_recursive.append(rel_path)
                                    if len(disk_files_recursive) >= max_files:
                                        break

            if not isinstance(view_hints, dict):
                return {
                    "node_id": int(row["id"]),
                    "n_name": row.get("nName"),
                    "n_view": n_view,
                    "n_view_equipment_profile": n_view_equipment,
                    "panel_hints": False,
                    "not_tr": "Bu nView için panel_navigation_hints.json içinde kayıt yok veya dosya eksik. read_point_display_template ile MENU.phtml okuyun veya hints dosyasına ekleyin.",
                    "warning": warn,
                    "point_display_root_ok": bool(root and Path(root).is_dir() and (Path(root) / n_view).is_dir()),
                    "template_files_on_disk": disk_files,
                    "template_files_on_disk_recursive": disk_files_recursive,
                }

            t = (topic or "").strip()
            if not t:
                summaries: list[dict[str, Any]] = []
                for key, block in view_hints.items():
                    if isinstance(block, dict):
                        summaries.append(
                            {"topic": key, "baslik_tr": block.get("baslik_tr") or key}
                        )
                return {
                    "node_id": int(row["id"]),
                    "n_name": row.get("nName"),
                    "n_view": n_view,
                    "n_view_equipment_profile": n_view_equipment,
                    "panel_hints": True,
                    "topics": summaries,
                    "hint_tr": "topic parametresi ile detay isteyin (örn. depo_doldurma).",
                    "template_files_on_disk": disk_files,
                    "template_files_on_disk_recursive": disk_files_recursive,
                }

            if t not in view_hints or not isinstance(view_hints[t], dict):
                return {
                    "error": "Bilinmeyen topic",
                    "n_view": n_view,
                    "n_view_equipment_profile": n_view_equipment,
                    "allowed_topics": list(view_hints.keys()),
                }

            block = view_hints[t]
            tag_list: list[str] = []
            et = block.get("ekrandaki_taglar")
            ex = block.get("ekrandaki_taglar_örnek")
            if isinstance(et, list):
                tag_list.extend(str(x) for x in et)
            if isinstance(ex, list):
                tag_list.extend(str(x) for x in ex)
            tag_list = list(dict.fromkeys(tag_list))
            nid = int(row["id"])
            tag_sample = ",".join(tag_list[:25])
            return {
                "node_id": nid,
                "n_name": row.get("nName"),
                "n_view": n_view,
                "n_view_equipment_profile": n_view_equipment,
                "topic": t,
                "guide": block,
                "tags_for_live_query": tag_list,
                "sonraki_adim_tr": (
                    f"Anlık değerler: get_device_tag_values(deviceId={nid}, tag_names=\"{tag_sample}\"...) — liste uzunsa birden fazla çağrı yapılabilir."
                ),
                "template_files_on_disk": disk_files,
                "template_files_on_disk_recursive": disk_files_recursive,
            }

        @mcp.tool(name=tool)
        def get_node_panel_settings_guide(node_id: int, topic: str = "") -> str:
            """Node panel ayarları rehberi. Hints JSON yoksa `panel_hints=false` döner; bu durumda MENU.phtml araçlarını kullanın."""
            return guard(prefixed_name(prefix, "get_node_panel_settings_guide"), _get_node_panel_settings_guide_impl)(node_id, topic)

        tool = prefixed_name(prefix, "get_operational_engineering_hints")

        def _get_operational_engineering_hints_impl(n_view: str, focus: str = "") -> Any:
            n_view = (n_view or "").strip()
            if not n_view:
                return {"error": "n_view gerekli (örn. a-kuyu-envest)"}
            path = _php_data_scada_path("operational_engineering_hints.json")
            if not path.exists():
                return {"error": "operational_engineering_hints.json bulunamadı veya boş"}
            data = _load_json_file(path)
            views = data.get("views") or {}
            if not isinstance(views, dict):
                return {"error": "views eksik"}
            key = n_view.lower()
            matched_key: str | None = None
            matched_via_dma = False
            for vk in views:
                if str(vk).lower() == key:
                    matched_key = str(vk)
                    break
            if matched_key is None and "dma" in key:
                for cand in ("a-dma-envest", "a-dma"):
                    if cand in views:
                        matched_key = cand
                        matched_via_dma = True
                        break
            if matched_key is None:
                return {
                    "n_view": n_view,
                    "available_views": list(views.keys()),
                    "not_tr": "Bu nView için operasyonel ipucu tanımı yok. JSON views altına eklenebilir.",
                }
            block = views[matched_key]
            if not isinstance(block, dict):
                return {"error": "Geçersiz view bloğu"}
            focus_trim = (focus or "").strip()
            header: dict[str, Any] = {
                "uyari_tr": data.get("uyari_tr"),
                "genel_fizik_tr": data.get("genel_fizik_tr"),
                "n_view": n_view,
                "matched_view_key": matched_key,
                "sonraki_canli_tag_sorgusu_tr": "İlgili taglar için get_device_tag_values(deviceId, tag_names=...) veya trend için log/grafik araçları.",
            }
            if matched_via_dma:
                header["eslestirme_tr"] = (
                    "nView tam anahtar eşleşmedi; adında «dma» geçtiği için " + matched_key + " operasyon notları kullanıldı."
                )
            if not focus_trim:
                topics: list[dict[str, Any]] = []
                for tag_key, detail in block.items():
                    if isinstance(detail, dict):
                        topics.append(
                            {
                                "focus": tag_key,
                                "baslik": detail.get("kisa_baslik_tr") or detail.get("rol_tr") or tag_key,
                            }
                        )
                return {
                    **header,
                    "konular": topics,
                    "arayuz_onerileri": data.get("arayuz_onerileri"),
                    "ipucu_tr": "focus parametresine tag adı verin (örn. BasincSensoru2).",
                }
            focus_lower = focus_trim.lower()
            selected = None
            selected_key = None
            for tag_key, detail in block.items():
                if isinstance(detail, dict) and str(tag_key).lower() == focus_lower:
                    selected = detail
                    selected_key = tag_key
                    break
            if selected is None:
                return {
                    **header,
                    "error": "Bu focus için kayıt yok",
                    "focus": focus_trim,
                    "allowed_focus": [k for k, v in block.items() if isinstance(v, dict)],
                }
            return {
                **header,
                "focus": selected_key,
                "icerik": selected,
                "arayuz_onerileri": data.get("arayuz_onerileri"),
            }

        @mcp.tool(name=tool)
        def get_operational_engineering_hints(n_view: str, focus: str = "") -> str:
            """Operasyonel mühendislik ipuçları."""
            return guard(tool, _get_operational_engineering_hints_impl)(n_view, focus)

        tool = prefixed_name(prefix, "list_point_display_templates")

        def _point_display_root() -> str:
            return (os.getenv("KORUBIN_POINT_DISPLAY_ROOT") or "").strip()

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

        tool = prefixed_name(prefix, "summarize_point_display_template")

        def _summarize_point_display_template_impl(
            n_view_folder: str,
            relative_path: str,
            node_id: int | None = None,
            max_excerpt_chars: int = 1800,
        ) -> Any:
            """
            Extract a user-friendly snapshot from a .phtml:
            - headings, menu-ish links, tables (header/row counts), form inputs (name/id/type),
            - tag candidates like XE_*, XD_* etc,
            - optional small plain-text excerpt.
            """
            payload = _read_point_display_template_impl(n_view_folder, relative_path, node_id)
            if isinstance(payload, dict) and payload.get("error"):
                return payload
            if not isinstance(payload, dict) or "content" not in payload:
                return {"error": "Şablon okunamadı"}
            content = str(payload.get("content") or "")
            rel = str(payload.get("relative_path") or relative_path)
            folder = str(payload.get("n_view_folder") or n_view_folder)

            # headings
            headings: list[dict[str, Any]] = []
            for m in re.finditer(r"(?is)<h([1-6])[^>]*>(.*?)</h\\1>", content):
                lvl = int(m.group(1))
                txt = _strip_html(m.group(2))
                if txt:
                    headings.append({"level": lvl, "text": txt})
                if len(headings) >= 20:
                    break

            # links (href)
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

            # inputs/selects/textareas (very simple)
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

            # tables: header cells + rough row count
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

            # tag candidates
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
                # very small excerpt
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
                    # NOTE: KoruMind UI bazı durumlarda `url` / `*_url` alanlarını dosya/görsel çıktısı sanıp
                    # yanlış kart basıyor. Bu yüzden alan adını `panel_link` tutuyoruz.
                    "panel_path": panel_path,
                    "panel_link": (f"{base}{panel_path}" if base else None),
                    "panel_base": base or None,
                    "warning_tr": "GENEL/MAIN gibi dosyalar bazı kurulumlarda ‘varsayılan ekran’ olabilir; doğru segment panel uygulamasına göre değişebilir. Gerekirse MENU.phtml içindeki linkleri çıkarın.",
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

            # capture href/src-like tokens and ./relative patterns
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
                    # keep tail after nodeId
                    parts = rr.split("/")
                    if len(parts) >= 5:
                        seg = "/".join(parts[5:]).strip("/")
                        relp = f"{seg}.phtml" if seg else None
                else:
                    # might already be a segment like bilgi/device_edit
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
                "id": "nodes",
                "title_tr": "Node / topo",
                "tools": [
                    p + "get_node_counts",
                    p + "list_nodes",
                    p + "find_nodes_by_keywords",
                    p + "get_node",
                    p + "list_product_types",
                ],
            },
            {
                "id": "alarms",
                "title_tr": "Alarmlar",
                "tools": [p + "list_alarms", p + "get_active_alarms", p + "get_alarm_subscribers"],
            },
            {
                "id": "schema",
                "title_tr": "DB şema / güvenli sorgu",
                "tools": [p + "get_database_schema", p + "get_table_info", p + "run_safe_query"],
            },
            {
                "id": "semantics",
                "title_tr": "Panel semantik / şablon",
                "tools": [
                    p + "get_nview_equipment_profile",
                    p + "get_scada_semantics",
                    p + "get_view_tag_meanings",
                    p + "get_counter_semantics",
                    p + "resolve_semantic_tag_candidates",
                    p + "get_node_scada_context",
                    p + "get_node_panel_settings_guide",
                    p + "get_operational_engineering_hints",
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

