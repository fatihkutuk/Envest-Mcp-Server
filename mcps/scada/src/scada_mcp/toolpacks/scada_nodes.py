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
                    # Bos sonuc: diger SCADA instance'larini dene uyarisi
                    out["hint_tr"] = (
                        f"'{kw}' icin bu SCADA'da ({prefix.rstrip('_')}) sonuc bulunamadi. "
                        "MULTI-INSTANCE SETUP: Eger bu merged MCP'de birden fazla SCADA varsa "
                        "(orn. corumscada_, envestbulutkorubin_), MUTLAKA diger prefix'lerde de AYNI ARAMA'yi tekrarla. "
                        "Ornek: corumscada_find_nodes_by_keywords bos dondurduyse, hemen "
                        "envestbulutkorubin_find_nodes_by_keywords('{kw}') cagir. "
                        "Hepsi bos dondurduyse kullaniciya bildir, tahmin yurutme."
                    )
                    out["next_action_required"] = (
                        "try_other_scada_instance_prefixes_before_asking_user"
                    )
                else:
                    out["hint_tr"] = (
                        "İlk satırlar genelde en kısa ve en iyi isim eşleşmesidir; birden fazla satır varsa "
                        "nName ve urun_tipi ile seçin (kuyu: genelde «Koru1000 Well» / nView a-kuyu-envest)."
                    )
                # Her node için nView'a bağlı skill önerisi — ayar/menü/çalışma modu soruları için
                for n in out.get("nodes", []):
                    nv = str(n.get("nView") or "")
                    if nv:
                        n["ekran_tipi_skill_path"] = f"screen-types/nview/{nv}.md"
                out["ayar_ve_menu_soru_icin_sonraki_adim_tr"] = (
                    "Kullanıcı 'ayar', 'çalışma modu', 'nereden ayarlayacağım', 'menü' gibi bir şey "
                    "sorduysa: get_skill(skill_name='korubin-scada', file_path='screen-types/nview/<nView>.md') "
                    "ile o nView'a özel skill dosyasını okuyun; içindeki 'Alt Menü Sayfaları' tablosunda "
                    "hangi alt sayfanın hangi parametreleri ayarladığı yazar. Örn: 'çalışma modu' -> "
                    "'calismamod' sayfası (XC_SabitMod* parametreleri). Canlı değer için ayrıca "
                    "get_device_tag_values(tagNames=['XC_CalismaModu']) çağrılabilir."
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
            """Node arama (isim, nView, nType). nView alt dizgesi ve ürün tipi adı dahil aranır.

            AYAR / MENÜ / ÇALIŞMA MODU soruları için iş akışı:
            1) Bu tool ile node'u bul (nodeId + nView alırsın).
            2) get_skill(skill_name='korubin-scada', file_path='screen-types/nview/<nView>.md')
               ile o ekran tipinin 'Alt Menü Sayfaları' ve 'Arayüz Ayarları' tablolarını oku.
            3) Canlı değer gerekiyorsa get_device_tag_values ile ilgili tag'i oku.
            Bu akış search_product_manual / get_product_specs YOLU DEĞİLDİR — onlar cihaz kataloğu,
            panel ayar menüsü değil.
            """
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
                node["ekran_tipi_skill_yonlendirme_tr"] = (
                    f"Bu node ekran tipi '{nv}'. Ayar/menü/konfigürasyon sorusu için: "
                    f"get_skill(skill_name='korubin-scada', file_path='screen-types/nview/{nv}.md') "
                    "çağırın. Skill dosyasının 'Alt Menü Sayfaları' tablosunda hangi alt sayfa hangi "
                    "parametreleri düzenliyor açık yazar (ör. calismamod -> XC_SabitMod*, "
                    "emniyet -> XE_*, sensor -> XS_* vb.). 'Arayüz Ayarları' tablosu ui_* bayraklarıyla "
                    "hangi tag'in aktif olduğunu gösterir."
                )

            # Pompa secimi icin KRITIK uyari — nView'a gore pompa ailesi + canli tag zorunlulugu
            nv_l = nv.lower()
            nname_l = str(node.get("nName") or "").lower()
            is_well = ("kuyu" in nv_l) or ("kuyu" in nname_l) or ("well" in nv_l)
            is_booster = ("terfi" in nv_l) or ("terfi" in nname_l) or ("booster" in nv_l) or ("hidro" in nv_l)
            if is_well or is_booster or "depo" in nv_l or "dma" in nv_l:
                node["pompa_secimi_kisa_yol_tr"] = (
                    f"POMPA SECIMI ICIN TEK CAGRI YETER: "
                    f"{prefix}prepare_pump_selection(nodeId={node.get('id')}). "
                    "Bu tool canli tag'leri okur (ToplamHm merkez), formulle dogrular "
                    "(P_hid = Q×H/367), hazir Q/H dondurur. Sonra next_action'i aynen cagir. "
                    "get_device_tag_values / get_node_all_tags ile manuel uğrasma."
                )
                node["pompa_secimi_yasak_tr"] = (
                    "BasincSensoru × 10.197 ile HM TURETME — bu hat basinci, kuyu derinligi "
                    "+ surtunme iceremez. ToplamHm tag'ini DOGRUDAN oku. "
                    "XD_BasmaYukseklik (ayar), np_PompaHm (katalog), XS_DebimetreMax (sensor tavani) "
                    "YASAK — hicbiri canli olcum degildir."
                )
            return node

        @mcp.tool(name=tool)
        def get_node(nodeId: int) -> str:
            """Tek node detayı (nView, nType, parametreler vb.). Panel şablon/menü için nView kritik alandır.

            Çıktıda 'ekran_tipi_skill_path' varsa: get_skill ile o dosyayı mutlaka okuyun — içinde
            bu ekran tipinin alt menüleri, ayar parametreleri, hangi tag nerede gibi tam referans var.
            Bu, search_product_manual / get_product_specs YERİNE kullanılır (onlar cihaz kataloğu)."""
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
                # VFD / surucu tespiti icin frekans tag'leri
                "An_SebFrekans", "P1_Frekans", "Pompa1Frekans",
                "PompaFrekans", "Frekans", "An_Frekans",
                "SurucuVar", "SurucuAktif",
            ]

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

            # Canli degerler — ToplamHm MERKEZ
            head_m = _num("ToplamHm")
            flow = _num("Debimetre") or _num("Debimetre1")
            flow_ltsn = _num("DebimetreLtSn")
            if flow is None and flow_ltsn is not None:
                flow = flow_ltsn * 3.6  # Lt/sn -> m3/h
            power_kw = _num("An_Guc") or _num("P1_Guc")
            eta_hyd = _num("YaklasikHidrolikVerim") or _num("HidrolikVerim") or _num("PompaVerim")

            # VFD / surucu tespiti — frekans tag'i varsa ve 50 Hz disindaysa VFD aktif
            freq_candidates = [
                ("An_SebFrekans", _num("An_SebFrekans")),
                ("P1_Frekans", _num("P1_Frekans")),
                ("Pompa1Frekans", _num("Pompa1Frekans")),
                ("PompaFrekans", _num("PompaFrekans")),
                ("Frekans", _num("Frekans")),
                ("An_Frekans", _num("An_Frekans")),
            ]
            freq_tags_present = [name for name, v in freq_candidates if v is not None]
            freq_val = next((v for _, v in freq_candidates if v is not None), None)
            surucu_flag = _num("SurucuVar") or _num("SurucuAktif")
            # Heuristik: An_SebFrekans "sebeke" frekansidir (genelde 50Hz sabit) —
            # tek basina VFD gostermez. Pompa-ozgu frekans (P1_Frekans, PompaFrekans)
            # 50'den farkliysa VFD aktif demektir.
            pump_freq = (
                _num("P1_Frekans") or _num("Pompa1Frekans")
                or _num("PompaFrekans") or _num("Frekans")
            )
            if surucu_flag is not None:
                vfd_detected: bool | None = bool(surucu_flag > 0.5)
                vfd_source = "SurucuVar/SurucuAktif tag'i"
            elif pump_freq is not None:
                vfd_detected = True  # pompa frekans tag'i varsa surucu vardir
                vfd_source = f"pompa frekans tag'i ({pump_freq} Hz) mevcut"
            else:
                vfd_detected = None  # belirsiz
                vfd_source = (
                    "Sistemde frekans veya surucu tag'i bulunamadi — "
                    "VFD varligi tag'lardan kesinlenemedi. "
                    "Kullaniciya saha durumu teyit ettirilmeli."
                )

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

            if vfd_detected is True:
                impeller_kural_tr = (
                    "Sistemde SURUCU/VFD VAR → TAM CAPLI (standart) pompa tercih et. "
                    "Tirasli fanli (isim sonunda N ornegin 'SP 125-8-AAN') pompadan kacin. "
                    "Surucu frekans dusurerek debiyi ayarlayabilir, tirasliya gerek yok. "
                    "Istisna: Surucu ile istenen noktaya ulasilamiyorsa tirasliya donulur."
                )
                korucaps_prefer_impeller = "full"
            elif vfd_detected is False:
                impeller_kural_tr = (
                    "Sistemde SURUCU/VFD YOK → Hem tam capli hem tirasli fanli pompa uygun. "
                    "Hangi seri calisma noktasina daha iyi oturuyorsa o secilir. "
                    "Tirasli fan (N ile biten, orn 'SP 125-8-AAN') daha esnek H ayarina izin verir."
                )
                korucaps_prefer_impeller = "any"
            else:
                impeller_kural_tr = (
                    "VFD varligi BELIRSIZ — tag'lardan tespit edilemedi. "
                    "Hem tam capli hem tirasli fanli sonuclari kullaniciya sun, "
                    "farkini anlat (tirasli = impelleri kuculup H/Q ayari, tam capli = standart). "
                    "Kullaniciya 'sahada sürücü var mi?' diye sor."
                )
                korucaps_prefer_impeller = "any"

            result: dict[str, Any] = {
                "node_id": nid,
                "node_name": node.get("nName"),
                "nView": node.get("nView"),
                "pump_type": pump_type_tr,
                "running": running,
                "canli_olcumler": {
                    "ToplamHm_m": head_m,
                    "Debimetre_m3h": flow,
                    "An_Guc_kW": power_kw,
                    "YaklasikHidrolikVerim": eta_hyd,
                    "BasincSensoru_bar": _num("BasincSensoru"),
                    "HatBasincSensoru_bar": _num("HatBasincSensoru"),
                    "pompa_frekans_Hz": pump_freq,
                    "sebeke_frekans_Hz": _num("An_SebFrekans"),
                },
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

            if result["hazir"]:
                vfd_param = "true" if vfd_detected is True else "false"
                result["next_action"] = (
                    f"korucaps_search_pumps(flow_m3h={flow}, head_m={head_m}, "
                    f"application='{kc_app}', sub_application='{kc_sub}', vfd={vfd_param})"
                )
                impeller_uyari = ""
                if vfd_detected is True:
                    impeller_uyari = (
                        " SUNARKEN: Sistemde VFD VAR — TAM CAPLI (isim sonunda N olmayan) "
                        "pompalari on-plana cikar, tirasli (N ile biten) alternatifleri "
                        "'surucu yoksa secenek' olarak ikinci sirada goster."
                    )
                elif vfd_detected is False:
                    impeller_uyari = (
                        " SUNARKEN: Sistemde VFD YOK — tam capli ve tirasli (N) seceneklerin"
                        " ikisini de sun, farkini kisaca anlat (tirasli = kuculmus impeller,"
                        " daha esnek H/Q ayari)."
                    )
                else:
                    impeller_uyari = (
                        " SUNARKEN: VFD varligi BELIRSIZ — kullaniciya 'sahada surucu var mi?'"
                        " diye sor. Cevaba gore tam capli veya tirasli (N) secenegi oner."
                    )
                result["hint_tr"] = (
                    "Veriler tutarli. Yukaridaki next_action komutunu AYNEN calistir. "
                    "Degerleri YUVARLAMA, hesaplari TEKRAR yapma." + impeller_uyari
                )
            else:
                highs = [c for c in checks if c["severity"] == "HIGH"]
                if highs:
                    result["next_action"] = "stop_and_resolve_checks"
                    result["hint_tr"] = (
                        "DURUM KRITIK — checks listesinde HIGH severity sorunlar var. "
                        "korucaps_search_pumps CAGIRMA. Once sorunlari kullaniciya bildir veya "
                        "eksik tag'leri tamamla. Ozellikle ToplamHm bulunamadiysa, "
                        "BasincSensoru'ndan HM TURETME."
                    )
                else:
                    result["hint_tr"] = (
                        "Uyarilar var ama kritik degil. Yine de kullaniciya teyit ederek ilerle."
                    )
            return result

        @mcp.tool(name=tool)
        def prepare_pump_selection(nodeId: int) -> str:
            """Pompa secimi icin TEK ADIMDA hersey: canli tag okuma + formulle dogrulama + hazir Q/H.

            KULLANIM: Kullanici bir node icin pompa secimi istediginde:
            1) find_node_everywhere ile node'u bul
            2) <prefix>_prepare_pump_selection(nodeId) -> CANLI Hm, Debi, guc, verim + tutarlilik check
            3) Response'ta 'hazir=true' ve 'next_action' varsa O KOMUTU AYNEN cagir
            4) 'checks' icinde HIGH varsa DURDURUK kullaniciya bildir

            ToplamHm bulamazsa BasincSensoru'ndan HM TURETME — cunki bu sadece hat basinci,
            kuyu derinligi + surtunme icermez. Yanlis H -> yanlis pompa.

            Formulle dogrular: P_hid = (Q × H) / 367, P1 = P_hid / η. An_Guc ile tutarsiz ise alarm.
            """
            return guard(tool, _prepare_pump_selection_impl)(nodeId)

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
