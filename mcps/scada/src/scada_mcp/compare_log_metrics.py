"""
İki log parametresini aynı zaman dilimleriyle hizalayıp karşılaştırma (ör. kuyu debi vs güç).
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from . import db as dbmod
from .chart_contract import koru_mind_log_timeseries_extras
from .chart_hints import GRAFIK_SUNUMU_MODEL_TALIMAT_TR
from .dma_demand import _resolve_node_for_seasonal_profile, _log_table_full
from .log_series_align import fetch_bucket_rows_for_param
from .log_value_cleanup import outlier_filtre_ozet_tr
from .scada_tag_lexicon import DEFAULT_COMPARE_GUC_HINT, DEFAULT_DMA_DEBI_HINT
from .trend_analysis import resolve_log_params_by_hint
from .types import InstanceConfig

_DEFAULT_PRIMARY_HINT = DEFAULT_DMA_DEBI_HINT
_DEFAULT_SECONDARY_HINT = DEFAULT_COMPARE_GUC_HINT


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = min(len(xs), len(ys))
    pairs = [(xs[i], ys[i]) for i in range(n)]
    pairs = [(a, b) for a, b in pairs if not (math.isnan(a) or math.isnan(b))]
    if len(pairs) < 3:
        return None
    xa = [p[0] for p in pairs]
    ya = [p[1] for p in pairs]
    mx = sum(xa) / len(xa)
    my = sum(ya) / len(ya)
    num = sum((xa[i] - mx) * (ya[i] - my) for i in range(len(xa)))
    denx = math.sqrt(sum((x - mx) ** 2 for x in xa))
    deny = math.sqrt(sum((y - my) ** 2 for y in ya))
    if denx < 1e-12 or deny < 1e-12:
        return None
    r = num / (denx * deny)
    return round(float(r), 4)


def compare_log_metrics_impl(
    cfg: InstanceConfig,
    nodeId: int = 0,
    nodeAdiAra: str = "",
    primaryTagHint: str = "",
    secondaryTagHint: str = "",
    primaryLogParamId: int = 0,
    secondaryLogParamId: int = 0,
    startDate: str = "",
    endDate: str = "",
    maxChartPoints: int = 140,
    chartType: str = "line",
    karsilastirmaAciklamasi: str = "",
) -> Any:
    """
    Aynı node üzerinde iki log parametresini ortak zaman kovalarıyla hizalar.
    primary ≈ debi, secondary ≈ güç için ipuçları boş bırakılırsa SCADA tipik etiketleri denenir.
    """
    if not cfg.db:
        raise RuntimeError("DB config is missing for this instance.")
    mp = max(24, min(600, int(maxChartPoints)))
    empty_err = {
        "hata": "nodeId > 0 veya nodeAdiAra gerekli.",
        "model_talimat_tr": (
            "İki log parametresini aynı grafikte karşılaştırmak için: nodeId veya nodeAdiAra (ör. «Serbest Bölge Kuyu»). "
            "primaryLogParamId / secondaryLogParamId veya primaryTagHint / secondaryTagHint (debi, güç). "
            "Varsayılan: debi akış + güç/kW."
        ),
    }
    with dbmod.connect(cfg.db) as conn:
        with conn.cursor() as cur:
            resolved = _resolve_node_for_seasonal_profile(
                cur,
                node_id=nodeId,
                node_adi_ara=nodeAdiAra,
                empty_search_err=empty_err,
                no_match_ipucu="find_nodes_by_keywords",
            )
            if isinstance(resolved, dict):
                return resolved
            nid, node = resolved
            full = _log_table_full(cur, nid)
            if not full:
                return {"hata": "Log tablosu yok."}

            p_hint = (primaryTagHint or "").strip() or _DEFAULT_PRIMARY_HINT
            s_hint = (secondaryTagHint or "").strip() or _DEFAULT_SECONDARY_HINT
            pid_a = int(primaryLogParamId) if primaryLogParamId else 0
            pid_b = int(secondaryLogParamId) if secondaryLogParamId else 0

            cands_a: list[dict[str, Any]] | None = None
            cands_b: list[dict[str, Any]] | None = None
            if pid_a <= 0:
                cands_a = resolve_log_params_by_hint(cur, nid, p_hint, limit=6)
                if not cands_a:
                    return {
                        "hata": "Birinci parametre bulunamadı.",
                        "aranan": p_hint,
                        "ipucu_tr": "primaryTagHint veya primaryLogParamId verin (ör. debimetre etiketi).",
                    }
                pid_a = int(cands_a[0]["id"])
                meta_a = cands_a[0]
            else:
                cur.execute(
                    "SELECT id, tagPath, description FROM kbindb.logparameters WHERE id=%s AND nid=%s",
                    (pid_a, nid),
                )
                row = cur.fetchone()
                if not row:
                    return {"hata": f"primaryLogParamId={pid_a} bu node için yok."}
                meta_a = {
                    "id": int(row["id"]),
                    "tagPath": str(row.get("tagPath") or ""),
                    "description": str(row.get("description") or ""),
                }

            if pid_b <= 0:
                cands_b = resolve_log_params_by_hint(cur, nid, s_hint, limit=6)
                if not cands_b:
                    return {
                        "hata": "İkinci parametre bulunamadı.",
                        "aranan": s_hint,
                        "ipucu_tr": "secondaryTagHint veya secondaryLogParamId verin (ör. güç, kW).",
                    }
                pid_b = int(cands_b[0]["id"])
                meta_b = cands_b[0]
            else:
                cur.execute(
                    "SELECT id, tagPath, description FROM kbindb.logparameters WHERE id=%s AND nid=%s",
                    (pid_b, nid),
                )
                row = cur.fetchone()
                if not row:
                    return {"hata": f"secondaryLogParamId={pid_b} bu node için yok."}
                meta_b = {
                    "id": int(row["id"]),
                    "tagPath": str(row.get("tagPath") or ""),
                    "description": str(row.get("description") or ""),
                }

            if pid_a == pid_b:
                return {"hata": "İki parametre aynı olamaz; farklı tagHint veya logParamId seçin."}

            wh_both = ["(l.logPId = %s OR l.logPId = %s)"]
            pr_both: list[Any] = [pid_a, pid_b]
            if (startDate or "").strip():
                wh_both.append("l.logTime >= %s")
                pr_both.append(startDate.strip())
            if (endDate or "").strip():
                wh_both.append("l.logTime <= %s")
                pr_both.append(endDate.strip())
            whs_both = "WHERE " + " AND ".join(wh_both)
            cur.execute(
                f"SELECT MIN(logTime) AS mn, MAX(logTime) AS mx, COUNT(*) AS c FROM {full} l {whs_both}",
                tuple(pr_both),
            )
            span = cur.fetchone() or {}
            mn, mx = span.get("mn"), span.get("mx")
            total_both = int(span.get("c") or 0)
            if not mn or not mx or total_both == 0:
                return {
                    "hata": "Seçilen aralıkta iki parametreden en az biri için veri yok.",
                    "node": {"id": nid, "nName": node.get("nName")},
                    "parametreler": {"a": meta_a, "b": meta_b},
                }

            try:
                min_ts = int(datetime.fromisoformat(str(mn).replace("Z", "+00:00")).timestamp())
                max_ts = int(datetime.fromisoformat(str(mx).replace("Z", "+00:00")).timestamp())
            except Exception:
                return {"hata": "logTime aralığı çözümlenemedi."}

            span_sec = max(1, max_ts - min_ts)
            bucket_sec = max(1, span_sec // mp)

            rows_a = fetch_bucket_rows_for_param(cur, full, pid_a, startDate, endDate, bucket_sec)
            rows_b = fetch_bucket_rows_for_param(cur, full, pid_b, startDate, endDate, bucket_sec)
            if not rows_a and not rows_b:
                return {"hata": "Kovalar oluşturulamadı.", "parametreler": {"a": meta_a, "b": meta_b}}

            map_a = {int(r["bi"]): r for r in rows_a}
            map_b = {int(r["bi"]): r for r in rows_b}
            all_bi = sorted(set(map_a) | set(map_b))
            if len(all_bi) > mp:
                all_bi = all_bi[-mp:]

            labels: list[str] = []
            va: list[float | None] = []
            vb: list[float | None] = []
            for bi in all_bi:
                ra = map_a.get(bi)
                rb = map_b.get(bi)
                lt = (ra or rb or {}).get("logTime")
                labels.append(str(lt) if lt is not None else str(bi))
                va.append(float(ra["tagValue"]) if ra else None)
                vb.append(float(rb["tagValue"]) if rb else None)

            pair_x: list[float] = []
            pair_y: list[float] = []
            for a, b in zip(va, vb, strict=True):
                if a is not None and b is not None:
                    pair_x.append(a)
                    pair_y.append(b)
            r_pearson = _pearson(pair_x, pair_y) if len(pair_x) >= 3 else None
            pair_a = [x for x in va if x is not None]
            pair_b_only = [y for y in vb if y is not None]

            lbl_a = str(meta_a.get("tagPath") or meta_a.get("description") or f"logPId {pid_a}")
            lbl_b = str(meta_b.get("tagPath") or meta_b.get("description") or f"logPId {pid_b}")
            node_name = str(node.get("nName") or nid)
            title = f"{node_name} — {lbl_a} × {lbl_b}"
            if startDate or endDate:
                title += f" ({startDate or '…'} → {endDate or '…'})"

            note_tr = (
                "Debi (m³/h) ile güç (kW) farklı birimdedir; mümkünse KoruMind çift Y ekseni (yAxisID y / y1) kullanın. "
                "Korelasyon yalnızca ortak zaman kovalarında hesaplanır; örnekleme aralığı bucket_seconds ile özetlenir."
            )
            aciklama = (karsilastirmaAciklamasi or "").strip()
            if aciklama:
                note_tr = aciklama + " " + note_tr

            ct = (chartType or "line").strip().lower()
            extras = koru_mind_log_timeseries_extras(ct)

            return {
                "_type": "chart",
                "grafik_sunumu_model_talimat_tr": GRAFIK_SUNUMU_MODEL_TALIMAT_TR,
                **extras,
                "chart_role_tr": "log_metric_pair_compare",
                "title": title,
                "subtitle": "Aynı zaman kovalarında iki parametre; çift eksen önerilir.",
                "labels": labels,
                "datasets": [
                    {
                        "label": lbl_a,
                        "data": va,
                        "yAxisID": "y",
                        "borderColor": "#0ea5e9",
                        "backgroundColor": "rgba(14,165,233,0.08)",
                        "fill": False,
                        "tension": 0.25,
                        "pointRadius": 0 if len(labels) > 80 else 2,
                    },
                    {
                        "label": lbl_b,
                        "data": vb,
                        "yAxisID": "y1",
                        "borderColor": "#f97316",
                        "backgroundColor": "rgba(249,115,22,0.08)",
                        "fill": False,
                        "tension": 0.25,
                        "pointRadius": 0 if len(labels) > 80 else 2,
                    },
                ],
                "stats": {
                    "ortak_kova_sayisi": len(all_bi),
                    "bucket_seconds": bucket_sec,
                    "toplam_ham_satir_araligi": total_both,
                    "pearson_ortak_nokta": r_pearson,
                    "birinci_ort": round(sum(pair_a) / len(pair_a), 4) if pair_a else None,
                    "ikinci_ort": round(sum(pair_b_only) / len(pair_b_only), 4) if pair_b_only else None,
                },
                "karsilastirma_notu_tr": note_tr,
                "dual_axis_suggested": True,
                "node": {"id": nid, "name": node_name, "nView": node.get("nView")},
                "parametre_birinci": {
                    "logParamId": pid_a,
                    "tagPath": meta_a.get("tagPath"),
                    "description": meta_a.get("description"),
                },
                "parametre_ikinci": {
                    "logParamId": pid_b,
                    "tagPath": meta_b.get("tagPath"),
                    "description": meta_b.get("description"),
                },
                "aday_parametreler": {
                    "birinci": cands_a,
                    "ikinci": cands_b,
                },
                "log_deger_temizlik_tr": outlier_filtre_ozet_tr(),
            }
