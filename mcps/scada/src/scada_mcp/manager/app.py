from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

from dotenv import dotenv_values
from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.applications import Starlette
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.routing import Route

from ..auth import TokenError, mint_token
from ..config import load_instance, validate_tool_prefix

logger = logging.getLogger("scada_mcp.manager")

_NAME_RE = re.compile(r"^[a-zA-Z0-9._-]{1,64}$")


@dataclass(frozen=True)
class InstanceListItem:
    name: str
    kind: str
    mcp_name: str
    mcp_description: str
    tool_prefix: str


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _instances_dir(root: Path) -> Path:
    return root / "instances"


def _jinja(root: Path) -> Environment:
    templates = root / "src" / "scada_mcp" / "manager" / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates)),
        autoescape=select_autoescape(["html"]),
    )
    return env


def _render(env: Environment, template_name: str, *, root_dir: str, **ctx: Any) -> HTMLResponse:
    tpl = env.get_template(template_name)
    html = tpl.render(root_dir=root_dir, **ctx)
    return HTMLResponse(html)


def _flash_message(code: str | None) -> str | None:
    if not code:
        return None
    m = {
        "created": "Instance created.",
        "saved": "Saved.",
        "deleted": "Instance deleted.",
        "delete_bad_confirm": "Please type the instance name correctly to confirm deletion.",
        "delete_forbidden": "This folder cannot be deleted.",
    }
    return m.get(code, code.replace("_", " "))


def _default_remote_mcp_url(request: Request) -> str:
    """
    Remote MCP URL (LM Studio, etc.): address the client connects to + /mcp/.
    """
    xf_proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
    xf_host = (request.headers.get("x-forwarded-host") or "").split(",")[0].strip()
    host = xf_host or (request.headers.get("host") or "").strip()
    if not host:
        host = request.url.netloc or "127.0.0.1:8000"
    scheme = xf_proto or (request.url.scheme or "http")
    if scheme not in ("http", "https"):
        scheme = "http"
    base = f"{scheme}://{host}".rstrip("/")
    return f"{base}/mcp/"


def _flash_tuple_from_code(code: str | None) -> tuple[str | None, str | None]:
    """(message, success|error|info) -- for layout color."""
    if not code:
        return None, None
    msg = _flash_message(code)
    if code in ("created", "saved", "deleted"):
        kind = "success"
    elif code.startswith("delete_") or code == "error":
        kind = "error"
    else:
        kind = "info"
    return msg, kind


def _list_instances(instances: Path) -> list[InstanceListItem]:
    items: list[InstanceListItem] = []
    if not instances.exists():
        return items
    for p in sorted(instances.iterdir()):
        if not p.is_dir():
            continue
        if p.name.startswith("."):
            continue
        if p.name == "_template":
            continue
        try:
            cfg = load_instance(p)
            items.append(
                InstanceListItem(
                    name=p.name,
                    kind="SCADA",
                    mcp_name=cfg.mcp_name,
                    mcp_description=cfg.mcp_description,
                    tool_prefix=cfg.tool_prefix,
                )
            )
        except Exception:
            continue
    return items


def _require_instance_name(name: str) -> str:
    name = name.strip()
    if not _NAME_RE.fullmatch(name):
        raise ValueError("Instance name must match ^[a-zA-Z0-9._-]{1,64}$")
    return name


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _scada_tool_groups(prefix: str) -> list[dict[str, Any]]:
    from ..toolpacks import default_scada_packs

    groups: list[dict[str, Any]] = []
    for spec in default_scada_packs():
        groups.extend(spec.pack.manifest_groups(prefix=prefix))
    return groups


def _indent_block(text: str, spaces: int) -> str:
    pad = " " * spaces
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        return pad
    return "\n".join(pad + line for line in text.split("\n"))


def _read_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    vals = dotenv_values(path)
    out: dict[str, str] = {}
    for k, v in vals.items():
        if isinstance(k, str) and isinstance(v, str):
            out[k] = v
    return out


def _write_env(path: Path, values: dict[str, str]) -> None:
    keys = [
        "MCP_PUBLIC_BASE_URL",
        "MCP_ADMIN_SECRET",
        "MCP_TOKEN_SECRET",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USERNAME",
        "DB_PASSWORD",
        "KORUBIN_POINT_DISPLAY_ROOT",
    ]
    lines: list[str] = []
    for k in keys:
        if k in values:
            lines.append(f"{k}={values[k]}")
    # keep any extras
    for k in sorted(values.keys()):
        if k in keys:
            continue
        lines.append(f"{k}={values[k]}")
    lines.append("")
    _write_text(path, "\n".join(lines))


def _write_instance_yaml(
    *,
    path: Path,
    mcp_name: str,
    mcp_version: str,
    mcp_description: str,
    mcp_instructions: str,
    tool_prefix: str,
    panel_base_url: str,
    db_host: str,
    db_port: int,
    db_name: str,
) -> None:
    desc_escaped = mcp_description.replace('"', '\\"')
    version_escaped = (mcp_version or "1.0.0").replace('"', '\\"')
    instructions_block = _indent_block(mcp_instructions, 2)
    content = "\n".join(
        [
            f'mcp_name: "{mcp_name}"',
            f'mcp_version: "{version_escaped}"',
            f'mcp_description: "{desc_escaped}"',
            "mcp_instructions: |",
            instructions_block,
            f'tool_prefix: "{tool_prefix}"',
            f'panel_base_url: "{panel_base_url}"',
            "",
            "db:",
            f'  host: "{db_host}"',
            f"  port: {db_port}",
            f'  dbname: "{db_name}"',
            '  username: "${DB_USERNAME}"',
            '  password: "${DB_PASSWORD}"',
            '  charset: "utf8mb4"',
            "  connect_timeout_sec: 5",
            "  query_timeout_ms: 8000",
            "",
            "auth:",
            "  enabled: true",
            '  admin_secret: "${MCP_ADMIN_SECRET}"',
            '  token_secret: "${MCP_TOKEN_SECRET}"',
            "  token_ttl_sec: 0  # 0 = long-lived (10 years); positive = seconds",
            "",
        ]
    )
    _write_text(path, content)


def _rewrite_manifest_prefix(manifest_path: Path, *, new_prefix: str) -> None:
    if not manifest_path.exists():
        return
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return
    groups = data.get("tool_groups")
    if not isinstance(groups, list):
        return
    data["tool_groups"] = _scada_tool_groups(new_prefix)
    _write_text(manifest_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


async def index(request: Request) -> Response:
    app = request.app
    root: Path = app.state.root  # type: ignore[attr-defined]
    env: Environment = app.state.jinja  # type: ignore[attr-defined]
    instances = _instances_dir(root)
    items = _list_instances(instances)
    flash, flash_kind = _flash_tuple_from_code(request.query_params.get("flash"))
    return _render(
        env,
        "index.html",
        title="Instances",
        root_dir=str(root),
        items=items,
        flash=flash,
        flash_kind=flash_kind,
    )


async def new_scada_get(request: Request) -> Response:
    app = request.app
    root: Path = app.state.root  # type: ignore[attr-defined]
    env: Environment = app.state.jinja  # type: ignore[attr-defined]
    default_point_display_root = str(
        (root / "korbin1.7-system-info" / "app" / "views" / "point" / "display" / "common").resolve()
    )
    return _render(
        env,
        "new_scada.html",
        title="New SCADA",
        root_dir=str(root),
        error=None,
        default_point_display_root=default_point_display_root,
    )


async def new_scada_post(request: Request) -> Response:
    app = request.app
    root: Path = app.state.root  # type: ignore[attr-defined]
    env: Environment = app.state.jinja  # type: ignore[attr-defined]
    instances = _instances_dir(root)
    template = instances / "_template"
    form: FormData = await request.form()
    try:
        name = _require_instance_name(str(form.get("name", "")))
        tool_prefix = validate_tool_prefix(str(form.get("tool_prefix", "")))
        mcp_name = str(form.get("mcp_name", "")).strip()
        mcp_description = str(form.get("mcp_description", "")).strip()
        mcp_instructions = str(form.get("mcp_instructions", "")).strip()
        panel_base_url = str(form.get("panel_base_url", "")).strip()

        db_host = str(form.get("db_host", "")).strip()
        db_port = int(str(form.get("db_port", "3306")).strip())
        db_name = str(form.get("db_name", "")).strip()
        db_user = str(form.get("db_user", "")).strip()
        db_pass = str(form.get("db_pass", "")).strip()
        point_display_root = str(form.get("point_display_root", "")).strip()

        admin_secret = str(form.get("admin_secret", "")).strip()
        token_secret = str(form.get("token_secret", "")).strip()

        if not (mcp_name and mcp_description and db_host and db_name and db_user and admin_secret and token_secret):
            raise ValueError("Missing required fields.")

        dst = instances / name
        if dst.exists():
            raise ValueError(f"Instance already exists: {name}")

        shutil.copytree(template, dst)

        env_lines = [
            f"MCP_ADMIN_SECRET={admin_secret}",
            f"MCP_TOKEN_SECRET={token_secret}",
            f"DB_HOST={db_host}",
            f"DB_PORT={db_port}",
            f"DB_NAME={db_name}",
            f"DB_USERNAME={db_user}",
            f"DB_PASSWORD={db_pass}",
            f"KORUBIN_POINT_DISPLAY_ROOT={point_display_root}" if point_display_root else "",
            "",
        ]
        _write_text(dst / ".env", "\n".join(env_lines))

        desc_escaped = mcp_description.replace('"', '\\"')
        instructions_block = _indent_block(mcp_instructions, 2)
        yaml_content = "\n".join(
            [
                f'mcp_name: "{mcp_name}"',
                'mcp_version: "1.0.0"',
                f'mcp_description: "{desc_escaped}"',
                "mcp_instructions: |",
                instructions_block,
                f'tool_prefix: "{tool_prefix}"',
                f'panel_base_url: "{panel_base_url}"',
                "",
                "db:",
                f'  host: "{db_host}"',
                f"  port: {db_port}",
                f'  dbname: "{db_name}"',
                '  username: "${DB_USERNAME}"',
                '  password: "${DB_PASSWORD}"',
                '  charset: "utf8mb4"',
                "  connect_timeout_sec: 5",
                "  query_timeout_ms: 8000",
                "",
                "auth:",
                "  enabled: true",
                '  admin_secret: "${MCP_ADMIN_SECRET}"',
                '  token_secret: "${MCP_TOKEN_SECRET}"',
                "  token_ttl_sec: 0  # 0 = long-lived (10 years); positive = seconds",
                "",
            ]
        )
        _write_text(dst / "instance.yaml", yaml_content)

        manifest = {
            "_schema": "scada_mcp_manifest",
            "version": 1,
            "title": f"SCADA MCP manifest ({name})",
            "purpose": mcp_description,
            "tool_groups": _scada_tool_groups(tool_prefix),
        }
        _write_text(dst / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

        och = getattr(request.app.state, "on_instances_changed", None)
        if och is not None:
            await och()

        return RedirectResponse(url=f"/instances/{name}?flash=created", status_code=303)
    except Exception as e:
        return _render(env, "new_scada.html", title="New SCADA", root_dir=str(root), error=str(e))


async def instance_view(request: Request) -> Response:
    app = request.app
    root: Path = app.state.root  # type: ignore[attr-defined]
    env: Environment = app.state.jinja  # type: ignore[attr-defined]
    instances = _instances_dir(root)
    name = request.path_params["name"]
    flash, flash_kind = _flash_tuple_from_code(request.query_params.get("flash"))
    p = instances / name
    cfg = load_instance(p)
    return _render(
        env,
        "instance.html",
        title=f"Instance {name}",
        root_dir=str(root),
        flash=flash,
        flash_kind=flash_kind,
        delete_error=None,
        name=name,
        cfg=cfg,
        instance_path=str(p),
        remote_mcp_url_default=_default_remote_mcp_url(request),
        files={
            "instance_yaml": str(p / "instance.yaml"),
            "dotenv": str(p / ".env"),
            "manifest": str(p / "manifest.json"),
        },
    )


async def edit_instance_get(request: Request) -> Response:
    app = request.app
    root: Path = app.state.root  # type: ignore[attr-defined]
    env: Environment = app.state.jinja  # type: ignore[attr-defined]
    instances = _instances_dir(root)
    name = request.path_params["name"]
    p = instances / name
    cfg = load_instance(p)
    envvals = _read_env(p / ".env")
    default_point_display_root = str(
        (root / "korbin1.7-system-info" / "app" / "views" / "point" / "display" / "common").resolve()
    )
    return _render(
        env,
        "edit_instance.html",
        title=f"Edit {name}",
        root_dir=str(root),
        name=name,
        cfg=cfg,
        envvals=envvals,
        default_point_display_root=default_point_display_root,
        error=None,
    )


async def edit_instance_post(request: Request) -> Response:
    app = request.app
    root: Path = app.state.root  # type: ignore[attr-defined]
    env: Environment = app.state.jinja  # type: ignore[attr-defined]
    instances = _instances_dir(root)
    name = request.path_params["name"]
    p = instances / name
    form: FormData = await request.form()
    try:
        cfg = load_instance(p)
        current_env = _read_env(p / ".env")

        mcp_name = str(form.get("mcp_name", "")).strip()
        mcp_version = str(form.get("mcp_version", "")).strip() or cfg.mcp_version
        mcp_description = str(form.get("mcp_description", "")).strip()
        mcp_instructions = str(form.get("mcp_instructions", "")).replace("\r\n", "\n").replace("\r", "\n")
        tool_prefix = validate_tool_prefix(str(form.get("tool_prefix", "")).strip())
        panel_base_url = str(form.get("panel_base_url", "")).strip()

        db_host = str(form.get("db_host", "")).strip()
        db_port = int(str(form.get("db_port", "3306")).strip())
        db_name = str(form.get("db_name", "")).strip()
        db_user = str(form.get("db_user", "")).strip()
        db_pass = str(form.get("db_pass", "")).strip()
        point_display_root = str(form.get("point_display_root", "")).strip()

        admin_secret = str(form.get("admin_secret", "")).strip()
        token_secret = str(form.get("token_secret", "")).strip()

        if not (mcp_name and mcp_description and db_host and db_name and db_user):
            raise ValueError("Missing required fields.")

        new_env = dict(current_env)
        new_env["DB_HOST"] = db_host
        new_env["DB_PORT"] = str(db_port)
        new_env["DB_NAME"] = db_name
        new_env["DB_USERNAME"] = db_user
        if db_pass != "":
            new_env["DB_PASSWORD"] = db_pass
        if point_display_root != "":
            new_env["KORUBIN_POINT_DISPLAY_ROOT"] = point_display_root
        else:
            new_env.pop("KORUBIN_POINT_DISPLAY_ROOT", None)
        if admin_secret != "":
            new_env["MCP_ADMIN_SECRET"] = admin_secret
        if token_secret != "":
            new_env["MCP_TOKEN_SECRET"] = token_secret
        _write_env(p / ".env", new_env)

        _write_instance_yaml(
            path=p / "instance.yaml",
            mcp_name=mcp_name,
            mcp_version=mcp_version,
            mcp_description=mcp_description,
            mcp_instructions=mcp_instructions,
            tool_prefix=tool_prefix,
            panel_base_url=panel_base_url,
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
        )

        _rewrite_manifest_prefix(p / "manifest.json", new_prefix=tool_prefix)

        return RedirectResponse(url=f"/instances/{name}?flash=saved", status_code=303)
    except Exception as e:
        cfg = load_instance(p)
        envvals = _read_env(p / ".env")
        return _render(
            env,
            "edit_instance.html",
            title=f"Edit {name}",
            root_dir=str(root),
            name=name,
            cfg=cfg,
            envvals=envvals,
            error=str(e),
        )


def _generate_mcp_servers_json(*, instance_path: str, local_key: str, remote_key: str, remote_url: str) -> dict[str, Any]:
    return {
        "mcpServers": {
            local_key: {
                "command": "py",
                "args": ["-m", "scada_mcp.cli", "--instance", instance_path, "--transport", "stdio"],
            },
            remote_key: {
                "url": remote_url,
                "headers": {"Authorization": "Bearer <EPHEMERAL_TOKEN>"},
            },
        }
    }


def _generate_mcp_servers_json_local(*, instance_path: str, local_key: str) -> dict[str, Any]:
    return {
        "mcpServers": {
            local_key: {
                "command": "py",
                "args": ["-m", "scada_mcp.cli", "--instance", instance_path, "--transport", "stdio"],
            }
        }
    }


def _normalize_remote_mcp_url(remote_url: str) -> str:
    """
    Streamable MCP base URL for scada-mcp-combined: .../mcp/ (trailing slash).
    Strips legacy .../sse so old configs map to the streamable endpoint.
    """
    u = urlparse(remote_url.strip())
    if not u.scheme or not u.netloc:
        return remote_url.strip()
    p = (u.path or "").rstrip("/")
    if p.endswith("/sse"):
        p = p[: -len("/sse")]
    if not p or p == "/mcp":
        out = "/mcp/"
    else:
        out = p + "/"
    return urlunparse((u.scheme, u.netloc, out, "", "", ""))


def _remote_mcp_url_with_path_token(remote_url: str, bearer_token: str) -> str:
    """
    LM Studio remote MCP: EventSource does not send Authorization -> 401.
    Server rewrites /mcp/k/h{hex(jwt)}/ to Bearer + /mcp/... (cli.McpPathTokenRewriteMiddleware).
    """
    base = _normalize_remote_mcp_url(remote_url).rstrip("/")
    seg = "h" + bearer_token.encode("utf-8").hex()
    return f"{base}/k/{seg}/"


def _generate_mcp_servers_json_remote(*, remote_key: str, remote_url: str, bearer_token: str) -> dict[str, Any]:
    return {
        "mcpServers": {
            remote_key: {
                "url": _remote_mcp_url_with_path_token(remote_url, bearer_token),
                "headers": {"Authorization": f"Bearer {bearer_token}"},
            }
        }
    }


async def delete_instance_post(request: Request) -> Response:
    app = request.app
    root: Path = app.state.root  # type: ignore[attr-defined]
    env: Environment = app.state.jinja  # type: ignore[attr-defined]
    instances = _instances_dir(root)
    name = request.path_params["name"]
    form: FormData = await request.form()
    confirm = str(form.get("confirm_name", "")).strip()

    def _instance_render(*, delete_error: str | None = None) -> HTMLResponse:
        p = instances / name
        cfg = load_instance(p)
        return _render(
            env,
            "instance.html",
            title=f"Instance {name}",
            root_dir=str(root),
            flash=None,
            flash_kind=None,
            delete_error=delete_error,
            name=name,
            cfg=cfg,
            instance_path=str(p),
            remote_mcp_url_default=_default_remote_mcp_url(request),
            files={
                "instance_yaml": str(p / "instance.yaml"),
                "dotenv": str(p / ".env"),
                "manifest": str(p / "manifest.json"),
            },
        )

    if name in ("_template",) or name.startswith("."):
        return RedirectResponse(url="/?flash=delete_forbidden", status_code=303)
    p = instances / name
    if not p.is_dir():
        return RedirectResponse(url="/?flash=deleted", status_code=303)
    if confirm != name:
        return _instance_render(
            delete_error=(
                f"Delete confirmation did not match. Type exactly: "
                f"<strong>{name}</strong> in the box below."
            ),
        )
    shutil.rmtree(p)
    och = getattr(request.app.state, "on_instances_changed", None)
    if och is not None:
        await och()
    return RedirectResponse(url="/?flash=deleted", status_code=303)


async def instance_mcpservers_json(request: Request) -> Response:
    app = request.app
    root: Path = app.state.root  # type: ignore[attr-defined]
    instances = _instances_dir(root)
    name = request.path_params["name"]
    p = instances / name
    instance_path = request.query_params.get("instance_path") or str(p)
    local_key = request.query_params.get("local_key") or name
    remote_key = request.query_params.get("remote_key") or f"{name}-remote"
    remote_url = request.query_params.get("remote_url") or _default_remote_mcp_url(request)

    payload = _generate_mcp_servers_json(
        instance_path=instance_path,
        local_key=local_key,
        remote_key=remote_key,
        remote_url=remote_url,
    )
    return JSONResponse(payload)


async def instance_mcpservers_local_json(request: Request) -> Response:
    app = request.app
    root: Path = app.state.root  # type: ignore[attr-defined]
    instances = _instances_dir(root)
    name = request.path_params["name"]
    p = instances / name
    instance_path = request.query_params.get("instance_path") or str(p)
    local_key = request.query_params.get("local_key") or name
    payload = _generate_mcp_servers_json_local(instance_path=instance_path, local_key=local_key)
    return JSONResponse(payload)


async def instance_mcpservers_remote_json(request: Request) -> Response:
    app = request.app
    root: Path = app.state.root  # type: ignore[attr-defined]
    instances = _instances_dir(root)
    name = request.path_params["name"]
    p = instances / name
    cfg = load_instance(p)

    remote_key = request.query_params.get("remote_key") or f"{name}-remote"
    remote_url = request.query_params.get("remote_url") or _default_remote_mcp_url(request)
    if not cfg.auth or not cfg.auth.enabled:
        return JSONResponse({"error": "auth disabled for this instance"}, status_code=400)

    try:
        token = mint_token(token_secret=cfg.auth.token_secret, sub=cfg.instance_id, ttl_sec=cfg.auth.token_ttl_sec)
    except TokenError as e:
        return JSONResponse({"error": "token mint failed", "detail": str(e)}, status_code=500)

    payload = _generate_mcp_servers_json_remote(remote_key=remote_key, remote_url=remote_url, bearer_token=token)
    return JSONResponse(payload)


async def api_instances(request: Request) -> Response:
    app = request.app
    root: Path = app.state.root  # type: ignore[attr-defined]
    instances = _instances_dir(root)
    items = _list_instances(instances)
    return JSONResponse({"items": items})


async def api_instance_detail(request: Request) -> Response:
    app = request.app
    root: Path = app.state.root  # type: ignore[attr-defined]
    instances = _instances_dir(root)
    name = request.path_params["name"]
    p = instances / name
    if not p.is_dir():
        return JSONResponse({"error": "not found"}, status_code=404)
    cfg = load_instance(p)
    payload = {
        "name": name,
        "instance_id": cfg.instance_id,
        "mcp": {
            "name": cfg.mcp_name,
            "version": cfg.mcp_version,
            "description": cfg.mcp_description,
            "tool_prefix": cfg.tool_prefix,
            "panel_base_url": cfg.panel_base_url,
        },
        "auth": {
            "enabled": bool(cfg.auth and cfg.auth.enabled),
            "token_ttl_sec": (cfg.auth.token_ttl_sec if cfg.auth else None),
        },
        "db": (
            {
                "host": cfg.db.host,
                "port": cfg.db.port,
                "dbname": cfg.db.dbname,
                "username": cfg.db.username,
                "connect_timeout_sec": cfg.db.connect_timeout_sec,
                "query_timeout_ms": cfg.db.query_timeout_ms,
            }
            if cfg.db
            else None
        ),
        "paths": {
            "instance_dir": str(p),
            "instance_yaml": str(p / "instance.yaml"),
            "dotenv": str(p / ".env"),
            "manifest": str(p / "manifest.json"),
        },
    }
    return JSONResponse(payload)


def build_app(
    *,
    root: Path,
    on_instances_changed: Callable[[], Awaitable[None]] | None = None,
) -> Starlette:
    app = Starlette(
        routes=[
            Route("/", index, methods=["GET"]),
            Route("/favicon.ico", lambda request: Response(status_code=204), methods=["GET"]),
            Route("/api/instances", api_instances, methods=["GET"]),
            Route("/api/instances/{name:str}", api_instance_detail, methods=["GET"]),
            Route("/instances/new", new_scada_get, methods=["GET"]),
            Route("/instances/new", new_scada_post, methods=["POST"]),
            Route("/instances/{name:str}", instance_view, methods=["GET"]),
            Route("/instances/{name:str}/delete", delete_instance_post, methods=["POST"]),
            Route("/instances/{name:str}/edit", edit_instance_get, methods=["GET"]),
            Route("/instances/{name:str}/edit", edit_instance_post, methods=["POST"]),
            Route("/instances/{name:str}/mcpServers.json", instance_mcpservers_json, methods=["GET"]),
            Route("/instances/{name:str}/mcpServers.local.json", instance_mcpservers_local_json, methods=["GET"]),
            Route("/instances/{name:str}/mcpServers.remote.json", instance_mcpservers_remote_json, methods=["GET"]),
        ]
    )
    app.state.root = root
    app.state.jinja = _jinja(root)
    app.state.on_instances_changed = on_instances_changed
    return app


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="scada-mcp-manager")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8002)
    p.add_argument("--root", default="", help="Project root (defaults to auto-detect)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(list(os.sys.argv[1:] if argv is None else argv))
    root = Path(ns.root).resolve() if ns.root else _project_root()
    app = build_app(root=root)
    import uvicorn

    uvicorn.run(app, host=ns.host, port=ns.port, log_level=os.getenv("LOG_LEVEL", "info"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
