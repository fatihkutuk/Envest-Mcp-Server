"""
DMA debimetre ve kuyu dinamik seviye için saatlik profil, yaz/kış karşılaştırması, K-Means kümeleri.
Ham log satırı döndürülmez; yalnızca SQL toplamları + 24 saatlik vektör.
"""

from __future__ import annotations

import random
from typing import Any, Literal

from . import db as dbmod
from .chart_contract import koru_mind_dma_hourly_profile_extras, koru_mind_tez_scatter_extras
from .chart_hints import (
    DMA_ANALIZ_SONRASI_GRAFIK_TALIMAT_TR,
    DUSUNCE_DONGUSU_KES_MODEL_TALIMAT_TR,
    GRAFIK_SUNUMU_MODEL_TALIMAT_TR,
    SEVIYE_ANALIZ_SONRASI_GRAFIK_TALIMAT_TR,
)
from .log_value_cleanup import fetch_log_value_bounds, outlier_filtre_ozet_tr
from .scada_tag_lexicon import DEFAULT_DMA_DEBI_HINT, DEFAULT_LEVEL_HINT
from .trend_analysis import resolve_log_params_by_hint
from .types import InstanceConfig

_SUMMER_MONTHS = (6, 7, 8)
_WINTER_MONTHS = (12, 1, 2)
_MIN_DAYS_FOR_SEASON_COMPARE = 300  # ~10 ay veri; tam yıl şartı değil ama anlamlı yaz/kış için


def _safe_like_fragment(s: str) -> str:
    return (s or "").strip().replace("%", "").replace("_", "")[:160]


def _rank_dma_log_candidates(cands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Otomatik seçimde _NoError gibi iç etiketleri geri it; debimetre/debi adaylarını öne al."""

    def sort_key(c: dict[str, Any]) -> tuple[int, int, str]:
        tp = (c.get("tagPath") or "").lower().strip()
        ds = (str(c.get("description") or "") or "").lower()
        if ds.startswith("{"):
            ds = ""
        blob = f"{tp} {ds}"
        low = blob.replace(" ", "")
        base = int(c.get("match_score") or 0)
        adj = base * 10_000
        if tp.startswith("_"):
            adj -= 50_000
        if "noerror" in low or tp == "_noerror":
            adj -= 50_000
        if "debimetre" in blob or "demimetre" in blob or "deminetre" in blob:
            adj += 100_000
        elif "debi" in blob:
            adj += 60_000
        if "debimetre1" in low.replace(" ", "") or "debimetre2" in low.replace(" ", ""):
            adj += 15_000
        if "akış" in blob or "akis" in blob:
            adj += 5_000
        if "flow" in blob:
            adj += 5_000
        return (-adj, len(tp), tp)

    return sorted(cands, key=sort_key)


def _log_table_full(cur: Any, node_id: int) -> str | None:
    t = f"log_{int(node_id)}"
    cur.execute(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='noktalog' AND TABLE_NAME=%s",
        (t,),
    )
    if not cur.fetchone():
        return None
    return f"noktalog.`{t}`"


def _norm_date_str(s: str | None) -> str | None:
    t = (s or "").strip()
    return t if t else None


def _log_where_parts(
    log_pid: int,
    months: tuple[int, ...] | None,
    date_from: str | None,
    date_to: str | None,
) -> tuple[list[str], list[Any]]:
    wh = ["logPId=%s"]
    params: list[Any] = [int(log_pid)]
    if months:
        ph = ",".join(["%s"] * len(months))
        wh.append(f"MONTH(logTime) IN ({ph})")
        params.extend(months)
    if date_from:
        wh.append("logTime >= %s")
        params.append(date_from)
    if date_to:
        wh.append("logTime <= %s")
        params.append(date_to)
    return wh, params


def _apply_value_bounds_to_wh(
    wh: list[str], params: list[Any], bounds: tuple[float, float] | None
) -> None:
    if bounds is None:
        return
    lo, hi = bounds
    wh.extend(["tagValue >= %s", "tagValue <= %s"])
    params.extend([lo, hi])


def _span_days(
    cur: Any,
    full: str,
    log_pid: int,
    date_from: str | None = None,
    date_to: str | None = None,
    value_bounds: tuple[float, float] | None = None,
) -> tuple[Any, Any, int]:
    wh, params = _log_where_parts(int(log_pid), None, date_from, date_to)
    _apply_value_bounds_to_wh(wh, params, value_bounds)
    whs = "WHERE " + " AND ".join(wh)
    cur.execute(
        f"SELECT MIN(logTime) AS mn, MAX(logTime) AS mx, COUNT(*) AS c FROM {full} {whs}",
        tuple(params),
    )
    r = cur.fetchone() or {}
    mn, mx = r.get("mn"), r.get("mx")
    if not mn or not mx:
        return mn, mx, 0
    cur.execute(
        f"SELECT DATEDIFF(MAX(logTime), MIN(logTime)) AS d FROM {full} {whs}",
        tuple(params),
    )
    d = int((cur.fetchone() or {}).get("d") or 0)
    return mn, mx, d


def _hourly_profile(
    cur: Any,
    full: str,
    log_pid: int,
    months: tuple[int, ...] | None,
    date_from: str | None = None,
    date_to: str | None = None,
    value_bounds: tuple[float, float] | None = None,
) -> tuple[list[float], list[int]]:
    """24 elemanlı ortalama debi ve her saat için örnek sayısı."""
    wh, params = _log_where_parts(int(log_pid), months, date_from, date_to)
    _apply_value_bounds_to_wh(wh, params, value_bounds)
    whs = "WHERE " + " AND ".join(wh)
    cur.execute(
        f"""
        SELECT HOUR(logTime) AS h,
               AVG(tagValue) AS avg_q,
               COUNT(*) AS cnt
        FROM {full}
        {whs}
        GROUP BY HOUR(logTime)
        ORDER BY h ASC
        """,
        tuple(params),
    )
    rows = {int(r["h"]): (float(r["avg_q"] or 0), int(r["cnt"] or 0)) for r in cur.fetchall()}
    flow = [round(rows.get(h, (0.0, 0))[0], 6) for h in range(24)]
    counts = [rows.get(h, (0.0, 0))[1] for h in range(24)]
    return flow, counts


def _fetch_raw_hour_value_sample(
    cur: Any,
    full: str,
    log_pid: int,
    date_from: str | None,
    date_to: str | None,
    *,
    sample_n: int,
    value_bounds: tuple[float, float] | None = None,
) -> list[tuple[int, float]]:
    """Tez stili scatter: ham log satırları (saat, değer); aralıktan örneklenir."""
    if sample_n <= 0:
        return []
    wh, params = _log_where_parts(int(log_pid), None, date_from, date_to)
    _apply_value_bounds_to_wh(wh, params, value_bounds)
    whs = "WHERE " + " AND ".join(wh)
    fetch_cap = min(40000, max(sample_n * 25, sample_n + 500))
    cur.execute(
        f"""
        SELECT HOUR(logTime) AS h, tagValue AS v
        FROM {full}
        {whs}
        ORDER BY logTime ASC
        LIMIT %s
        """,
        (*params, int(fetch_cap)),
    )
    raw = [(int(r["h"]), float(r["v"] or 0)) for r in cur.fetchall()]
    if len(raw) <= sample_n:
        return raw
    return random.sample(raw, int(sample_n))


def _build_tez_scatter_chart(
    *,
    node_name: str,
    tag_path: str,
    mode: Literal["dma", "level"],
    palette: list[str],
    labels_24: list[int],
    rank_map: dict[int, int],
    medoids_ranked: list[dict[str, Any]],
    raw_points: list[tuple[int, float]],
    date_from: str | None,
    date_to: str | None,
) -> dict[str, Any] | None:
    if not raw_points:
        return None
    unit = "m³/h" if mode == "dma" else "m"
    y_lbl = f"Debi ({unit})" if mode == "dma" else f"Seviye ({unit})"
    data_pts: list[dict[str, Any]] = []
    colors: list[str] = []
    for h, v in raw_points:
        h = int(h) % 24
        j = int(labels_24[h])
        kn = int(rank_map.get(j, j + 1))
        data_pts.append({"x": float(h), "y": round(float(v), 4)})
        colors.append(palette[(kn - 1) % len(palette)])
    med_ds = {
        "label": "Medoid (X)",
        "data": [{"x": float(m["saat"]), "y": float(m["deger"])} for m in medoids_ranked],
        "pointStyle": "cross",
        "pointRadius": 9,
        "borderWidth": 2,
        "borderColor": "#111827",
        "backgroundColor": "#111827",
        "showLine": False,
    }
    aralik = ""
    if date_from or date_to:
        aralik = f" ({date_from or '…'} → {date_to or '…'})"
    gecis = [
        float(h)
        for h in range(1, 24)
        if labels_24[h] != labels_24[h - 1]
    ]
    return {
        "_type": "chart",
        "chart_type": "scatter",
        **koru_mind_tez_scatter_extras(),
        "chart_role_tr": "tez_saat_kume_scatter",
        "title": f"{node_name} — saat–{'debi' if mode == 'dma' else 'seviye'} kümeleri{aralik} [{tag_path}]",
        "x_axis_label_tr": "Günün saati (0–23)",
        "y_axis_label_tr": y_lbl,
        "y_axis_label": y_lbl,
        "yAxisLabel": y_lbl,
        "datasets": [
            {
                "label": "Ölçüm (renk = o saatin K-Means kümesi)",
                "data": data_pts,
                "pointBackgroundColor": colors,
                "pointRadius": 2,
                "showLine": False,
            },
            med_ds,
        ],
        "kume_gecis_saatleri": gecis,
        "koru_mind_chart_js_tr": (
            "Chart.js type scatter; x=saat 0–23, y=ham değer; pointBackgroundColor dizisi hazır. "
            "Dikey kesik çizgiler: kume_gecis_saatleri — annotation plugin xMin/xMax. "
            "Ham zaman serisi (tarih ekseni) değil; tezdeki gibi saat–debi düzlemi."
        ),
        "grafik_sunumu_model_talimat_tr": GRAFIK_SUNUMU_MODEL_TALIMAT_TR,
        "ornek_sayisi": len(raw_points),
    }


def kmeans_1d(x: list[float], k: int, iters: int = 45) -> tuple[list[float], list[int]]:
    """Lloyd; x[i] saat i'deki ortalama debi. k küme merkezi (debiye göre talep bandı)."""
    n = len(x)
    if n == 0 or k <= 0:
        return [], []
    k = min(k, n, 24)
    xs = sorted(x)
    if k == 1:
        c = [sum(x) / n]
        return c, [0] * n
    cent = [xs[int(i * (n - 1) / max(k - 1, 1))] for i in range(k)]
    labels = [0] * n
    for _ in range(iters):
        for i in range(n):
            labels[i] = min(range(k), key=lambda j: (x[i] - cent[j]) ** 2)
        moved = False
        for j in range(k):
            mem = [x[i] for i in range(n) if labels[i] == j]
            if mem:
                nc = sum(mem) / len(mem)
                if abs(nc - cent[j]) > 1e-9:
                    moved = True
                cent[j] = nc
        if not moved:
            break
    return cent, labels


def _cluster_rank_by_centroid(centroids: list[float]) -> dict[int, int]:
    """Ham küme indeksini seviye/değere göre sıralı küme numarasına (1=düşük … k=yüksek) çevir."""
    if not centroids:
        return {}
    order = sorted(range(len(centroids)), key=lambda j: centroids[j])
    return {order[i]: i + 1 for i in range(len(order))}


def _medoid_hour_per_cluster(x: list[float], labels: list[int], k: int) -> list[dict[str, Any]]:
    """1D vektörde her küme için L1 medoid saati (gerçek örnek noktası; tez grafiğindeki X)."""
    out: list[dict[str, Any]] = []
    for j in range(k):
        hours = [h for h in range(len(x)) if labels[h] == j]
        if not hours:
            continue
        best_h = min(hours, key=lambda h: sum(abs(x[h] - x[i]) for i in hours))
        out.append({"ham_kume": j, "saat": best_h, "deger": round(float(x[best_h]), 4)})
    return out


def _bands_from_labels(
    labels: list[int], centroids: list[float], value_key: str = "ortalama_debi_band_araligi"
) -> list[dict[str, Any]]:
    """Küme indeksini ölçüm düzeyine göre sırala (düşük→yüksek)."""
    if not centroids:
        return []
    rank = _cluster_rank_by_centroid(centroids)
    out: list[dict[str, Any]] = []
    for h in range(24):
        j = labels[h]
        row: dict[str, Any] = {
            "saat": h,
            "kume_no": rank.get(j, j + 1),
            "ham_kume": j,
        }
        row[value_key] = round(centroids[j], 4)
        out.append(row)
    return out


def _consecutive_periods_ranked(labels: list[int], rank_map: dict[int, int]) -> list[str]:
    """Ardışık aynı küme saatleri; küme_no = değere göre sıralı etiket (1=düşük … k=yüksek)."""
    if len(labels) != 24:
        return []
    out: list[str] = []
    start = 0
    for h in range(1, 24):
        if labels[h] != labels[start]:
            kn = int(rank_map.get(labels[start], labels[start] + 1))
            out.append(f"{start:02d}:00–{h-1:02d}:59 | küme_no {kn}")
            start = h
    kn = int(rank_map.get(labels[start], labels[start] + 1))
    out.append(f"{start:02d}:00–23:59 | küme_no {kn}")
    return out


def _hour_ranges_tr(hours: list[int]) -> str:
    """[0,1,2,5,6] → 00:00–02:59, 05:00–06:59"""
    if not hours:
        return "—"
    hs = sorted(set(int(h) for h in hours))
    segs: list[tuple[int, int]] = []
    a = b = hs[0]
    for x in hs[1:]:
        if x == b + 1:
            b = x
        else:
            segs.append((a, b))
            a = b = x
    segs.append((a, b))
    parts: list[str] = []
    for a, b in segs:
        if a == b:
            parts.append(f"{a:02d}:00")
        else:
            parts.append(f"{a:02d}:00–{b:02d}:59")
    return ", ".join(parts)


def _clusters_ranked_table(
    use_vec: list[float],
    labels: list[int],
    centroids: list[float],
    rank_map: dict[int, int],
    merkez_alan_adi: str,
) -> list[dict[str, Any]]:
    """Her dolu küme için bir satır; UI/model tüm satırları tabloda gösterebilir."""
    rows: list[dict[str, Any]] = []
    for raw_j in range(len(centroids)):
        hours = [h for h in range(24) if labels[h] == raw_j]
        if not hours:
            continue
        kn = int(rank_map.get(raw_j, raw_j + 1))
        vals = [float(use_vec[h]) for h in hours]
        row: dict[str, Any] = {
            "kume_no": kn,
            "saatler": hours,
            "saat_araliklari_tr": _hour_ranges_tr(hours),
            "olcum_min": round(min(vals), 4),
            "olcum_max": round(max(vals), 4),
        }
        row[merkez_alan_adi] = round(float(centroids[raw_j]), 4)
        rows.append(row)
    rows.sort(key=lambda r: int(r["kume_no"]))
    return rows


def _olcum_kaynagi_seviye_tr(tag_path: str, node_name: str, lp_description: str) -> dict[str, Any]:
    """Tag/node üzerinden ölçünün ne olduğunu netleştir; modelin yanlış fiziksel iddia etmesini azaltır."""
    tp = (tag_path or "").lower()
    nn = (node_name or "").lower()
    ds = (lp_description or "").lower()
    blob = f"{tp} {nn} {ds}"
    etiket_parcalari: list[str] = []
    if "depo" in blob or "tank" in blob:
        etiket_parcalari.append("depo/tank")
    if "kuyu" in blob:
        etiket_parcalari.append("kuyu")
    if "seviye" in blob or "level" in blob:
        etiket_parcalari.append("seviye")
    if "link" in tp or "hat" in blob:
        etiket_parcalari.append("hat/link")

    if "depo" in blob or "tank" in blob:
        anlasilir = "Depo veya tank seviye ölçümü (SCADA tag yolu)"
        fiziksel = (
            "Etikette «depo»/«tank» geçiyor: bu kanal genelde depo/tank sıvı yüksekliğidir; "
            "klasik «kuyu dinamik seviye» (yeraltı suyu) ile aynı şey olmayabilir."
        )
    elif "kuyu" in blob:
        anlasilir = "Kuyu / kuyu ile ilişkili seviye ölçümü"
        fiziksel = "Node veya tag adında kuyu vurgusu var; yorumu kuyu hidroliği ile ilişkilendirmek daha tutarlıdır."
    else:
        anlasilir = "Seviye ölçümü (tag yolundan türetilen genel sınıf)"
        fiziksel = "Etiket depo/kuyu açıkça ayırt etmiyorsa fiziksel anlamı tesis şeması veya operatör onayı ile doğrulayın."

    terminoloji = (
        "Kullanıcı «dinamik seviye» dediğinde bu, yazılımda genel bir ifadedir. "
        f"Bu analizde kullanılan gerçek sinyal: tagPath={tag_path!r}. "
        "Yanıt metninde önce bu etiketi, sonra yorumu kullanın; etiketi gizleyip yalnızca «dinamik seviye» demeyin."
    )
    return {
        "tagPath": tag_path,
        "anlasilir_isim_tr": anlasilir,
        "fiziksel_yorum_tr": fiziksel,
        "terminoloji_notu_tr": terminoloji,
        "etiket_anahtar_kelime_tespiti": etiket_parcalari,
    }


def list_dma_station_nodes_impl(cfg: InstanceConfig, limit: int = 50) -> Any:
    if not cfg.db:
        raise RuntimeError("DB config is missing for this instance.")
    limit = min(max(int(limit), 1), 80)
    sql = """
        SELECT n.id, n.nName, n.nView, n.nPath, n.nType, n.nState, pt.name AS urun_tipi
        FROM kbindb.node n
        LEFT JOIN kbindb.node_product_type pt ON n.nView = pt.nView
        WHERE n.nState IN (-1, 0, 1, 100)
          AND (
            LOWER(COALESCE(n.nView,'')) LIKE '%dma%'
            OR LOWER(COALESCE(n.nName,'')) LIKE '%dma%'
            OR LOWER(COALESCE(n.nPath,'')) LIKE '%dma%'
            OR LOWER(COALESCE(pt.name,'')) LIKE '%dma%'
          )
        ORDER BY n.nName ASC
        LIMIT %s
    """
    with dbmod.connect(cfg.db) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            rows = list(cur.fetchall())
    return {
        "_type": "dma_node_list",
        "adet": len(rows),
        "dma_istasyonlari": rows,
        "not_tr": "nView genelde a-dma-envest, aqua-dma vb. olabilir; tezdeki DMA akış analizi bu düğümlere uygundur.",
    }


def _resolve_node_for_seasonal_profile(
    cur: Any,
    *,
    node_id: int,
    node_adi_ara: str,
    empty_search_err: dict[str, Any],
    no_match_ipucu: str,
) -> tuple[int, dict[str, Any]] | dict[str, Any]:
    nid = int(node_id)
    name_q = (node_adi_ara or "").strip()
    if nid <= 0:
        if not name_q:
            return empty_search_err
        frag = _safe_like_fragment(name_q)
        cur.execute(
            """
            SELECT id, nName, nView FROM kbindb.node
            WHERE nName LIKE %s AND nState IN (-1, 0, 1, 100)
            ORDER BY CHAR_LENGTH(nName) ASC, n.id DESC
            LIMIT 20
            """,
            (f"%{frag}%",),
        )
        matches = list(cur.fetchall())
        if not matches:
            return {"hata": f"«{name_q}» ile eşleşen node yok.", "ipucu": no_match_ipucu}
        if len(matches) > 1:
            return {
                "hata": "Birden fazla node eşleşti; tam nodeId verin veya nodeAdiAra metnini daraltın.",
                "adaylar": [
                    {"id": int(r["id"]), "nName": r.get("nName"), "nView": r.get("nView")}
                    for r in matches[:15]
                ],
            }
        nid = int(matches[0]["id"])
    cur.execute("SELECT id, nName, nView FROM kbindb.node WHERE id=%s", (nid,))
    node = cur.fetchone()
    if not node:
        return {"hata": f"Node {nid} bulunamadı."}
    return (nid, node)


def _seasonal_hourly_kmeans_for_param(
    cur: Any,
    *,
    nid: int,
    node: dict[str, Any],
    mode: Literal["dma", "level"],
    default_tag_hint: str,
    tag_hint: str,
    log_param_id: int,
    k: int,
    min_samples: int,
    uyari_dma: str | None,
    start_date: str = "",
    end_date: str = "",
    max_scatter_points: int = 0,
) -> Any:
    full = _log_table_full(cur, nid)
    if not full:
        return {"hata": "Log tablosu yok."}
    d_from = _norm_date_str(start_date)
    d_to = _norm_date_str(end_date)
    pid = int(log_param_id) if log_param_id else 0
    dma_param_secim_notu: str | None = None
    if pid <= 0:
        hint = (tag_hint or "").strip() or default_tag_hint
        cand_lim = 14 if mode == "level" else 8
        cands = resolve_log_params_by_hint(cur, nid, hint, limit=cand_lim)
        if not cands:
            msg = (
                "Debimetre/akış log parametresi bulunamadı."
                if mode == "dma"
                else "Dinamik seviye / seviye log parametresi bulunamadı."
            )
            return {"hata": msg, "ipucu": "tagHint veya logParamId verin."}
        if mode == "dma":
            prev_first = int(cands[0]["id"])
            cands = _rank_dma_log_candidates(cands)
            new_first = int(cands[0]["id"])
            if prev_first != new_first:
                dma_param_secim_notu = (
                    f"Liste sırası düzeltildi: önceki ilk aday id={prev_first} yerine "
                    f"DMA için daha uygun görülen id={new_first} ({cands[0].get('tagPath')!r}) kullanılıyor. "
                    "Yanlışsa logParamId veya tagHint='Debimetre2' gibi daraltın."
                )
        pid = int(cands[0]["id"])
    else:
        cur.execute(
            "SELECT id, tagPath, description FROM kbindb.logparameters WHERE id=%s AND nid=%s",
            (pid, nid),
        )
        row = cur.fetchone()
        if not row:
            return {"hata": f"logParamId={pid} bu node için yok."}
        cands = [
            {
                "id": int(row["id"]),
                "tagPath": str(row.get("tagPath") or ""),
                "description": str(row.get("description") or ""),
            }
        ]
    debi_aday_sayisi = (
        sum(1 for c in cands if "debi" in (c.get("tagPath") or "").lower()) if mode == "dma" else 0
    )
    cur.execute("SELECT tagPath, description FROM kbindb.logparameters WHERE id=%s", (pid,))
    lp = cur.fetchone() or {}
    tag_path = str(lp.get("tagPath") or "")
    wh_b, pr_b = _log_where_parts(int(pid), None, d_from, d_to)
    whs_b = "WHERE " + " AND ".join(wh_b)
    value_bounds = fetch_log_value_bounds(
        cur, f"SELECT tagValue FROM {full} {whs_b}", tuple(pr_b)
    )
    mn, mx, span_days = _span_days(cur, full, pid, d_from, d_to, value_bounds)
    if span_days <= 0:
        return {"hata": "Bu parametre için log yok (tarih filtresi çok dar olabilir)."}
    yillik_ky = span_days >= 365
    yaz_kis_anlamli = span_days >= _MIN_DAYS_FOR_SEASON_COMPARE
    flow_all, cnt_all = _hourly_profile(cur, full, pid, None, d_from, d_to, value_bounds)
    flow_su, cnt_su = _hourly_profile(cur, full, pid, _SUMMER_MONTHS, d_from, d_to, value_bounds)
    flow_ki, cnt_ki = _hourly_profile(cur, full, pid, _WINTER_MONTHS, d_from, d_to, value_bounds)

    def filt_min(flow: list[float], cnt: list[int]) -> list[float]:
        return [flow[i] if cnt[i] >= min_samples else 0.0 for i in range(24)]

    fa = filt_min(flow_all, cnt_all)
    fs = filt_min(flow_su, cnt_su)
    fw = filt_min(flow_ki, cnt_ki)
    use_vec = fs if yaz_kis_anlamli and sum(cnt_su) > 200 and sum(cnt_ki) > 200 else fa
    centroids, labels = kmeans_1d(use_vec, k)
    band_key = "ortalama_debi_band_araligi" if mode == "dma" else "ortalama_seviye_olcum"
    bands = _bands_from_labels(labels, centroids, value_key=band_key)
    rank_map = _cluster_rank_by_centroid(centroids)
    periods = _consecutive_periods_ranked(labels, rank_map)
    merkez_field_tablo = "merkez_debi" if mode == "dma" else "merkez_seviye"
    kume_tablosu = _clusters_ranked_table(
        use_vec, labels, centroids, rank_map, merkez_field_tablo
    )
    medoids_raw = _medoid_hour_per_cluster(use_vec, labels, len(centroids))
    medoids_ranked = [
        {
            "kume_no": int(rank_map.get(int(m["ham_kume"]), int(m["ham_kume"]) + 1)),
            "saat": int(m["saat"]),
            "deger": m["deger"],
        }
        for m in medoids_raw
    ]
    medoids_ranked.sort(key=lambda r: r["kume_no"])
    # Tez stili scatter: her saat iki mevsim noktası; renk = küme (kümeleme vektörü use_vec'e göre)
    unit_y = "m³/h" if mode == "dma" else "m"
    scatter_points: list[dict[str, Any]] = []
    for h in range(24):
        ku = int(rank_map.get(labels[h], labels[h] + 1))
        row: dict[str, Any] = {
            "saat": h,
            "kume_no": ku,
            "deger_kumeleme": round(float(use_vec[h]), 4),
        }
        if yaz_kis_anlamli:
            row["deger_yaz"] = round(float(fs[h]), 4)
            row["deger_kis"] = round(float(fw[h]), 4)
        else:
            row["deger_tum_veri"] = round(float(fa[h]), 4)
        scatter_points.append(row)
    cluster_colors = [
        "#22c55e",
        "#f97316",
        "#1d4ed8",
        "#38bdf8",
        "#eab308",
        "#ec4899",
        "#ef4444",
        "#a855f7",
        "#14b8a6",
        "#f59e0b",
        "#6366f1",
        "#84cc16",
        "#0ea5e9",
        "#d946ef",
        "#64748b",
        "#78716c",
        "#dc2626",
        "#059669",
    ]
    k_eff = len(centroids)
    palette = [cluster_colors[i % len(cluster_colors)] for i in range(k_eff)]
    raw_scatter: list[tuple[int, float]] = []
    if max_scatter_points > 0:
        raw_scatter = _fetch_raw_hour_value_sample(
            cur,
            full,
            pid,
            d_from,
            d_to,
            sample_n=min(int(max_scatter_points), 20000),
            value_bounds=value_bounds,
        )
    tez_scatter_chart = _build_tez_scatter_chart(
        node_name=str(node.get("nName") or ""),
        tag_path=tag_path,
        mode=mode,
        palette=palette,
        labels_24=labels,
        rank_map=rank_map,
        medoids_ranked=medoids_ranked,
        raw_points=raw_scatter,
        date_from=d_from,
        date_to=d_to,
    )
    kumeleme_kaynak = (
        "yaz_haziran_agustos"
        if yaz_kis_anlamli and sum(cnt_su) > 200 and sum(cnt_ki) > 200
        else "tum_veri"
    )
    tez_grafigi: dict[str, Any] = {
        "baslik_tr": "Saat–ölçüm saçılımı + küme renkleri + medoid (X); tez K-medoids/K-Means görünümüne uygun veri.",
        "kumeleme_algoritma_tr": (
            "Kümeleme: saatlik ortalama vektörü üzerinde 1D K-Means (Lloyd). "
            "Medoid: her kümede gerçek bir saat noktası, L1'de kümenin temsilcisi (grafikte X)."
        ),
        "eksen_x": "Günün saati (0–23)",
        "eksen_y": f"{'Debi' if mode == 'dma' else 'Seviye'} ({unit_y})",
        "kumeleme_kaynak": kumeleme_kaynak,
        "renk_paleti_kume_hex": palette,
        "noktalar": scatter_points,
        "medoid_isaretleri": medoids_ranked,
        "koru_mind_chart_js_tr": (
            "Scatter: Chart.js 'scatter' tipi; data: {{x: saat, y: deger_yaz|deger_kis}}; "
            "pointBackgroundColor: renk_paleti_kume_hex[kume_no-1]. "
            "Medoidlar: ikinci dataset veya annotation plugin ile (saat, deger) konumunda X."
        ),
    }
    per_excerpt = ", ".join(periods[:8]) if periods else "—"
    k_uygulanan = len(centroids)
    lp_desc_full = str(lp.get("description") or "")
    olcum_kaynagi_level: dict[str, Any] | None = None
    if mode == "level":
        olcum_kaynagi_level = _olcum_kaynagi_seviye_tr(
            tag_path, str(node.get("nName") or ""), lp_desc_full
        )
    log_desc_clean = lp_desc_full if not lp_desc_full.startswith("{") else ""
    coklu_aday_uyarisi_tr: str | None = None
    if len(cands) > 1:
        s0, s1 = cands[0].get("match_score"), cands[1].get("match_score")
        if s0 is not None and s1 is not None:
            i0, i1 = int(s0), int(s1)
            if i0 == i1 or (i0 > 0 and 0 <= i0 - i1 <= 2):
                coklu_aday_uyarisi_tr = (
                    f"Birden fazla aday parametre var; otomatik seçilen id={pid}, tagPath={tag_path!r}. "
                    "Skorlar yakınsa yanlış sinyal seçilmiş olabilir; logParamId veya dar tagHint ile doğrulatın."
                )

    if mode == "dma":
        chart_title = f"{node.get('nName')} — DMA saatlik debi profili ({tag_path})"
        result_type = "dma_seasonal_profile"
        tez_tr = (
            "K-Means ile günün zaman dilimlerine bölme ve PRV zaman çizelgesi fikri: "
            "Fatih Kütük LR tezi (DMA SCADA akış verileri). Burada saatlik ortalama debi vektörüne 1D k-ortalama uygulanır."
        )
        ozet_tr = (
            "Saatlik ortalama debiye göre K-Means kümeleri; «bölge» = benzer talep seviyesindeki saat aralıkları "
            f"(özet: {per_excerpt}). Tez: günün dilimleri; fiziksel alt hat debisi değil."
        )
        centroids_key = "kume_merkezleri_debi"
        hourly_key = "saatlik_ortalama_debi"
        lbl_yaz, lbl_kis, lbl_all = (
            "Yaz (Haz–Ağu) ort. debi",
            "Kış (Ara–Şub) ort. debi",
            "Tüm veri — ort. debi (saatlik)",
        )
        ui_hints = [
            "Öncelik: tez_scatter_chart (scatter) — x=saat 0–23, y=ham debi, renk=saat dilimine göre küme; medoid ikinci dataset.",
            "İkinci: kök line chart — 24 saatlik ortalama (yaz/kış veya tüm veri).",
            "Dikey kesik çizgiler: tez_scatter_chart.kume_gecis_saatleri (annotation).",
            "Tablo: kmeans.kumelerin_kume_no_tablosu — tüm küme_no satırları.",
            "Veri < 1 yıl: yaz/kış çizgisi kısıtlı olabilir; startDate/endDate ile son N ay daraltılabilir.",
        ]
    else:
        chart_title = f"{node.get('nName')} — seviye saatlik profil [{tag_path}]"
        result_type = "seasonal_level_profile"
        tez_tr = (
            "Saatlik ortalama seviye vektörü üzerinde 1D K-Means; küme_no düşük = görece alçak ölçüm bandı. "
            "Yıllık düşüş için analyze_log_trend (long_term). Fiziksel anlam (depo vs kuyu) tagPath ve olcum_kaynagi ile hizalanmalıdır."
        )
        ozet_tr = (
            f"Ölçüm kanalı: {tag_path}. Saatlik profile göre K-Means bölgeleri (özet dilimler: {per_excerpt}). "
            "Tam küme listesi: kmeans.kumelerin_kume_no_tablosu — yanıtta tüm satırlar tabloda verilmelidir."
        )
        centroids_key = "kume_merkezleri_seviye"
        hourly_key = "saatlik_ortalama_seviye"
        lbl_yaz, lbl_kis, lbl_all = (
            "Yaz (Haz–Ağu) ort. seviye",
            "Kış (Ara–Şub) ort. seviye",
            "Tüm veri — ort. seviye (saatlik)",
        )
        ui_hints = [
            "Başlıkta ve özetinde parametre.tagPath açık yazılsın; olcum_kaynagi ile depo/kuyu ayrımı kullanıcıya sorulabilsin.",
            "Tez stili: tez_scatter_chart (saat×seviye, küme rengi + medoid X); çizgi özeti kök datasets.",
            "Tablo: kmeans.kumelerin_kume_no_tablosu — tüm küme_no satırları.",
            "Uzun yıllık düşüş: analyze_log_trend analysisMode=long_term.",
        ]

    hourly_block = {
        "tum_veri": fa,
        "yaz_haziran_agustos": fs if yaz_kis_anlamli else None,
        "kis_aralik_subat": fw if yaz_kis_anlamli else None,
        "ornek_sayilari_saat_basi": cnt_all,
    }
    y_axis_kartesyen = f"{'Ortalama debi' if mode == 'dma' else 'Ortalama seviye'} ({unit_y})"
    out: dict[str, Any] = {
        "_type": result_type,
        "olcum_modu": mode,
        "log_deger_temizlik_tr": outlier_filtre_ozet_tr(),
        "tez_referansi_tr": tez_tr,
        "node": {"id": nid, "nName": node.get("nName"), "nView": node.get("nView")},
        "veri_araligi": {
            "ilk": str(mn),
            "son": str(mx),
            "gun_farki": span_days,
            "yillik_karsilastirma_icin_yeterli": yillik_ky,
            "yaz_kis_ayrimi_anlamli": yaz_kis_anlamli,
            "tarih_filtresi": {
                "baslangic": d_from,
                "bitis": d_to,
                "aktif": bool(d_from or d_to),
            },
        },
        "parametre": {
            "id": pid,
            "tagPath": tag_path,
            "log_description": log_desc_clean,
            "adaylar": cands,
        },
        hourly_key: hourly_block,
        "kmeans": {
            "k": k_uygulanan,
            "k_istenen": k,
            centroids_key: [round(c, 4) for c in sorted(centroids)],
            "saat_basina_kume": bands,
            "ardisik_donem_ozeti": periods,
            "kumelerin_kume_no_tablosu": kume_tablosu,
        },
        "tez_grafigi": tez_grafigi,
        **({"tez_scatter_chart": tez_scatter_chart} if tez_scatter_chart else {}),
        "ui_onerileri": {"koru_mind": ui_hints},
        "grafik_sunumu_model_talimat_tr": GRAFIK_SUNUMU_MODEL_TALIMAT_TR,
        "_type_chart": "chart",
        "chart_type": "line",
        **koru_mind_dma_hourly_profile_extras(),
        "title": chart_title,
        "y_axis_label": y_axis_kartesyen,
        "yAxisLabel": y_axis_kartesyen,
        "labels": [f"{h:02d}:00" for h in range(24)],
        "datasets": (
            [
                {
                    "label": lbl_yaz,
                    "data": [round(v, 4) for v in fs],
                    "borderColor": "#f97316",
                    "fill": False,
                    "tension": 0.2,
                },
                {
                    "label": lbl_kis,
                    "data": [round(v, 4) for v in fw],
                    "borderColor": "#3b82f6",
                    "fill": False,
                    "tension": 0.2,
                },
            ]
            if yaz_kis_anlamli
            else [
                {
                    "label": lbl_all,
                    "data": [round(v, 4) for v in fa],
                    "borderColor": "#0d9488" if mode == "level" else "#0ea5e9",
                    "fill": True,
                    "tension": 0.25,
                }
            ]
        ),
        "stats": {
            "pik_saat": int(max(range(24), key=lambda h: fa[h])),
            "dusuk_saat": (
                int(min(valid_h, key=lambda h: fa[h]))
                if (valid_h := [h for h in range(24) if cnt_all[h] > 0])
                else 0
            ),
        },
    }
    if tez_scatter_chart:
        out["grafik_oncelik_model_talimat_tr"] = (
            "Tez tarzı saat–ölçüm düzlemi (kümelere göre renkli noktalar + medoid X): tez_scatter_chart. "
            "get_chart_data / get_node_log_chart_data tarih eksenli ham seridir; debi «bölgeleri» grafiği değildir. "
            "24 saatlik özet çizgisi: kökteki line chart (datasets)."
        )
    out["dusunce_dongusu_kes_model_talimat_tr"] = DUSUNCE_DONGUSU_KES_MODEL_TALIMAT_TR
    if mode == "dma":
        out["dma_grafik_ve_dongu_model_talimat_tr"] = DMA_ANALIZ_SONRASI_GRAFIK_TALIMAT_TR
    else:
        out["seviye_grafik_ve_dongu_model_talimat_tr"] = SEVIYE_ANALIZ_SONRASI_GRAFIK_TALIMAT_TR
    if coklu_aday_uyarisi_tr:
        out["parametre_secim_uyarisi_tr"] = coklu_aday_uyarisi_tr
    if mode == "level" and olcum_kaynagi_level:
        out["olcum_kaynagi"] = olcum_kaynagi_level
        out["model_talimat_tr"] = (
            "Önce seviye_grafik_ve_dongu_model_talimat_tr ve dusunce_dongusu_kes_model_talimat_tr. "
            "Zorunlu: İlk cümlede parametre.tagPath ve olcum_kaynagi.anlasilir_isim_tr ile hangi SCADA sinyalinin kullanıldığını yazın. "
            "Kullanıcı «dinamik seviye» dediyse etiket farklıysa (ör. DepoSeviye) olcum_kaynagi.terminoloji_notu_tr ve fiziksel_yorum_tr'yu açıkça aktarın; "
            "depo ile kuyu seviyesini birbirine karıştırmayın. "
            f"kmeans.kumelerin_kume_no_tablosu içindeki {len(kume_tablosu)} satırın TAMAMINI tablo olarak verin "
            "(k satırına indirgeme yok; iki–üç «bölge» özetine sıkıştırmayın). "
            "ardisik_donem_ozeti tüm saat dilimlerini içerir. "
            "Yanıt sonunda kullanıcıdan parametre (logParamId) veya kClusters doğrulaması isteyin: kullanici_dogrulama_tr."
        )
        out["kullanici_dogrulama_tr"] = {
            "secili_parametre": {"logParamId": pid, "tagPath": tag_path},
            "kume_sayisi": {"k_istenen": k, "k_uygulanan": k_uygulanan},
            "sorulacak_kisa_tr": (
                "Bu tag (ör. depo seviyesi) sizin kastettiğiniz ölçüm mü? "
                "Değilse aynı aracı logParamId veya tagHint ile yeniden çağırın. "
                "Küme sayısı için kClusters=6…18 verebilirsiniz."
            ),
        }
    if mode == "dma":
        out["debi_bolgeleri_ozet_tr"] = ozet_tr
        out["uyari_dma"] = uyari_dma
        if dma_param_secim_notu:
            out["parametre_secim_aciklamasi_tr"] = dma_param_secim_notu
        if debi_aday_sayisi > 1:
            out["birden_fazla_debi_uyarisi_tr"] = (
                f"Bu node’da tag yolunda «debi» geçen {debi_aday_sayisi} parametre var (ör. Debimetre / Debimetre2). "
                "Hangi debimetrenin DMA için geçerli olduğunu kullanıcıdan doğrulayın veya logParamId ile sabitleyin."
            )
        out["model_talimat_tr"] = (
            "Önce dma_grafik_ve_dongu_model_talimat_tr ve dusunce_dongusu_kes_model_talimat_tr uygulayın (grafik isteğinde ek araç yok). "
            f"parametre.tagPath ile debi kanalını söyleyin. kmeans.kumelerin_kume_no_tablosu ({len(kume_tablosu)} satır) tam tablo. "
            "birden_fazla_debi_uyarisi_tr varsa logParamId doğrulatın."
        )
    else:
        out["seviye_bolgeleri_ozet_tr"] = ozet_tr
        out["iliskili_arac_tr"] = "Yıllara sari seviye düşüşü: analyze_log_trend (long_term); debi DMA: analyze_dma_seasonal_demand."
    return out


def analyze_dma_seasonal_demand_impl(
    cfg: InstanceConfig,
    nodeId: int = 0,
    nodeAdiAra: str = "",
    tagHint: str = "",
    logParamId: int = 0,
    kClusters: int = 12,
    minSamplesPerHour: int = 2,
    startDate: str = "",
    endDate: str = "",
    maxScatterPoints: int = 3500,
) -> Any:
    """Debimetre logunda saatlik ortalama; yaz/kış; K-Means; tez scatter (isteğe bağlı tarih aralığı)."""
    if not cfg.db:
        raise RuntimeError("DB config is missing for this instance.")
    k = min(max(int(kClusters), 3), 18)
    empty_err = {
        "hata": "nodeId > 0 veya nodeAdiAra gerekli (ör. nodeAdiAra='Kale - 12').",
        "model_talimat_tr": (
            "Kullanıcı «debi bölgeleri», «K-Means», «tez gibi saatlik dilimler» derse bu aracı çağırın. "
            "Son N ay için startDate/endDate verin; tez tarzı scatter: yanıttaki tez_scatter_chart (get_chart_data ile karıştırmayın). "
            "Birden fazla debimetre: logParamId veya tagHint='Debimetre2'. Dinamik seviye: analyze_seasonal_level_profile."
        ),
    }
    with dbmod.connect(cfg.db) as conn:
        with conn.cursor() as cur:
            resolved = _resolve_node_for_seasonal_profile(
                cur,
                node_id=nodeId,
                node_adi_ara=nodeAdiAra,
                empty_search_err=empty_err,
                no_match_ipucu="find_nodes_by_keywords veya list_dma_station_nodes",
            )
            if isinstance(resolved, dict):
                return resolved
            nid, node = resolved
            n_view = str(node.get("nView") or "").lower()
            uyari_dma = None
            if "dma" not in n_view and "dma" not in str(node.get("nName") or "").lower():
                uyari_dma = (
                    "Bu node nView/nName içinde «dma» geçmiyor; analiz yine debimetre üzerinden yapıldı. "
                    "list_dma_station_nodes ile DMA düğümlerini listeleyebilirsiniz."
                )
            return _seasonal_hourly_kmeans_for_param(
                cur,
                nid=nid,
                node=node,
                mode="dma",
                default_tag_hint=DEFAULT_DMA_DEBI_HINT,
                tag_hint=tagHint,
                log_param_id=logParamId,
                k=k,
                min_samples=minSamplesPerHour,
                uyari_dma=uyari_dma,
                start_date=startDate,
                end_date=endDate,
                max_scatter_points=max(0, int(maxScatterPoints)),
            )


def analyze_seasonal_level_profile_impl(
    cfg: InstanceConfig,
    nodeId: int = 0,
    nodeAdiAra: str = "",
    tagHint: str = "",
    logParamId: int = 0,
    kClusters: int = 12,
    minSamplesPerHour: int = 2,
    startDate: str = "",
    endDate: str = "",
    maxScatterPoints: int = 2500,
) -> Any:
    """Dinamik seviye logu: saatlik ortalama, yaz/kış, K-Means; tez scatter isteğe bağlı."""
    if not cfg.db:
        raise RuntimeError("DB config is missing for this instance.")
    k = min(max(int(kClusters), 3), 18)
    empty_err = {
        "hata": "nodeId > 0 veya nodeAdiAra gerekli.",
        "model_talimat_tr": (
            "Dinamik / kuyu / depo seviyesi için bu araç. Yanlış sinyal seçimini önlemek için mümkünse tagHint "
            "(ör. depo, kuyu, tag yolu parçası) veya logParamId verin. "
            "Yanıtta model tüm kmeans.kumelerin_kume_no_tablosu satırlarını tabloda vermeli; kısa «3 bölge» özetine düşmemeli."
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
            return _seasonal_hourly_kmeans_for_param(
                cur,
                nid=nid,
                node=node,
                mode="level",
                default_tag_hint=DEFAULT_LEVEL_HINT,
                tag_hint=tagHint,
                log_param_id=logParamId,
                k=k,
                min_samples=minSamplesPerHour,
                uyari_dma=None,
                start_date=startDate,
                end_date=endDate,
                max_scatter_points=max(0, int(maxScatterPoints)),
            )
