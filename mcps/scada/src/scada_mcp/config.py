from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from .types import AuthConfig, DbConfig, InstanceConfig, JsonDict

logger = logging.getLogger("scada_mcp.config")

_TOOL_NAME_RE = re.compile(r"^[a-zA-Z0-9._/-]{1,64}$")
_TOOL_PREFIX_RE = re.compile(r"^[a-zA-Z0-9._/-]+$")


def _require_str(d: dict[str, Any], key: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"Missing/invalid '{key}' in instance config.")
    return v.strip()


def _opt_str(d: dict[str, Any], key: str) -> str | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, str):
        raise ValueError(f"Invalid '{key}' in instance config (must be string).")
    v = v.strip()
    return v if v else None


def _opt_int(d: dict[str, Any], key: str, default: int) -> int:
    v = d.get(key, default)
    if isinstance(v, bool):
        raise ValueError(f"Invalid '{key}' in instance config (must be int).")
    if isinstance(v, (int, float)) and int(v) == v:
        return int(v)
    if isinstance(v, str) and v.strip().lstrip("-").isdigit():
        return int(v.strip())
    raise ValueError(f"Invalid '{key}' in instance config (must be int).")


def _read_yaml_or_json(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".json"}:
        data = json.loads(raw)
    else:
        # Support ${ENV_VAR} substitutions to keep secrets in .env.
        def _sub(match: re.Match[str]) -> str:
            key = match.group(1)
            return os.getenv(key, "")

        substituted = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", _sub, raw)
        substituted = os.path.expandvars(substituted)
        data = yaml.safe_load(substituted)
    if not isinstance(data, dict):
        raise ValueError(f"Instance config must be an object: {path}")
    return data


def validate_tool_prefix(prefix: str) -> str:
    prefix = prefix.strip()
    if prefix == "":
        return ""
    if not _TOOL_PREFIX_RE.fullmatch(prefix):
        raise ValueError("tool_prefix may only contain letters, numbers and ._/-")
    return prefix


def validate_tool_name(name: str) -> str:
    if not _TOOL_NAME_RE.fullmatch(name):
        raise ValueError(f"Invalid tool name: {name}")
    return name


def _env_first(*keys: str) -> str | None:
    """Return the first non-empty environment variable value (after instance .env load_dotenv)."""
    for k in keys:
        v = os.getenv(k)
        if v is not None and str(v).strip() != "":
            return str(v).strip()
    return None


# When loading multiple instances in the same process, load_dotenv does not remove
# missing keys from os.environ; previous instance's DB_HOST etc. can leak.
# We clear these keys before loading each instance's .env.
_INSTANCE_ENV_ISOLATION_KEYS: tuple[str, ...] = (
    "WINCAPS_DB_HOST",
    "WINCAPS_DB_PORT",
    "WINCAPS_DB_NAME",
    "WINCAPS_DB_USER",
    "WINCAPS_DB_PASSWORD",
    "KORUBIN_DB_HOST",
    "KORUBIN_DB_PORT",
    "KORUBIN_DB_NAME",
    "KORUBIN_DB_DATABASE",
    "KORUBIN_DB_USERNAME",
    "KORUBIN_DB_USER",
    "KORUBIN_DB_PASSWORD",
    "KORUBIN_DB_CHARSET",
    "CORUM_DB_HOST",
    "CORUM_DB_PORT",
    "CORUM_DB_NAME",
    "CORUM_DB_USERNAME",
    "CORUM_DB_PASSWORD",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_DATABASE",
    "DB_USERNAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_CHARSET",
    "KORUBIN_POINT_DISPLAY_ROOT",
    "MCP_ADMIN_SECRET",
    "MCP_TOKEN_SECRET",
    "MCP_PUBLIC_BASE_URL",
)


def _clear_instance_env_leaks() -> None:
    for k in _INSTANCE_ENV_ISOLATION_KEYS:
        os.environ.pop(k, None)


def _merge_db_env_overrides(db_raw: dict[str, Any]) -> dict[str, Any]:
    """
    Override instance.yaml db: block with KORUBIN_DB_* / CORUM_DB_* / DB_* env vars.
    This allows host/port/dbname/user/password to be managed entirely via .env.
    """
    out = dict(db_raw)
    h = _env_first("KORUBIN_DB_HOST", "CORUM_DB_HOST", "DB_HOST")
    if h:
        out["host"] = h
    p = _env_first("KORUBIN_DB_PORT", "CORUM_DB_PORT", "DB_PORT")
    if p:
        try:
            out["port"] = int(p)
        except ValueError:
            pass
    name = _env_first(
        "KORUBIN_DB_NAME",
        "KORUBIN_DB_DATABASE",
        "CORUM_DB_NAME",
        "DB_NAME",
        "DB_DATABASE",
    )
    if name:
        out["dbname"] = name
    user = _env_first(
        "KORUBIN_DB_USERNAME",
        "KORUBIN_DB_USER",
        "CORUM_DB_USERNAME",
        "DB_USERNAME",
        "DB_USER",
    )
    if user:
        out["username"] = user
    pw = _env_first("KORUBIN_DB_PASSWORD", "CORUM_DB_PASSWORD", "DB_PASSWORD")
    if pw is not None:
        out["password"] = pw
    cs = _env_first("KORUBIN_DB_CHARSET", "DB_CHARSET")
    if cs:
        out["charset"] = cs
    return out


def load_instance(instance_dir: Path) -> InstanceConfig:
    instance_dir = instance_dir.resolve()
    if not instance_dir.is_dir():
        raise FileNotFoundError(f"Instance directory not found: {instance_dir}")

    _clear_instance_env_leaks()
    load_dotenv(instance_dir / ".env", override=True)

    cfg_path_yaml = instance_dir / "instance.yaml"
    cfg_path_yml = instance_dir / "instance.yml"
    cfg_path_json = instance_dir / "instance.json"
    if cfg_path_yaml.exists():
        raw_cfg = _read_yaml_or_json(cfg_path_yaml)
    elif cfg_path_yml.exists():
        raw_cfg = _read_yaml_or_json(cfg_path_yml)
    elif cfg_path_json.exists():
        raw_cfg = _read_yaml_or_json(cfg_path_json)
    else:
        raise FileNotFoundError(
            f"Missing instance.yaml / instance.yml / instance.json in {instance_dir}"
        )

    instance_id = raw_cfg.get("instance_id")
    if not isinstance(instance_id, str) or not instance_id.strip():
        instance_id = instance_dir.name
    instance_id = instance_id.strip()

    tool_prefix = validate_tool_prefix(_require_str(raw_cfg, "tool_prefix"))

    db_cfg: DbConfig | None = None
    db_raw = raw_cfg.get("db")
    if isinstance(db_raw, dict):
        db_raw = _merge_db_env_overrides(db_raw)
        db_cfg = DbConfig(
            host=_require_str(db_raw, "host"),
            port=_opt_int(db_raw, "port", 3306),
            dbname=_require_str(db_raw, "dbname"),
            username=_require_str(db_raw, "username"),
            password=str(db_raw.get("password", "")),
            charset=str(db_raw.get("charset") or "utf8mb4"),
            connect_timeout_sec=_opt_int(db_raw, "connect_timeout_sec", 5),
            query_timeout_ms=_opt_int(db_raw, "query_timeout_ms", 8000),
        )

    auth_cfg: AuthConfig | None = None
    auth_raw = raw_cfg.get("auth")
    if isinstance(auth_raw, dict):
        enabled = bool(auth_raw.get("enabled", True))
        admin_secret = str(auth_raw.get("admin_secret") or os.getenv("MCP_ADMIN_SECRET") or "").strip()
        token_secret = str(auth_raw.get("token_secret") or os.getenv("MCP_TOKEN_SECRET") or "").strip()
        # Auto-provision a persistent per-instance download/signed-url secret if none configured.
        # Stored at <instance_dir>/.download_secret (gitignore'de). Survives restarts,
        # combined.py deploy'una ihtiyac duymaz — signed download URL'leri burada dogar.
        if not token_secret:
            secret_path = instance_dir / ".download_secret"
            try:
                if secret_path.exists():
                    token_secret = secret_path.read_text(encoding="utf-8").strip()
                if not token_secret:
                    import secrets as _secrets
                    token_secret = _secrets.token_hex(32)
                    try:
                        secret_path.write_text(token_secret, encoding="utf-8")
                        # permissions: rw------ (Unix)
                        try:
                            import stat as _stat
                            secret_path.chmod(_stat.S_IRUSR | _stat.S_IWUSR)
                        except Exception:
                            pass
                    except Exception as _e:
                        logger.warning("could not persist download secret: %s", _e)
            except Exception as _e:
                logger.warning("download_secret load failed for %s: %s", instance_id, _e)
                import secrets as _secrets
                token_secret = _secrets.token_hex(32)
        ttl = _opt_int(auth_raw, "token_ttl_sec", 900)
        auth_cfg = AuthConfig(
            enabled=enabled,
            admin_secret=admin_secret,
            token_secret=token_secret,
            token_ttl_sec=ttl,
        )

    pub_base = _opt_str(raw_cfg, "mcp_public_base_url")
    if not pub_base:
        pub_base = (os.getenv("MCP_PUBLIC_BASE_URL") or "").strip() or None
    if pub_base:
        pub_base = pub_base.rstrip("/")

    # Optional toolpacks list: if specified, only those packs are loaded.
    raw_toolpacks = raw_cfg.get("toolpacks")
    toolpacks_list: list[str] | None = None
    if isinstance(raw_toolpacks, list):
        toolpacks_list = [str(tp).strip() for tp in raw_toolpacks if str(tp).strip()]

    logger.info("Loaded instance %s from %s", instance_id, instance_dir)

    return InstanceConfig(
        instance_id=instance_id,
        base_dir=instance_dir,
        mcp_name=_require_str(raw_cfg, "mcp_name"),
        mcp_version=str(raw_cfg.get("mcp_version") or "1.0.0"),
        mcp_description=_require_str(raw_cfg, "mcp_description"),
        mcp_instructions=_opt_str(raw_cfg, "mcp_instructions"),
        tool_prefix=tool_prefix,
        panel_base_url=_opt_str(raw_cfg, "panel_base_url"),
        mcp_public_base_url=pub_base,
        mcp_log_file=_opt_str(raw_cfg, "mcp_log_file"),
        mcp_max_concurrency=_opt_int(raw_cfg, "mcp_max_concurrency", 0),
        mcp_concurrency_wait_ms=_opt_int(raw_cfg, "mcp_concurrency_wait_ms", 0),
        toolpacks=toolpacks_list,
        db=db_cfg,
        auth=auth_cfg,
    )


def mcp_public_privacy_notice() -> JsonDict:
    """
    Privacy notice for model and client: which sensitive info is intentionally not exposed.
    """
    return {
        "exposes_database_host_or_port": False,
        "exposes_database_credentials": False,
        "exposes_mcp_secrets": False,
        "description": (
            "This MCP server does not return database server address (IP/host), port, "
            "username, or password in tool outputs for security reasons. Only the fact that "
            "a connection is configured, database name (dbname), and schema/table info may be shared."
        ),
        "model_instruction": (
            "If the user asks for database IP, MySQL host, or password: "
            "this information is not provided via MCP tools. Tell the user briefly that "
            "this info is not exposed via MCP and they should consult the system administrator."
        ),
    }


def instance_as_public_dict(cfg: InstanceConfig) -> JsonDict:
    d = asdict(cfg)
    # Remove secrets (passwords, token secrets).
    if isinstance(d.get("db"), dict):
        db = d["db"]
        dbn = db.get("dbname")
        d["db"] = {
            "configured": True,
            "dbname": dbn,
        }
    if isinstance(d.get("auth"), dict):
        d["auth"].pop("admin_secret", None)
        d["auth"].pop("token_secret", None)
    d["base_dir"] = str(cfg.base_dir)
    d["mcp_privacy"] = mcp_public_privacy_notice()
    return d
