"""DMA analysis, demand profiling, K-Means clustering, seasonal level profile."""
from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..tools.core import guard, prefixed_name
from ..dma_demand import (
    analyze_dma_seasonal_demand_impl,
    analyze_seasonal_level_profile_impl,
    list_dma_station_nodes_impl,
)
from ..types import InstanceConfig

log = logging.getLogger(__name__)


class ScadaDmaPack:
    """DMA analysis, demand profiling, K-Means clustering."""

    id = "scada_dma"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix

        # --- list_dma_station_nodes ---
        tool = prefixed_name(prefix, "list_dma_station_nodes")

        def _list_dma_station_nodes_impl_w(limit: int = 50) -> Any:
            return list_dma_station_nodes_impl(cfg, limit)

        @mcp.tool(name=tool)
        def list_dma_station_nodes(limit: int = 50) -> str:
            """DMA istasyon listesi (nView, ürün tipi, isim). Saatlik debi/K-Means analizi: analyze_dma_seasonal_demand."""
            return guard(tool, _list_dma_station_nodes_impl_w)(limit)

        # --- analyze_dma_seasonal_demand ---
        tool = prefixed_name(prefix, "analyze_dma_seasonal_demand")

        def _analyze_dma_seasonal_demand_impl_w(
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
            return analyze_dma_seasonal_demand_impl(
                cfg,
                nodeId,
                nodeAdiAra=nodeAdiAra,
                tagHint=tagHint,
                logParamId=logParamId,
                kClusters=kClusters,
                minSamplesPerHour=minSamplesPerHour,
                startDate=startDate,
                endDate=endDate,
                maxScatterPoints=maxScatterPoints,
            )

        @mcp.tool(name=tool)
        def analyze_dma_seasonal_demand(
            nodeId: int = 0,
            nodeAdiAra: str = "",
            tagHint: str = "",
            logParamId: int = 0,
            kClusters: int = 12,
            minSamplesPerHour: int = 2,
            startDate: str = "",
            endDate: str = "",
            maxScatterPoints: int = 3500,
        ) -> str:
            """DMA debi bolgeleri K-Means analizi (saatlik ortalama, yaz-kis, scatter chart). startDate/endDate ile aralik daraltma."""
            return guard(tool, _analyze_dma_seasonal_demand_impl_w)(
                nodeId, nodeAdiAra, tagHint, logParamId,
                kClusters, minSamplesPerHour, startDate, endDate, maxScatterPoints,
            )

        # --- analyze_seasonal_level_profile ---
        tool = prefixed_name(prefix, "analyze_seasonal_level_profile")

        def _analyze_seasonal_level_profile_impl_w(
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
            return analyze_seasonal_level_profile_impl(
                cfg,
                nodeId,
                nodeAdiAra=nodeAdiAra,
                tagHint=tagHint,
                logParamId=logParamId,
                kClusters=kClusters,
                minSamplesPerHour=minSamplesPerHour,
                startDate=startDate,
                endDate=endDate,
                maxScatterPoints=maxScatterPoints,
            )

        @mcp.tool(name=tool)
        def analyze_seasonal_level_profile(
            nodeId: int = 0,
            nodeAdiAra: str = "",
            tagHint: str = "",
            logParamId: int = 0,
            kClusters: int = 12,
            minSamplesPerHour: int = 2,
            startDate: str = "",
            endDate: str = "",
            maxScatterPoints: int = 2500,
        ) -> str:
            """Seviye profili (kuyu/depo): saatlik ortalama + yaz/kis + K-Means scatter."""
            return guard(tool, _analyze_seasonal_level_profile_impl_w)(
                nodeId, nodeAdiAra, tagHint, logParamId,
                kClusters, minSamplesPerHour, startDate, endDate, maxScatterPoints,
            )

    def manifest_groups(self, *, prefix: str) -> list[dict]:
        p = prefix
        return [
            {
                "id": "dma",
                "title_tr": "DMA / mevsimsel analiz",
                "tools": [
                    p + "list_dma_station_nodes",
                    p + "analyze_dma_seasonal_demand",
                    p + "analyze_seasonal_level_profile",
                ],
            },
        ]
