from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from . import db as dbmod
from .types import InstanceConfig


@dataclass(frozen=True)
class PumpSnapshot:
    node_id: int
    flow_m3h: float | None
    pressure_bar: float | None
    power_kw: float | None
    frequency_hz: float | None
    timestamp: str | None
    used_tags: dict[str, str]
    # Birim / kaynak şeffaflığı (Hm: önce doğrudan tag, yoksa basınç; debi: Lt/s tag → m³/h)
    head_m: float | None = None
    head_source: str = ""
    flow_raw: float | None = None
    flow_unit: str = ""  # "m3h" | "lps"
    process_adapter: str = "generic"
    n_name: str | None = None
    n_type: str | None = None
    n_view: str | None = None


def _to_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        try:
            s = str(v).strip().replace(",", ".")
            return float(s)
        except Exception:
            return None


def _now_iso() -> str:
    return datetime.now().isoformat(sep=" ", timespec="seconds")


def _get_latest_tag_values(cur: Any, *, node_id: int, tag_names: list[str]) -> dict[str, Any]:
    if not tag_names:
        return {}
    # MySQL parameter placeholders for IN (...)
    ph = ",".join(["%s"] * len(tag_names))
    cur.execute(
        f"""
        SELECT tagName, tagValue, readTime
        FROM kbindb._tagoku
        WHERE devId = %s AND tagName IN ({ph})
        """,
        (int(node_id), *tag_names),
    )
    rows = list(cur.fetchall() or [])
    out: dict[str, Any] = {}
    for r in rows:
        out[str(r.get("tagName") or "")] = r
    return out


def _pick_first(cur_rows: dict[str, Any], names: list[str]) -> tuple[float | None, str | None, str | None]:
    """
    Return (value, used_tag, time_iso_str).
    """
    for n in names:
        row = cur_rows.get(n)
        if not row:
            continue
        v = _to_float(row.get("tagValue"))
        t = row.get("readTime")
        ts = None
        if t is not None:
            ts = str(t)
        return v, n, ts
    return None, None, None


_LPS_TO_M3H = 3.6

# Doğrudan metre cinsinden toplam / pompa basma (Hm); varsa basınç dönüşümünden öncelikli.
_HEAD_M_TAG_CANDIDATES = [
    "ToplamHm",
    "TotalHm",
    "TOPHAMHM",
    "Toplam_Hm",
    "T_ToplamHm",
    "PompaHm",
    "Pompa_Hm",
    "T_Hm",
    "BasmaYuksekligi",
    "BasmaYuksekigi",
    "Basma_Yuksekligi",
    "GercekHm",
    "Gercek_Hm",
    "Hm",  # en sonda; kısa ad, yanlış eşleşme riski
]

# m³/h varsayılan adaylar (legacy PHP ile uyumlu)
_FLOW_M3H_CANDIDATES = [
    "Debimetre",
    "T_Debi",
    "Debimetre1",
    "GirisToplamDebi",
    "CikisToplamDebimetre",
    "CikisAnlikDebi",
    "DebiM3h",
    "Debi_m3h",
    "AnlikDebiM3h",
    "Qm3h",
]

# Lt/s (veya L/s) — değer × 3.6 = m³/h
_FLOW_LPS_CANDIDATES = [
    "T_DebiLtSn",
    "DebimetreLtSn",
    "LtSn",
    "LTSn",
    "Lt_sn",
    "LT_SN",
    "DebiLtSn",
    "AnlikDebiLtSn",
    "DebiLs",
    "Debi_ls",
    "QltSn",
    "QLtsn",
    "LitreSn",
    "Litre_Sn",
    "DebimetreLt",
]


def _classify_process_adapter(*, n_type: str, n_view: str) -> str:
    """get_node_scada_context (scada_ported) ile aynı süreç ailesi — kuyu/terfi ayrımı için."""
    v = (n_view or "").strip().lower()
    t = str(n_type or "").strip()
    if t == "666" or v.startswith("a-system") or v.startswith("_a-multi"):
        return "system"
    if t == "777" or "kuyu" in v or "well" in v:
        return "well"
    if "depo" in v or "tank" in v or "store" in v:
        return "tank"
    if "terfi" in v or "riser" in v:
        return "riser"
    return "generic"


def _resolve_flow_m3h(
    rows: dict[str, Any],
    *,
    process_adapter: str,
    used: dict[str, str],
) -> tuple[float | None, float | None, str, str | None]:
    """
    (flow_m3h, flow_raw_lps_or_m3h, flow_unit, timestamp).
    Kuyuda Lt/s tag'i varsa genel Debimetre'ye göre öncelik (yanlış birim riski).
    """
    lps_v, lps_tag, lps_ts = _pick_first(rows, _FLOW_LPS_CANDIDATES)
    m3_v, m3_tag, m3_ts = _pick_first(rows, _FLOW_M3H_CANDIDATES)

    prefer_lps = False
    if lps_v is not None and lps_tag:
        if process_adapter == "well":
            prefer_lps = True
        elif m3_v is None:
            prefer_lps = True
        elif m3_v is not None and m3_tag:
            # İkisi de var: kuyu dışında m³/h adayına güven (terfi/depo)
            prefer_lps = False

    if prefer_lps and lps_v is not None:
        used["flow_m3h"] = lps_tag
        used["flow_conversion"] = "lps_to_m3h_x3.6"
        return float(lps_v) * _LPS_TO_M3H, float(lps_v), "lps", lps_ts

    if m3_v is not None and m3_tag:
        used["flow_m3h"] = m3_tag
        return float(m3_v), float(m3_v), "m3h", m3_ts

    return None, None, "", lps_ts or m3_ts


def _resolve_head_m(
    rows: dict[str, Any],
    *,
    pressure_bar: float | None,
    pressure_tag: str | None,
    pressure_ts: str | None,
    used: dict[str, str],
) -> tuple[float | None, str, str | None]:
    """(head_m, head_source, timestamp) — önce Hm tag, yoksa basınç × ~10.2 m."""
    hv, htag, hts = _pick_first(rows, _HEAD_M_TAG_CANDIDATES)
    if hv is not None and htag and float(hv) > 0:
        used["head_m_tag"] = htag
        return float(hv), f"tag:{htag}", hts

    if pressure_bar is not None and pressure_tag and float(pressure_bar) > 0:
        used["pressure_bar"] = pressure_tag
        hm = float(pressure_bar) * 10.197162129779
        return hm, f"pressure:{pressure_tag}", pressure_ts

    return None, "", pressure_ts


def get_pump_snapshot(cfg: InstanceConfig, *, node_id: int) -> PumpSnapshot:
    if not cfg.db:
        raise RuntimeError("DB config is missing for this instance.")

    pressure_candidates = ["BasincSensoru", "T_Basinc", "CikisBasincSensoru", "GirisBasincSensoru", "GirisBasinc"]
    power_candidates = ["An_Guc", "T_Guc"]
    freq_candidates = ["An_SebFrekans", "T_Frekans", "Frekans"]

    n_name: str | None = None
    n_type: str | None = None
    n_view: str | None = None
    adapter = "generic"

    with dbmod.connect(cfg.db) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT nName, nType, nView FROM kbindb.node WHERE id = %s LIMIT 1",
                (int(node_id),),
            )
            nrow = cur.fetchone()
            if nrow:
                n_name = str(nrow.get("nName") or "") or None
                n_type = str(nrow.get("nType") or "") or None
                n_view = str(nrow.get("nView") or "") or None
                adapter = _classify_process_adapter(n_type=n_type or "", n_view=n_view or "")

            wanted = sorted(
                set(
                    _HEAD_M_TAG_CANDIDATES
                    + _FLOW_M3H_CANDIDATES
                    + _FLOW_LPS_CANDIDATES
                    + pressure_candidates
                    + power_candidates
                    + freq_candidates
                )
            )
            rows = _get_latest_tag_values(cur, node_id=int(node_id), tag_names=wanted)

    used: dict[str, str] = {"process_adapter": adapter}
    if n_view:
        used["n_view"] = n_view

    pressure, pres_tag, pres_ts = _pick_first(rows, pressure_candidates)
    head_m, head_source, _hts = _resolve_head_m(
        rows,
        pressure_bar=pressure,
        pressure_tag=pres_tag,
        pressure_ts=pres_ts,
        used=used,
    )
    flow, flow_raw, flow_unit, ts = _resolve_flow_m3h(rows, process_adapter=adapter, used=used)

    power, pwr_tag, _ = _pick_first(rows, power_candidates)
    if pwr_tag:
        used["power_kw"] = pwr_tag
    freq, fq_tag, _ = _pick_first(rows, freq_candidates)
    if fq_tag:
        used["frequency_hz"] = fq_tag

    return PumpSnapshot(
        node_id=int(node_id),
        flow_m3h=flow,
        pressure_bar=pressure if pres_tag else None,
        power_kw=power,
        frequency_hz=freq,
        timestamp=ts,
        used_tags=used,
        head_m=head_m,
        head_source=head_source,
        flow_raw=flow_raw,
        flow_unit=flow_unit,
        process_adapter=adapter,
        n_name=n_name,
        n_type=n_type,
        n_view=n_view,
    )


def calculate_hydraulic_metrics(
    *,
    flow_m3h: float | None,
    pressure_bar: float | None,
    power_kw: float | None,
    total_head_m: float | None = None,
    head_source: str = "",
    rho_kg_m3: float = 1000.0,
    g_m_s2: float = 9.80665,
) -> dict[str, Any]:
    """
    Minimal, SCADA-friendly hydraulic metrics:
    - total_head_m: ToplamHm vb. tag varsa doğrudan kullanılır; yoksa basınçtan H ≈ p_bar * 10.197 m
    - Specific energy: kWh/m³ ≈ kW / (m³/h)
    - Hydraulic power: Ph = rho*g*Q*H
    """
    out: dict[str, Any] = {"timestamp": _now_iso()}
    if flow_m3h is None:
        out["flow_m3h"] = None
    else:
        out["flow_m3h"] = round(float(flow_m3h), 3)
    if pressure_bar is None:
        out["pressure_bar"] = None
    else:
        out["pressure_bar"] = round(float(pressure_bar), 3)

    head_m: float | None
    if total_head_m is not None and float(total_head_m) > 0:
        head_m = float(total_head_m)
        out["head_m"] = round(head_m, 2)
        out["head_m_source"] = (head_source or "tag").strip() or "total_head_tag"
    elif pressure_bar is not None:
        head_m = float(pressure_bar) * 10.197162129779  # m H2O per bar
        out["head_m"] = round(head_m, 2)
        out["head_m_source"] = "pressure_bar"
    else:
        head_m = None
        out["head_m"] = None
        out["head_m_source"] = ""

    if power_kw is None:
        out["power_kw"] = None
    else:
        out["power_kw"] = round(float(power_kw), 3)

    if flow_m3h and flow_m3h > 0 and power_kw and power_kw > 0:
        out["specific_energy_kwh_per_m3"] = round(float(power_kw) / float(flow_m3h), 4)
    else:
        out["specific_energy_kwh_per_m3"] = None

    if head_m is not None and flow_m3h and flow_m3h > 0:
        q_m3_s = float(flow_m3h) / 3600.0
        ph_w = float(rho_kg_m3) * float(g_m_s2) * q_m3_s * float(head_m)
        out["hydraulic_power_kw"] = round(ph_w / 1000.0, 4)
    else:
        out["hydraulic_power_kw"] = None

    if out.get("hydraulic_power_kw") and power_kw and power_kw > 0:
        out["wire_to_water_efficiency"] = round(float(out["hydraulic_power_kw"]) / float(power_kw), 4)
    else:
        out["wire_to_water_efficiency"] = None

    return out


def analyze_pump_performance(cfg: InstanceConfig, *, node_id: int) -> dict[str, Any]:
    snap = get_pump_snapshot(cfg, node_id=int(node_id))
    metrics = calculate_hydraulic_metrics(
        flow_m3h=snap.flow_m3h,
        pressure_bar=snap.pressure_bar,
        power_kw=snap.power_kw,
        total_head_m=snap.head_m,
        head_source=snap.head_source,
    )
    vfd_hint = None
    if snap.frequency_hz is not None:
        vfd_hint = "vfd_detected"
    out: dict[str, Any] = {
        "node_id": snap.node_id,
        "snapshot": {
            "flow_m3h": snap.flow_m3h,
            "pressure_bar": snap.pressure_bar,
            "power_kw": snap.power_kw,
            "frequency_hz": snap.frequency_hz,
            "read_time": snap.timestamp,
            "used_tags": snap.used_tags,
            "process_adapter": snap.process_adapter,
            "n_name": snap.n_name,
            "n_type": snap.n_type,
            "n_view": snap.n_view,
            "head_m": snap.head_m,
            "head_source": snap.head_source,
            "flow_raw": snap.flow_raw,
            "flow_unit": snap.flow_unit,
        },
        "metrics": metrics,
        "selection_guidance_tr": [
            "H (basma yüksekliği): Önce ToplamHm / TotalHm vb. tag okunur; yoksa çıkış basıncından yaklaşık H hesaplanır (1 bar ≈ 10.2 mSS).",
            "Q (debi): m³/h tag'leri ile Lt/s (L/s) adları ayrılır; Lt/s değer × 3.6 = m³/h. Kuyu istasyonunda Lt/s tag'i varsa, genel Debimetre'ye göre önceliklidir.",
            "Sürücülü (VFD) için anlık frekans tag'i varsa VFD olduğu anlaşılır; pompa eğrisi eşlemesi katalog / ürün verisi gerektirir.",
        ],
        "vfd_hint": vfd_hint,
    }
    return out


def get_pump_catalog_for_node(cfg: InstanceConfig, *, node_id: int) -> dict[str, Any]:
    """Node'un anlık duty point'ine en yakın pump_specs kayıtlarını döndürür."""
    snap = get_pump_snapshot(cfg, node_id=int(node_id))

    head_m = snap.head_m
    if head_m is None and snap.pressure_bar is not None and snap.pressure_bar > 0:
        head_m = float(snap.pressure_bar) * 10.197162

    # Freq belirleme: VFD varsa 0 (tüm frekanslar), yoksa 50
    freq_filter = 0  # default: hepsini getir
    if snap.frequency_hz is None:
        freq_filter = 50  # VFD yok → sadece 50Hz

    # pump_specs'den en yakın pompayı bul
    catalog_results = select_pump_from_catalog(
        cfg,
        target_hm=head_m or 0,
        target_flow=snap.flow_m3h or 0,
        freq=freq_filter,
        limit=5,
    )

    return {
        "node_id": int(node_id),
        "current_duty_point": {
            "flow_m3h": snap.flow_m3h,
            "pressure_bar": snap.pressure_bar,
            "head_m": round(head_m, 2) if head_m else None,
            "head_source": snap.head_source,
            "flow_unit": snap.flow_unit,
            "process_adapter": snap.process_adapter,
            "power_kw": snap.power_kw,
            "frequency_hz": snap.frequency_hz,
        },
        "catalog_matches": catalog_results.get("pumps", []),
        "catalog_count": catalog_results.get("total_found", 0),
        "freq_filter_used": freq_filter,
        "vfd_detected": snap.frequency_hz is not None,
    }


def select_pump_from_catalog(
    cfg: InstanceConfig,
    *,
    target_hm: float,
    target_flow: float,
    freq: float = 0,
    limit: int = 10,
) -> dict[str, Any]:
    """
    pump_specs tablosundan (Hm, Flow) duty point'ine en yakın pompaları seçer.
    PHP ProcPumpSelection mantığını taklit eder:
    - freq=50 → sadece 50Hz (sürücüsüz/şebeke)
    - freq=0  → tüm frekanslar (sürücülü dahil)
    - Sonuçlar Öklid mesafesine (difft) göre sıralanır.
    """
    if not cfg.db:
        raise RuntimeError("DB config is missing for this instance.")

    target_hm = float(target_hm or 0)
    target_flow = float(target_flow or 0)
    freq = float(freq or 0)
    limit = max(1, min(50, int(limit)))

    if target_hm <= 0 and target_flow <= 0:
        return {
            "success": False,
            "error_tr": "Hm ve Flow değerlerinden en az biri > 0 olmalıdır.",
            "pumps": [],
            "total_found": 0,
        }

    # Stored procedure yerine doğrudan SQL ile aynı mantık:
    # Öklid mesafesi: sqrt((Hm - target)^2 + (Flow - target)^2)
    freq_clause = ""
    params: list[Any] = [target_hm, target_flow]
    if freq > 0:
        freq_clause = "WHERE Freq = %s"
        params.append(freq)

    params.extend([target_hm, target_flow, limit])

    sql = f"""
        SELECT
            pId, Label, Hm, Flow, Freq, P1, Etap, Etam, Etapm,
            SQRT(POW(Hm - %s, 2) + POW(Flow - %s, 2)) AS difft
        FROM dbanalytics.pump_specs
        {freq_clause}
        HAVING difft IS NOT NULL
        ORDER BY SQRT(POW(Hm - %s, 2) + POW(Flow - %s, 2)) ASC
        LIMIT %s
    """

    try:
        with dbmod.connect(cfg.db) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
                rows = list(cur.fetchall() or [])
    except Exception as e:
        return {
            "success": False,
            "error_tr": f"pump_specs sorgusu başarısız: {e.__class__.__name__}",
            "pumps": [],
            "total_found": 0,
        }

    pumps = []
    for r in rows:
        pumps.append({
            "pId": r.get("pId"),
            "label": r.get("Label"),
            "hm": _to_float(r.get("Hm")),
            "flow_m3h": _to_float(r.get("Flow")),
            "freq_hz": _to_float(r.get("Freq")),
            "p1_kw": _to_float(r.get("P1")),
            "etap_pct": _to_float(r.get("Etap")),
            "etam_pct": _to_float(r.get("Etam")),
            "etapm_pct": _to_float(r.get("Etapm")),
            "distance_score": round(float(r.get("difft") or 0), 3),
        })

    # En iyi eşleşme için özet
    best = pumps[0] if pumps else None
    summary = None
    if best:
        drive_mode = "sürücülü (VFD)" if best["freq_hz"] and best["freq_hz"] != 50 else "sürücüsüz (50Hz)"
        summary = {
            "best_match_label": best["label"],
            "best_match_hm": best["hm"],
            "best_match_flow": best["flow_m3h"],
            "best_match_p1_kw": best["p1_kw"],
            "best_match_etapm": best["etapm_pct"],
            "drive_mode_tr": drive_mode,
            "distance_score": best["distance_score"],
        }

    return {
        "success": True,
        "target": {"hm": target_hm, "flow_m3h": target_flow, "freq_filter": freq},
        "summary_tr": summary,
        "pumps": pumps,
        "total_found": len(pumps),
        "note_tr": (
            "Sonuçlar hedef (Hm, Flow) noktasına Öklid mesafesine göre sıralıdır. "
            "En düşük distance_score = en yakın eşleşme."
        ),
    }


def list_pump_catalog_summary(
    cfg: InstanceConfig,
    *,
    freq: float = 0,
    min_hm: float = 0,
    max_hm: float = 0,
    min_flow: float = 0,
    max_flow: float = 0,
    limit: int = 30,
) -> dict[str, Any]:
    """pump_specs tablosunun genel özetini ve isteğe bağlı filtrelenmiş listesini döndürür."""
    if not cfg.db:
        raise RuntimeError("DB config is missing for this instance.")

    limit = max(1, min(200, int(limit)))

    with dbmod.connect(cfg.db) as conn:
        with conn.cursor() as cur:
            # Genel istatistik
            cur.execute("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(DISTINCT Label) AS distinct_labels,
                    MIN(Hm) AS min_hm, MAX(Hm) AS max_hm,
                    MIN(Flow) AS min_flow, MAX(Flow) AS max_flow,
                    MIN(P1) AS min_p1, MAX(P1) AS max_p1,
                    COUNT(DISTINCT Freq) AS freq_count
                FROM dbanalytics.pump_specs
            """)
            stats = cur.fetchone() or {}

            cur.execute("SELECT DISTINCT Freq FROM dbanalytics.pump_specs ORDER BY Freq")
            freq_values = [r["Freq"] for r in cur.fetchall()]

            # Filtrelenmiş liste
            where_parts: list[str] = []
            params: list[Any] = []

            if freq > 0:
                where_parts.append("Freq = %s")
                params.append(freq)
            if min_hm > 0:
                where_parts.append("Hm >= %s")
                params.append(min_hm)
            if max_hm > 0:
                where_parts.append("Hm <= %s")
                params.append(max_hm)
            if min_flow > 0:
                where_parts.append("Flow >= %s")
                params.append(min_flow)
            if max_flow > 0:
                where_parts.append("Flow <= %s")
                params.append(max_flow)

            where_sql = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""
            params.append(limit)

            cur.execute(
                f"SELECT pId, Label, Hm, Flow, Freq, P1, Etap, Etam, Etapm FROM dbanalytics.pump_specs{where_sql} ORDER BY Hm, Flow LIMIT %s",
                tuple(params),
            )
            rows = list(cur.fetchall() or [])

    pumps = []
    for r in rows:
        pumps.append({
            "pId": r.get("pId"),
            "label": r.get("Label"),
            "hm": _to_float(r.get("Hm")),
            "flow_m3h": _to_float(r.get("Flow")),
            "freq_hz": _to_float(r.get("Freq")),
            "p1_kw": _to_float(r.get("P1")),
            "etap_pct": _to_float(r.get("Etap")),
            "etam_pct": _to_float(r.get("Etam")),
            "etapm_pct": _to_float(r.get("Etapm")),
        })

    return {
        "catalog_stats": {
            "total_records": stats.get("total", 0),
            "distinct_labels": stats.get("distinct_labels", 0),
            "hm_range": [stats.get("min_hm"), stats.get("max_hm")],
            "flow_range": [stats.get("min_flow"), stats.get("max_flow")],
            "p1_range": [stats.get("min_p1"), stats.get("max_p1")],
            "available_frequencies": freq_values,
        },
        "filtered_pumps": pumps,
        "filtered_count": len(pumps),
    }


def search_pump_alternatives(
    cfg: InstanceConfig,
    *,
    node_id: int,
    desired_flow_m3h: float | None = None,
    desired_head_m: float | None = None,
    allow_vfd: bool = True,
) -> dict[str, Any]:
    snap = get_pump_snapshot(cfg, node_id=int(node_id))
    metrics = calculate_hydraulic_metrics(
        flow_m3h=snap.flow_m3h,
        pressure_bar=snap.pressure_bar,
        power_kw=snap.power_kw,
        total_head_m=snap.head_m,
        head_source=snap.head_source,
    )
    duty_flow = float(desired_flow_m3h) if desired_flow_m3h is not None else (snap.flow_m3h or 0.0)
    duty_head = float(desired_head_m) if desired_head_m is not None else (float(metrics.get("head_m") or 0.0))
    # pump_specs katalogdan eşleşme ara
    freq_filter = 0 if allow_vfd else 50
    catalog = select_pump_from_catalog(
        cfg,
        target_hm=duty_head,
        target_flow=duty_flow,
        freq=freq_filter,
        limit=10,
    )

    result: dict[str, Any] = {
        "node_id": int(node_id),
        "desired_duty_point": {"flow_m3h": round(duty_flow, 3), "head_m": round(duty_head, 2)},
        "current_snapshot": {
            "flow_m3h": snap.flow_m3h,
            "pressure_bar": snap.pressure_bar,
            "head_m": snap.head_m,
            "head_source": snap.head_source,
            "flow_unit": snap.flow_unit,
            "process_adapter": snap.process_adapter,
            "power_kw": snap.power_kw,
            "frequency_hz": snap.frequency_hz,
        },
        "constraints": {"allow_vfd": bool(allow_vfd), "freq_filter": freq_filter},
    }

    if catalog.get("success") and catalog.get("total_found", 0) > 0:
        result["catalog_matches"] = catalog["pumps"]
        result["best_match"] = catalog.get("summary_tr")
        result["total_alternatives"] = catalog["total_found"]

        # Güç karşılaştırması
        best = catalog["pumps"][0]
        if snap.power_kw and best.get("p1_kw"):
            diff = round(float(snap.power_kw) - float(best["p1_kw"]), 2)
            result["power_comparison_tr"] = {
                "current_kw": snap.power_kw,
                "recommended_kw": best["p1_kw"],
                "difference_kw": diff,
                "note_tr": (
                    f"Mevcut güç: {snap.power_kw:.2f} kW, Önerilen: {best['p1_kw']:.2f} kW. "
                    f"Fark: {abs(diff):.2f} kW {'tasarruf' if diff > 0 else 'artış'}."
                ),
            }
    else:
        result["catalog_matches"] = []
        result["total_alternatives"] = 0
        result["note_tr"] = "pump_specs katalogunda uygun eşleşme bulunamadı."

    return result

