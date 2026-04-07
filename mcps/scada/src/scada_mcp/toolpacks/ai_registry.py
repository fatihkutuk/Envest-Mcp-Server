from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..config import instance_as_public_dict, mcp_public_privacy_notice
from ..tools.core import prefixed_name
from ..types import InstanceConfig


class AiRegistryPack:
    id = "ai_registry"

    def _load_registry(self, cfg: InstanceConfig) -> Any:
        # Allow per-instance override first.
        override = cfg.base_dir / "ai_module_registry.json"
        if override.exists():
            return json.loads(override.read_text(encoding="utf-8"))

        # Default: keep parity with PHP data file location (vendored into repo).
        # We resolve relative to project root (same heuristic as manager app).
        project_root = Path(__file__).resolve().parents[4]
        default_path = project_root / "eskiprojeornekicin" / "data" / "scada" / "ai_module_registry.json"
        return json.loads(default_path.read_text(encoding="utf-8"))

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        tool_name = prefixed_name(cfg.tool_prefix, "get_korubin_ai_mcp_registry")

        @mcp.tool(name=tool_name)
        def get_korubin_ai_mcp_registry() -> Any:
            """AI modül ve yetenek registry özeti."""
            payload = self._load_registry(cfg)
            if isinstance(payload, dict):
                payload = dict(payload)
                payload["instance"] = instance_as_public_dict(cfg)
                payload["privacy"] = mcp_public_privacy_notice()
                payload["registered_tool_name"] = tool_name
            return payload

    def manifest_groups(self, *, prefix: str) -> list[dict]:
        p = prefix
        return [
            {
                "id": "ai_registry",
                "title_tr": "AI modül / yetenek registry",
                "tools": [p + "get_korubin_ai_mcp_registry"],
            }
        ]
