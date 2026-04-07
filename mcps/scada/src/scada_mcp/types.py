from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    dbname: str
    username: str
    password: str
    charset: str = "utf8mb4"
    connect_timeout_sec: int = 5
    query_timeout_ms: int = 8000


@dataclass(frozen=True)
class AuthConfig:
    enabled: bool
    admin_secret: str
    token_secret: str
    token_ttl_sec: int = 900


@dataclass(frozen=True)
class InstanceConfig:
    instance_id: str
    base_dir: Path

    mcp_name: str
    mcp_version: str
    mcp_description: str
    mcp_instructions: str | None

    tool_prefix: str

    panel_base_url: str | None = None
    mcp_public_base_url: str | None = None

    mcp_log_file: str | None = None
    mcp_max_concurrency: int = 0
    mcp_concurrency_wait_ms: int = 0

    toolpacks: list[str] | None = None

    db: DbConfig | None = None
    auth: AuthConfig | None = None
