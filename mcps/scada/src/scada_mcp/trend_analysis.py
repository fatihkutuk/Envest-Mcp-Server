"""
Log trend analizi: doğal dil ipucu ile parametre seçimi, uzun dönem özet, basınç düşüşü+plato sezgisi.
Ağır sorgular yerine GROUP BY / örnekleme kullanır; binlerce ham satır döndürmez.
"""

from __future__ import annotations

import re
from statistics import mean, pstdev
from typing import Any

from . import db as dbmod
from .chart_contract import koru_mind_log_timeseries_extras
from .chart_hints import GRAFIK_SUNUMU_MODEL_TALIMAT_TR
from .log_value_cleanup import fetch_log_value_bounds, outlier_filtre_ozet_tr
from .scada_tag_lexicon import hint_expansion_fragments
from .types import InstanceConfig

_MAX_CANDIDATES_SQL = 80
_MAX_HINT_TOKENS = 6


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _hint_tokens(hint: str) -> list[str]:
    raw = _norm(hint)
    if not raw:
        return []
    parts = re.split(r"[\s,;]+", raw)
    stop = {"ve", "ile", "için", "the", "a", "an", "veya", "bir", "bu", "şu", "gibi"}
    out = [p for p in parts if len(p) > 1 and p not in stop]
    return out[:_MAX_HINT_TOKENS]


def _score_row(tag_path: str, desc: str, tokens: list[str]) -> int:
    hay = _norm(f"{tag_path} {desc}")
    s = 0
    for t in tokens:
        if t in hay:
            s += 3
        elif any(t in x for x in hay.split()):
            s += 2
    if not tokens and hay:
        s += 1
    return s


def resolve_log_params_by_hint(
    cur: Any, node_id: int, hint: str, *, limit: int = 8
) -> list[dict[str, Any]]:
    """nid için tagPath/description üzerinde hafif SQL + skor; çok satır dönmez."""
    nid = int(node_id)
    tokens = _hint_tokens(hint)
    if not tokens:
        cur.execute(
            """
            SELECT id, tagPath, description
            FROM kbindb.logparameters
            WHERE nid = %s AND state = 1
            ORDER BY id DESC
            LIMIT %s
            """,
            (nid, min(limit, 20)),
        )
        rows = list(cur.fetchall())
    else:
        # OR zinciri: kullanıcı kelimeleri + scada_tag_lexicon varsayılan parçaları (debimetre1/2, an_guc…).
        frags = hint_expansion_fragments(hint)
        if not frags:
            frags = tokens
        conds: list[str] = []
        params: list[Any] = [nid]
        for t in frags:
            like = f"%{t}%"
            conds.append("(LOWER(IFNULL(tagPath,'')) LIKE %s OR LOWER(IFNULL(description,'')) LIKE %s)")
            params.extend([like, like])
        wh = " OR ".join(conds)
        cur.execute(
            f"""
            SELECT id, tagPath, description
            FROM kbindb.logparameters
            WHERE nid = %s AND state = 1 AND ({wh})
            ORDER BY id DESC
            LIMIT %s
            """,
            (*params, _MAX_CANDIDATES_SQL),
        )
        rows = list(cur.fetchall())
        if not rows:
            cur.execute(
                """
                SELECT id, tagPath, description FROM kbindb.logparameters
                WHERE nid = %s AND state = 1
                ORDER BY id DESC
                LIMIT %s
                """,
                (nid, _MAX_CANDIDATES_SQL),
            )
            rows = list(cur.fetchall())
    scored: list[tuple[int, dict[str, Any]]] = []
    for r in rows:
        tp = str(r.get("tagPath") or "")
        ds = str(r.get("description") or "")
        if ds.startswith("{"):
            ds = ""
        sc = _score_row(tp, ds, tokens)
        scored.append(
            (
                sc,
                {
                    "id": int(r["id"]),
                    "tagPath": tp,
                    "description": ds or tp,
                    "match_score": sc,
                },
            )
        )
    scored.sort(key=lambda x: (-x[0], x[1]["tagPath"]))
    out = [x[1] for x in scored[:limit]]
    if not out and not tokens:
        cur.execute(
            """
            SELECT id, tagPath, description FROM kbindb.logparameters
            WHERE nid = %s AND state = 1
            ORDER BY id DESC
            LIMIT %s
            """,
            (nid, limit),
        )
        for r in cur.fetchall():
            tp = str(r.get("tagPath") or "")
            ds = str(r.get("description") or "")
            out.append(
                {
                    "id": int(r["id"]),
                    "tagPath": tp,
                    "description": (ds if not ds.startswith("{") else "") or tp,
                    "match_score": 0,
                }
            )
    return out[:limit]


def _log_table_full(cur: Any, node_id: int) -> str | None:
    t = f"log_{int(node_id)}"
    cur.execute(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='noktalog' AND TABLE_NAME=%s",
        (t,),
    )
    if not cur.fetchone():
        return None
    return f"noktalog.`{t}`"


def fetch_long_term_buckets(
    cur: Any,
    node_id: int,
    log_param_id: int,
    start: str,
    end: str,
    granularity: str,
) -> list[dict[str, Any]]:
    full = _log_table_full(cur, node_id)
    if not full:
        return []
    gran = (granularity or "month").lower().strip()
    if gran == "year":
        fmt = "%Y"
        label = "yil"
    else:
        fmt = "%Y-%m"
        label = "ay"
    wh = ["logPId = %s"]
    params: list[Any] = [int(log_param_id)]
    if (start or "").strip():
        wh.append("logTime >= %s")
        params.append(start.strip())
    if (end or "").strip():
        wh.append("logTime <= %s")
        params.append(end.strip())
    whs0 = "WHERE " + " AND ".join(wh)
    vb = fetch_log_value_bounds(cur, f"SELECT tagValue FROM {full} {whs0}", tuple(params))
    if vb:
        lo, hi = vb
        wh.extend(["tagValue >= %s", "tagValue <= %s"])
        params.extend([lo, hi])
    whs = "WHERE " + " AND ".join(wh)
    cur.execute(
        f"""
        SELECT DATE_FORMAT(logTime, %s) AS bucket,
               AVG(tagValue) AS avg_v,
               MIN(tagValue) AS min_v,
               MAX(tagValue) AS max_v,
               COUNT(*) AS n
        FROM {full}
        {whs}
        GROUP BY DATE_FORMAT(logTime, %s)
        ORDER BY bucket ASC
        LIMIT 360
        """,
        (fmt, *params, fmt),
    )
    rows = list(cur.fetchall())
    return [
        {
            "bucket": r["bucket"],
            "ort": round(float(r["avg_v"] or 0), 4),
            "min": round(float(r["min_v"] or 0), 4),
            "max": round(float(r["max_v"] or 0), 4),
            "kayit": int(r["n"] or 0),
        }
        for r in rows
    ]


def _fetch_sampled_series(
    cur: Any,
    node_id: int,
    log_param_id: int,
    start: str,
    end: str,
    max_pts: int,
) -> tuple[list[dict[str, Any]], int, str]:
    """scada_more._fetch_sampled_log ile aynı fikir — tekrar kullanım için yerel."""
    from datetime import datetime

    tname = f"log_{int(node_id)}"
    full = f"noktalog.`{tname}`"
    where = ["l.logPId = %s"]
    params: list[Any] = [int(log_param_id)]
    if (start or "").strip():
        where.append("l.logTime >= %s")
        params.append(start.strip())
    if (end or "").strip():
        where.append("l.logTime <= %s")
        params.append(end.strip())
    wh0 = "WHERE " + " AND ".join(where)
    vb = fetch_log_value_bounds(cur, f"SELECT tagValue FROM {full} l {wh0}", tuple(params))
    if vb:
        lo, hi = vb
        where.extend(["l.tagValue >= %s", "l.tagValue <= %s"])
        params.extend([lo, hi])
    wh = "WHERE " + " AND ".join(where)
    cur.execute(f"SELECT COUNT(*) AS c, MIN(logTime) AS mn, MAX(logTime) AS mx FROM {full} l {wh}", params)
    m = cur.fetchone() or {}
    total = int(m.get("c") or 0)
    if total == 0:
        return [], 0, "yok"
    mp = max(20, min(800, int(max_pts)))
    if total <= mp:
        cur.execute(
            f"SELECT tagValue, logTime FROM {full} l {wh} ORDER BY logTime ASC",
            params,
        )
        return list(cur.fetchall()), total, "yok"
    mn = m.get("mn")
    mx = m.get("mx")
    try:
        min_ts = int(datetime.fromisoformat(str(mn).replace("Z", "+00:00")).timestamp())
        max_ts = int(datetime.fromisoformat(str(mx).replace("Z", "+00:00")).timestamp())
    except Exception:
        cur.execute(
            f"SELECT tagValue, logTime FROM {full} l {wh} ORDER BY logTime ASC LIMIT %s",
            (*params, mp),
        )
        return list(cur.fetchall()), total, "limit"
    bucket_sec = max(1, (max_ts - min_ts) // mp)
    cur.execute(
        f"""
        SELECT ROUND(AVG(l.tagValue),6) AS tagValue,
               MIN(l.logTime) AS logTime
        FROM {full} l {wh}
        GROUP BY FLOOR(UNIX_TIMESTAMP(l.logTime) / %s)
        ORDER BY logTime ASC
        LIMIT %s
        """,
        (*params, bucket_sec, mp + 5),
    )
    rows = list(cur.fetchall())
    if bucket_sec < 60:
        lbl = f"~{bucket_sec}s"
    elif bucket_sec < 3600:
        lbl = f"~{round(bucket_sec / 60)}dk"
    elif bucket_sec < 86400:
        lbl = f"~{round(bucket_sec / 3600, 1)}saa"
    else:
        lbl = f"~{round(bucket_sec / 86400, 1)}gun"
    return rows, total, lbl


def _detect_plateau_decay(vals: list[float]) -> dict[str, Any]:
    """
    Basit sezgisel analiz: başlangıç ortalaması > son plato ortalaması ve son segmentte düşük varyans.
    Tıbbi/hidrolik kesin teşhis değil — operatör ipucu.
    """
    n = len(vals)
    if n < 12:
        return {"yeterli_veri": False, "aciklama_tr": "Analiz için en az ~12 örnek gerekir."}
    third = max(3, n // 3)
    first = vals[:third]
    last = vals[-third:]
    m_first = mean(first)
    m_last = mean(last)
    try:
        sd_last = pstdev(last) if len(last) > 1 else 0.0
    except Exception:
        sd_last = 0.0
    span = max(abs(m_first), abs(m_last), 1e-6)
    rel_drop = (m_first - m_last) / span
    rel_noise = sd_last / span if span else 0.0
    plateau = rel_noise < 0.02 and abs(m_first - m_last) / span > 0.05
    return {
        "yeterli_veri": True,
        "ilk_segment_ort": round(m_first, 4),
        "son_segment_ort": round(m_last, 4),
        "goreli_dusus_orani": round(rel_drop, 4),
        "son_segment_goreli_std": round(rel_noise, 4),
        "plato_sinyali": plateau,
        "yorum_tr": (
            "Son bölümde değer görece sabitlenmiş görünüyor; önceki seviyeye göre anlamlı düşüş var. "
            "Boru patlağı / hat kaçağı gibi kesin tanı için sahada basınç testi ve uzman değerlendirmesi gerekir."
            if plateau and rel_drop > 0.03
            else "Belirgin bir 'düşüş + plato' paterni için veri yetersiz veya trend farklı; aralığı daraltın veya daha fazla nokta isteyin."
        ),
    }


def analyze_log_trend_impl(
    cfg: InstanceConfig,
    nodeId: int,
    tagHint: str = "",
    logParamId: int = 0,
    analysisMode: str = "auto",
    startDate: str = "",
    endDate: str = "",
    longTermGranularity: str = "month",
    maxChartPoints: int = 120,
) -> Any:
    if not cfg.db:
        raise RuntimeError("DB config is missing for this instance.")
    nid = int(nodeId)
    mode = (analysisMode or "auto").lower().strip()
    hint = (tagHint or "").strip()
    pid = int(logParamId) if logParamId else 0

    with dbmod.connect(cfg.db) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT nName FROM kbindb.node WHERE id=%s", (nid,))
            nr = cur.fetchone()
            node_name = str(nr["nName"]) if nr else f"Node {nid}"

            candidates: list[dict[str, Any]] = []
            chosen: dict[str, Any] | None = None

            if pid > 0:
                cur.execute(
                    "SELECT id, tagPath, description FROM kbindb.logparameters WHERE id=%s AND nid=%s",
                    (pid, nid),
                )
                row = cur.fetchone()
                if not row:
                    return {"hata": f"logParamId={pid} bu node için bulunamadı."}
                chosen = {
                    "id": int(row["id"]),
                    "tagPath": str(row.get("tagPath") or ""),
                    "description": str(row.get("description") or ""),
                }
            else:
                if not hint:
                    return {
                        "hata": "tagHint veya logParamId gerekli.",
                        "ornek_tagHint": "SuSeviye, dinamik seviye, basınç, hat basıncı",
                    }
                candidates = resolve_log_params_by_hint(cur, nid, hint, limit=8)
                if not candidates:
                    return {"hata": "Eşleşen log parametresi yok.", "aranan": hint}
                chosen = candidates[0]
                pid = int(chosen["id"])

            cur.execute(
                "SELECT id, tagPath, description, rangeMin, rangeMax FROM kbindb.logparameters WHERE id=%s",
                (pid,),
            )
            pi = cur.fetchone()
            if not pi:
                return {"hata": "Parametre kaydı yok."}
            raw_d = pi.get("description") or ""
            desc = raw_d if raw_d and str(raw_d)[0] != "{" else pi.get("tagPath")

            if _log_table_full(cur, nid) is None:
                return {"hata": f"Node {nid} için noktalog tablosu yok."}

            mp = max(30, min(500, int(maxChartPoints)))

            # Uzun dönem modu: ham nokta yerine kümeleme
            if mode in ("long_term", "long_term_trend", "yillik", "multi_year"):
                buckets = fetch_long_term_buckets(
                    cur, nid, pid, startDate, endDate, longTermGranularity or "month"
                )
                if not buckets:
                    return {
                        "hata": "Seçilen aralıkta özet veri yok.",
                        "parametre": {"id": pid, "tagPath": pi.get("tagPath")},
                    }
                vals = [b["ort"] for b in buckets]
                trend = None
                if len(vals) >= 2:
                    trend = round(vals[-1] - vals[0], 4)
                return {
                    "_type": "trend_summary",
                    "analysisMode": "long_term",
                    "granularity": longTermGranularity or "month",
                    "node": {"id": nid, "name": node_name},
                    "parametre": {
                        "id": pid,
                        "tagPath": pi.get("tagPath"),
                        "description": desc,
                    },
                    "tarih_araligi": {"baslangic": startDate or "tümü", "bitis": endDate or "tümü"},
                    "ozet_serisi": buckets,
                    "istatistik": {
                        "kova_sayisi": len(buckets),
                        "ilk_ort": vals[0],
                        "son_ort": vals[-1],
                        "yaklasik_trend_farki": trend,
                    },
                    "ipucu_tr": "Yıllara sari düşüş için 'month' veya 'year' ile karşılaştırın; dar aralıkta get_chart_data kullanın.",
                    "log_deger_temizlik_tr": outlier_filtre_ozet_tr(),
                    "aday_parametreler": candidates if candidates else None,
                }

            if mode in ("pressure_plateau", "decay_plateau", "basinc_plato"):
                series, total, sampling = _fetch_sampled_series(
                    cur, nid, pid, startDate, endDate, min(mp, 400)
                )
                if not series:
                    return {"hata": "Aralıkta örnek yok.", "parametre": {"id": pid}}
                vlist = [float(r.get("tagValue") or 0) for r in series]
                plat = _detect_plateau_decay(vlist)
                return {
                    "_type": "trend_analysis",
                    "analysisMode": "pressure_plateau",
                    "node": {"id": nid, "name": node_name},
                    "parametre": {"id": pid, "tagPath": pi.get("tagPath"), "description": desc},
                    "tarih_araligi": {"baslangic": startDate or "otomatik", "bitis": endDate or "otomatik"},
                    "toplam_log_satiri": total,
                    "ornekleme": sampling,
                    "analiz": plat,
                    "seri_ozet": {
                        "nokta": len(vlist),
                        "min": round(min(vlist), 4),
                        "max": round(max(vlist), 4),
                    },
                    "log_deger_temizlik_tr": outlier_filtre_ozet_tr(),
                    "aday_parametreler": candidates if candidates else None,
                }

            # auto / chart: örneklenmiş çizgi + kısa istatistik
            series, total, sampling = _fetch_sampled_series(
                cur, nid, pid, startDate, endDate, mp
            )
            if not series:
                return {"hata": "Aralıkta veri yok.", "parametre": {"id": pid}}
            labels = [r["logTime"] for r in series]
            values = [float(r.get("tagValue") or 0) for r in series]
            mn = min(values)
            mx = max(values)
            avg = round(sum(values) / len(values), 4) if values else 0.0
            plat = _detect_plateau_decay(values)

            return {
                "_type": "chart",
                "grafik_sunumu_model_talimat_tr": GRAFIK_SUNUMU_MODEL_TALIMAT_TR,
                **koru_mind_log_timeseries_extras("line"),
                "title": f"{node_name} — trend ({desc})",
                "labels": labels,
                "datasets": [
                    {
                        "label": str(desc) + (" (örnekli)" if sampling != "yok" else ""),
                        "data": [round(v, 4) for v in values],
                        "borderColor": "#0ea5e9",
                        "fill": True,
                        "tension": 0.25,
                        "pointRadius": 0 if len(values) > 60 else 2,
                    }
                ],
                "stats": {
                    "min": round(mn, 4),
                    "max": round(mx, 4),
                    "avg": avg,
                    "chart_points": len(values),
                    "total_db_rows_in_range": total,
                    "sampling": sampling,
                },
                "y_axis_label": str(desc),
                "yAxisLabel": str(desc),
                "trend_heuristic": plat,
                "node": {"id": nid, "name": node_name},
                "parameter": {"id": pid, "path": pi.get("tagPath"), "desc": desc},
                "cozum": {
                    "tagHint_kullanilan": hint or None,
                    "aday_parametreler": candidates if candidates else None,
                },
                "kullanim_tr": (
                    "Uzun dönem (yıl/ay özet): analysisMode=long_term, longTermGranularity=year|month. "
                    "Pompa durunca basınç düşüşü + sabitlenme: analysisMode=pressure_plateau."
                ),
                "log_deger_temizlik_tr": outlier_filtre_ozet_tr(),
            }