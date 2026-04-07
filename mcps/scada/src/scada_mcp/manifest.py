from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .types import JsonDict

logger = logging.getLogger("scada_mcp.manifest")


def load_manifest(instance_dir: Path) -> JsonDict:
    path = instance_dir / "manifest.json"
    if not path.exists():
        logger.warning("manifest.json not found in %s", instance_dir)
        return {"_schema": "scada_mcp_manifest", "version": 1, "note": "manifest.json not found"}
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("manifest.json must be an object")
    data.setdefault("_schema", "scada_mcp_manifest")
    data.setdefault("version", 1)
    return data


def safe_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str)
