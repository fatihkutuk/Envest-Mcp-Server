"""
Birden fazla log parametresi için ortak zaman kovası (bucket) hizalaması.
get_multi_chart_data eskiden yalnızca ilk serinin etiketlerini kullanıyordu; seriler kayıyordu.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .log_value_cleanup import fetch_log_value_bounds


def _where_pid_range(pid: int, start: str, end: str) -> tuple[list[str], list[Any]]:
    wh = ["l.logPId = %s"]
    params: list[Any] = [int(pid)]
    if (start or "").strip():
        wh.append("l.logTime >= %s")
        params.append(start.strip())
    if (end or "").strip():
        wh.append("l.logTime <= %s")
        params.append(end.strip())
    return wh, params


def fetch_bucket_rows_for_param(
    cur: Any,
    full: str,
    pid: int,
    start: str,
    end: str,
    bucket_sec: int,
) -> list[dict[str, Any]]:
    wh, params = _where_pid_range(pid, start, end)
    wh0 = "WHERE " + " AND ".join(wh)
    vb = fetch_log_value_bounds(cur, f"SELECT tagValue FROM {full} l {wh0}", tuple(params))
    if vb:
        lo, hi = vb
        wh.extend(["l.tagValue >= %s", "l.tagValue <= %s"])
        params.extend([lo, hi])
    whs = "WHERE " + " AND ".join(wh)
    cur.execute(
        f"""
        SELECT FLOOR(UNIX_TIMESTAMP(l.logTime) / %s) AS bi,
               ROUND(AVG(l.tagValue), 5) AS tagValue,
               MIN(l.logTime) AS logTime,
               COUNT(*) AS n
        FROM {full} l
        {whs}
        GROUP BY bi
        ORDER BY bi ASC
        """,
        (*params, int(bucket_sec)),
    )
    return list(cur.fetchall())


def aligned_multi_log_series(
    cur: Any,
    full: str,
    pids: list[int],
    start: str,
    end: str,
    max_pts: int,
) -> dict[str, Any] | None:
    """
    Tüm pid'ler için aynı bucket_sec; birleşik bi indeksleri üzerinde hizalı değer listeleri.
    Dönüş: labels, values_per_param (her biri len(labels) kadar, eksik kovada None), bucket_seconds, total_rows.
    """
    pids_u = [int(p) for p in pids if int(p) > 0]
    if not pids_u:
        return None
    mp = max(20, min(600, int(max_pts)))
    ph = ",".join(["%s"] * len(pids_u))
    wh_both = [f"l.logPId IN ({ph})"]
    params: list[Any] = list(pids_u)
    if (start or "").strip():
        wh_both.append("l.logTime >= %s")
        params.append(start.strip())
    if (end or "").strip():
        wh_both.append("l.logTime <= %s")
        params.append(end.strip())
    whs = "WHERE " + " AND ".join(wh_both)
    cur.execute(
        f"SELECT MIN(logTime) AS mn, MAX(logTime) AS mx, COUNT(*) AS c FROM {full} l {whs}",
        tuple(params),
    )
    span = cur.fetchone() or {}
    mn, mx = span.get("mn"), span.get("mx")
    total = int(span.get("c") or 0)
    if not mn or not mx or total == 0:
        return None
    try:
        min_ts = int(datetime.fromisoformat(str(mn).replace("Z", "+00:00")).timestamp())
        max_ts = int(datetime.fromisoformat(str(mx).replace("Z", "+00:00")).timestamp())
    except Exception:
        return None
    span_sec = max(1, max_ts - min_ts)
    bucket_sec = max(1, span_sec // mp)

    row_maps: list[dict[int, dict[str, Any]]] = []
    for pid in pids_u:
        rows = fetch_bucket_rows_for_param(cur, full, pid, start, end, bucket_sec)
        row_maps.append({int(r["bi"]): r for r in rows})

    all_bi: set[int] = set()
    for m in row_maps:
        all_bi |= set(m.keys())
    all_bi_sorted = sorted(all_bi)
    if len(all_bi_sorted) > mp:
        all_bi_sorted = all_bi_sorted[-mp:]

    labels: list[str] = []
    values_per_param: list[list[float | None]] = [[] for _ in pids_u]
    for bi in all_bi_sorted:
        ref = None
        for m in row_maps:
            if bi in m:
                ref = m[bi]
                break
        lt = (ref or {}).get("logTime")
        labels.append(str(lt) if lt is not None else str(bi))
        for i, m in enumerate(row_maps):
            r = m.get(bi)
            values_per_param[i].append(float(r["tagValue"]) if r else None)

    return {
        "labels": labels,
        "values_per_param": values_per_param,
        "bucket_seconds": bucket_sec,
        "total_rows": total,
    }
