"""
KoruMind istemcisi için _type: chart JSON alanları (server/docs/MCP-CHART-WIDGET.md ile uyum).
"""

from __future__ import annotations

from typing import Any

# Chart.js kök türleri + MCP özel scatter
_TR_CHART_ALIASES: dict[str, str] = {
    "pasta": "pie",
    "halka": "doughnut",
    "donut": "doughnut",
    "kutupsal": "polarArea",
    "cubuk": "bar",
    "çizgi": "line",
    "cizgi": "line",
}
_VALID_CHART_JS: frozenset[str] = frozenset(
    {"line", "bar", "pie", "doughnut", "polarArea", "radar", "scatter"}
)


def normalize_chart_js_type(chart_type: str | None, *, default: str = "line") -> str:
    """Türkçe takma adları ve bilinmeyen değerleri Chart.js türüne çevir."""
    s = (chart_type or default).strip().lower()
    s = _TR_CHART_ALIASES.get(s, s)
    if s not in _VALID_CHART_JS:
        return default
    return s


_COKULU_LOG_MODEL_TALIMAT_TR = (
    "Bu yanıt tarih ekseninde birden fazla log serisidir (labels = zaman, datasets = parametreler). "
    "Model ve arayüz: varsayılan çizgi veya BAR (zaman eksenli) kullanın. "
    "PASTA / HALKA / KUTUPSAL ALAN kullanmayın — bu türler bu veri şekli için yanlıştır ve yanıltıcı özet üretir. "
    "Üst araç çubuğunda yalnızca line ve bar arasında geçiş uygun. "
    "İki parametre (ör. debi + güç) farklı birimdeyse ve çift eksen isteniyorsa: compare_log_metrics aracı daha uygundur."
)


def koru_mind_log_timeseries_extras(chart_type: str | None) -> dict[str, Any]:
    """
    Tarih eksenli ham log: pasta/radar ve saat-küme sentezi istenmez (KoruMind series_kind=log).
    """
    ct = normalize_chart_js_type(chart_type, default="line")
    return {
        "series_kind": "log",
        "chart_type": ct,
        "chart_js_type": ct,
        "chart_alternates": ["line", "bar"],
    }


def koru_mind_coklu_log_chart_extras(chart_type: str | None) -> dict[str, Any]:
    """get_multi_chart_data: hizalı çoklu zaman serisi; pasta sentezi yasak."""
    ex = koru_mind_log_timeseries_extras(chart_type)
    ex["chart_alternates"] = ["line", "bar"]
    ex["coklu_log_grafik_model_talimat_tr"] = _COKULU_LOG_MODEL_TALIMAT_TR
    ex["chart_roots_skip_auto_pie_tr"] = True
    ex["koru_mind_disallowed_chart_types_for_this_payload"] = ["pie", "doughnut", "polarArea"]
    return ex


def koru_mind_dma_hourly_profile_extras() -> dict[str, Any]:
    """24 saatlik ortalama profil (tarih ekseni değil); series_kind log kullanılmaz."""
    return {
        "chart_js_type": "line",
        "chart_alternates": ["line", "bar", "radar"],
    }


def koru_mind_tez_scatter_extras() -> dict[str, Any]:
    """Saat×değer scatter + medoid; ham log zaman serisi değil."""
    return {
        "chart_js_type": "scatter",
        "chart_alternates": ["scatter", "line", "bar"],
    }
