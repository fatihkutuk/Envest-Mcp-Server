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
            minPressure: float = 0.0,
            maxPressure: float = 0.0,
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
                minPressure=minPressure,
                maxPressure=maxPressure,
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
            minPressure: float = 0.0,
            maxPressure: float = 0.0,
        ) -> str:
            """DMA debi bolgeleri K-Means analizi (Fatih Kutuk LR tezi: saatlik ortalama, yaz-kis, scatter).

            PARAMETRE KULLANIM KURALLARI (kritik):

            - kClusters: VARSAYILAN 12. Kullanici acikca "N bolgeye ayir / N kumeli"
              demedikce 12 birak. Kendi kafandan 6 veya 8 gecme.

            - startDate/endDate: Bos birakirsan tool otomatik son 30 gun kullanir. Kullanici
              "son X ay" / "Y-Z tarihleri arasi" demedikce bos gecebilirsin.

            - minPressure/maxPressure: SADECE kullanici sayisal bir band verdiginde (ornek:
              "3-5 bar", "4 ile 6 bar arasina olcekle") bu parametreleri gec. Kullanici
              sadece "basinc bolgelerini belirle" dediyse: BAND UYDURMAA — parametresiz
              cagir. Tool node'un basinc sensor log'undan min/max'i otomatik tespit edecek
              (ciktida `tez_basinc_ayarlama.kaynak = "sensor_log"` ve
              `otomatik_basinc_bandi.tagPath` bunu belgeler).

            Cikti:
            - `tez_basinc_ayarlama.calisma_tablosu` varsa tezdeki Tablo 3.3 formatinda
              (zaman dilimi, baslangic saat:dk, bitis saat:dk, debi, basinc_set_bar)
              TAMAMINI tablo olarak verin.
            - `kullanici_basinc_bandi_sorusu_tr` varsa: sensor bulunamamis, kullaniciya
              min/max bar isteyin; TABLO UYDURMAYIN.
            - `basinc_sensor_tarama_tr.taranan_adaylar` hangi tag'lerin arandigini gosterir.
            """
            return guard(tool, _analyze_dma_seasonal_demand_impl_w)(
                nodeId, nodeAdiAra, tagHint, logParamId,
                kClusters, minSamplesPerHour, startDate, endDate, maxScatterPoints,
                minPressure, maxPressure,
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
