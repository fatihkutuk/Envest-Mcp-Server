"""File export tools: reports, custom exports, alarm exports."""
from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..export_files import (
    export_active_alarms_impl,
    export_alarm_definitions_impl,
    export_alarms_history_impl,
    export_custom_data_impl,
    export_log_data_impl,
    export_nodes_impl,
    export_user_groups_impl,
    export_users_impl,
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

        # --- export_users ---
        tool = prefixed_name(prefix, "export_users")

        def _export_users_impl_wrapped(
            format: str = "xlsx", status: str = "all",
            company: str = "", city: str = "",
        ) -> Any:
            return export_users_impl(cfg, format, status, company, city)

        @mcp.tool(name=tool)
        def export_users(
            format: str = "xlsx", status: str = "all",
            company: str = "", city: str = "",
        ) -> str:
            """Tüm kullanıcıları Excel/CSV export (server-side, LLM'den data geçmez).
format: xlsx|csv. status: all|active|inactive. company/city: filtre.
list_users+export_custom_data YERİNE bunu kullan."""
            return guard(tool, _export_users_impl_wrapped)(format, status, company, city)

        # --- export_nodes ---
        tool = prefixed_name(prefix, "export_nodes")

        def _export_nodes_impl_wrapped(
            format: str = "xlsx", nType: str = "",
            keyword: str = "", only_active: bool = False,
        ) -> Any:
            return export_nodes_impl(cfg, format, nType, keyword, only_active)

        @mcp.tool(name=tool)
        def export_nodes(
            format: str = "xlsx", nType: str = "",
            keyword: str = "", only_active: bool = False,
        ) -> str:
            """Tüm node'ları Excel/CSV export.
format: xlsx|csv. nType: tip kodu (777=kuyu). keyword: isim filtresi. only_active: nState>=0."""
            return guard(tool, _export_nodes_impl_wrapped)(format, nType, keyword, only_active)

        # --- export_alarm_definitions ---
        tool = prefixed_name(prefix, "export_alarm_definitions")

        def _export_alarm_definitions_impl_wrapped(format: str = "xlsx", nodeId: int = 0) -> Any:
            return export_alarm_definitions_impl(cfg, format, nodeId)

        @mcp.tool(name=tool)
        def export_alarm_definitions(format: str = "xlsx", nodeId: int = 0) -> str:
            """Alarm tanımları (alarmparameters). nodeId>0 → sadece o node.
Aktif alarm için export_active_alarms, tarih aralığı için export_alarms_history."""
            return guard(tool, _export_alarm_definitions_impl_wrapped)(format, nodeId)

        # --- export_alarms_history ---
        tool = prefixed_name(prefix, "export_alarms_history")

        def _export_alarms_history_impl_wrapped(
            format: str = "xlsx", start_date: str = "",
            end_date: str = "", only_active: bool = False, limit: int = 5000,
        ) -> Any:
            return export_alarms_history_impl(cfg, format, start_date, end_date, only_active, limit)

        @mcp.tool(name=tool)
        def export_alarms_history(
            format: str = "xlsx", start_date: str = "",
            end_date: str = "", only_active: bool = False, limit: int = 5000,
        ) -> str:
            """alarmstate zaman aralığı export.
start_date/end_date: 'YYYY-MM-DD[ HH:MM:SS]'. only_active: state=1. limit max 20000.
Not: ayrı history tablosu yok, alarmstate.time üzerinden yaklaşım."""
            return guard(tool, _export_alarms_history_impl_wrapped)(format, start_date, end_date, only_active, limit)

        # --- export_user_groups ---
        tool = prefixed_name(prefix, "export_user_groups")

        def _export_user_groups_impl_wrapped(format: str = "xlsx") -> Any:
            return export_user_groups_impl(cfg, format)

        @mcp.tool(name=tool)
        def export_user_groups(format: str = "xlsx") -> str:
            """TUM kullanici gruplari + her grubun kullanici sayisi."""
            return guard(tool, _export_user_groups_impl_wrapped)(format)

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
                    p + "export_users",
                    p + "export_nodes",
                    p + "export_alarm_definitions",
                    p + "export_alarms_history",
                    p + "export_user_groups",
                ],
            },
        ]
