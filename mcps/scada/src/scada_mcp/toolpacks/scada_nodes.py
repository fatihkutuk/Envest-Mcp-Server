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


def _fetch_last_running_avg(cfg: "InstanceConfig", nid: int) -> dict[str, Any] | None:
    """
    Pompa suan dursa bile son 24 saatteki pompanin calisma donemindeki ortalamalari bul.

    Strateji:
    1) Pompa1StartStopDurumu (veya PompaStartStopDurumu) = 1 olan en son log zamani T'yi bul
    2) Window = [T - 60dk, T]
    3) Ilgili tag'lerin (ToplamHm, Debimetre, An_Guc, An_InvFrekans) bu pencerede
       ortalamasini al. Pencerede asgari N nokta olmalidir.
    """
    if not cfg.db:
        return None
    tname = f"log_{int(nid)}"
    try:
        with dbmod.connect(cfg.db) as conn:
            with conn.cursor() as cur:
                # Log tablosu var mi?
                cur.execute(
                    "SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
                    "WHERE TABLE_SCHEMA='noktalog' AND TABLE_NAME=%s LIMIT 1",
                    (tname,),
                )
                if not cur.fetchone():
                    return {"error": "log tablosu yok", "table": tname}

                # Ilgili logparameters IDs
                cur.execute(
                    """
                    SELECT id, tagPath FROM kbindb.logparameters
                    WHERE nid = %s AND tagPath IN (
                        'Pompa1StartStopDurumu','PompaStartStopDurumu','PompaCalismaDurumu',
                        'ToplamHm','Debimetre','Debimetre1','An_Guc','P1_Guc',
                        'An_InvFrekans','An_InverterFrekans','P1_Frekans','PompaFrekans'
                    )
                    """,
                    (nid,),
                )
                lp_rows = list(cur.fetchall())
                if not lp_rows:
                    return {"error": "logparameters'ta ilgili tag yok"}
                id_to_tag = {int(r["id"]): str(r["tagPath"]) for r in lp_rows}
                tag_to_ids = {}
                for lid, tname_tag in id_to_tag.items():
                    tag_to_ids.setdefault(tname_tag, []).append(lid)

                # Pompa calisma durumu tag'lerinin ID'leri
                running_ids = []
                for t in ("Pompa1StartStopDurumu", "PompaStartStopDurumu", "PompaCalismaDurumu"):
                    running_ids.extend(tag_to_ids.get(t, []))
                if not running_ids:
                    return {"error": "pompa calisma tag'i log'da yok"}

                # Son 24 saatte pompa calisma kaydi
                rph = ",".join(["%s"] * len(running_ids))
                cur.execute(
                    f"""
                    SELECT l.logTime FROM noktalog.`{tname}` l
                    WHERE l.logPId IN ({rph}) AND l.tagValue > 0.5
                      AND l.logTime >= NOW() - INTERVAL 24 HOUR
                    ORDER BY l.logTime DESC
                    LIMIT 1
                    """,
                    tuple(running_ids),
                )
                last_run_row = cur.fetchone()
                if not last_run_row:
                    return {
                        "error": "son 24 saatte pompa calisma kaydi yok",
                        "oneri": "Daha uzun log araligi sorgulanmali (get_node_log_data ile 48h+)",
                    }
                last_run_time = last_run_row["logTime"]

                # Window: last_run_time - 60dk -> last_run_time
                all_ids = list(id_to_tag.keys())
                all_ph = ",".join(["%s"] * len(all_ids))
                cur.execute(
                    f"""
                    SELECT l.logPId, l.tagValue, l.logTime
                    FROM noktalog.`{tname}` l
                    WHERE l.logPId IN ({all_ph})
                      AND l.logTime <= %s
                      AND l.logTime >= DATE_SUB(%s, INTERVAL 60 MINUTE)
                    """,
                    tuple(all_ids + [last_run_time, last_run_time]),
                )
                rows = list(cur.fetchall())

        # Gruplandirma ve pompa calisirkenki ortalamalar
        running_times: set = set()
        for r in rows:
            lid = int(r["logPId"])
            if lid in running_ids:
                try:
                    if float(r["tagValue"]) > 0.5:
                        running_times.add(r["logTime"])
                except (TypeError, ValueError):
                    pass

        # Tag bazinda ortalama
        per_tag: dict[str, list[float]] = {}
        for r in rows:
            lid = int(r["logPId"])
            tag = id_to_tag.get(lid)
            if not tag or tag in ("Pompa1StartStopDurumu", "PompaStartStopDurumu", "PompaCalismaDurumu"):
                continue
            # Sadece pompa calisirkenki kayitlar (yakin zamanda)
            # Basitlestirme: tum penceredeki degerleri al (pompa pencerede calisiyor kabul)
            try:
                per_tag.setdefault(tag, []).append(float(r["tagValue"]))
            except (TypeError, ValueError):
                pass

        def _avg(name: str) -> float | None:
            vals = per_tag.get(name) or []
            if not vals:
                return None
            return round(sum(vals) / len(vals), 2)

        result: dict[str, Any] = {
            "son_calisma_bitim_zamani": str(last_run_time),
            "pencere_dakika": 60,
            "sample_count": sum(len(v) for v in per_tag.values()),
            "ortalama_ToplamHm": _avg("ToplamHm"),
            "ortalama_Debimetre": _avg("Debimetre") or _avg("Debimetre1"),
            "ortalama_An_Guc": _avg("An_Guc") or _avg("P1_Guc"),
            "ortalama_Frekans": (
                _avg("An_InvFrekans") or _avg("An_InverterFrekans")
                or _avg("P1_Frekans") or _avg("PompaFrekans")
            ),
            "aciklama_tr": (
                "Pompa şu an durmuş; son 1 saatlik çalışma dönemi ortalamaları. "
                "Verim/analiz hesaplarında canli_olcumler yerine bu değerleri kullan. "
                "Kullanıcıya 'pompa şu an durduğu için son çalışma dönemi (X zamanı) "
                "ortalamaları alındı' diye belirt."
            ),
        }
        return {k: v for k, v in result.items() if v is not None}
    except Exception as exc:
        return {"error": f"log okunamadi: {type(exc).__name__}: {exc}"}


def _evaluate_installed_fit(
    *,
    installed_pump: dict[str, Any] | None,
    live_flow: float | None,
    live_head: float | None,
    live_power: float | None,
    pump_output_freq: float | None,
) -> dict[str, Any] | None:
    """
    Mevcut pompanin is noktasina uygunlugunu degerlendirir.

    Dogru boyutlandirilmis pompa yerine baska pompa onerisi vermek YANLIS.
    Bu fonksiyon: duty point pompanin calisma bandinda mi, BEP'e yakin mi,
    VFD ile surdurulebilir mi — degerlendirir.
    """
    if not installed_pump or not live_flow or not live_head:
        return None

    def _tof(v: Any) -> float | None:
        if v is None:
            return None
        try:
            if isinstance(v, str):
                v = v.strip().replace(",", ".")
            return float(v)
        except (TypeError, ValueError):
            return None

    nom_q = _tof(installed_pump.get("nominal_Q") or installed_pump.get("nominal_Q_m3h"))
    nom_h = _tof(installed_pump.get("nominal_H") or installed_pump.get("nominal_H_m"))
    nom_p = _tof(installed_pump.get("motor_kW") or installed_pump.get("motor_gucu_kW"))
    if not nom_q or not nom_h:
        return {
            "karar": "belirsiz",
            "sebep": "Mevcut pompanın nominal Q/H değerleri yok — kıyas yapılamaz.",
        }

    q_ratio = live_flow / nom_q  # duty Q / nominal Q
    h_ratio = live_head / nom_h  # duty H / nominal H

    # Pompa eğrisinde typik çalışma bandı:
    #  - Q: nominal'in %60-120'si (BEP etrafı)
    #  - H: frekans ayarıyla da düşürülebilir, nominal'in %40-110 arası kabul edilebilir
    q_in_range = 0.55 <= q_ratio <= 1.25
    h_in_range = 0.35 <= h_ratio <= 1.15

    # BEP yakınlığı: duty Q, nominal Q'nun %85-105'indeyse BEP'e yakın
    near_bep = 0.80 <= q_ratio <= 1.10

    # VFD desteği ile H azaltımı: h_ratio < 1 ise pompa daha az H veriyor
    # affinity Q∝f, H∝f² — freq'de kisi yaklasik sqrt(h_ratio)
    # pratik calisma: f_ratio = sqrt(h_ratio) mantikli
    # Eger pump_output_freq varsa gercek kullan
    f1 = pump_output_freq or 50.0

    notlar: list[str] = []
    if near_bep:
        notlar.append(
            f"Q={live_flow} m³/h, nominal {nom_q} m³/h'nin %{round(q_ratio*100)} — BEP yakınında."
        )
    elif q_in_range:
        notlar.append(
            f"Q={live_flow} m³/h, nominal {nom_q} m³/h'nin %{round(q_ratio*100)} — çalışma bandında (BEP dışı)."
        )
    else:
        notlar.append(
            f"Q={live_flow} m³/h, nominal {nom_q} m³/h'nin %{round(q_ratio*100)} — BANT DIŞI, yanlış ölçek."
        )

    if h_ratio < 0.7:
        notlar.append(
            f"H={live_head} m, nominal {nom_h} m'nin %{round(h_ratio*100)} — pompa ZIADİ (fazla basma veriyor), VFD ile {f1:.0f} Hz'de kısılmış."
        )
    elif h_ratio > 1.05:
        notlar.append(
            f"H={live_head} m, nominal H {nom_h} m — pompa zorlanıyor olabilir, hız artmış ya da kademeler yetersiz."
        )

    # Kademe bilgisi — buffer avantajı için
    kademe = installed_pump.get("kademe") or installed_pump.get("pompa_kademe")
    try:
        kademe_num = int(kademe) if kademe is not None else None
    except (TypeError, ValueError):
        kademe_num = None

    # H buffer'ı hesaplama: nominal H'ye ne kadar başlık kaldı?
    # Nominal H'nin %50 altında çalışıyorsa ciddi buffer var.
    h_buffer_pct = round((1.0 - h_ratio) * 100, 1) if h_ratio < 1 else 0.0

    # Karar mantığı — RİSK-ODAKLI (pump-sizing-philosophy.md)
    # Varsayılan: mevcut pompa KORUMA. Değiştirme önerisi ancak gerçek gerekçeyle.
    if q_in_range and h_ratio < 1.15:
        if near_bep:
            karar = "mevcut_uygun"
            karar_tr = (
                "Mevcut pompa BU iş noktasına UYGUN (BEP yakın). "
                "Değiştirme ÖNERME. Tasarruf: VFD ince ayar, boru/vana kontrolü, bakım."
            )
        elif h_ratio < 0.65 and kademe_num and kademe_num >= 3:
            # H çok düşük + çok kademeli → ESNEKLIK avantajı var
            karar = "mevcut_uygun_esneklik"
            karar_tr = (
                f"Mevcut pompa {kademe_num} kademeli — H buffer'ı var (%{h_buffer_pct}). "
                "VFD ile frekans düşürülmüş. "
                "DEĞİŞTİRMEYİ ÖNERMEDEN ÖNCE düşün: H ihtiyacı yükselirse (kuyu seviyesi "
                "düşmesi, boru yaşlanması) bu pompa karşılayabilir. "
                "Az kademeli pompa (örn. 2 kademe) şu an verimli gözükür ama H limiti düşer "
                "→ gelecekte sistem çökebilir. "
                "Varsayılan öneri: MEVCUDU KORU + VFD optimize et. "
                "Az kademeli alternatifi SADECE kullanıcı 'kesinlikle sabit H' derse sun, "
                "üstelik H risk uyarısıyla."
            )
        elif h_ratio < 0.65:
            # H düşük ama kademe bilgisi yok veya az
            karar = "mevcut_dusuk_verim"
            karar_tr = (
                "Mevcut pompa H'ı VFD ile kısılmış (nominal'in %"
                f"{round(h_ratio*100)}'si). Verim düşük olabilir. "
                "Kullanıcının saha riski (H varyasyonu) düşükse aynı seride az kademeli "
                "alternatifi *seçenek* olarak sun (tek seçenek dayatma değil). "
                "H varyasyonu biliniyorsa risk analizi yap. "
                "Varsayılan: mevcudu VFD ile optimize et."
            )
        else:
            karar = "mevcut_bep_disi"
            karar_tr = (
                "Mevcut pompa çalışma bandında ama BEP'te değil. "
                "Enerji kazancı belirgin + tesis koşulları stabilse alternatif "
                "BEP'e daha iyi oturan model sun — ama ZORUNLU değil. "
                "Öncelik: VFD/işletme optimizasyonu."
            )
    else:
        karar = "uygunsuz_boyutlu"
        karar_tr = (
            "Mevcut pompa bu iş noktası için uygun ölçekte değil "
            f"(Q oranı %{round(q_ratio*100)}, H oranı %{round(h_ratio*100)}). "
            "Alternatif pompa seçimi değerlendirilmeli."
        )

    return {
        "karar": karar,
        "karar_tr": karar_tr,
        "duty_Q_m3h": live_flow,
        "duty_H_m": live_head,
        "nominal_Q_m3h": nom_q,
        "nominal_H_m": nom_h,
        "kademe": kademe_num,
        "q_ratio_duty_over_nominal": round(q_ratio, 3),
        "h_ratio_duty_over_nominal": round(h_ratio, 3),
        "h_buffer_pct": h_buffer_pct,
        "bep_yakin_mi": near_bep,
        "bant_ici_mi": q_in_range and h_in_range,
        "vfd_cikis_freq_Hz": f1,
        "notlar": notlar,
        "karar_kurali_tr": (
            "LLM için: VARSAYILAN = MEVCUT POMPAYI KORU. "
            "Değiştirme önerisi için: pump-sizing-philosophy.md skill'ini oku. "
            "Aynı seri az kademeli öneri SADECE H risk uyarısıyla SEÇENEK olarak sunulur, "
            "dayatma değil. Kullanıcıya 'Koruma (A) vs değişim (B)' karşılaştırması ver."
        ),
        "onerilen_sunum_yapisi": (
            "1) Mevcut durum + değerlendirme\n"
            "2) Seçenek A: Mevcut pompayı koru + VFD ince ayar (VARSAYILAN)\n"
            "3) Seçenek B: Aynı seri az kademeli (H risk uyarısıyla)\n"
            "4) Seçenek C: Farklı seri (sadece duty uyuyorsa)\n"
            "5) Öneri: konservatif/agresif tercih matrisi"
        ),
    }


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
                "SuSeviye", "StatikSuSeviye", "DinamikSeviye",
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
                # Calisma modu — pompa durusu normal mi kritik mi kararinda kritik
                "XC_CalismaModu", "XC_SabitModSecim",
                "XC_SabitModBasinc", "XC_SabitModDebi", "XC_SabitModSeviye",
                "XC_SabitModGuc", "XC_SabitModFrekans",
                "XC_KuyuModu", "XC_TerfiMasterModu", "XC_TerfiSlaveModu",
                # a-kuyu-p tarzi nView'larda XC_CalismaModu yerine ayri bayraklar
                "XC_OtoDepoDolMod", "XC_OtoHidroforMod", "XC_OtoSerbestMod",
                "DepoSeviye", "DepoSeviye1", "DepoSeviye2", "HedefDepoSeviye",
                "XD_DepoMaxSeviye", "XD_DepoMinSeviye",
                # Hidrolik ag parametreleri (XV_* = sistem/tesisat konfigurasyonu)
                # Bu degerler verim analizinde kullanilmalidir: sürtünme, kablo kaybi,
                # sürücü kaybi, motor verimi, boru uzunluk/cap/purislulugu.
                "XV_BoruUzunluk",     # boru uzunlugu (m)
                "XV_BoruIcCap",       # boru ic capi (mm)
                "XV_PipeRoughness",   # boru purislulugu (mm cinsinden, genelde 0.1mm civari)
                "XV_Nsurtunme",       # sürtünme verim faktörü (0-1)
                "XV_Nmotor",          # motor verimi (%)
                "XV_KabloKayip",      # kablo kaybi (%)
                "XV_SurucuKayip",     # sürücü kaybi (%)
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

            # Calisma modu ve setpoint okuma (pompa durusu yorumu icin)
            # nView-AWARE: her nView farkli mapping kullanir, dogru olanini sec
            calisma_modu_val = _num("XC_CalismaModu")
            sabit_mod_secim_val = _num("XC_SabitModSecim")
            _nview_key = str(node.get("nView") or "").strip().lower()

            # nView-spesifik XC_CalismaModu mapping — skill dosyalarindan (calisma-modlari-*.md)
            _mode_maps_by_nview = {
                # Kuyu ailesi
                "a-kuyu-envest":       {1: "Depo Doldurma", 2: "Hidrofor", 3: "Serbest Kuyu"},
                "a-kuyu-envest-drenaj":{1: "Depo Doldurma", 2: "Hidrofor", 3: "Serbest Kuyu"},
                "a-kuyu-envest-v2":    {1: "Depo Doldurma", 2: "Hidrofor", 3: "Serbest Kuyu"},
                "a-kuyu-envest-act":   {1: "Depo Doldurma", 2: "Hidrofor", 3: "Serbest Kuyu"},
                "a-aqua-cnt-kuyu-v2":  {0: "Serbest Akış", 3: "Basınç PI", 4: "Seviye Doldurma PI"},
                "a-aqua-cnt-kuyu":     {0: "Serbest Akış", 3: "Basınç PI", 4: "Seviye Doldurma PI"},
                "a-kuyu-p-v4":         {1: "Serbest", 2: "Hidrofor", 3: "Depo Doldurma", 4: "Terfi"},
                "a-kuyu-p-v4.1":       {1: "Serbest", 2: "Hidrofor", 3: "Depo Doldurma", 4: "Terfi"},
                # a-kuyu-p XC_CalismaModu kullanmaz, ayri XC_Oto* bayraklari var
                # Terfi ailesi
                "a-terfi-envest":      {1: "Depo Doldurma", 2: "Hidrofor", 3: "Serbest"},
                "a-terfi-envestdalgic":{1: "Depo Doldurma", 2: "Hidrofor", 3: "Serbest"},
                "a-terfi-p-v4":        {1: "Serbest", 2: "Hidrofor", 3: "Depo Doldurma", 4: "Terfi"},
                "a-terfi-p-v3":        {1: "Serbest", 2: "Hidrofor", 3: "Depo Doldurma", 4: "Terfi"},
                "a-aqua-cnt-terfi-v2": {0: "FreeFlow", 1: "TargetLevel", 2: "TargetPressure", 3: "PressurePI"},
                "a-aqua-cnt-terfi-v2-3b":{0: "FreeFlow", 1: "TargetLevel", 2: "TargetPressure", 3: "PressurePI"},
                # Klor (a-aqua-cnt-depo-klor) XC_CalismaMod (not Modu) — farkli isim
                "a-aqua-cnt-depo-klor":{1: "Link Debi Oransal Klorlama", 2: "Motor Kontrol Klorlama",
                                        3: "Dahili Klorlama", 4: "Link Bakiye Klorlama"},
            }
            _default_kuyu_map = {1: "Depo Doldurma", 2: "Hidrofor", 3: "Serbest Kuyu"}
            _mode_map = _mode_maps_by_nview.get(_nview_key, _default_kuyu_map)

            # Not: a-kuyu-p gibi nView'larda XC_CalismaModu yok — XC_Oto* bayraklariyla calisir.
            # Tespit: _num("XC_OtoDepoDolMod"), _num("XC_OtoHidroforMod"), _num("XC_OtoSerbestMod")
            if calisma_modu_val is None:
                oto_depo = _num("XC_OtoDepoDolMod")
                oto_hidro = _num("XC_OtoHidroforMod")
                oto_serbest = _num("XC_OtoSerbestMod")
                if any(v is not None for v in (oto_depo, oto_hidro, oto_serbest)):
                    if oto_depo and oto_depo > 0.5:
                        calisma_modu_val = 1  # map to generic
                        mode_source = "XC_OtoDepoDolMod"
                    elif oto_hidro and oto_hidro > 0.5:
                        calisma_modu_val = 2
                        mode_source = "XC_OtoHidroforMod"
                    elif oto_serbest and oto_serbest > 0.5:
                        calisma_modu_val = 3
                        mode_source = "XC_OtoSerbestMod"
                    else:
                        mode_source = "XC_Oto* tumu pasif"
                else:
                    mode_source = None
            else:
                mode_source = "XC_CalismaModu"

            _sabit_map = {1: "Sabit Basinc", 2: "Sabit Debi", 3: "Sabit Seviye",
                          4: "Sabit Guc", 5: "Sabit Frekans"}
            calisma_modu: dict[str, Any] = {
                "nView": node.get("nView"),
                "mode_source": mode_source,
                "mapping_kaynagi_tr": (
                    f"nView '{_nview_key}' icin kod-icinde tanimli"
                    if _nview_key in _mode_maps_by_nview else
                    "nView bilinmeyen — varsayilan kuyu mapping kullanildi, "
                    "dogrulamak icin get_skill('korubin-scada','conventions/calisma-modlari-<aile>.md')"
                ),
                "XC_CalismaModu": calisma_modu_val,
                "mod_adi": _mode_map.get(int(calisma_modu_val), "belirsiz") if calisma_modu_val is not None else None,
                "XC_SabitModSecim": sabit_mod_secim_val,
                "sabit_mod_adi": _sabit_map.get(int(sabit_mod_secim_val), "belirsiz") if sabit_mod_secim_val else None,
                "setpoint_basinc_bar": _num("XC_SabitModBasinc"),
                "setpoint_debi_m3h": _num("XC_SabitModDebi"),
                "setpoint_seviye_m": _num("XC_SabitModSeviye"),
                "setpoint_guc_kW": _num("XC_SabitModGuc"),
                "setpoint_frekans_Hz": _num("XC_SabitModFrekans"),
                "kuyu_modu_aktif": _num("XC_KuyuModu"),
                "terfi_master_aktif": _num("XC_TerfiMasterModu"),
                "terfi_slave_aktif": _num("XC_TerfiSlaveModu"),
                # a-kuyu-p tarzi ayri bayraklari da surface et
                "XC_OtoDepoDolMod": _num("XC_OtoDepoDolMod"),
                "XC_OtoHidroforMod": _num("XC_OtoHidroforMod"),
                "XC_OtoSerbestMod": _num("XC_OtoSerbestMod"),
            }
            calisma_modu = {k: v for k, v in calisma_modu.items() if v is not None}

            # Pompa DURUSU yorumlama — mode-aware (Depo Doldurmada ust seviyede normal durus)
            durus_degerlendirme: dict[str, Any] | None = None
            if not running:
                durus_sebep = "belirsiz"
                durus_normal = False
                if calisma_modu_val and int(calisma_modu_val) == 1:
                    # Depo Doldurma modu: seviye setpoint'e ulasilinca normal durus
                    setpoint_sev = _num("XC_SabitModSeviye")
                    depo_sev = (_num("DepoSeviye") or _num("DepoSeviye1")
                                or _num("HedefDepoSeviye"))
                    if setpoint_sev and depo_sev and depo_sev >= setpoint_sev * 0.95:
                        durus_sebep = "depo_dolu_normal_durus"
                        durus_normal = True
                    else:
                        durus_sebep = "depo_doldurma_modunda_durmus_ama_seviye_dusuk"
                elif calisma_modu_val and int(calisma_modu_val) == 2:
                    durus_sebep = "hidrofor_modu_basinc_hedefinde_durmus_olabilir"
                    durus_normal = True  # hidrofor'da pompa sık sık açılıp kapanır
                elif calisma_modu_val and int(calisma_modu_val) == 3:
                    durus_sebep = "serbest_kuyu_modunda_durmus_manuel_veya_ariza"
                    durus_normal = False
                durus_degerlendirme = {
                    "sebep": durus_sebep,
                    "normal_durus_mu": durus_normal,
                    "mod_adi": calisma_modu.get("mod_adi"),
                    "aciklama_tr": {
                        "depo_dolu_normal_durus": (
                            "Pompa Depo Doldurma modunda — hedef seviyeye ulaştığı için durmuş. "
                            "Bu NORMAL bir durum, kritik değil. Verim analizi için log'dan "
                            "son çalışma dönemi ortalaması alınır."
                        ),
                        "depo_doldurma_modunda_durmus_ama_seviye_dusuk": (
                            "Pompa Depo Doldurma modunda durmuş ama depo seviyesi hedefe ulaşmamış. "
                            "Olası: manuel kapatma, alarm, hedef haberleşme sorunu. Kontrol edilmeli."
                        ),
                        "hidrofor_modu_basinc_hedefinde_durmus_olabilir": (
                            "Hidrofor modunda pompa basınç hedefine ulaşınca durur, tüketim artınca tekrar başlar. NORMAL."
                        ),
                        "serbest_kuyu_modunda_durmus_manuel_veya_ariza": (
                            "Serbest Kuyu modunda pompa durmuş — normalde sürekli çalışmalıydı. "
                            "Manuel kapatma veya arıza olabilir."
                        ),
                        "belirsiz": (
                            "Çalışma modu tag'leri okunamadığı için durma sebebi belirlenemedi."
                        ),
                    }.get(durus_sebep, ""),
                }

            # Pompa durmuşsa log'dan son calisma donemi ortalamasi
            son_calisma: dict[str, Any] | None = None
            if not running:
                son_calisma = _fetch_last_running_avg(cfg, nid)

            # Canli degerler — ToplamHm MERKEZ (raw _tagoku degeri)
            head_m_raw = _num("ToplamHm")
            # HAT BASINCI oncelik sirasi: HatBasincSensoru > BasincSensoru2 > BasincSensoru
            #   - BasincSensoru  = pompa cikis basinci (pompa tarafi)
            #   - BasincSensoru2 / HatBasincSensoru = hat basinci (sebeke tarafi)
            hat_basinc_bar = _num("HatBasincSensoru") or _num("BasincSensoru2")
            pompa_cikis_bar = _num("BasincSensoru")
            basinc_bar_used = hat_basinc_bar if hat_basinc_bar is not None else pompa_cikis_bar
            basinc_kaynak = (
                "HatBasincSensoru" if _num("HatBasincSensoru") is not None else
                "BasincSensoru2" if _num("BasincSensoru2") is not None else
                "BasincSensoru (pompa cikis — hat DEGIL, yaklaşık)"
            ) if basinc_bar_used is not None else None

            su_seviye_tag = _num("SuSeviye") or _num("DinamikSeviye") or _num("dinamikseviye")
            statik_sev = _num("StatikSeviye") or _num("StatikSuSeviye")
            xd_basma = _num("XD_BasmaYukseklik")         # kuyu-depo kot farki (m)
            xd_cikisdepo = _num("XD_CikisDepoYukseklik") # cikis depo yuksekligi (m)
            kuyukot = _num("kuyukot")
            depokot = _num("depokot")

            head_m_computed: float | None = None
            head_m_formula: str | None = None
            head_m_components: dict[str, Any] = {}
            if basinc_bar_used is not None:
                # H_pressure = line pressure in metre su sütunu
                h_pressure = basinc_bar_used * 10.197
                head_m_components["hat_basinc_m"] = round(h_pressure, 2)
                head_m_components["basinc_kaynak"] = basinc_kaynak

                comp = h_pressure
                parts = [f"{basinc_kaynak}({basinc_bar_used})×10.197={round(h_pressure,2)}"]

                # Dinamik kuyu seviyesi (pompa emme tarafi statik H)
                if su_seviye_tag is not None:
                    comp += su_seviye_tag
                    parts.append(f"+SuSeviye({su_seviye_tag})")
                    head_m_components["dinamik_su_seviye_m"] = su_seviye_tag

                # Kuyu-depo kot farki (static H)
                if xd_basma is not None:
                    comp += xd_basma
                    parts.append(f"+XD_BasmaYukseklik({xd_basma})")
                    head_m_components["kuyu_depo_kot_farki_m"] = xd_basma
                elif kuyukot is not None and depokot is not None:
                    kot_diff = depokot - kuyukot
                    comp += kot_diff
                    parts.append(f"+(depokot-kuyukot)({kot_diff})")
                    head_m_components["kot_farki_m"] = kot_diff

                head_m_computed = round(comp, 2)
                head_m_formula = " ".join(parts) + f" = {head_m_computed}"
                head_m_components["formul"] = head_m_formula
                head_m_components["toplam_m"] = head_m_computed

            # Enstruman/Cekvalf tanisi: pompa cikis vs hat basinc farki
            cekvalf_tani: dict[str, Any] | None = None
            if pompa_cikis_bar is not None and hat_basinc_bar is not None:
                fark_bar = round(pompa_cikis_bar - hat_basinc_bar, 3)
                fark_m = round(fark_bar * 10.197, 2)
                # Beklenen: pompa cikis ≥ hat (vana/borulardaki kayip).
                # Fark <0 ise olcum hatasi. Fark cok buyukse cekvalf/borulama sorunu.
                if fark_bar < -0.2:
                    durum = "olcum_hatasi"
                    aciklama = (
                        f"BasincSensoru ({pompa_cikis_bar}) < HatBasincSensoru ({hat_basinc_bar}). "
                        "Pompa cikis basinci hat basincindan DUSUK olamaz (geri akis olmadikca). "
                        "Sensor kalibrasyon hatasi veya basinc etiketleri tersine takilmis olabilir."
                    )
                elif fark_bar > 1.5:
                    durum = "cekvalf_veya_borulama_sorunu"
                    aciklama = (
                        f"Pompa cikis basinci hat basincindan {fark_bar} bar (~{fark_m} m) fazla. "
                        "Bu NORMALDEN yuksek — pompa ile hat arasinda asiri direnç var. "
                        "Olasi sebepler: CEKVALF kapaliya yakin ya da sikilmiş, izolasyon vanasi "
                        "kismen kapali, manifold birikimi, ters yonde tik-tak yapan cekvalf."
                    )
                elif fark_bar < 0.3:
                    durum = "cok_yakin_sifir"
                    aciklama = (
                        f"Pompa cikis ve hat basinci cok yakin ({fark_bar} bar). "
                        "Beklenti: pompa cikis, hat + vana/boru kaybi kadar fazla olmali. "
                        "Debi duserse cekvalf sizinti olabilir (geri akis)."
                    )
                else:
                    durum = "normal"
                    aciklama = f"Pompa-hat fark {fark_bar} bar — normal aralikta."
                cekvalf_tani = {
                    "pompa_cikis_bar": pompa_cikis_bar,
                    "hat_basinc_bar": hat_basinc_bar,
                    "fark_bar": fark_bar,
                    "fark_m": fark_m,
                    "durum": durum,
                    "aciklama_tr": aciklama,
                }

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

            # Pompa durduysa son_calisma ortalamalarini kullan (eger mevcutsa)
            used_source = "canli"
            if not running and son_calisma and not son_calisma.get("error"):
                sc_flow = son_calisma.get("ortalama_Debimetre")
                sc_head = son_calisma.get("ortalama_ToplamHm")
                sc_power = son_calisma.get("ortalama_An_Guc")
                if sc_flow and sc_head:
                    flow = float(sc_flow)
                    head_m_raw = float(sc_head)
                    head_m = head_m_raw
                    if sc_power:
                        power_kw = float(sc_power)
                    used_source = "log_son_calisma_ortalama"

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

            # Hidrolik ag / tesisat parametreleri (XV_*) — verim analizi icin kritik
            xv_boru_l = _num("XV_BoruUzunluk")       # m
            xv_boru_d = _num("XV_BoruIcCap")         # mm
            xv_pipe_rough = _num("XV_PipeRoughness") # mm (veya farkli birim olabilir)
            xv_n_surt = _num("XV_Nsurtunme")         # 0-1
            xv_n_motor = _num("XV_Nmotor")           # %
            xv_kablo_kayip = _num("XV_KabloKayip")   # %
            xv_surucu_kayip = _num("XV_SurucuKayip") # %
            hidrolik_ag_params: dict[str, Any] = {
                "boru_uzunluk_m": xv_boru_l,
                "boru_ic_cap_mm": xv_boru_d,
                "boru_purislulug_mm": xv_pipe_rough,
                "surtunme_verim_faktor": xv_n_surt,
                "motor_verim_pct": xv_n_motor,
                "kablo_kayip_pct": xv_kablo_kayip,
                "surucu_kayip_pct": xv_surucu_kayip,
            }
            # None alanları temizle
            hidrolik_ag_params = {k: v for k, v in hidrolik_ag_params.items() if v is not None}

            # Sürtünme kaybı basit tahmin (Darcy-Weisbach yaklaşıkı, f≈0.02 varsayım)
            # Daha iyi için LLM skill'i (analysis/hydraulic-network-analysis.md) kullanmalı
            friction_loss_est: float | None = None
            if flow and xv_boru_l and xv_boru_d and xv_boru_d > 0:
                # v = Q / A, Q(m3/s) = flow/3600, A = π/4 · (D/1000)²
                import math as _m
                A = _m.pi / 4.0 * (xv_boru_d / 1000.0) ** 2
                v = (flow / 3600.0) / A if A > 0 else 0
                # f ≈ 0.02 (pürüzlü boru varsayım), g=9.81
                friction_loss_est = round(0.02 * (xv_boru_l / (xv_boru_d / 1000.0)) * (v * v) / (2 * 9.81), 2)

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
                # Severity mode-aware: normal durus ise INFO, ariza suphesi ise HIGH
                _sev = "INFO" if (durus_degerlendirme and durus_degerlendirme.get("normal_durus_mu")) else "MEDIUM"
                _detail = (
                    durus_degerlendirme.get("aciklama_tr")
                    if durus_degerlendirme else
                    "Pompa calismiyor — canli Hm ve Debi GUVENILMEZ."
                )
                checks.append({
                    "severity": _sev,
                    "issue": "pompa_durmus",
                    "detail": _detail + " Log son calisma ortalamasi kullaniliyor.",
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
                "hidrolik_ag": hidrolik_ag_params if hidrolik_ag_params else None,
                "tahmini_surtunme_kaybi_m": friction_loss_est,
                "son_calisma": son_calisma,
                "veri_kaynagi": used_source,  # "canli" veya "log_son_calisma_ortalama"
                "calisma_modu": calisma_modu if calisma_modu else None,
                "durus_degerlendirme": durus_degerlendirme,
                "head_m_components": head_m_components if head_m_components else None,
                "pompa_cikis_vs_hat_basinc": cekvalf_tani,
                "mevcut_pompa_uygunluk": _evaluate_installed_fit(
                    installed_pump=installed_pump,
                    live_flow=flow,
                    live_head=head_m,
                    live_power=power_kw,
                    pump_output_freq=pump_output_freq,
                ),
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
                "hazir": bool(
                    flow and head_m
                    # Pompa calisiyorsa VEYA log ortalamasi alinabildiyse kabul
                    and (running or used_source == "log_son_calisma_ortalama")
                    and not any(c["severity"] == "HIGH" for c in checks if c.get("issue") != "pompa_durmus")
                ),
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
                fit = result.get("mevcut_pompa_uygunluk") or {}
                karar = fit.get("karar", "belirsiz")

                # Veri kaynağı log ortalaması ise uyarı
                veri_uyarisi = ""
                if used_source == "log_son_calisma_ortalama" and son_calisma:
                    sct = son_calisma.get("son_calisma_bitim_zamani", "?")
                    veri_uyarisi = (
                        f" | Q/H/P değerleri CANLI DEĞİL — pompa şu an durmuş. "
                        f"Son çalışma dönemi ({sct}, 60 dk pencere) ortalamaları kullanıldı. "
                        "Kullanıcıya bu bilgiyi AYIKLA."
                    )

                # Mevcut pompa uygun → search_pumps cagirma
                if karar in ("mevcut_uygun", "mevcut_uygun_esneklik"):
                    result["next_action"] = None
                    if karar == "mevcut_uygun_esneklik":
                        result["hint_tr"] = (
                            "MEVCUT POMPA UYGUN — KADEME ESNEKLİK AVANTAJI VAR. "
                            "Kullanıcıya: mevcut pompa fazla kademeli (H buffer'ı var), "
                            "VFD ile kısılmış, şu anki duty için verimli. "
                            "H ihtiyacı yükselirse (kuyu seviyesi, boru yaşlanma) hazır. "
                            "get_skill('korubin-scada','analysis/pump-sizing-philosophy.md') "
                            "oku ve 'Seçenek A (mevcut) + VFD ince ayar' varsayılan olarak sun. "
                            "Az kademeli alternatifi SADECE kullanıcı esneklik istemiyorsa, "
                            "H risk uyarısıyla SEÇENEK olarak sun — dayatma değil. "
                            "korucaps_search_pumps ÇAĞIRMA (gereksiz)."
                            + ip_summary + veri_uyarisi
                        )
                    else:
                        result["hint_tr"] = (
                            "MEVCUT POMPA UYGUN (BEP yakın) — yeni pompa önerme. "
                            "VFD frekans ince ayarı, boru/vana kontrolü, bakım öner. "
                            "korucaps_search_pumps ÇAĞIRMA (gereksiz)."
                            + ip_summary + veri_uyarisi
                        )
                elif karar == "mevcut_dusuk_verim":
                    result["next_action"] = (
                        f"korucaps_search_pumps(flow_m3h={flow}, head_m={head_m}, "
                        f"application='{kc_app}', sub_application='{kc_sub}', vfd={vfd_param})"
                    )
                    result["hint_tr"] = (
                        "Mevcut pompa VFD ile çok kısılmış, verim düşük. "
                        "get_skill('korubin-scada','analysis/pump-sizing-philosophy.md') oku. "
                        "AYNI SERİDEN az kademeli alternatifi H-risk uyarısıyla SEÇENEK olarak "
                        "sun (örn. SP 215-3 → SP 215-2: max H ~55m sınırı). "
                        "Farklı seri (SP 160 gibi) önerme. "
                        "Kullanıcıya A (mevcut+VFD) / B (az kademeli) karşılaştırması sun — "
                        "dayatma değil, seçim."
                        + ip_summary + veri_uyarisi
                    )
                else:
                    # mevcut_bep_disi, uygunsuz_boyutlu, belirsiz
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
                        "Tutarlı. next_action'ı çağır."
                        + _imp + ip_summary
                        + " | Sonuçları mevcut pompa ile karşılaştır. Belirgin enerji kazancı "
                        "VE tesis koşulları stabil DEĞİLSE mevcudu öner. "
                        "get_skill('korubin-scada','analysis/pump-sizing-philosophy.md') oku."
                        + veri_uyarisi
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
            """Pompa seçimi + VERİM ANALİZİ tek adımda.
Response:
  canli_olcumler (ToplamHm, Debimetre, An_Guc, pompa_cikis_frekans)
  mevcut_pompa (marka, model, nominal Q/H, sürücü, annexa iç hesapta)
  hidrolik_ag (XV_BoruUzunluk, XV_BoruIcCap, XV_PipeRoughness, XV_Nmotor, XV_KabloKayip, XV_SurucuKayip)
  tahmini_surtunme_kaybi_m (Darcy-Weisbach yaklaşık)
  ui_hesaplanmis (hidrolik ve sistem verim)
  next_action (hazır=true ise korucaps_search_pumps komutu)

VERİM ANALİZİ için ek adım: get_skill('korubin-scada','analysis/hydraulic-network-analysis.md').
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
annexa: katalog-saha sapma toleransı (1=nominal, <1=saha daha düşük — yaşlanma DEĞİL tolerans).
  0 → pump_eff'ten okunur, yoksa 1.0. H_pompa = H_katalog × annexa.
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
                    "annexa = katalog-saha sapma toleransıdır (yaşlanma katsayısı DEĞİL). "
                    "Kullanıcıya SADECE ölçüm-etiket sapması sorulduğunda veya frekans/pompa değişim hesabında sun. "
                    "'pompa %X yaşlanmış' yorumu YASAK — aşınma için core-rules 3-kanıt kuralı gerekir."
                )
            return result

        @mcp.tool(name=tool)
        def get_installed_pump_info(nodeId: int) -> str:
            """Node'a takılı mevcut pompa bilgisi.
Kaynak önceliği: pump_eff (marka, model, annexa katalog-saha sapma toleransı, montage) >
node_param np_* (np_PompaModel, np_PompaMarka, np_PompaDebi, np_PompaHm, np_PompaGuc...).
'kendi pompası ne', 'mevcut pompa ne', 'takılı pompa' sorularında kullan.
annexa = katalog ile saha performansı arasındaki NORMAL TOLERANS (yaşlanma DEĞİL).
Frekans projeksiyonu/pompa değişim hesabında: H_beklenen = H_katalog × annexa.
Aşınma kararı için core-rules Bölüm 5'teki 3-kanıt kuralı zorunludur."""
            return guard(tool, _get_installed_pump_info_impl)(nodeId)

        # --- analyze_hydraulic_network ---
        # Akışkanlar mekaniği katmanı: ToplamHm'i statik + sürtünme + yerel kayıp
        # bileşenlerine ayırır. Darcy-Weisbach + Colebrook-White iteratif, korubin
        # calc.helper.js ile bire bir uyumlu (g=9.7905, ν(T) tablosu, k=nm→m).
        tool = prefixed_name(prefix, "analyze_hydraulic_network")

        def _analyze_hydraulic_network_impl(nodeId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            nid = int(nodeId)

            # XV_* install sabitleri + canlı ölçüm tag'leri
            tag_names = [
                # Install sabitleri
                "XV_BoruIcCap", "XV_BoruUzunluk", "XV_PipeRoughness",
                "XV_Nsurtunme", "XV_Nmotor", "XV_KabloKayip", "XV_SurucuKayip",
                # Canlı ölçüm
                "ToplamHm", "Debimetre", "Debimetre1", "DebimetreLtSn",
                "BasincSensoru", "BasincSensoru2",
                "SuSeviye", "StatikSeviye", "StatikSuSeviye",
                "SuSicaklik",
                "An_Guc", "P1_Guc",
                "Pompa1StartStopDurumu", "PompaStartStopDurumu", "PompaCalismaDurumu",
            ]
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, nName, nView FROM node WHERE id = %s",
                        (nid,),
                    )
                    node = cur.fetchone()
                    if not node:
                        return {"error": f"Node {nid} bulunamadı"}
                    ph = ",".join(["%s"] * len(tag_names))
                    cur.execute(
                        f"SELECT tagName, tagValue FROM _tagoku "
                        f"WHERE devId = %s AND tagName IN ({ph})",
                        tuple([nid] + tag_names),
                    )
                    rows = {r["tagName"]: r["tagValue"] for r in cur.fetchall()}
                    # node_param: montaj derinliği (kuyu pompaları için well-lift hesabı)
                    try:
                        cur.execute(
                            "SELECT pKey, pVal FROM node_param "
                            "WHERE nodeId = %s AND pKey IN ('nPMontaj','np_BasmaDerinlik')",
                            (nid,),
                        )
                        np_install = {r["pKey"]: r["pVal"] for r in cur.fetchall()}
                    except Exception:
                        np_install = {}

            def _f(name: str) -> float | None:
                v = rows.get(name)
                if v is None:
                    return None
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return None

            # Install sabitleri
            d_mm = _f("XV_BoruIcCap")
            L_m = _f("XV_BoruUzunluk")
            rough_nm = _f("XV_PipeRoughness")
            exloss_m = _f("XV_Nsurtunme") or 0.0  # yerel kayıp (m)
            motor_eff_pct = _f("XV_Nmotor")
            cable_loss_pct = _f("XV_KabloKayip") or 0.0
            vfd_loss_pct = _f("XV_SurucuKayip") or 0.0

            # Canlı ölçüm
            hm = _f("ToplamHm")
            flow_m3h = _f("Debimetre") or _f("Debimetre1")
            if flow_m3h is None:
                lps = _f("DebimetreLtSn")
                if lps is not None:
                    flow_m3h = lps * 3.6
            pr_bar = _f("BasincSensoru")
            if pr_bar is None or pr_bar <= 0:
                pr_bar = _f("BasincSensoru2")
            su_seviye_dyn = _f("SuSeviye")
            su_seviye_static = _f("StatikSuSeviye") or _f("StatikSeviye")
            su_seviye = su_seviye_dyn if su_seviye_dyn is not None else su_seviye_static
            t_c = _f("SuSicaklik") or 15.0  # varsayılan 15°C (Türkiye yeraltı ort.)
            an_guc = _f("An_Guc") or _f("P1_Guc")

            # Kuyu pompası well-lift: pompa montaj derinliği varsa
            # "pompa kaldırma yüksekliği" = max(0, montaj_derinligi − statik_su_seviyesi)
            def _npf(k: str) -> float | None:
                v = np_install.get(k)
                if v is None:
                    return None
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return None
            mount_depth_m = _npf("nPMontaj") or _npf("np_BasmaDerinlik")
            nv_lower = str(node.get("nView") or "").lower()
            is_well_pump = "kuyu" in nv_lower or "well" in nv_lower
            well_lift_m = None
            if is_well_pump and mount_depth_m and mount_depth_m > 0:
                # Statik su seviyesi (yerden itibaren suyun üst yüzeyi)
                ssl = su_seviye_static if su_seviye_static is not None else su_seviye_dyn
                if ssl is not None and ssl >= 0:
                    well_lift_m = max(0.0, float(mount_depth_m) - float(ssl))
                else:
                    # Statik seviye yoksa pompa derinliği tek başına alt sınır
                    well_lift_m = float(mount_depth_m)

            running = any(
                (_f(k) or 0) > 0.5
                for k in ("Pompa1StartStopDurumu", "PompaStartStopDurumu", "PompaCalismaDurumu")
            )

            missing: list[str] = []
            if d_mm is None or d_mm <= 0:
                missing.append("XV_BoruIcCap (boru iç çapı mm)")
            if L_m is None or L_m <= 0:
                missing.append("XV_BoruUzunluk (boru uzunluğu m)")
            if rough_nm is None:
                missing.append("XV_PipeRoughness (pürüzlülük nm)")
            if flow_m3h is None or flow_m3h <= 0:
                missing.append("Debimetre (canlı)")
            if hm is None or hm <= 0:
                missing.append("ToplamHm (canlı)")

            if missing:
                return {
                    "node_id": nid,
                    "node_name": node.get("nName"),
                    "nView": node.get("nView"),
                    "running": running,
                    "hata_tr": "Hidrolik ayrıştırma için eksik veri",
                    "eksik_taglar": missing,
                    "oneri_tr": (
                        "Panel → pompaverim sayfasından XV_* sabitleri girilmeli. "
                        "XV_BoruIcCap (mm), XV_BoruUzunluk (m), XV_PipeRoughness (UI'da mm, "
                        "DB'de nanometre olarak saklanır: 0.1 mm = 100000). "
                        "Veri girildiğinde bu araç tekrar çalıştırılabilir."
                    ),
                }

            if not running:
                return {
                    "node_id": nid,
                    "node_name": node.get("nName"),
                    "nView": node.get("nView"),
                    "running": False,
                    "hata_tr": (
                        "Pompa DURUYOR — canlı Debi ve ToplamHm dinamik değerleri güvenilmez. "
                        "Sürtünme kaybı akışa bağlıdır, pompa kapalıyken anlamsızdır."
                    ),
                    "oneri_tr": (
                        "get_node_log_data ile son çalışma dönemini bul, o zaman aralığında "
                        "Debimetre + ToplamHm ortalaması al, sonra bu araç çalıştırılabilir."
                    ),
                }

            # --- Hidrolik hesaplar (korubin calc.helper.js ile bire bir uyumlu) ---
            import math

            d_m = float(d_mm) / 1000.0              # mm → m
            # XV_PipeRoughness: DB'de nm, UI factor="0.000001" ile mm gösterir, calc'ta m (÷1e9)
            eps_m = float(rough_nm) / 1.0e9
            eps_mm_display = float(rough_nm) / 1.0e6  # bilgilendirme
            area_m2 = math.pi * d_m * d_m / 4.0
            q_m3s = float(flow_m3h) / 3600.0
            velocity = q_m3s / area_m2              # m/s

            # Kinematik viskozite — calc.helper.js tablosu (cSt × 1e-6 = m²/s)
            vis_table = [
                (0, 1.791468), (5, 1.517938), (10, 1.306096), (15, 1.138451),
                (20, 1.003317), (25, 0.892654), (30, 0.800782), (35, 0.723598),
                (40, 0.658075), (45, 0.601942), (50, 0.553461), (55, 0.511289),
                (60, 0.474368), (65, 0.441859), (70, 0.413086), (75, 0.387498),
                (80, 0.364647), (85, 0.344158), (90, 0.325721), (95, 0.309076),
                (100, 0.294002),
            ]
            t_use = max(0.1, min(99.9, float(t_c)))
            for i in range(1, len(vis_table)):
                if t_use < vis_table[i][0]:
                    t1, v1 = vis_table[i - 1]
                    t2, v2 = vis_table[i]
                    v_interp = ((t2 - t_use) * (v1 - v2)) / (t2 - t1) + v2
                    break
            else:
                v_interp = vis_table[-1][1]
            nu = v_interp / 1.0e6  # m²/s

            reynolds = velocity * d_m / nu
            if reynolds < 2300:
                regime = "laminer"
            elif reynolds < 4000:
                regime = "türbülans-laminer arası (geçiş)"
            else:
                regime = "türbülanslı"

            # Colebrook-White iteratif (calc.helper.js ile aynı algoritma)
            # 1/√λ = -2·log10( 2.51/(Re·√λ) + ε/(d·3.72) )
            lambda_f = 0.08
            if reynolds > 0 and d_m > 0:
                for _ in range(2000):  # emniyet sınırı
                    lsqrt = math.sqrt(lambda_f)
                    left = 1.0 / lsqrt
                    inside = 2.51 / (reynolds * lsqrt) + eps_m / d_m / 3.72
                    if inside <= 0:
                        break
                    right = -2.0 * math.log10(inside)
                    if right - left < 0:
                        break
                    lambda_f -= 0.0005
                    if lambda_f < 0.005:
                        lambda_f = 0.005
                        break

            # Sürtünme yükü (Türkiye pratiği g=9.7905 — calc.helper.js ile birebir)
            G_LOCAL = 9.7905
            if d_m > 0 and velocity > 0:
                h_friction_pipe = lambda_f * L_m * velocity * velocity / (d_m * 2.0 * G_LOCAL)
            else:
                h_friction_pipe = 0.0

            h_local = exloss_m
            h_friction_total = h_friction_pipe + h_local

            # ToplamHm ayrıştırması
            h_static_pressure = float(pr_bar) * 10.197162 if pr_bar else 0.0
            h_static_well = float(su_seviye) if su_seviye is not None else 0.0
            h_well_lift = float(well_lift_m) if well_lift_m is not None else 0.0
            h_static_total = h_static_pressure + h_static_well + h_well_lift
            hm_reconstructed = h_static_total + h_friction_total
            hm_residual = float(hm) - hm_reconstructed

            def _pct(x: float) -> float:
                return round((x / float(hm) * 100.0), 2) if hm > 0 else 0.0

            # Verim ağacı (korubin calc formülleri)
            eff_power_kw = None
            eta_hydraulic_pct = None
            eta_system_pct = None
            if an_guc is not None and motor_eff_pct is not None and motor_eff_pct > 0:
                eff_power_kw = float(an_guc) * (
                    1.0 - cable_loss_pct / 100.0 - vfd_loss_pct / 100.0
                )
                if eff_power_kw > 0 and flow_m3h > 0:
                    # η_hid = (Hm × Q) / (367.2 × P × me/10000)  ≡  Hm×Q / 367 / P_shaft_kW × 100
                    denom = 367.2 * eff_power_kw * motor_eff_pct / 10000.0
                    if denom > 0:
                        eta_hydraulic_pct = round((float(hm) * float(flow_m3h)) / denom, 2)
                        eta_system_pct = round(eta_hydraulic_pct * motor_eff_pct / 100.0, 2)

            # Tanı
            friction_share = _pct(h_friction_total)
            static_share = _pct(h_static_total)

            if friction_share < 10.0:
                diagnosis = (
                    f"Sürtünme payı çok düşük (%{friction_share:.1f}). "
                    "Toplam Hm büyük ölçüde STATİK bileşenden geliyor "
                    "(kuyu dinamik seviyesi + basma yüksekliği). "
                    "Boru çapı yeterli; boru değiştirme önerilmez."
                )
                pipe_upgrade_recommended = False
                upgrade_reason = "Statik baskın — boru büyütme kazanç sağlamaz"
            elif friction_share < 25.0:
                diagnosis = (
                    f"Sürtünme payı dengeli (%{friction_share:.1f}). "
                    "Boru büyütme yalnızca çok yüksek enerji fiyatında marjinal olur."
                )
                pipe_upgrade_recommended = False
                upgrade_reason = "Dengeli — senaryo çalıştırılabilir ama beklenti düşük"
            elif friction_share < 40.0:
                diagnosis = (
                    f"Sürtünme payı YÜKSEK (%{friction_share:.1f}). "
                    "Boru bir kademe büyük (örn. DN150→DN200) senaryosu çalıştırılmalı."
                )
                pipe_upgrade_recommended = True
                upgrade_reason = "Sürtünme yüksek — boru büyütme senaryosu değerlendirilmeli"
            else:
                diagnosis = (
                    f"Sürtünme payı HAKİM (%{friction_share:.1f}). "
                    "Boru çapı ciddi şekilde yetersiz — acil yatırım analizi önerilir."
                )
                pipe_upgrade_recommended = True
                upgrade_reason = "Sürtünme hakim — acil senaryo"

            # Kalıntı (unaccounted) büyükse uyarı
            residual_warn = None
            if abs(hm_residual) > max(2.0, 0.08 * float(hm)):
                residual_warn = (
                    f"ToplamHm ayrıştırma kalıntısı {round(hm_residual, 2)} m "
                    f"(%{_pct(abs(hm_residual))}). "
                    "Basınç/seviye/sıcaklık ölçümü veya XV_* girişlerinde hata olabilir."
                )

            result: dict[str, Any] = {
                "node_id": nid,
                "node_name": node.get("nName"),
                "nView": node.get("nView"),
                "running": running,
                "input_params": {
                    "pipe_inner_diameter_mm": d_mm,
                    "pipe_length_m": L_m,
                    "pipe_roughness_mm": round(eps_mm_display, 6),
                    "pipe_roughness_m": eps_m,
                    "local_loss_m": exloss_m,
                    "motor_efficiency_pct": motor_eff_pct,
                    "cable_loss_pct": cable_loss_pct,
                    "vfd_loss_pct": vfd_loss_pct,
                    "flow_m3h": flow_m3h,
                    "total_head_m": hm,
                    "pressure_bar": pr_bar,
                    "dynamic_well_level_m": su_seviye,
                    "water_temperature_c": t_c,
                    "mains_power_an_guc_kw": an_guc,
                    "pump_mount_depth_m": mount_depth_m,
                    "static_water_level_m": su_seviye_static,
                    "is_well_pump": is_well_pump,
                },
                "flow_dynamics": {
                    "velocity_m_s": round(velocity, 3),
                    "reynolds": round(reynolds, 0),
                    "regime": regime,
                    "darcy_friction_factor": round(lambda_f, 5),
                    "relative_roughness": round(eps_m / d_m, 8) if d_m > 0 else None,
                    "kinematic_viscosity_m2_s": nu,
                },
                "head_breakdown_m": {
                    "total_hm": round(float(hm), 3),
                    "static_pressure_component": round(h_static_pressure, 3),
                    "static_well_level_component": round(h_static_well, 3),
                    "well_lift_component": round(h_well_lift, 3),
                    "static_total": round(h_static_total, 3),
                    "pipe_friction_darcy_weisbach": round(h_friction_pipe, 3),
                    "local_losses_xv_nsurtunme": round(h_local, 3),
                    "friction_total": round(h_friction_total, 3),
                    "reconstructed_total": round(hm_reconstructed, 3),
                    "residual_unaccounted": round(hm_residual, 3),
                },
                "share_pct": {
                    "static_share_pct": static_share,
                    "well_lift_pct": _pct(h_well_lift),
                    "static_pressure_pct": _pct(h_static_pressure),
                    "dynamic_well_level_pct": _pct(h_static_well),
                    "friction_share_pct": friction_share,
                    "pipe_friction_pct": _pct(h_friction_pipe),
                    "local_loss_pct": _pct(h_local),
                    "residual_pct": _pct(abs(hm_residual)),
                },
                "efficiency_tree": {
                    "mains_power_kw": an_guc,
                    "effective_power_after_losses_kw": (
                        round(eff_power_kw, 3) if eff_power_kw else None
                    ),
                    "losses": {
                        "cable_loss_pct": cable_loss_pct,
                        "vfd_loss_pct": vfd_loss_pct,
                        "motor_efficiency_pct": motor_eff_pct,
                    },
                    "eta_hydraulic_pump_pct": eta_hydraulic_pct,
                    "eta_system_wire_to_water_pct": eta_system_pct,
                    "formula_tr": (
                        "guc_eff = An_Guc × (1 − XV_SurucuKayip/100 − XV_KabloKayip/100) ; "
                        "η_hid = Hm×Q / (367.2 × guc_eff × XV_Nmotor/10000) ; "
                        "η_sys = η_hid × XV_Nmotor/100"
                    ),
                },
                "diagnosis_tr": diagnosis,
                "pipe_upgrade": {
                    "recommended": pipe_upgrade_recommended,
                    "reason_tr": upgrade_reason,
                    "next_tool_tr": (
                        f"analyze_pipe_upgrade_economics(nodeId={nid}, "
                        "alternative_inner_diameter_mm=<yeni_cap>)"
                    ) if pipe_upgrade_recommended else None,
                },
                "warnings_tr": [w for w in [residual_warn] if w],
                "hint_tr": (
                    "ToplamHm'i statik/sürtünme/yerel/kalıntı bileşenlerine AYRIŞTIRILMIŞ halde "
                    "kullanıcıya göster. friction_share_pct < %10 ise boru önerisi YAPMA. "
                    ">%25 ise analyze_pipe_upgrade_economics ile senaryo çalıştır. "
                    "annexa iç hesap içindir; 'yaşlanmış' yorumu yasak (bkz. core-rules §5)."
                ),
            }
            return result

        @mcp.tool(name=tool)
        def analyze_hydraulic_network(nodeId: int) -> str:
            """Pompa + boru hidrolik şebeke ayrıştırma (akışkanlar mekaniği uzman katmanı).

ToplamHm'i dört bileşene ayırır:
  H_statik_basınç (BasincSensoru × 10.197)
  H_statik_kuyu (SuSeviye dinamik)
  H_sürtünme_boru (Darcy-Weisbach + Colebrook-White)
  H_yerel (XV_Nsurtunme — vana/dirsek)

Kullanılan sabitler (XV_* install constants):
  XV_BoruIcCap (mm), XV_BoruUzunluk (m), XV_PipeRoughness (nm),
  XV_Nsurtunme (m), XV_Nmotor (%), XV_KabloKayip (%), XV_SurucuKayip (%)

Çıktı: bileşen payları, Reynolds, Darcy faktörü, verim ağacı, tanı,
boru büyütme önerisi (friction_share>%25 ise analyze_pipe_upgrade_economics'e yönlendirir).

Use: "pompa verim analizi", "neden çok enerji çekiyor", "sürtünme ne kadar",
"boru çapı yeterli mi", "iletim kayıpları". XV_* tag'leri yoksa açıkça bildirir, fail etmez."""
            return guard(tool, _analyze_hydraulic_network_impl)(nodeId)

        # --- analyze_pipe_upgrade_economics ---
        # Alternatif boru çapı senaryosu: yeni sürtünme, yıllık kWh tasarrufu,
        # TL tasarrufu (XM_Tn* tarifelerinden), basit geri ödeme, 20 yıllık NPV.
        tool = prefixed_name(prefix, "analyze_pipe_upgrade_economics")

        def _analyze_pipe_upgrade_economics_impl(
            nodeId: int,
            alternative_inner_diameter_mm: float,
            pipe_cost_tl_per_meter: float = 0.0,
            installation_factor: float = 1.3,
            daily_operating_hours: float = 0.0,
            design_life_years: int = 20,
            discount_rate_pct: float = 10.0,
        ) -> Any:
            """
            Alternatif boru çapı senaryosu ekonomik analizi.
            
            pipe_cost_tl_per_meter=0 → sadece kWh ve TL tasarrufu raporlanır (NPV yok)
            daily_operating_hours=0 → XM_Tn* tariflerinden hesaplanır (yoksa 12h varsayılır)
            """
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")

            # Mevcut hidrolik durumu al (aynı alt fonksiyonu çağır)
            current = _analyze_hydraulic_network_impl(nodeId)
            if isinstance(current, dict) and current.get("hata_tr"):
                return {
                    "node_id": int(nodeId),
                    "hata_tr": "Mevcut hidrolik durum alınamıyor — önce bu düzeltilmeli",
                    "neden": current.get("hata_tr"),
                    "detay": current,
                }

            nid = int(nodeId)
            inp = current["input_params"]
            flow_m3h = float(inp["flow_m3h"])
            hm_current = float(inp["total_head_m"])
            d_old_mm = float(inp["pipe_inner_diameter_mm"])
            L_m = float(inp["pipe_length_m"])
            eps_m = float(inp["pipe_roughness_m"])
            exloss_m = float(inp["local_loss_m"])
            t_c = float(inp["water_temperature_c"])
            an_guc = float(inp.get("mains_power_an_guc_kw") or 0)
            motor_eff = float(inp.get("motor_efficiency_pct") or 0)
            cable_loss = float(inp.get("cable_loss_pct") or 0)
            vfd_loss = float(inp.get("vfd_loss_pct") or 0)

            eta_system = current["efficiency_tree"].get("eta_system_wire_to_water_pct")
            h_friction_current = float(current["head_breakdown_m"]["friction_total"])

            d_new_mm = float(alternative_inner_diameter_mm)
            if d_new_mm <= 0:
                return {"hata_tr": "alternative_inner_diameter_mm > 0 olmalı"}

            # Yeni boru için hidrolik tekrar hesap
            import math
            d_new_m = d_new_mm / 1000.0
            area_new = math.pi * d_new_m * d_new_m / 4.0
            velocity_new = (flow_m3h / 3600.0) / area_new

            # Aynı viskozite interpolasyonu
            vis_table = [
                (0, 1.791468), (5, 1.517938), (10, 1.306096), (15, 1.138451),
                (20, 1.003317), (25, 0.892654), (30, 0.800782), (35, 0.723598),
                (40, 0.658075), (45, 0.601942), (50, 0.553461), (55, 0.511289),
                (60, 0.474368), (65, 0.441859), (70, 0.413086), (75, 0.387498),
                (80, 0.364647), (85, 0.344158), (90, 0.325721), (95, 0.309076),
                (100, 0.294002),
            ]
            t_use = max(0.1, min(99.9, t_c))
            v_interp = vis_table[-1][1]
            for i in range(1, len(vis_table)):
                if t_use < vis_table[i][0]:
                    t1, v1 = vis_table[i - 1]
                    t2, v2 = vis_table[i]
                    v_interp = ((t2 - t_use) * (v1 - v2)) / (t2 - t1) + v2
                    break
            nu = v_interp / 1.0e6

            re_new = velocity_new * d_new_m / nu
            lambda_new = 0.08
            for _ in range(2000):
                lsqrt = math.sqrt(lambda_new)
                left = 1.0 / lsqrt
                inside = 2.51 / (re_new * lsqrt) + eps_m / d_new_m / 3.72
                if inside <= 0:
                    break
                right = -2.0 * math.log10(inside)
                if right - left < 0:
                    break
                lambda_new -= 0.0005
                if lambda_new < 0.005:
                    lambda_new = 0.005
                    break

            G_LOCAL = 9.7905
            h_friction_pipe_new = lambda_new * L_m * velocity_new * velocity_new / (
                d_new_m * 2.0 * G_LOCAL
            )
            h_friction_total_new = h_friction_pipe_new + exloss_m
            delta_h = h_friction_current - h_friction_total_new
            hm_new = hm_current - delta_h

            # Yıllık çalışma saati — XM_Tn* tariflerinden
            xm_tags = [
                "XM_T1Fiyat", "XM_T1GunlukSaat", "XM_T1YillikGun",
                "XM_T2Fiyat", "XM_T2GunlukSaat", "XM_T2YillikGun",
                "XM_T3Fiyat", "XM_T3GunlukSaat", "XM_T3YillikGun",
            ]
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    ph = ",".join(["%s"] * len(xm_tags))
                    cur.execute(
                        f"SELECT tagName, tagValue FROM _tagoku "
                        f"WHERE devId = %s AND tagName IN ({ph})",
                        tuple([nid] + xm_tags),
                    )
                    xm_rows = {r["tagName"]: r["tagValue"] for r in cur.fetchall()}

            def _xmf(n: str) -> float | None:
                v = xm_rows.get(n)
                if v is None:
                    return None
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return None

            t1_h = (_xmf("XM_T1GunlukSaat") or 0) * (_xmf("XM_T1YillikGun") or 0)
            t2_h = (_xmf("XM_T2GunlukSaat") or 0) * (_xmf("XM_T2YillikGun") or 0)
            t3_h = (_xmf("XM_T3GunlukSaat") or 0) * (_xmf("XM_T3YillikGun") or 0)
            total_annual_hours = t1_h + t2_h + t3_h

            # Ortalama tarife fiyatı (ağırlıklı)
            t1_p = _xmf("XM_T1Fiyat") or 0.0
            t2_p = _xmf("XM_T2Fiyat") or 0.0
            t3_p = _xmf("XM_T3Fiyat") or 0.0
            tariff_source = "XM_Tn* tag'leri"
            if total_annual_hours > 0:
                avg_price = (t1_h * t1_p + t2_h * t2_p + t3_h * t3_p) / total_annual_hours
            else:
                avg_price = t1_p or 0.0
                tariff_source = (
                    "XM_T1Fiyat (T2/T3 saatleri girilmemiş)" if t1_p > 0
                    else "elektrik fiyatı yok — TL tasarrufu hesaplanamaz"
                )

            # Çalışma saati override
            hours_override_source = "XM_Tn* toplam"
            if daily_operating_hours and daily_operating_hours > 0:
                total_annual_hours = daily_operating_hours * 365.0
                hours_override_source = f"kullanıcı parametre ({daily_operating_hours} h/gün)"
            elif total_annual_hours <= 0:
                total_annual_hours = 12.0 * 365.0  # varsayılan 12h/gün
                hours_override_source = "varsayılan 12 h/gün (XM_Tn* yok, parametre yok)"

            # Yıllık kWh tasarrufu
            # ΔP_hid = ρ·g·Q·ΔH / 1e6 [kW]
            # ΔP_electric = ΔP_hid / η_toplam
            eta_sys_frac = None
            if eta_system and eta_system > 0:
                eta_sys_frac = eta_system / 100.0
            elif motor_eff and motor_eff > 0:
                # Tahmini: pompa verimi ~%70, motor ~verim
                eta_sys_frac = 0.70 * (motor_eff / 100.0)

            annual_kwh_savings = None
            annual_tl_savings = None
            if eta_sys_frac and eta_sys_frac > 0:
                # ΔP_hidrolik_kW = Q × ΔH / 367 (m3/h, m)
                delta_p_hidrolik_kw = (flow_m3h * delta_h) / 367.0
                delta_p_electric_kw = delta_p_hidrolik_kw / eta_sys_frac
                annual_kwh_savings = round(
                    delta_p_electric_kw * total_annual_hours, 1
                )
                if avg_price > 0:
                    annual_tl_savings = round(annual_kwh_savings * avg_price, 2)

            # Yatırım
            investment_tl = None
            if pipe_cost_tl_per_meter and pipe_cost_tl_per_meter > 0:
                material = L_m * pipe_cost_tl_per_meter
                investment_tl = round(material * installation_factor, 2)

            # Geri ödeme (simple payback) ve NPV
            simple_payback_years = None
            npv_tl = None
            lcc_current_tl = None
            lcc_alternative_tl = None
            if investment_tl and annual_tl_savings and annual_tl_savings > 0:
                simple_payback_years = round(investment_tl / annual_tl_savings, 2)
                # NPV: Σ savings/(1+r)^t − investment
                r = discount_rate_pct / 100.0
                npv = -investment_tl
                for year in range(1, design_life_years + 1):
                    npv += annual_tl_savings / ((1 + r) ** year)
                npv_tl = round(npv, 2)

                # LCC (yaklaşık: bugünkü değer yatırım + bugünkü değer enerji maliyeti)
                annual_current_cost = (
                    avg_price * total_annual_hours * an_guc if an_guc and avg_price else 0
                )
                annual_alt_cost = annual_current_cost - annual_tl_savings if annual_current_cost else 0
                pv_factor = sum(1 / ((1 + r) ** y) for y in range(1, design_life_years + 1))
                lcc_current_tl = round(annual_current_cost * pv_factor, 2) if annual_current_cost else None
                lcc_alternative_tl = round(
                    (annual_alt_cost * pv_factor) + investment_tl, 2
                ) if annual_current_cost else None

            # Öneri kararı
            if simple_payback_years is None:
                if annual_kwh_savings is None:
                    recommendation = "incomplete"
                    rec_tr = (
                        "Ekonomik değerlendirme için yeterli veri yok. "
                        "Sadece hidrolik kazanç raporlanır."
                    )
                elif annual_kwh_savings <= 0:
                    recommendation = "not_recommended"
                    rec_tr = (
                        f"Yeni çapta sürtünme kaybı daha yüksek (ΔH={round(delta_h,2)} m). "
                        "Senaryo anlamsız."
                    )
                else:
                    recommendation = "analyze_further"
                    rec_tr = (
                        f"Yılda ~{annual_kwh_savings:,.0f} kWh tasarruf potansiyeli var. "
                        "Boru birim fiyatı (pipe_cost_tl_per_meter) girilirse geri ödeme hesaplanabilir."
                    )
            elif simple_payback_years < 3:
                recommendation = "strongly_recommended"
                rec_tr = (
                    f"Geri ödeme çok iyi ({simple_payback_years} yıl < 3). "
                    "Yatırım güçlü şekilde önerilir."
                )
            elif simple_payback_years < 7:
                recommendation = "recommended"
                rec_tr = (
                    f"Geri ödeme makul ({simple_payback_years} yıl). "
                    "20 yıllık NPV pozitifse önerilir."
                )
            else:
                recommendation = "not_recommended"
                rec_tr = (
                    f"Geri ödeme uzun ({simple_payback_years} yıl > 7). "
                    "Pompa/hat ömrü buna denk gelmez — önerilmez."
                )

            # Sürtünme payı uyarısı
            friction_share_current = current["share_pct"]["friction_share_pct"]
            friction_warn = None
            if friction_share_current < 10.0:
                friction_warn = (
                    f"DİKKAT: Mevcut sürtünme payı sadece %{friction_share_current}. "
                    "ToplamHm statik baskın — boru büyütme kazanç sağlamaz. "
                    "Bu senaryo teorik; pratikte öneriLMEZ."
                )
                if recommendation in ("strongly_recommended", "recommended"):
                    recommendation = "not_recommended"
                    rec_tr = friction_warn + " " + rec_tr

            return {
                "node_id": nid,
                "node_name": current.get("node_name"),
                "current_state": {
                    "pipe_inner_diameter_mm": d_old_mm,
                    "friction_total_m": round(h_friction_current, 3),
                    "friction_share_pct": friction_share_current,
                    "total_head_m": round(hm_current, 3),
                    "flow_m3h": flow_m3h,
                    "eta_system_pct": eta_system,
                },
                "alternative_state": {
                    "pipe_inner_diameter_mm": d_new_mm,
                    "velocity_m_s": round(velocity_new, 3),
                    "reynolds": round(re_new, 0),
                    "darcy_friction_factor": round(lambda_new, 5),
                    "friction_pipe_m": round(h_friction_pipe_new, 3),
                    "friction_total_m": round(h_friction_total_new, 3),
                    "delta_head_saved_m": round(delta_h, 3),
                    "new_total_head_m": round(hm_new, 3),
                },
                "energy_savings": {
                    "annual_operating_hours": round(total_annual_hours, 0),
                    "hours_source": hours_override_source,
                    "eta_system_used": round(eta_sys_frac, 3) if eta_sys_frac else None,
                    "annual_kwh_savings": annual_kwh_savings,
                    "avg_electricity_price_tl_kwh": round(avg_price, 4) if avg_price else None,
                    "tariff_source": tariff_source,
                    "annual_tl_savings": annual_tl_savings,
                },
                "investment": {
                    "pipe_cost_tl_per_meter": pipe_cost_tl_per_meter or None,
                    "installation_factor": installation_factor,
                    "pipe_length_m": L_m,
                    "total_investment_tl": investment_tl,
                },
                "economics": {
                    "simple_payback_years": simple_payback_years,
                    "design_life_years": design_life_years,
                    "discount_rate_pct": discount_rate_pct,
                    "npv_tl": npv_tl,
                    "lcc_current_tl": lcc_current_tl,
                    "lcc_alternative_tl": lcc_alternative_tl,
                },
                "recommendation": recommendation,
                "recommendation_tr": rec_tr,
                "warnings_tr": [w for w in [friction_warn] if w],
                "hint_tr": (
                    "Kullanıcıya şunları ayrı ayrı göster: mevcut vs yeni sürtünme, "
                    "yıllık kWh+TL tasarrufu, yatırım tutarı (varsa), geri ödeme süresi, NPV. "
                    "pipe_cost_tl_per_meter girilmediyse 'fiyat bilinirse geri ödeme hesaplanabilir' de. "
                    "Öneri HER ZAMAN friction_share_pct ile tutarlı olmalı — sürtünme düşükse NPV pozitif olsa bile önerme."
                ),
            }

        @mcp.tool(name=tool)
        def analyze_pipe_upgrade_economics(
            nodeId: int,
            alternative_inner_diameter_mm: float,
            pipe_cost_tl_per_meter: float = 0.0,
            installation_factor: float = 1.3,
            daily_operating_hours: float = 0.0,
            design_life_years: int = 20,
            discount_rate_pct: float = 10.0,
        ) -> str:
            """Alternatif boru çapı senaryosu: yeni sürtünme, kWh/TL tasarrufu, geri ödeme, NPV.

Giriş:
  alternative_inner_diameter_mm: önerilen yeni iç çap (mm, örn. 200)
  pipe_cost_tl_per_meter: metre başına boru + ekipman fiyatı (0 → yatırım hesaplanmaz, sadece tasarruf)
  installation_factor: montaj-işçilik çarpanı (varsayılan 1.3)
  daily_operating_hours: günlük pompa çalışma saati (0 → XM_Tn* tariflerinden hesaplanır)
  design_life_years: amortisman süresi (varsayılan 20)
  discount_rate_pct: NPV iskonto oranı (varsayılan %10)

Çıktı: mevcut vs alternatif sürtünme, ΔH, yıllık kWh ve TL tasarrufu, yatırım,
simple payback, 20 yıl NPV, LCC karşılaştırma, öneri kararı.

ÖNEMLİ: Tool, friction_share_pct < %10 ise ekonomik NPV pozitif olsa bile 'önerilmez'
döner — statik baskın sistemlerde boru değişimi anlamsızdır."""
            return guard(tool, _analyze_pipe_upgrade_economics_impl)(
                nodeId, alternative_inner_diameter_mm, pipe_cost_tl_per_meter,
                installation_factor, daily_operating_hours, design_life_years,
                discount_rate_pct,
            )

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
            {
                "id": "pump_hydraulic",
                "title_tr": "Pompa / hidrolik analiz",
                "tools": [
                    p + "prepare_pump_selection",
                    p + "analyze_pump_at_frequency",
                    p + "get_installed_pump_info",
                    p + "analyze_hydraulic_network",
                    p + "analyze_pipe_upgrade_economics",
                ],
            },
        ]
