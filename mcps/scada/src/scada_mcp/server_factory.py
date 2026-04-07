from __future__ import annotations

import logging
import os

from mcp.server.fastmcp import FastMCP

from .toolpacks import default_scada_packs, resolve_packs
from .types import InstanceConfig

logger = logging.getLogger("scada_mcp.server_factory")


def create_mcp_server(cfg: InstanceConfig) -> FastMCP:
    # Instance-scope info is stated once in the instructions field (token savings).
    instance_scope = (
        f"[INSTANCE-SCOPE] All tools operate on {cfg.mcp_name} (id={cfg.instance_id}) DB. "
        f"Panel: {cfg.panel_base_url or 'N/A'}. "
        f"LOOP PREVENTION: Do not call the same tool with the same parameters more than 2 times -- "
        f"the server rejects on the 3rd call. "
        f"If you get an error, try a different tool or parameters. "
        f"Node name (e.g. 'OLD', 'Golkent') is NOT a tool name; tools start with prefix (e.g. {cfg.tool_prefix}get_node). "
        f"If many tools exist, call smart_tool_select first to identify suitable tools for the query."
    )

    enable_instructions = (os.getenv("MCP_ENABLE_INSTRUCTIONS") or "").strip() in {"1", "true", "yes", "on"}
    if enable_instructions and cfg.mcp_instructions:
        instructions = f"{instance_scope}\n\n{cfg.mcp_instructions}"
    else:
        instructions = instance_scope

    mcp = FastMCP(
        cfg.mcp_name,
        instructions=instructions,
        json_response=True,
    )

    # Toolpack selection: if cfg.toolpacks is set, load only those packs.
    # Otherwise, load the default SCADA packs (backward compatible).
    if cfg.toolpacks:
        packs = resolve_packs(cfg.toolpacks)
    else:
        packs = default_scada_packs()

    for spec in packs:
        spec.pack.register(mcp, cfg)

    logger.info("Created MCP server '%s' (id=%s, prefix=%s)", cfg.mcp_name, cfg.instance_id, cfg.tool_prefix)
    return mcp
