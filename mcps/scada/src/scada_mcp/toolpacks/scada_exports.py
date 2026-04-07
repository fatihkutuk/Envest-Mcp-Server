"""File export tools: reports, custom exports, alarm exports."""
from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..export_files import (
    export_active_alarms_impl,
    export_custom_data_impl,
    export_log_data_impl,
    generate_node_report_impl,
    generate_scada_report_impl,
)
from ..tools.core import guard, prefixed_name
from ..types import InstanceConfig

log = logging.getLogger(__name__)


class ScadaExportsPack:
    """File export tools (Excel, PDF, CSV, JSON)."""

    id = "scada_exports"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix

        # --- export_log_data ---
        tool = prefixed_name(prefix, "export_log_data")

        def _export_log_data_impl_w(
            nodeId: int,
            format: str = "xlsx",
            startDate: str = "",
            endDate: str = "",
            logParamIds: str = "",
        ) -> Any:
            return export_log_data_impl(cfg, nodeId, format, startDate, endDate, logParamIds)

        @mcp.tool(name=tool)
        def export_log_data(
            nodeId: int,
            format: str = "xlsx",
            startDate: str = "",
            endDate: str = "",
            logParamIds: str = "",
        ) -> str:
            """Node log verisini Excel (.xlsx), CSV veya JSON dosyası olarak üretir; sonuçta _type=file ve filepath döner."""
            return guard(tool, _export_log_data_impl_w)(nodeId, format, startDate, endDate, logParamIds)

        # --- generate_scada_report ---
        tool = prefixed_name(prefix, "generate_scada_report")

        def _generate_scada_report_impl_wrapped(format: str = "pdf") -> Any:
            return generate_scada_report_impl(cfg, format)

        @mcp.tool(name=tool)
        def generate_scada_report(format: str = "pdf") -> str:
            """SCADA özet raporu PDF veya Word (.docx)."""
            return guard(tool, _generate_scada_report_impl_wrapped)(format)

        # --- generate_node_report ---
        tool = prefixed_name(prefix, "generate_node_report")

        def _generate_node_report_impl_wrapped(nodeId: int, format: str = "pdf") -> Any:
            return generate_node_report_impl(cfg, nodeId, format)

        @mcp.tool(name=tool)
        def generate_node_report(nodeId: int, format: str = "pdf") -> str:
            """Tek node için detaylı rapor (PDF veya DOCX): canlı taglar, alarmlar, log parametreleri."""
            return guard(tool, _generate_node_report_impl_wrapped)(nodeId, format)

        # --- export_custom_data ---
        tool = prefixed_name(prefix, "export_custom_data")

        def _export_custom_data_impl_wrapped(
            title: str,
            headers: str,
            rowsJson: str = "",
            format: str = "xlsx",
            rows_json: str = "",
        ) -> Any:
            rj = (rowsJson or rows_json or "").strip()
            return export_custom_data_impl(cfg, title, headers, rj, format)

        @mcp.tool(name=tool)
        def export_custom_data(
            title: str,
            headers: str,
            rowsJson: str = "",
            format: str = "xlsx",
            rows_json: str = "",
        ) -> str:
            """Genel amacli tablo export (Excel/CSV/JSON/PDF). headers: virgul ayrili sutun adlari, rowsJson: JSON array."""
            return guard(tool, _export_custom_data_impl_wrapped)(title, headers, rowsJson, format, rows_json)

        # --- export_active_alarms ---
        tool = prefixed_name(prefix, "export_active_alarms")

        def _export_active_alarms_impl_wrapped(format: str = "xlsx", limit: int = 500) -> Any:
            return export_active_alarms_impl(cfg, format, limit)

        @mcp.tool(name=tool)
        def export_active_alarms(format: str = "xlsx", limit: int = 500) -> str:
            """Aktif alarmları Excel veya CSV dosyası olarak dışa aktarır."""
            return guard(tool, _export_active_alarms_impl_wrapped)(format, limit)

    def manifest_groups(self, *, prefix: str) -> list[dict]:
        p = prefix
        return [
            {
                "id": "export_reports",
                "title_tr": "Export / raporlar (Excel PDF CSV)",
                "tools": [
                    p + "export_log_data",
                    p + "generate_scada_report",
                    p + "generate_node_report",
                    p + "export_custom_data",
                    p + "export_active_alarms",
                ],
            },
        ]
