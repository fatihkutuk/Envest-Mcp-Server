"""
Smart Tool Selector — keyword-based tool routing for token optimization.

Instead of the model choosing from 95+ tools, it can call `smart_tool_select`
first to get a short list of relevant tools for the user's query.
This dramatically reduces the cognitive load on smaller models and saves tokens.
"""
from __future__ import annotations

import re
from typing import Any


# Tool categories: base names (without instance prefix)
TOOL_CATEGORIES: dict[str, list[str]] = {
    "alarm": [
        "list_alarms",
        "get_active_alarms",
        "get_alarm_subscribers",
        "export_active_alarms",
    ],
    "tag_live": [
        "search_tags",
        "get_device_tag_values",
        "list_live_tag_across_nodes",
        "get_device_all_tags",
        "get_node_all_tags",
        "get_tag_address",
    ],
    "log_chart": [
        "get_node_log_data",
        "get_node_log_summary",
        "get_node_log_latest_values",
        "get_node_log_chart_data",
        "get_chart_data",
        "get_multi_chart_data",
        "get_recent_log_chart_by_tag",
        "compare_log_metrics",
        "export_log_data",
    ],
    "trend_analysis": [
        "analyze_log_trend",
        "analyze_dma_seasonal_demand",
        "analyze_seasonal_level_profile",
        "list_dma_station_nodes",
    ],
    "node_info": [
        "get_node",
        "find_nodes_by_keywords",
        "list_nodes",
        "get_node_counts",
        "get_scada_system_stats",
        "get_scada_summary",
        "get_node_distribution",
    ],
    "device_kepware": [
        "get_channel_device_detail",
        "list_channel_devices",
        "list_channel_types",
        "list_device_types",
        "get_device_type_tags",
        "get_device_individual_tags",
        "list_device_status_codes",
        "get_device_connection_params",
        "check_exchanger_status",
    ],
    "driver_service": [
        "list_drivers",
        "get_driver_detail",
        "list_service_instances",
        "get_service_activities",
    ],
    "product_docs": [
        "get_product_specs",
        "search_product_manual",
        "get_product_settings",
        "get_product_troubleshoot",
        "get_product_sensor_info",
        "list_product_types",
    ],
    "panel_view": [
        "get_nview_equipment_profile",
        "get_node_panel_settings_guide",
        "list_point_display_templates",
        "read_point_display_template",
        "search_point_display_templates",
        "get_panel_url_for_template",
        "extract_menu_links",
        "summarize_point_display_template",
        "list_point_display_files",
    ],
    "semantic": [
        "get_scada_semantics",
        "get_view_tag_meanings",
        "get_counter_semantics",
        "resolve_semantic_tag_candidates",
        "get_node_scada_context",
        "get_operational_engineering_hints",
        "get_korubin_data_concepts",
    ],
    "schema_query": [
        "get_database_schema",
        "get_table_info",
        "run_safe_query",
    ],
    "user_auth": [
        "get_user_permissions",
        "get_node_permissions",
        "list_user_groups",
        "get_group_members",
        "list_users",
        "get_user",
        "search_users",
        "get_user_stats",
    ],
    "tag_links": [
        "list_tag_links",
        "list_tag_clones",
        "list_log_params",
    ],
    "export": [
        "export_log_data",
        "export_custom_data",
        "export_active_alarms",
        "generate_scada_report",
        "generate_node_report",
    ],
    "routing": [
        "get_scada_mcp_manifest",
        "get_korubin_ui_and_tool_routing_tr",
        "get_scada_site_routing_hints",
        "get_scada_tag_naming_defaults_tr",
    ],
}

# Keyword → category mapping (Turkish + English)
# Each pattern is compiled as case-insensitive regex
_KEYWORD_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("alarm", re.compile(r"alarm|uyar[ıi]|sorun|ar[ıi]za|aktif alarm|hata", re.IGNORECASE)),
    ("tag_live", re.compile(
        r"\btag\b|debi|g[üu][çc]|bas[ıi]n[çc]|seviye|frekans|canl[ıi]|anl[ıi]k|[öo]l[çc][üu]m|voltaj|s[ıi]cakl[ıi]k",
        re.IGNORECASE,
    )),
    ("log_chart", re.compile(r"\blog\b|trend|grafik|[çc]iz|chart|ge[çc]mi[şs]|tarihsel", re.IGNORECASE)),
    ("trend_analysis", re.compile(
        r"analiz|mevsimsel|dma|k-means|profil|d[üu][şs][üu][şs]|seasonal",
        re.IGNORECASE,
    )),
    ("node_info", re.compile(
        r"\bnode\b|nokta|istasyon|kuyu|terfi|depo|say[ıi]|[öo]zet|ka[çc]|da[gğ][ıi]l[ıi]m",
        re.IGNORECASE,
    )),
    ("device_kepware", re.compile(r"kepware|device|cihaz|channel|ba[gğ]lant[ıi]|opc|exchanger", re.IGNORECASE)),
    ("driver_service", re.compile(r"driver|s[üu]r[üu]c[üu]|servis|service", re.IGNORECASE)),
    ("product_docs", re.compile(
        r"[üu]r[üu]n|product|modbus|led|modem|k[ıi]lavuz|model|aqua|sensor",
        re.IGNORECASE,
    )),
    ("panel_view", re.compile(
        r"panel|ekran|men[üu]|sayfa|view|[şs]ablon|phtml|template|display",
        re.IGNORECASE,
    )),
    ("semantic", re.compile(r"semantik|anlam|nedir|ne\s+demek|kavram|concept", re.IGNORECASE)),
    ("schema_query", re.compile(r"\bsql\b|tablo|veritaban[ıi]|[şs]ema|sorgu|query|schema", re.IGNORECASE)),
    ("user_auth", re.compile(r"kullan[ıi]c[ıi]|yetki|grup|izin|user|permission", re.IGNORECASE)),
    ("tag_links", re.compile(r"tag\s*link|tag\s*clone|log\s*param", re.IGNORECASE)),
    ("export", re.compile(r"export|excel|pdf|csv|rapor|d[ıi][şs]a\s*aktar|word|docx", re.IGNORECASE)),
]

# Default fallback categories when nothing matches
_FALLBACK_CATEGORIES = ["node_info", "alarm", "tag_live"]


def select_tools(user_query: str, *, prefix: str = "") -> dict[str, Any]:
    """
    Keyword-based tool routing. Returns recommended tool names for the query.

    Always includes 'routing' category. Unmatched queries get sensible fallbacks.
    If prefix is given, tool names are returned with the prefix applied.
    """
    matched: list[str] = ["routing"]

    for category, pattern in _KEYWORD_PATTERNS:
        if pattern.search(user_query):
            matched.append(category)

    # Remove duplicates while preserving order
    seen: set[str] = set()
    unique_matched: list[str] = []
    for cat in matched:
        if cat not in seen:
            seen.add(cat)
            unique_matched.append(cat)

    # Fallback if only routing matched
    if len(unique_matched) <= 1:
        unique_matched.extend(_FALLBACK_CATEGORIES)

    # Build tool list
    tools: list[str] = []
    tools_seen: set[str] = set()
    for cat in unique_matched:
        for tool_name in TOOL_CATEGORIES.get(cat, []):
            if tool_name not in tools_seen:
                tools_seen.add(tool_name)
                full_name = f"{prefix}{tool_name}" if prefix else tool_name
                tools.append(full_name)

    total_available = sum(len(v) for v in TOOL_CATEGORIES.values())

    return {
        "matched_categories": unique_matched,
        "recommended_tools": tools,
        "total_available": total_available,
        "recommended_count": len(tools),
        "note_tr": (
            "Bu liste sorgunuza en uygun araçları içerir. "
            "Listede olmayan bir araca ihtiyaç duyarsanız doğrudan çağırabilirsiniz."
        ),
    }
