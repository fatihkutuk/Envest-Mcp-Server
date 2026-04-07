"""
Log tagValue outlier reduction: winsorize extreme highs/lows using percentile
bounds from a sample set, or produce SQL filter bounds.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Sequence

logger = logging.getLogger("scada_mcp.log_value_cleanup")

# Settings: narrow range = aggressive cleanup; wide = more raw data kept.
_P_LOW = 1.0
_P_HIGH = 99.0
_MIN_VALUES_FOR_CLEAN = 25
_DEFAULT_SAMPLE_LIMIT = 8000


def percentile_bounds(
    values: Sequence[float],
    *,
    low_pct: float = _P_LOW,
    high_pct: float = _P_HIGH,
    min_count: int = _MIN_VALUES_FOR_CLEAN,
) -> tuple[float, float] | None:
    """Return lower/upper bounds from sample; None if too few points."""
    xs = [
        float(x)
        for x in values
        if x is not None and not (isinstance(x, float) and math.isnan(x))
    ]
    if len(xs) < min_count:
        return None
    xs.sort()
    n = len(xs)
    il = int(round((low_pct / 100.0) * (n - 1)))
    ih = int(round((high_pct / 100.0) * (n - 1)))
    il = max(0, min(il, n - 1))
    ih = max(0, min(ih, n - 1))
    if il > ih:
        il, ih = ih, il
    lo, hi = xs[il], xs[ih]
    if abs(hi - lo) < 1e-12:
        pad = max(abs(lo) * 1e-6, 1e-6)
        lo -= pad
        hi += pad
    return (lo, hi)


def winsorize_float_series(
    values: list[float],
    *,
    low_pct: float = _P_LOW,
    high_pct: float = _P_HIGH,
    min_count: int = _MIN_VALUES_FOR_CLEAN,
) -> list[float]:
    b = percentile_bounds(values, low_pct=low_pct, high_pct=high_pct, min_count=min_count)
    if b is None:
        return list(values)
    lo, hi = b
    return [min(hi, max(lo, float(v))) for v in values]


def winsorize_tagvalue_rows(
    rows: list[dict[str, Any]],
    *,
    value_key: str = "tagValue",
    low_pct: float = _P_LOW,
    high_pct: float = _P_HIGH,
    min_count: int = _MIN_VALUES_FOR_CLEAN,
) -> list[dict[str, Any]]:
    """Row copy; tagValue winsorized (for charts/exports)."""
    if not rows:
        return rows
    vals: list[float] = []
    for r in rows:
        try:
            vals.append(float(r.get(value_key) or 0))
        except (TypeError, ValueError):
            vals.append(0.0)
    b = percentile_bounds(vals, low_pct=low_pct, high_pct=high_pct, min_count=min_count)
    if b is None:
        return rows
    lo, hi = b
    out: list[dict[str, Any]] = []
    for r in rows:
        rr = dict(r)
        try:
            v = float(r.get(value_key) or 0)
            rr[value_key] = round(min(hi, max(lo, v)), 6)
        except (TypeError, ValueError):
            pass
        out.append(rr)
    return out


def fetch_log_value_bounds(
    cur: Any,
    tagvalue_select_sql: str,
    params: tuple[Any, ...],
    *,
    sample_limit: int = _DEFAULT_SAMPLE_LIMIT,
) -> tuple[float, float] | None:
    """
    tagvalue_select_sql: 'SELECT tagValue FROM ... WHERE ...' (no ORDER BY/LIMIT).
    Samples last N records; returns percentile bounds.
    """
    cur.execute(
        tagvalue_select_sql + " ORDER BY logTime DESC LIMIT %s",
        (*params, int(sample_limit)),
    )
    vals: list[float] = []
    for r in cur.fetchall():
        try:
            vals.append(float(r.get("tagValue") if isinstance(r, dict) else r[0]))
        except (TypeError, ValueError, KeyError, IndexError):
            continue
    return percentile_bounds(vals)


def outlier_filtre_ozet_tr() -> str:
    return (
        f"Log values: P{_P_LOW}-P{_P_HIGH} bounds from last ~{_DEFAULT_SAMPLE_LIMIT} records; "
        "outlier rows excluded from SQL averages, chart rows are winsorized."
    )
