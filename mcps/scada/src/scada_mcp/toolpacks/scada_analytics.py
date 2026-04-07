"""Trend analysis, metric comparison, pump aging analytics."""
from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..compare_log_metrics import compare_log_metrics_impl
from ..tools.core import guard, prefixed_name
from ..trend_analysis import analyze_log_trend_impl
from ..types import InstanceConfig

log = logging.getLogger(__name__)


class ScadaAnalyticsPack:
    """Trend analysis, seasonal profiles, metric comparison."""

    id = "scada_analytics"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix

        # --- compare_log_metrics ---
        tool = prefixed_name(prefix, "compare_log_metrics")

        def _compare_log_metrics_impl_w(
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
            return compare_log_metrics_impl(
                cfg,
                nodeId=nodeId,
                nodeAdiAra=nodeAdiAra,
                primaryTagHint=primaryTagHint,
                secondaryTagHint=secondaryTagHint,
                primaryLogParamId=primaryLogParamId,
                secondaryLogParamId=secondaryLogParamId,
                startDate=startDate,
                endDate=endDate,
                maxChartPoints=maxChartPoints,
                chartType=chartType,
                karsilastirmaAciklamasi=karsilastirmaAciklamasi,
            )

        @mcp.tool(name=tool)
        def compare_log_metrics(
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
        ) -> str:
            """Iki log parametresini hizalar (orn. debi + guc). Cift Y ekseni onerilir."""
            return guard(tool, _compare_log_metrics_impl_w)(
                nodeId, nodeAdiAra, primaryTagHint, secondaryTagHint,
                primaryLogParamId, secondaryLogParamId,
                startDate, endDate, maxChartPoints, chartType, karsilastirmaAciklamasi,
            )

        # --- analyze_log_trend ---
        tool = prefixed_name(prefix, "analyze_log_trend")

        def _analyze_log_trend_impl_w(
            nodeId: int,
            tagHint: str = "",
            logParamId: int = 0,
            analysisMode: str = "auto",
            startDate: str = "",
            endDate: str = "",
            longTermGranularity: str = "month",
            maxChartPoints: int = 120,
        ) -> Any:
            return analyze_log_trend_impl(
                cfg,
                nodeId,
                tagHint=tagHint,
                logParamId=logParamId,
                analysisMode=analysisMode,
                startDate=startDate,
                endDate=endDate,
                longTermGranularity=longTermGranularity,
                maxChartPoints=maxChartPoints,
            )

        @mcp.tool(name=tool)
        def analyze_log_trend(
            nodeId: int,
            tagHint: str = "",
            logParamId: int = 0,
            analysisMode: str = "auto",
            startDate: str = "",
            endDate: str = "",
            longTermGranularity: str = "month",
            maxChartPoints: int = 120,
        ) -> str:
            """Trend analizi (auto/long_term/pressure_plateau). Dogal dil ile parametre secimi destekler."""
            return guard(tool, _analyze_log_trend_impl_w)(
                nodeId, tagHint, logParamId, analysisMode,
                startDate, endDate, longTermGranularity, maxChartPoints,
            )

    def manifest_groups(self, *, prefix: str) -> list[dict]:
        p = prefix
        return [
            {
                "id": "analytics",
                "title_tr": "Trend / karşılaştırma analizi",
                "tools": [
                    p + "compare_log_metrics",
                    p + "analyze_log_trend",
                ],
            },
        ]
