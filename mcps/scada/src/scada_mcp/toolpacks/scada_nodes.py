"""Node-related tools: list_nodes, get_node, find_nodes_by_keywords, get_node_counts,
list_product_types, get_node_scada_context, get_node_panel_settings_guide,
get_operational_engineering_hints.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..tools.core import guard, prefixed_name
from ..types import InstanceConfig
from .. import db as dbmod

log = logging.getLogger(__name__)

_FOLDER_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")


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


def _safe_resolve_under(base: Path, *parts: str) -> Path | None:
    try:
        target = (base.joinpath(*parts)).resolve()
    except Exception:
        return None
    if not str(target).startswith(str(base) + os.sep):
        return None
    return target


def _normalize_nview(nview: str) -> str:
    if nview.startswith("_a-multi"):
        return nview.replace("_a-multi", "a-system", 1)
    return nview


class ScadaNodesPack:
    """Node / topology tools ported from PHP NodeTools + ScreenSemanticsTools."""

    id = "scada_nodes"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix

        # --- get_node_counts ---
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

        # --- list_nodes ---
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

        # --- find_nodes_by_keywords ---
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
                nodes_list = out.get("nodes") or []
                if not nodes_list:
                    out["hint_tr"] = (
                        f"'{kw}' bu SCADA'da yok. Merged MCP'de diğer prefix'leri dene "
                        "(find_node_everywhere tercih et). Hepsi boşsa kullanıcıya bildir."
                    )
                    out["next_action_required"] = "try_other_scada_instance_prefixes_before_asking_user"
                else:
                    out["hint_tr"] = "İlk satır genelde en iyi eşleşme. nName + urun_tipi ile seç."
                for n in out.get("nodes", []):
                    nv = str(n.get("nView") or "")
                    if nv:
                        n["ekran_tipi_skill_path"] = f"screen-types/nview/{nv}.md"
                out["ayar_menu_tr"] = (
                    "Ayar/çalışma modu/menü sorusu: get_skill('korubin-scada', "
                    "'screen-types/nview/<nView>.md')."
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
            """Node arama (isim, nView, nType, ürün tipi).
Ayar/menü sorusu için: bu tool → nView al → get_skill('screen-types/nview/<nView>.md').
search_product_manual/get_product_specs DEĞİL (onlar cihaz kataloğu)."""
            return guard(tool, _find_nodes_by_keywords_impl)(
                keywords, nType, limit, anahtar_kelime, ara
            )

        # --- get_node ---
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
            # nView'a özel ekran skill dosyası önerisi — ayar/menü/çalışma modu sorularında kritik
            nv = str(node.get("nView") or "")
            if nv:
                node["ekran_tipi_skill_path"] = f"screen-types/nview/{nv}.md"
                node["ayar_skill_tr"] = (
                    f"Ayar sorusu için: get_skill('korubin-scada', 'screen-types/nview/{nv}.md')."
                )

            # Pompa secimi icin KRITIK uyari — nView'a gore pompa ailesi + canli tag zorunlulugu
            nv_l = nv.lower()
            nname_l = str(node.get("nName") or "").lower()
            is_well = ("kuyu" in nv_l) or ("kuyu" in nname_l) or ("well" in nv_l)
            is_booster = ("terfi" in nv_l) or ("terfi" in nname_l) or ("booster" in nv_l) or ("hidro" in nv_l)
            if is_well or is_booster or "depo" in nv_l or "dma" in nv_l:
                node["pompa_secimi_tr"] = (
                    f"Pompa seçimi: {prefix}prepare_pump_selection(nodeId={node.get('id')}). "
                    "Tek çağrı → canlı tag + doğrulama + hazır Q/H + next_action. "
                    "YASAK: XD_BasmaYukseklik, np_*, XS_*, BasincSensoru×10.197."
                )
            return node

        @mcp.tool(name=tool)
        def get_node(nodeId: int) -> str:
            """Node detayı (nView, nType, parametreler). nView = panel şablon kilit alan.
ekran_tipi_skill_path dönerse get_skill ile oku. search_product_manual YERİNE."""
            return guard(tool, _get_node_impl)(nodeId)

        # --- prepare_pump_selection ---
        # Pompa secimi icin TEK ADIMDA hersey: canli tag, formulle dogrulama, hazir Q/H.
        tool = prefixed_name(prefix, "prepare_pump_selection")

        def _prepare_pump_selection_impl(nodeId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            nid = int(nodeId)

            # Kritik canli tag'ler — ToplamHm MERKEZDE
            pump_tags = [
                "ToplamHm",            # canli basma yuksekligi (metre) — EN KRITIK
                "Debimetre", "Debimetre1", "Debimetre2",
                "DebimetreLtSn",
                "BasincSensoru", "BasincSensoru2", "HatBasincSensoru",
                "Pompa1StartStopDurumu", "Pompa2StartStopDurumu",
                "PompaStartStopDurumu", "PompaCalismaDurumu", "Pompa1Calisiyor",
                "P1_Durum", "P2_Durum",
                "An_Guc", "P1_Guc",
                "YaklasikHidrolikVerim", "HidrolikVerim", "PompaVerim",
                "SuSeviye", "StatikSuSeviye",
                # VFD CIKIS frekans (gercek pompa donme frekansi) — oncelik sirasiyla:
                "An_InvFrekans",         # en yaygin (a-kuyu-envest, a-terfi-envest...)
                "An_InverterFrekans",    # OCP110 serisi
                "Pompa1CikisFrekansDeger", "Pompa2CikisFrekansDeger",  # coklu pompa
                "CikisFrekansDeger",     # pompa-test
                "P1_Frekans", "Pompa1Frekans", "PompaFrekans", "Frekans", "An_Frekans",
                # Sebeke (sebeke HZ — VFD DEGIL, sadece referans)
                "An_SebFrekans",
                # VFD setpoint/referans ayar (XC_/XINV_ = AYAR, olcum degil — tespit icin bakilir)
                "XC_SabitFrekansDeger", "XINV_SurucuFrekans", "XINV_SurucuFrekansReferans",
                # Sürücü varligi flag tag'leri (varsa)
                "SurucuVar", "SurucuAktif",
            ]

            installed_pump: dict[str, Any] | None = None
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    # Node
                    cur.execute(
                        "SELECT id, nName, nView, nType, nState FROM node WHERE id = %s",
                        (nid,),
                    )
                    node = cur.fetchone()
                    if not node:
                        return {"error": f"Node {nid} bulunamadi"}
                    # Canli tag'ler
                    placeholders = ",".join(["%s"] * len(pump_tags))
                    cur.execute(
                        f"SELECT tagName, tagValue, readTime FROM _tagoku "
                        f"WHERE devId = %s AND tagName IN ({placeholders})",
                        tuple([nid] + pump_tags),
                    )
                    tag_rows = {r["tagName"]: r for r in cur.fetchall()}
                    # Mevcut pompa bilgisi — HER IKI kaynak birlesik
                    pe_row: dict[str, Any] | None = None
                    try:
                        cur.execute(
                            "SELECT brand, model, flow, hm, motor_power, pump_stage, "
                            "pump_max_eff, motor_max_eff, annexa, montage "
                            "FROM pump_eff WHERE nid = %s ORDER BY updateTime DESC LIMIT 1",
                            (nid,),
                        )
                        pe_row = cur.fetchone()
                    except Exception:
                        pe_row = None
                    cur.execute(
                        "SELECT pKey, pVal FROM node_param WHERE nodeId = %s "
                        "AND pKey IN ('np_PompaMarka','np_PompaModel','np_PompaDebi',"
                        "'np_PompaHm','np_PompaGuc','np_PompaTip','np_PompaCap',"
                        "'np_SurucuGuc','np_SurucuModel','np_KolonCap','np_KabloKesit',"
                        "'np_Debimetre','nPMontaj','nPModel')",
                        (nid,),
                    )
                    np_rows = {r["pKey"]: r["pVal"] for r in cur.fetchall()}
                    def _s2(v: Any) -> Any:
                        if v is None: return None
                        if isinstance(v, str):
                            v = v.strip()
                            return v or None
                        return v
                    pe_b = _s2(pe_row.get("brand")) if pe_row else None
                    pe_m = _s2(pe_row.get("model")) if pe_row else None
                    np_b = _s2(np_rows.get("np_PompaMarka"))
                    np_m = _s2(np_rows.get("np_PompaModel"))
                    _generic = {"dalgıç pompa", "submersible", "genel", "generic", "pompa"}
                    pe_m_generic = pe_m is not None and pe_m.lower() in _generic
                    best_b = np_b or pe_b
                    best_m = np_m if (np_m and (not pe_m or pe_m_generic)) else (pe_m or np_m)
                    if best_b or best_m or pe_row or np_rows:
                        installed_pump = {
                            "marka": best_b,
                            "model": best_m,
                            "nominal_Q": (
                                _s2(pe_row.get("flow")) if pe_row and pe_row.get("flow")
                                else _s2(np_rows.get("np_PompaDebi"))
                            ),
                            "nominal_H": (
                                _s2(pe_row.get("hm")) if pe_row and pe_row.get("hm")
                                else _s2(np_rows.get("np_PompaHm"))
                            ),
                            "motor_kW": (
                                _s2(pe_row.get("motor_power")) if pe_row and pe_row.get("motor_power")
                                else _s2(np_rows.get("np_PompaGuc"))
                            ),
                            "kademe": _s2(pe_row.get("pump_stage")) if pe_row else None,
                            "annexa": _s2(pe_row.get("annexa")) if pe_row else None,
                            "montage": _s2(pe_row.get("montage")) if pe_row else None,
                            "pompa_cap_inch": _s2(np_rows.get("np_PompaCap")),
                            "surucu_model": _s2(np_rows.get("np_SurucuModel")),
                            "surucu_kW": _s2(np_rows.get("np_SurucuGuc")),
                            "kolon_cap_mm": _s2(np_rows.get("np_KolonCap")),
                            "montaj_derinlik_m": _s2(np_rows.get("nPMontaj")),
                        }
                        installed_pump = {k: v for k, v in installed_pump.items() if v is not None}

            def _num(name: str) -> float | None:
                r = tag_rows.get(name)
                if not r:
                    return None
                try:
                    return float(r["tagValue"])
                except (TypeError, ValueError):
                    return None

            # Pompa tipi / seri
            nv_l = str(node.get("nView") or "").lower()
            nname_l = str(node.get("nName") or "").lower()
            is_well = ("kuyu" in nv_l) or ("kuyu" in nname_l) or ("well" in nv_l)
            is_booster = (
                "terfi" in nv_l or "terfi" in nname_l
                or "booster" in nv_l or "hidro" in nv_l
            )
            if is_well:
                kc_app = "groundwater"
                kc_sub = "WELLINS"
                pump_series = "SP"
                pump_type_tr = "kuyu (dalgic)"
            elif is_booster:
                kc_app = "booster"
                kc_sub = "BOOSPUMP"
                pump_series = "CR"
                pump_type_tr = "terfi/booster"
            else:
                kc_app = None
                kc_sub = None
                pump_series = None
                pump_type_tr = "belirsiz"

            # Pompa calisiyor mu?
            running_flags = [
                _num("Pompa1StartStopDurumu"),
                _num("PompaStartStopDurumu"),
                _num("PompaCalismaDurumu"),
                _num("Pompa1Calisiyor"),
                _num("P1_Durum"),
            ]
            running = any((v is not None and v > 0.5) for v in running_flags)

            # Canli degerler — ToplamHm MERKEZ (raw _tagoku degeri)
            head_m_raw = _num("ToplamHm")
            # UI'da toplamHm bazi nView'larda JS formuluyle hesaplaniyor:
            # typical: BasincSensoru * 10.197 + SuSeviye (+ varsa XD_BasmaYukseklik)
            basinc_bar = _num("BasincSensoru")
            su_seviye_tag = _num("SuSeviye") or _num("DinamikSeviye") or _num("dinamikseviye")
            xd_basma = _num("XD_BasmaYukseklik")
            head_m_computed: float | None = None
            head_m_formula: str | None = None
            if basinc_bar is not None:
                comp = basinc_bar * 10.197
                parts = [f"BasincSensoru({basinc_bar})×10.197={round(comp,2)}"]
                if su_seviye_tag is not None:
                    comp += su_seviye_tag
                    parts.append(f"+SuSeviye({su_seviye_tag})")
                if xd_basma is not None:
                    comp += xd_basma
                    parts.append(f"+XD_BasmaYukseklik({xd_basma})")
                head_m_computed = round(comp, 2)
                head_m_formula = " ".join(parts) + f" = {head_m_computed}"

            # Kullanilacak deger: raw varsa oncelikle onu (DB _tagoku sunucu tarafi),
            # yoksa hesaplanmis fallback. Ikisi farkliysa uyar.
            head_m = head_m_raw if head_m_raw is not None else head_m_computed
            head_m_mismatch: dict[str, Any] | None = None
            if (head_m_raw is not None and head_m_computed is not None
                    and abs(head_m_raw - head_m_computed) > max(1.0, 0.05 * abs(head_m_raw))):
                head_m_mismatch = {
                    "raw": head_m_raw, "computed": head_m_computed,
                    "fark_m": round(head_m_raw - head_m_computed, 2),
                    "formula": head_m_formula,
                    "uyari_tr": "Raw ≠ hesap. UI JS farklı olabilir, nView skill'ini güncelle.",
                }

            flow = _num("Debimetre") or _num("Debimetre1")
            flow_ltsn = _num("DebimetreLtSn")
            if flow is None and flow_ltsn is not None:
                flow = flow_ltsn * 3.6  # Lt/sn -> m3/h
            power_kw = _num("An_Guc") or _num("P1_Guc")
            eta_hyd = _num("YaklasikHidrolikVerim") or _num("HidrolikVerim") or _num("PompaVerim")

            # UI'daki 'hidrolikVerim' ve 'sistemVerim' JS ile hesaplanir.
            # Typical formul: hidrolikVerim(%) = (Q*H/367) / P1_kW * 100
            #                 sistemVerim(%) = hidrolikVerim * motor_verim_faktoru (~0.85)
            # Her nView'da kesin formul farkli olabilir — burada best-effort hesap donulur,
            # UI degeriyle tutmazsa kullaniciya panel JS formulunu paylasmasi soylenir.
            ui_computed: dict[str, Any] = {}
            if flow and head_m and power_kw and power_kw > 0:
                p_hid = (flow * head_m) / 367.0
                hid_verim = round((p_hid / power_kw) * 100.0, 2)
                ui_computed["hidrolikVerim_computed_pct"] = hid_verim
                ui_computed["sistemVerim_computed_pct"] = round(hid_verim * 0.85, 2)
                ui_computed["formul"] = "P_hid=Q*H/367; η_hid=P_hid/P1*100; η_sys≈η_hid*0.85"
                ui_computed["uyari_tr"] = "UI JS farklı olabilir, karşılaştır."

            # VFD / surucu tespiti — CIKIS frekans tag'i VFD varligi demektir.
            # Oncelik: An_InvFrekans > An_InverterFrekans > Pompa1CikisFrekansDeger
            # > CikisFrekansDeger > P1_Frekans/Pompa1Frekans/...
            # An_SebFrekans SEBEKE frekansidir — tek basina VFD gostermez.
            vfd_output_freq_tags = [
                ("An_InvFrekans", _num("An_InvFrekans")),
                ("An_InverterFrekans", _num("An_InverterFrekans")),
                ("Pompa1CikisFrekansDeger", _num("Pompa1CikisFrekansDeger")),
                ("Pompa2CikisFrekansDeger", _num("Pompa2CikisFrekansDeger")),
                ("CikisFrekansDeger", _num("CikisFrekansDeger")),
                ("P1_Frekans", _num("P1_Frekans")),
                ("Pompa1Frekans", _num("Pompa1Frekans")),
                ("PompaFrekans", _num("PompaFrekans")),
                ("Frekans", _num("Frekans")),
                ("An_Frekans", _num("An_Frekans")),
            ]
            vfd_setpoint_tags = [
                ("XC_SabitFrekansDeger", _num("XC_SabitFrekansDeger")),
                ("XINV_SurucuFrekans", _num("XINV_SurucuFrekans")),
                ("XINV_SurucuFrekansReferans", _num("XINV_SurucuFrekansReferans")),
            ]
            sebeke_freq = _num("An_SebFrekans")
            surucu_flag = _num("SurucuVar") or _num("SurucuAktif")

            # Canli cikis frekansi — pompa gercek donme frekansi
            pump_output_freq: float | None = None
            pump_output_freq_tag: str | None = None
            for name, v in vfd_output_freq_tags:
                if v is not None and v > 0:
                    pump_output_freq = v
                    pump_output_freq_tag = name
                    break

            # VFD setpoint (ayar) — varligi VFD'yi kanitlar
            vfd_setpoint: float | None = None
            vfd_setpoint_tag: str | None = None
            for name, v in vfd_setpoint_tags:
                if v is not None:
                    vfd_setpoint = v
                    vfd_setpoint_tag = name
                    break

            # Mevcut tum freq tag'leri (raporlama icin)
            freq_tags_present = [
                name for name, v in (vfd_output_freq_tags + vfd_setpoint_tags)
                if v is not None
            ]
            if sebeke_freq is not None:
                freq_tags_present.append("An_SebFrekans")

            # Karar mantigi:
            if surucu_flag is not None:
                vfd_detected: bool | None = bool(surucu_flag > 0.5)
                vfd_source = "SurucuVar/SurucuAktif tag'i (acik flag)"
            elif pump_output_freq is not None:
                vfd_detected = True
                vfd_source = (
                    f"VFD cikis frekans tag'i '{pump_output_freq_tag}' = {pump_output_freq} Hz "
                    "mevcut -> surucu var"
                )
            elif vfd_setpoint_tag is not None:
                vfd_detected = True
                vfd_source = (
                    f"VFD setpoint tag'i '{vfd_setpoint_tag}' = {vfd_setpoint} mevcut "
                    "-> surucu var (ama cikis tag'i okunamiyor)"
                )
            elif sebeke_freq is not None:
                vfd_detected = None
                vfd_source = (
                    "Sadece 'An_SebFrekans' (sebeke) var — bu VFD olcumu DEGIL. "
                    "Surucu varligi belirsiz; sahada teyit gerek."
                )
            else:
                vfd_detected = None
                vfd_source = (
                    "Hic frekans/surucu tag'i bulunamadi — "
                    "VFD varligi tag'lardan kesinlenemedi. "
                    "Kullaniciya saha durumu teyit ettirilmeli."
                )

            # pump_freq geriye-uyumluluk (onceki kodda kullanilan isim) — yeni isim:
            pump_freq = pump_output_freq

            # Formulle cross-check: P_hid = (Q × H) / 367 (m3/h, m, kW icin)
            checks: list[dict[str, Any]] = []
            p_hyd_calc = None
            p1_expected = None
            if flow and head_m:
                p_hyd_calc = round((flow * head_m) / 367.0, 2)
                if eta_hyd:
                    # eta yuzde mi ondalik mi kestir
                    eta = eta_hyd / 100.0 if eta_hyd > 1.5 else eta_hyd
                    if eta > 0.05:
                        p1_expected = round(p_hyd_calc / eta, 2)
                if power_kw is not None and p_hyd_calc is not None:
                    ratio = power_kw / max(p_hyd_calc, 0.01)
                    # Hidrolik_guc > shaft_guc ise mantiksiz
                    if power_kw < p_hyd_calc * 0.9:
                        checks.append({
                            "severity": "HIGH",
                            "issue": "olcum_tutarsiz",
                            "detail": (
                                f"An_Guc ({power_kw} kW) < hidrolik guc ({p_hyd_calc} kW). "
                                "Fiziksel mumkun degil — ya flow/head yanlis ya power olcumu yanlis. "
                                "Flow/Head degerlerini TEKRAR OKU."
                            ),
                        })
                    elif ratio > 3.0:
                        checks.append({
                            "severity": "MEDIUM",
                            "issue": "asiri_guc",
                            "detail": (
                                f"An_Guc/P_hid orani {ratio:.1f}x — verim %33'un altinda görünüyor. "
                                "Verim sensor kontrol et veya baska nokta secimi yanlis olabilir."
                            ),
                        })
                if p1_expected is not None and power_kw is not None:
                    diff = abs(power_kw - p1_expected) / max(p1_expected, 0.01)
                    if diff > 0.4:
                        checks.append({
                            "severity": "HIGH",
                            "issue": "verim_hesabi_tutarsiz",
                            "detail": (
                                f"Hesaplanan P1 ({p1_expected} kW) ile canli An_Guc ({power_kw} kW) "
                                f"arasi fark >%40. Ya flow/head yanlis ya verim tag'i yanlis. "
                                f"Sıra: ToplamHm, Debimetre, An_Guc, YaklasikHidrolikVerim'i kontrol et."
                            ),
                        })

            if not running:
                checks.append({
                    "severity": "HIGH",
                    "issue": "pompa_durmus",
                    "detail": (
                        "Pompa calismiyor — canli Hm ve Debi GUVENILMEZ. "
                        "get_node_log_data ile son calistigi donemi bulup o tarihten ortalama al."
                    ),
                })
            if head_m is None:
                checks.append({
                    "severity": "HIGH",
                    "issue": "toplam_hm_yok",
                    "detail": (
                        "ToplamHm tag'i bulunamadi. Bu tag pompa basma yuksekligi icin merkez deger. "
                        "DIKKAT: BasincSensoru × 10.197 ile HM TURETME — bu sadece hat basinci, "
                        "kuyu su seviyesi ve surtunme kayipi iceremez. get_device_data ile tag listesini "
                        "gor, Hm/TotalHead benzeri farklı isim var mi bak."
                    ),
                })

            # Tıraşlı çark = torna ile çapı küçültülmüş, sabit iş noktasına uyarlanmış (isim sonu N).
            if vfd_detected is True:
                impeller_kural_tr = "VFD VAR → standart çark tercih. Tıraşlı (N) = esneklik kaybı."
                korucaps_prefer_impeller = "standart"
            elif vfd_detected is False:
                impeller_kural_tr = "VFD YOK → sabit iş noktasında tıraşlı (N) daha verimli, standart da uygun."
                korucaps_prefer_impeller = "any"
            else:
                impeller_kural_tr = "VFD belirsiz → her iki seçeneği sun, kullanıcıya sor."
                korucaps_prefer_impeller = "any"

            result: dict[str, Any] = {
                "node_id": nid,
                "node_name": node.get("nName"),
                "nView": node.get("nView"),
                "pump_type": pump_type_tr,
                "running": running,
                "canli_olcumler": {
                    "ToplamHm_m": head_m,
                    "ToplamHm_raw_tag": head_m_raw,
                    "ToplamHm_computed": head_m_computed,
                    "ToplamHm_formula_debug": head_m_formula,
                    "Debimetre_m3h": flow,
                    "An_Guc_kW": power_kw,
                    "YaklasikHidrolikVerim": eta_hyd,
                    "BasincSensoru_bar": _num("BasincSensoru"),
                    "HatBasincSensoru_bar": _num("HatBasincSensoru"),
                    "SuSeviye_m": su_seviye_tag,
                    "XD_BasmaYukseklik_m": xd_basma,
                    "pompa_cikis_frekans_Hz": pump_freq,
                    "pompa_cikis_frekans_tag": pump_output_freq_tag,
                    "sebeke_frekans_Hz": sebeke_freq,
                    "vfd_setpoint": vfd_setpoint,
                    "vfd_setpoint_tag": vfd_setpoint_tag,
                },
                "ui_hesaplanmis": ui_computed,
                "toplam_hm_mismatch": head_m_mismatch,
                "mevcut_pompa": installed_pump,
                "hesaplamalar": {
                    "P_hidrolik_hesap_kW": p_hyd_calc,
                    "P1_beklenen_kW": p1_expected,
                    "formul": "P_hid = (Q × H) / 367, P1 = P_hid / η",
                },
                "vfd": {
                    "mevcut": vfd_detected,  # true / false / null (belirsiz)
                    "tespit_kaynagi": vfd_source,
                    "frekans_tag_listesi": freq_tags_present,
                    "impeller_kurali_tr": impeller_kural_tr,
                },
                "korucaps_parametreleri": (
                    {
                        "flow_m3h": flow,
                        "head_m": head_m,
                        "application": kc_app,
                        "sub_application": kc_sub,
                        "pump_series_hint": pump_series,
                        "vfd": bool(vfd_detected is True),
                        "prefer_impeller": korucaps_prefer_impeller,
                    } if (flow and head_m and not checks) else None
                ),
                "checks": checks,
                "hazir": bool(flow and head_m and running and not any(c["severity"] == "HIGH" for c in checks)),
            }

            # Mevcut pompa bilgisi varsa kısa özet (annexa gösterilmez, iç hesapta)
            ip_summary = ""
            if installed_pump:
                ip_parts = []
                if installed_pump.get("marka") and installed_pump.get("model"):
                    ip_parts.append(f"{installed_pump['marka']} {installed_pump['model']}")
                if installed_pump.get("nominal_Q") and installed_pump.get("nominal_H"):
                    ip_parts.append(f"Nominal Q={installed_pump['nominal_Q']} H={installed_pump['nominal_H']}")
                if installed_pump.get("motor_kW"):
                    ip_parts.append(f"{installed_pump['motor_kW']}kW")
                if installed_pump.get("kademe"):
                    ip_parts.append(f"{installed_pump['kademe']} kademe")
                if ip_parts:
                    ip_summary = " | TAKILI: " + " ".join(ip_parts)

            if result["hazir"]:
                vfd_param = "true" if vfd_detected is True else "false"
                result["next_action"] = (
                    f"korucaps_search_pumps(flow_m3h={flow}, head_m={head_m}, "
                    f"application='{kc_app}', sub_application='{kc_sub}', vfd={vfd_param})"
                )
                if vfd_detected is True:
                    _imp = " VFD var → standart öne."
                elif vfd_detected is False:
                    _imp = " VFD yok → her ikisi uygun."
                else:
                    _imp = " VFD belirsiz → kullanıcıya sor."
                result["hint_tr"] = (
                    "Tutarlı. next_action'ı aynen çağır. Yuvarlama yok."
                    + _imp + ip_summary
                    + " | KULLANICIYA mevcut_pompa alanındaki TÜM detayı göster (marka, model, Q, H, motor, kademe, sürücü, montaj)."
                )
            else:
                highs = [c for c in checks if c["severity"] == "HIGH"]
                if highs:
                    result["next_action"] = "stop_and_resolve_checks"
                    result["hint_tr"] = (
                        "KRİTİK: checks içinde HIGH var. search_pumps çağırma, kullanıcıya bildir."
                        + ip_summary
                    )
                else:
                    result["hint_tr"] = "Uyarı var, teyit alarak ilerle." + ip_summary
            return result

        @mcp.tool(name=tool)
        def prepare_pump_selection(nodeId: int) -> str:
            """Pompa seçimi tek adımda: canlı tag + doğrulama + hazır Q/H.
Kullanım: find_node_everywhere → prepare_pump_selection(nodeId) → response'ta hazır=true ise
next_action'ı aynen çağır. checks'de HIGH varsa kullanıcıya bildir, devam etme.
ToplamHm yoksa BasincSensoru×10.197 ile TÜRETME. Formül: P_hid=Q×H/367."""
            return guard(tool, _prepare_pump_selection_impl)(nodeId)

        # --- analyze_pump_at_frequency ---
        # Mevcut canli is noktasindan hareketle, hedef frekansta ne olacagini
        # SISTEM EGRISI modeliyle tahmin eder. Saf Affinity Laws DEGIL.
        tool = prefixed_name(prefix, "analyze_pump_at_frequency")

        def _analyze_pump_at_frequency_impl(
            nodeId: int,
            target_freq_hz: float,
            current_freq_hz: float = 0.0,
            h_static_m: float = 0.0,
            annexa: float = 0.0,
        ) -> Any:
            """Sistem egrisi kalibrasyonu ile frekans projeksiyonu.

            H_sys(Q) = H_static + k·Q²
            Mevcut (Q1, H1) ile k kalibre edilir → yeni pompa egrisi (f2, annexa) ile kesisim bulunur.
            annexa < 1 ise pompa yaslanmis, egri asagi kayar.
            """
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")

            # 1) Mevcut canli noktayi al
            nid = int(nodeId)
            pump_tags = [
                "ToplamHm", "Debimetre", "Debimetre1", "DebimetreLtSn",
                "An_Guc", "P1_Guc",
                "YaklasikHidrolikVerim", "HidrolikVerim", "PompaVerim",
                "P1_Frekans", "Pompa1Frekans", "PompaFrekans", "Frekans", "An_Frekans",
                "Pompa1StartStopDurumu", "PompaStartStopDurumu", "PompaCalismaDurumu",
                "SuSeviye", "StatikSuSeviye",
            ]
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    placeholders = ",".join(["%s"] * len(pump_tags))
                    cur.execute(
                        f"SELECT tagName, tagValue FROM _tagoku "
                        f"WHERE devId = %s AND tagName IN ({placeholders})",
                        tuple([nid] + pump_tags),
                    )
                    tag_rows = {r["tagName"]: r for r in cur.fetchall()}

            def _num(name: str) -> float | None:
                r = tag_rows.get(name)
                if not r:
                    return None
                try:
                    return float(r["tagValue"])
                except (TypeError, ValueError):
                    return None

            q1 = _num("Debimetre") or _num("Debimetre1")
            if q1 is None:
                ltsn = _num("DebimetreLtSn")
                if ltsn is not None:
                    q1 = ltsn * 3.6
            h1 = _num("ToplamHm")
            p1_kw = _num("An_Guc") or _num("P1_Guc")
            eta_live = _num("YaklasikHidrolikVerim") or _num("HidrolikVerim") or _num("PompaVerim")
            f1_live = (
                _num("P1_Frekans") or _num("Pompa1Frekans")
                or _num("PompaFrekans") or _num("Frekans") or _num("An_Frekans")
            )
            running = any(
                (v is not None and v > 0.5)
                for v in (
                    _num("Pompa1StartStopDurumu"),
                    _num("PompaStartStopDurumu"),
                    _num("PompaCalismaDurumu"),
                )
            )

            f1 = float(current_freq_hz) if current_freq_hz and current_freq_hz > 0 else (f1_live or 50.0)
            f2 = float(target_freq_hz)
            if f2 <= 0 or f2 > 65:
                return {"error": "target_freq_hz gecersiz (0 < f <= 65)."}

            checks: list[dict[str, Any]] = []
            if not running:
                checks.append({
                    "severity": "HIGH",
                    "issue": "pompa_durmus",
                    "detail": (
                        "Pompa durmus — canli Q, H guvenilmez. "
                        "Calisma donemindeki (log) degerle tekrar dene."
                    ),
                })
            if q1 is None or h1 is None or q1 <= 0 or h1 <= 0:
                return {
                    "error": "Canli Q (Debimetre) veya H (ToplamHm) alinamadi.",
                    "debimetre_m3h": q1, "toplam_hm_m": h1,
                    "hint_tr": "prepare_pump_selection ile durumu teyit et.",
                }

            # 2) H_static tahmini
            # Kullanici verdiyse onu kullan, yoksa SuSeviye (dinamik kuyu seviyesi) bakar,
            # yoksa H1'in %25'i ile baslanir (yaygin varsayim).
            if h_static_m and h_static_m > 0:
                h_static = float(h_static_m)
                h_static_source = "user_param"
            else:
                su_seviye = _num("SuSeviye") or _num("StatikSuSeviye")
                if su_seviye is not None and 0 < su_seviye < h1:
                    h_static = float(su_seviye)
                    h_static_source = "SuSeviye/StatikSuSeviye canli tag"
                else:
                    h_static = round(h1 * 0.25, 2)
                    h_static_source = "varsayilan (H1 * 0.25)"

            if h_static >= h1:
                return {
                    "error": "H_static >= H1 — sistem modeli gecersiz.",
                    "h_static_m": h_static, "h1_m": h1,
                    "hint_tr": "h_static_m parametresiyle manuel ver veya log'dan kalibre et.",
                }

            # 3) Sistem egrisi: H_sys(Q) = H_static + k·Q²
            k = (h1 - h_static) / (q1 * q1)

            # 4) Pompa egrisi modeli
            # annexa: pompa yaslanma katsayisi (1 = nominal, <1 = asinmis)
            # Otomatik oku: pump_eff tablosu varsa annexa oradan, yoksa kullanici parametresi
            annexa_used = float(annexa) if annexa and annexa > 0 else 1.0
            annexa_source = "user_param"
            if not (annexa and annexa > 0):
                try:
                    with dbmod.connect(cfg.db) as conn2:
                        with conn2.cursor() as cur2:
                            cur2.execute(
                                "SELECT annexa FROM pump_eff WHERE nid = %s "
                                "ORDER BY updateTime DESC LIMIT 1",
                                (nid,),
                            )
                            row = cur2.fetchone()
                            if row and row.get("annexa") is not None:
                                annexa_used = float(row["annexa"])
                                annexa_source = "pump_eff_table"
                except Exception:
                    pass

            ratio = f2 / f1
            q_pump_at_f2_nominal = q1 * ratio                             # Q ∝ f
            h_pump_at_f2_nominal = h1 * ratio * ratio * annexa_used       # H ∝ f² × annexa

            # Pompa Q-H egrisini yerel olarak lineerleştir:
            # dH/dQ ≈ -2 * (H_pump_nominal - H_static_f2) / Q_nominal
            # (basit varsayım: BEP civarında yaklaşım)
            # Daha doğru için: 3 nokta ile fit; burada tek nokta var.
            # Yaklaşım: pompa egrisi egimi -(H1/Q1) civarında.
            slope_pump_f1 = -h1 / q1  # m / (m3/h)
            slope_pump_f2 = slope_pump_f1  # affinity'de egim ~ sabit (Q∝f, H∝f²)

            # Pompa egrisi f2: H_pump(Q) = H_pump_nominal + slope*(Q - Q_nominal)
            # Sistem egrisi: H_sys(Q) = H_static + k·Q²
            # Kesişim: h_pump_nominal + slope*(Q - q_nom) = h_static + k·Q²
            # → k·Q² - slope·Q + (h_static - h_pump_nominal + slope*q_nom) = 0
            a_q = k
            b_q = -slope_pump_f2
            c_q = h_static - h_pump_at_f2_nominal + slope_pump_f2 * q_pump_at_f2_nominal

            disc = b_q * b_q - 4 * a_q * c_q
            if disc < 0 or a_q <= 0:
                return {
                    "error": "Sistem/pompa kesisimi cozulemedi (discriminant < 0).",
                    "hint_tr": "h_static_m degerini manuel ver veya daha fazla log noktasi topla.",
                    "debug": {"a": a_q, "b": b_q, "c": c_q, "disc": disc},
                }
            import math as _math
            q2_a = (-b_q + _math.sqrt(disc)) / (2 * a_q)
            q2_b = (-b_q - _math.sqrt(disc)) / (2 * a_q)
            candidates = [x for x in (q2_a, q2_b) if x > 0]
            if not candidates:
                return {"error": "Pozitif Q2 cozumu bulunamadi."}
            q2 = min(candidates, key=lambda x: abs(x - q_pump_at_f2_nominal))
            h2 = h_static + k * q2 * q2

            # Yeni güç tahmini
            p_hyd2 = (q2 * h2) / 367.0
            eta_use = eta_live if eta_live is not None else 60.0
            if eta_use > 1.5:
                eta_decimal = eta_use / 100.0
            else:
                eta_decimal = eta_use
            p1_2 = p_hyd2 / max(eta_decimal, 0.1)

            result = {
                "node_id": nid,
                "running": running,
                "mevcut_nokta": {
                    "frekans_Hz": round(f1, 2),
                    "Q_m3h": round(q1, 2),
                    "H_m": round(h1, 2),
                    "P1_kW": round(p1_kw, 2) if p1_kw is not None else None,
                    "verim_pct": round(eta_live, 1) if eta_live is not None else None,
                },
                "sistem_egrisi": {
                    "H_static_m": round(h_static, 2),
                    "H_static_kaynak": h_static_source,
                    "k_coef": round(k, 6),
                    "formul": "H_sys(Q) = H_static + k·Q²",
                },
                "hedef_frekans_Hz": f2,
                "tahmin_yeni_nokta": {
                    "Q2_m3h": round(q2, 2),
                    "H2_m": round(h2, 2),
                    "P_hidrolik_kW": round(p_hyd2, 2),
                    "P1_tahmin_kW": round(p1_2, 2),
                    "verim_varsayim_pct": round(eta_use, 1),
                },
                "affinity_sadece_pompa": {
                    "Q_m3h": round(q_pump_at_f2_nominal, 2),
                    "H_m": round(h_pump_at_f2_nominal, 2),
                    "uyari": "NAİF affinity + annexa (referans). Gerçek: tahmin_yeni_nokta.",
                },
                "annexa": {
                    "value": annexa_used,
                    "source": annexa_source,
                    "aciklama": (
                        "H_pump = H_nominal × annexa (pompa yaşlanma katsayısı). "
                        "Ölçüm-etiket arası sapmayı kapatmak için kullanılır. "
                        "Bu HESAPTA kullanıldı; kullanıcıya sadece bu hesap için açıklayarak sun."
                    ),
                },
                "belirsizlik_tr": (
                    f"±%10-15. H_static kaynak: {h_static_source}. "
                    "Daha iyi: log'dan çok nokta topla, kalibre et."
                ),
                "checks": checks,
            }
            return result

        @mcp.tool(name=tool)
        def analyze_pump_at_frequency(
            nodeId: int,
            target_freq_hz: float,
            current_freq_hz: float = 0.0,
            h_static_m: float = 0.0,
            annexa: float = 0.0,
        ) -> str:
            """Frekans projeksiyonu: hedef frekansta Q/H/P tahmini (sistem eğrisi + annexa).
Saf Affinity DEĞİL — H_sys(Q)=H_static+k·Q² ∩ pompa eğrisi.
annexa: pompa yaşlanma (1=nominal, <1=aşınmış). 0 → pump_eff'ten okunur, yoksa 1.0.
current_freq_hz=0 → canlı tag. h_static_m=0 → SuSeviye veya 0.25·H1.
Kullan: "X Hz'de ne olur", "en verimli frekans", "frekans düşürürsem debi"."""
            return guard(tool, _analyze_pump_at_frequency_impl)(
                nodeId, target_freq_hz, current_freq_hz, h_static_m, annexa,
            )

        # --- list_product_types ---
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

        # --- get_installed_pump_info ---
        # Node'a takili mevcut pompanin bilgisi — iki kaynak:
        #   1) kbindb.pump_eff (marka, model, annexa yaslanma katsayisi, montage tarihi)
        #   2) node_param np_* (catalog/etiket: np_PompaModel, np_PompaHm, np_PompaDebi, ...)
        tool = prefixed_name(prefix, "get_installed_pump_info")

        def _get_installed_pump_info_impl(nodeId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            nid = int(nodeId)
            pump_eff_row = None
            np_params: dict[str, Any] = {}
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    # pump_eff: en guncel kayit
                    try:
                        cur.execute(
                            """
                            SELECT id, brand, model, motor_brand, flow, flow_rate, hm,
                                   pump_stage, motor_power, pump_max_eff, motor_max_eff,
                                   annexa, montage, note, updateTime, createdTime
                            FROM pump_eff
                            WHERE nid = %s
                            ORDER BY updateTime DESC, id DESC
                            LIMIT 1
                            """,
                            (nid,),
                        )
                        pump_eff_row = cur.fetchone()
                    except Exception as exc:
                        pump_eff_row = {"error": f"pump_eff okunamadi: {type(exc).__name__}"}
                    # node_param np_* ve nP* anahtarlari — known key listesi (SQL LIKE
                    # underscore'u escape etmek yerine IN ile spesifik)
                    known_keys = (
                        "np_PompaMarka", "np_PompaModel", "np_PompaTip", "np_PompaCap",
                        "np_PompaDebi", "np_PompaHm", "np_PompaGuc",
                        "np_SurucuGuc", "np_SurucuModel", "np_SurucuMarka",
                        "np_KolonCap", "np_KabloKesit", "np_Debimetre",
                        "np_MotorMarka", "np_MotorModel", "np_MotorGuc",
                        "np_NPSH", "np_Kademe", "np_BasmaDerinlik",
                        "nPModel", "nPMontaj", "nPMontage", "nPSerial",
                    )
                    placeholders = ",".join(["%s"] * len(known_keys))
                    cur.execute(
                        f"SELECT pKey, pVal FROM node_param "
                        f"WHERE nodeId = %s AND pKey IN ({placeholders})",
                        tuple([nid] + list(known_keys)),
                    )
                    for r in cur.fetchall():
                        np_params[r["pKey"]] = r["pVal"]

            # annexa — ic hesaplama icin, kullaniciya her seferinde sunulmaz.
            # Sadece sapma dogrulama ihtiyaci cikarsa (orn. frekans projeksiyonu) uyari olusur.
            annexa_val = None
            if isinstance(pump_eff_row, dict) and pump_eff_row.get("annexa") is not None:
                try:
                    annexa_val = float(pump_eff_row["annexa"])
                except (TypeError, ValueError):
                    pass

            # Pompa bilgisini HER IKI kaynaktan da al ve BIRLESTIR.
            # Spesifik alan tercihi: node_param genelde daha detayli (model no, surucu)
            # pump_eff: annexa, motor_max_eff, montage — orada eşsiz.
            def _s(v: Any) -> Any:
                if v is None:
                    return None
                if isinstance(v, str):
                    v = v.strip()
                    return v or None
                return v

            pe_brand = _s(pump_eff_row.get("brand")) if isinstance(pump_eff_row, dict) else None
            pe_model = _s(pump_eff_row.get("model")) if isinstance(pump_eff_row, dict) else None
            np_brand = _s(np_params.get("np_PompaMarka"))
            np_model = _s(np_params.get("np_PompaModel"))

            # Eger pump_eff model'i generic ("Dalgıç Pompa" gibi) ise np_ tercih edilir
            generic_keywords = {"dalgıç pompa", "submersible", "genel", "generic", "pompa"}
            pe_model_is_generic = (
                pe_model is not None
                and pe_model.lower() in generic_keywords
            )

            best_brand = np_brand or pe_brand
            best_model = np_model if (np_model and (not pe_model or pe_model_is_generic)) else (pe_model or np_model)

            installed_summary: dict[str, Any] = {}
            if best_brand or best_model or pump_eff_row or np_params:
                installed_summary = {
                    "kaynak": (
                        "pump_eff + node_param" if (pump_eff_row and np_params)
                        else ("pump_eff" if pump_eff_row else "node_param")
                    ),
                    "marka": best_brand,
                    "model": best_model,
                    "motor_marka": _s(pump_eff_row.get("motor_brand")) if isinstance(pump_eff_row, dict) else None,
                    "nominal_Q_m3h": (
                        _s(pump_eff_row.get("flow")) if isinstance(pump_eff_row, dict) and pump_eff_row.get("flow")
                        else _s(np_params.get("np_PompaDebi"))
                    ),
                    "nominal_H_m": (
                        _s(pump_eff_row.get("hm")) if isinstance(pump_eff_row, dict) and pump_eff_row.get("hm")
                        else _s(np_params.get("np_PompaHm"))
                    ),
                    "motor_gucu_kW": (
                        _s(pump_eff_row.get("motor_power")) if isinstance(pump_eff_row, dict) and pump_eff_row.get("motor_power")
                        else _s(np_params.get("np_PompaGuc"))
                    ),
                    "pompa_kademe": _s(pump_eff_row.get("pump_stage")) if isinstance(pump_eff_row, dict) else None,
                    "pompa_max_verim_pct": _s(pump_eff_row.get("pump_max_eff")) if isinstance(pump_eff_row, dict) else None,
                    "motor_max_verim_pct": _s(pump_eff_row.get("motor_max_eff")) if isinstance(pump_eff_row, dict) else None,
                    "annexa": annexa_val,
                    "montage": _s(pump_eff_row.get("montage")) if isinstance(pump_eff_row, dict) else None,
                    "note": _s(pump_eff_row.get("note")) if isinstance(pump_eff_row, dict) else None,
                    # node_param'dan eşsiz alanlar
                    "pompa_tip": _s(np_params.get("np_PompaTip")),
                    "pompa_cap_inch": _s(np_params.get("np_PompaCap")),
                    "surucu_guc_kW": _s(np_params.get("np_SurucuGuc")),
                    "surucu_model": _s(np_params.get("np_SurucuModel")),
                    "debimetre": _s(np_params.get("np_Debimetre")),
                    "kablo_kesit": _s(np_params.get("np_KabloKesit")),
                    "kolon_cap_mm": _s(np_params.get("np_KolonCap")),
                    "montaj_derinlik_m": _s(np_params.get("nPMontaj")),
                }
                # None degerleri temizle (LLM'e daha sade gelsin)
                installed_summary = {k: v for k, v in installed_summary.items() if v is not None}

            result: dict[str, Any] = {
                "node_id": nid,
                "installed_pump": installed_summary or None,
                "pump_eff_raw": pump_eff_row,
                "node_param_np_keys": np_params,
                # annexa iç hesap için — kullanıcıya her sefer gösterilmesin.
                # Yalnızca frekans projeksiyonu / tutarsızlık doğrulamasında kullan.
                "annexa_internal": annexa_val,
            }
            if not installed_summary:
                result["hint_tr"] = (
                    "Mevcut pompa bilgisi bulunamadi — ne pump_eff ne node_param. Kullaniciya bildir."
                )
            else:
                # Kullanici sunumu icin detay listesi — annexa DAHIL DEGIL
                parts: list[str] = []
                if installed_summary.get("marka") and installed_summary.get("model"):
                    parts.append(f"{installed_summary['marka']} {installed_summary['model']}")
                elif installed_summary.get("model"):
                    parts.append(str(installed_summary['model']))
                if installed_summary.get("nominal_Q_m3h") and installed_summary.get("nominal_H_m"):
                    parts.append(f"Q={installed_summary['nominal_Q_m3h']} m3/h, H={installed_summary['nominal_H_m']} m")
                if installed_summary.get("motor_gucu_kW"):
                    parts.append(f"Motor: {installed_summary['motor_gucu_kW']} kW")
                if installed_summary.get("pompa_kademe"):
                    parts.append(f"{installed_summary['pompa_kademe']} kademe")
                if installed_summary.get("pompa_cap_inch"):
                    parts.append(f"Çap: {installed_summary['pompa_cap_inch']}\"")
                if installed_summary.get("surucu_model") and installed_summary.get("surucu_guc_kW"):
                    parts.append(f"Sürücü: {installed_summary['surucu_model']} {installed_summary['surucu_guc_kW']} kW")
                if installed_summary.get("montaj_derinlik_m"):
                    parts.append(f"Montaj: {installed_summary['montaj_derinlik_m']} m")
                if installed_summary.get("montage"):
                    parts.append(f"Tarih: {installed_summary['montage']}")
                summary_line = " | ".join(parts) if parts else "veri eksik"
                result["hint_tr"] = (
                    f"Mevcut pompa: {summary_line}. "
                    "TÜM detayları kullanıcıya göster (marka, model, Q, H, motor, kademe, sürücü, montaj). "
                    "annexa'yı kullanıcıya SADECE ölçüm ile etiket arasında sapma varsa veya frekans/pompa değişikliği hesabı sorulduğunda sun."
                )
            return result

        @mcp.tool(name=tool)
        def get_installed_pump_info(nodeId: int) -> str:
            """Node'a takılı mevcut pompa bilgisi.
Kaynak önceliği: pump_eff (marka, model, annexa yaşlanma katsayısı, montage) >
node_param np_* (np_PompaModel, np_PompaMarka, np_PompaDebi, np_PompaHm, np_PompaGuc...).
'kendi pompası ne', 'mevcut pompa ne', 'takılı pompa' sorularında kullan.
annexa < 1 ise pompa yaşlanmış → H_gerçek = H_katalog × annexa."""
            return guard(tool, _get_installed_pump_info_impl)(nodeId)

        # --- get_node_scada_context ---
        tool = prefixed_name(prefix, "get_node_scada_context")

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
            """Node SCADA bağlamı: tag'ler, alarmlar, loglar. Sözlükler eksikse `warnings` döner."""
            return guard(prefixed_name(prefix, "get_node_scada_context"), _get_node_scada_context_impl)(node_id)

        # --- get_node_panel_settings_guide ---
        tool = prefixed_name(prefix, "get_node_panel_settings_guide")

        def _point_display_root() -> str:
            return (os.getenv("KORUBIN_POINT_DISPLAY_ROOT") or "").strip()

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

            root = _point_display_root()
            disk_files: list[str] = []
            disk_files_recursive: list[str] = []
            if root and Path(root).is_dir():
                dpath = Path(root) / n_view
                if dpath.is_dir():
                    for fn in sorted(os.listdir(dpath)):
                        fl = fn.lower()
                        if fl.endswith(".phtml") or fl.endswith(".js"):
                            disk_files.append(fn)
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
            """DEPRECATED — çalışma modu / ayar / menü soruları için bu yerine:
            get_skill(skill_name='korubin-scada', file_path='screen-types/nview/<nView>.md').
            Bu tool eski JSON hint dosyasına bakar; nView skill dosyaları çok daha zengin
            (her alt menü sayfasının başlığı + XC_*/XS_*/XE_* ayar parametreleri)."""
            return guard(prefixed_name(prefix, "get_node_panel_settings_guide"), _get_node_panel_settings_guide_impl)(node_id, topic)

        # --- get_operational_engineering_hints ---
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

    def manifest_groups(self, *, prefix: str) -> list[dict]:
        p = prefix
        return [
            {
                "id": "nodes",
                "title_tr": "Node / topo",
                "tools": [
                    p + "get_node_counts",
                    p + "list_nodes",
                    p + "find_nodes_by_keywords",
                    p + "get_node",
                    p + "list_product_types",
                    p + "get_node_scada_context",
                    p + "get_node_panel_settings_guide",
                    p + "get_operational_engineering_hints",
                ],
            },
        ]
