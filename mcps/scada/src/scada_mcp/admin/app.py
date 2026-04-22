from __future__ import annotations

import json
import logging
import re
import shutil
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.applications import Starlette
from starlette.datastructures import FormData
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Receive, Scope, Send

from ..config import load_instance, validate_tool_prefix
from .auth_session import (
    create_session,
    destroy_session,
    get_session,
    get_session_from_request,
    verify_password,
)
from .store import DataStore

logger = logging.getLogger("scada_mcp.admin")

_NAME_RE = re.compile(r"^[a-zA-Z0-9._-]{1,64}$")

# Paths exempt from authentication
_PUBLIC_PATH_PREFIXES = ("/login", "/static/", "/mcp", "/files")


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class AdminAuthMiddleware:
    """ASGI middleware that guards all routes behind session auth.

    Exempt paths (login, static, mcp, etc.) are passed through.
    For everything else, the ``admin_session`` cookie is validated.
    If invalid the user is redirected to ``/login``.
    If valid the session's user info is injected into ``scope["state"]``.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")

        # Check exempt paths
        if path == "/login" or any(path.startswith(p) for p in _PUBLIC_PATH_PREFIXES):
            await self.app(scope, receive, send)
            return

        # Validate session cookie
        request = Request(scope)
        session = get_session_from_request(request)
        if session is None:
            response = RedirectResponse(url="/login", status_code=302)
            await response(scope, receive, send)
            return

        # Inject user info into scope state
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["user"] = {
            "username": session["username"],
            "role": session["role"],
        }

        await self.app(scope, receive, send)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _instances_dir(root: Path) -> Path:
    return root / "instances"


def _jinja_env() -> Environment:
    templates_dir = Path(__file__).resolve().parent / "templates"
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
    )


def _render(
    env: Environment,
    template_name: str,
    *,
    user: dict | None = None,
    flash: dict | None = None,
    **ctx: Any,
) -> HTMLResponse:
    tpl = env.get_template(template_name)
    html = tpl.render(user=user or {}, flash=flash, **ctx)
    return HTMLResponse(html)


def _get_user(request: Request) -> dict:
    """Extract user dict from request scope (set by middleware)."""
    return request.state.user


def _require_admin(request: Request) -> dict:
    """Return user dict if admin, otherwise raise a 403-level ValueError."""
    user = _get_user(request)
    if user.get("role") != "admin":
        raise PermissionError("Admin role required")
    return user


def _flash_from_query(request: Request) -> dict | None:
    code = request.query_params.get("flash")
    if not code:
        return None
    messages = {
        "created": ("Instance created.", "success"),
        "saved": ("Saved.", "success"),
        "deleted": ("Instance deleted.", "success"),
        "token_created": ("Token created.", "success"),
        "token_revoked": ("Token revoked.", "success"),
        "token_deleted": ("Token deleted.", "success"),
        "user_created": ("User created.", "success"),
        "user_deleted": ("User deleted.", "success"),
        "user_updated": ("User updated.", "success"),
        "password_changed": ("Password changed.", "success"),
        "password_mismatch": ("Passwords do not match.", "error"),
        "password_too_short": ("Password must be at least 4 characters.", "error"),
        "skill_created": ("Skill created.", "success"),
        "skill_saved": ("Skill saved.", "success"),
        "skill_deleted": ("Skill deleted.", "success"),
        "skill_file_created": ("File created.", "success"),
        "skill_file_deleted": ("File deleted.", "success"),
        "error": ("An error occurred.", "error"),
        "forbidden": ("Permission denied.", "error"),
        "delete_bad_confirm": ("Please type the instance name correctly to confirm.", "error"),
    }
    msg, kind = messages.get(code, (code.replace("_", " "), "info"))
    return {"message": msg, "type": kind}


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


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
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USERNAME",
        "DB_PASSWORD",
        "KORUBIN_POINT_DISPLAY_ROOT",
    ]
    # Legacy DB alias'larini .env'e yazma — config.py'deki _env_first
    # bu alias'lara ONCE bakar ve yeni DB_USERNAME/DB_PASSWORD degerlerini
    # override eder. Eski degerlerin kaymasini onlemek icin strip et.
    legacy_db_aliases = {
        "KORUBIN_DB_HOST", "KORUBIN_DB_PORT", "KORUBIN_DB_NAME", "KORUBIN_DB_DATABASE",
        "KORUBIN_DB_USERNAME", "KORUBIN_DB_USER", "KORUBIN_DB_PASSWORD", "KORUBIN_DB_CHARSET",
        "CORUM_DB_HOST", "CORUM_DB_PORT", "CORUM_DB_NAME",
        "CORUM_DB_USERNAME", "CORUM_DB_PASSWORD",
        "WINCAPS_DB_HOST", "WINCAPS_DB_PORT", "WINCAPS_DB_NAME",
        "WINCAPS_DB_USER", "WINCAPS_DB_PASSWORD",
        "DB_USER", "DB_DATABASE", "DB_CHARSET",
        # Eski secret'lar da silinir — auto-generate ediliyor artik
        "MCP_ADMIN_SECRET", "MCP_TOKEN_SECRET",
    }
    lines: list[str] = []
    for k in keys:
        if k in values:
            lines.append(f"{k}={values[k]}")
    for k in sorted(values.keys()):
        if k in keys or k in legacy_db_aliases:
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
    toolpacks: str = "scada",
) -> None:
    desc_escaped = mcp_description.replace('"', '\\"')
    version_escaped = (mcp_version or "1.0.0").replace('"', '\\"')
    instructions_block = _indent_block(mcp_instructions, 2)

    # Build toolpacks list from comma-separated value
    tp_list = [t.strip() for t in toolpacks.split(",") if t.strip()]
    if not tp_list:
        tp_list = ["scada"]
    # Legacy "both" support
    if tp_list == ["both"]:
        tp_list = ["scada", "korucaps"]
    tp_lines = "".join(f'\n  - "{t}"' for t in tp_list)

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
            f"toolpacks:{tp_lines}",
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
            "",
        ]
    )
    _write_text(path, content)


def _scada_tool_groups(prefix: str) -> list[dict[str, Any]]:
    from ..toolpacks import default_scada_packs

    groups: list[dict[str, Any]] = []
    for spec in default_scada_packs():
        groups.extend(spec.pack.manifest_groups(prefix=prefix))
    return groups


def _resolve_tool_names(cfg) -> list[str]:
    """Load all tool names for an instance by resolving its toolpacks."""
    from ..toolpacks import default_scada_packs, resolve_packs

    tool_names: list[str] = []
    if cfg.toolpacks:
        packs = resolve_packs(cfg.toolpacks)
    else:
        packs = default_scada_packs()

    for spec in packs:
        try:
            for group in spec.pack.manifest_groups(prefix=cfg.tool_prefix):
                for tool in group.get("tools", []):
                    name = tool.get("name")
                    if name:
                        tool_names.append(name)
        except Exception:
            continue
    return tool_names


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


def _require_instance_name(name: str) -> str:
    name = name.strip()
    if not _NAME_RE.fullmatch(name):
        raise ValueError("Instance name must match ^[a-zA-Z0-9._-]{1,64}$")
    return name


def _list_instances(instances_path: Path) -> list[dict]:
    """Return a list of dicts describing each instance directory."""
    items: list[dict] = []
    if not instances_path.exists():
        return items
    for p in sorted(instances_path.iterdir()):
        if not p.is_dir() or p.name.startswith(".") or p.name == "_template":
            continue
        try:
            cfg = load_instance(p)
            # Determine type from toolpacks
            tp = cfg.toolpacks or ["scada"]
            if "scada" in tp and "korucaps" in tp:
                inst_type = "both"
            elif "korucaps" in tp:
                inst_type = "korucaps"
            else:
                inst_type = "scada"

            items.append({
                "name": p.name,
                "type": inst_type,
                "mcp_name": cfg.mcp_name,
                "tool_prefix": cfg.tool_prefix,
                "description": cfg.mcp_description,
                "panel_url": cfg.panel_base_url,
                "db_host": cfg.db.host if cfg.db else None,
                "db_port": cfg.db.port if cfg.db else None,
                "db_name": cfg.db.dbname if cfg.db else None,
                "db_username": cfg.db.username if cfg.db else None,
            })
        except Exception:
            continue
    return items


def _get_token_status(tok: dict) -> str:
    if tok.get("revoked"):
        return "revoked"
    exp = tok.get("expires_at")
    if exp:
        try:
            exp_dt = datetime.fromisoformat(exp)
            if exp_dt < datetime.now(timezone.utc):
                return "expired"
        except Exception:
            pass
    return "active"


def _format_tokens(tokens: list[dict]) -> list[dict]:
    """Format token records for template display."""
    result = []
    for tok in tokens:
        result.append({
            "id": tok.get("token_id", ""),
            "name": tok.get("name", ""),
            "instances": tok.get("allowed_instances", []),
            "created_by": tok.get("created_by", ""),
            "created_at": tok.get("created_at", ""),
            "expires_at": tok.get("expires_at"),
            "status": _get_token_status(tok),
        })
    return result


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

async def login_get(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    # If already logged in, redirect to dashboard
    session = get_session_from_request(request)
    if session is not None:
        return RedirectResponse(url="/", status_code=302)
    return _render(env, "login.html", error=None, username="")


async def login_post(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    store: DataStore = request.app.state.store
    form: FormData = await request.form()

    username = str(form.get("username", "")).strip()
    password = str(form.get("password", ""))

    user = store.get_user(username)
    if user is None or not verify_password(password, user["password_hash"]):
        return _render(env, "login.html", error="Invalid username or password.", username=username)

    token = create_session(username, user["role"])
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        "admin_session",
        token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )
    return response


async def logout_post(request: Request) -> Response:
    cookie = request.cookies.get("admin_session")
    if cookie:
        destroy_session(cookie)
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("admin_session")
    return response


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

async def dashboard(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    store: DataStore = request.app.state.store
    root: Path = request.app.state.root
    user = _get_user(request)

    instances = _list_instances(_instances_dir(root))
    tokens = store.load_tokens()
    active_tokens = [t for t in tokens if not t.get("revoked")]
    users = store.load_users()

    flash = _flash_from_query(request)
    return _render(
        env,
        "dashboard.html",
        user=user,
        flash=flash,
        instance_count=len(instances),
        token_count=len(active_tokens),
        user_count=len(users),
    )


# ---------------------------------------------------------------------------
# Instances
# ---------------------------------------------------------------------------

async def instances_list(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    root: Path = request.app.state.root
    user = _get_user(request)

    instances = _list_instances(_instances_dir(root))
    flash = _flash_from_query(request)
    return _render(
        env,
        "instances.html",
        user=user,
        flash=flash,
        instances=instances,
    )


async def instance_create_get(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    user = _get_user(request)
    try:
        _require_admin(request)
    except PermissionError:
        return Response("Forbidden", status_code=403)

    return _render(env, "instance_create.html", user=user, error=None)


async def instance_create_post(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    root: Path = request.app.state.root
    user = _get_user(request)
    try:
        _require_admin(request)
    except PermissionError:
        return Response("Forbidden", status_code=403)

    instances_path = _instances_dir(root)
    template_dir = instances_path / "_template"
    form: FormData = await request.form()

    try:
        name = _require_instance_name(str(form.get("instance_name", "")))
        toolpacks_value = str(form.get("toolpacks", "scada")).strip()
        tool_prefix = validate_tool_prefix(str(form.get("tool_prefix", "")))
        mcp_name = str(form.get("mcp_name", "")).strip()
        mcp_description = str(form.get("mcp_description", "")).strip()

        db_host = str(form.get("db_host", "")).strip()
        db_port = int(str(form.get("db_port", "3306")).strip() or "3306")
        db_name = str(form.get("db_name", "")).strip()
        db_username = str(form.get("db_username", "")).strip()
        db_password = str(form.get("db_password", "")).strip()

        if not (mcp_name and mcp_description and db_host and db_name):
            raise ValueError("Missing required fields.")

        dst = instances_path / name
        if dst.exists():
            raise ValueError(f"Instance already exists: {name}")

        # Copy template if it exists, otherwise create dir
        if template_dir.exists():
            shutil.copytree(template_dir, dst)
        else:
            dst.mkdir(parents=True, exist_ok=True)

        # Write .env
        env_values: dict[str, str] = {}
        if db_host:
            env_values["DB_HOST"] = db_host
        env_values["DB_PORT"] = str(db_port)
        if db_name:
            env_values["DB_NAME"] = db_name
        if db_username:
            env_values["DB_USERNAME"] = db_username
        if db_password:
            env_values["DB_PASSWORD"] = db_password
        _write_env(dst / ".env", env_values)

        # Write instance.yaml
        _write_instance_yaml(
            path=dst / "instance.yaml",
            mcp_name=mcp_name,
            mcp_version="1.0.0",
            mcp_description=mcp_description,
            mcp_instructions="",
            tool_prefix=tool_prefix,
            panel_base_url="",
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            toolpacks=toolpacks_value,
        )

        # Write manifest.json
        manifest = {
            "_schema": "scada_mcp_manifest",
            "version": 1,
            "title": f"SCADA MCP manifest ({name})",
            "purpose": mcp_description,
            "tool_groups": _scada_tool_groups(tool_prefix),
        }
        _write_text(dst / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

        # Notify callback
        och = request.app.state.on_instances_changed
        if och is not None:
            await och()

        return RedirectResponse(url=f"/instances/{name}?flash=created", status_code=303)

    except Exception as e:
        logger.exception("Failed to create instance")
        return _render(env, "instance_create.html", user=user, error=str(e))


async def instance_detail(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    root: Path = request.app.state.root
    store: DataStore = request.app.state.store
    user = _get_user(request)
    name = request.path_params["name"]

    instances_path = _instances_dir(root)
    p = instances_path / name
    if not p.is_dir():
        return RedirectResponse(url="/instances?flash=error", status_code=302)

    cfg = load_instance(p)

    # Determine type
    tp = cfg.toolpacks or ["scada"]
    if "scada" in tp and "korucaps" in tp:
        inst_type = "both"
    elif "korucaps" in tp:
        inst_type = "korucaps"
    else:
        inst_type = "scada"

    # Resolve tools
    tool_names = _resolve_tool_names(cfg)

    # Get tokens for this instance
    all_tokens = store.load_tokens()
    instance_tokens = [t for t in all_tokens if name in t.get("allowed_instances", [])]
    formatted_tokens = _format_tokens(instance_tokens)

    # Load skills for this instance
    skills_data = []
    try:
        from ..skills.loader import SkillLoader
        instance_skills = p / "skills"
        global_skills = instances_path.parent / "skills"
        loader = SkillLoader(instance_skills if instance_skills.is_dir() else None, global_skills if global_skills.is_dir() else None)
        for s in loader.list():
            s["files"] = loader.list_files(s["name"])
            skills_data.append(s)
    except Exception:
        pass

    instance_data = {
        "name": name,
        "type": inst_type,
        "toolpacks": tp,
        "mcp_name": cfg.mcp_name,
        "tool_prefix": cfg.tool_prefix,
        "description": cfg.mcp_description,
        "panel_url": cfg.panel_base_url,
        "db_host": cfg.db.host if cfg.db else None,
        "db_port": cfg.db.port if cfg.db else None,
        "db_name": cfg.db.dbname if cfg.db else None,
    }

    flash = _flash_from_query(request)
    return _render(
        env,
        "instance_detail.html",
        user=user,
        flash=flash,
        instance=instance_data,
        tools=tool_names,
        tokens=formatted_tokens,
        skills=skills_data,
    )


async def instance_edit_get(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    root: Path = request.app.state.root
    user = _get_user(request)
    try:
        _require_admin(request)
    except PermissionError:
        return Response("Forbidden", status_code=403)

    name = request.path_params["name"]
    instances_path = _instances_dir(root)
    p = instances_path / name
    if not p.is_dir():
        return RedirectResponse(url="/instances?flash=error", status_code=302)

    cfg = load_instance(p)
    envvals = _read_env(p / ".env")

    # Build toolpacks comma-separated value for the dropdown
    tp = cfg.toolpacks or ["scada"]
    toolpacks_value = ",".join(tp)

    instance_data = {
        "name": name,
        "toolpacks_value": toolpacks_value,
        "mcp_name": cfg.mcp_name,
        "tool_prefix": cfg.tool_prefix,
        "description": cfg.mcp_description,
        "panel_url": cfg.panel_base_url,
        "db_host": cfg.db.host if cfg.db else None,
        "db_port": cfg.db.port if cfg.db else None,
        "db_name": cfg.db.dbname if cfg.db else None,
        "db_username": cfg.db.username if cfg.db else None,
    }

    return _render(
        env,
        "instance_edit.html",
        user=user,
        instance=instance_data,
        error=None,
    )


async def instance_edit_post(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    root: Path = request.app.state.root
    user = _get_user(request)
    try:
        _require_admin(request)
    except PermissionError:
        return Response("Forbidden", status_code=403)

    name = request.path_params["name"]
    instances_path = _instances_dir(root)
    p = instances_path / name
    form: FormData = await request.form()

    try:
        cfg = load_instance(p)
        current_env = _read_env(p / ".env")

        toolpacks_value = str(form.get("toolpacks", "scada")).strip()
        mcp_name = str(form.get("mcp_name", "")).strip()
        mcp_description = str(form.get("mcp_description", "")).strip()
        tool_prefix = validate_tool_prefix(str(form.get("tool_prefix", "")).strip())

        db_host = str(form.get("db_host", "")).strip()
        db_port = int(str(form.get("db_port", "3306")).strip() or "3306")
        db_name = str(form.get("db_name", "")).strip()
        db_username = str(form.get("db_username", "")).strip()
        db_password = str(form.get("db_password", "")).strip()

        if not (mcp_name and mcp_description and db_host and db_name):
            raise ValueError("Missing required fields.")

        # Update .env
        new_env = dict(current_env)
        # Remove legacy secrets if present
        new_env.pop("MCP_ADMIN_SECRET", None)
        new_env.pop("MCP_TOKEN_SECRET", None)
        new_env["DB_HOST"] = db_host
        new_env["DB_PORT"] = str(db_port)
        new_env["DB_NAME"] = db_name
        if db_username:
            new_env["DB_USERNAME"] = db_username
        if db_password:
            new_env["DB_PASSWORD"] = db_password
        _write_env(p / ".env", new_env)

        # Update instance.yaml
        _write_instance_yaml(
            path=p / "instance.yaml",
            mcp_name=mcp_name,
            mcp_version=cfg.mcp_version,
            mcp_description=mcp_description,
            mcp_instructions=cfg.mcp_instructions or "",
            tool_prefix=tool_prefix,
            panel_base_url=cfg.panel_base_url or "",
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            toolpacks=toolpacks_value,
        )

        # Rewrite manifest with new prefix
        _rewrite_manifest_prefix(p / "manifest.json", new_prefix=tool_prefix)

        # Notify callback
        och = request.app.state.on_instances_changed
        if och is not None:
            await och()

        return RedirectResponse(url=f"/instances/{name}?flash=saved", status_code=303)

    except Exception as e:
        logger.exception("Failed to edit instance %s", name)
        cfg = load_instance(p)
        tp = cfg.toolpacks or ["scada"]
        toolpacks_value = ",".join(tp)
        instance_data = {
            "name": name,
            "toolpacks_value": toolpacks_value,
            "mcp_name": cfg.mcp_name,
            "tool_prefix": cfg.tool_prefix,
            "description": cfg.mcp_description,
            "panel_url": cfg.panel_base_url,
            "db_host": cfg.db.host if cfg.db else None,
            "db_port": cfg.db.port if cfg.db else None,
            "db_name": cfg.db.dbname if cfg.db else None,
            "db_username": cfg.db.username if cfg.db else None,
        }
        return _render(
            env,
            "instance_edit.html",
            user=user,
            instance=instance_data,
            error=str(e),
        )


async def instance_delete_post(request: Request) -> Response:
    root: Path = request.app.state.root
    try:
        _require_admin(request)
    except PermissionError:
        return Response("Forbidden", status_code=403)

    name = request.path_params["name"]
    instances_path = _instances_dir(root)

    if name in ("_template",) or name.startswith("."):
        return RedirectResponse(url="/instances?flash=forbidden", status_code=303)

    p = instances_path / name
    if not p.is_dir():
        return RedirectResponse(url="/instances?flash=deleted", status_code=303)

    shutil.rmtree(p)

    och = request.app.state.on_instances_changed
    if och is not None:
        await och()

    return RedirectResponse(url="/instances?flash=deleted", status_code=303)


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

async def tokens_list(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    root: Path = request.app.state.root
    store: DataStore = request.app.state.store
    user = _get_user(request)

    all_tokens = store.load_tokens()
    formatted_tokens = _format_tokens(all_tokens)
    instances = _list_instances(_instances_dir(root))

    flash = _flash_from_query(request)
    new_token_jwt = request.query_params.get("new_token_jwt")

    scheme = request.headers.get("x-forwarded-proto", request.url.scheme or "http")
    host = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost:8001"))
    mcp_base_url = f"{scheme}://{host}"

    return _render(
        env,
        "tokens.html",
        user=user,
        flash=flash,
        tokens=formatted_tokens,
        instances=instances,
        new_token_jwt=new_token_jwt,
        new_token_name=request.query_params.get("new_token_name", "envest-mcp"),
        mcp_base_url=mcp_base_url,
    )


async def token_create_post(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    root: Path = request.app.state.root
    store: DataStore = request.app.state.store
    user = _get_user(request)

    form: FormData = await request.form()

    token_name = str(form.get("token_name", "")).strip()
    instance_access = form.getlist("instance_access")
    expiry_type = str(form.get("expiry_type", "unlimited")).strip()
    expires_at_str = str(form.get("expires_at", "")).strip()

    if not token_name:
        # Reload page with error
        all_tokens = store.load_tokens()
        formatted_tokens = _format_tokens(all_tokens)
        instances = _list_instances(_instances_dir(root))
        return _render(
            env,
            "tokens.html",
            user=user,
            tokens=formatted_tokens,
            instances=instances,
            flash={"message": "Token name is required.", "type": "error"},
            new_token_jwt=None,
        )

    expires_at: str | None = None
    if expiry_type == "custom" and expires_at_str:
        # Convert date string to ISO datetime
        expires_at = datetime.fromisoformat(expires_at_str).replace(
            tzinfo=timezone.utc
        ).isoformat()

    allowed_instances = [str(i) for i in instance_access]

    try:
        _record, jwt_string = store.create_token(
            name=token_name,
            allowed_instances=allowed_instances,
            created_by=user["username"],
            expires_at=expires_at,
        )
    except Exception as e:
        logger.exception("Failed to create token")
        all_tokens = store.load_tokens()
        formatted_tokens = _format_tokens(all_tokens)
        instances = _list_instances(_instances_dir(root))
        return _render(
            env,
            "tokens.html",
            user=user,
            tokens=formatted_tokens,
            instances=instances,
            flash={"message": f"Token creation failed: {e}", "type": "error"},
            new_token_jwt=None,
        )

    # Reload tokens and render with the JWT shown
    all_tokens = store.load_tokens()
    formatted_tokens = _format_tokens(all_tokens)
    instances = _list_instances(_instances_dir(root))

    # Build MCP base URL from request
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme or "http")
    host = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost:8001"))
    mcp_base_url = f"{scheme}://{host}"

    return _render(
        env,
        "tokens.html",
        user=user,
        flash={"message": "Token created.", "type": "success"},
        tokens=formatted_tokens,
        instances=instances,
        new_token_jwt=jwt_string,
        new_token_name=token_name,
        mcp_base_url=mcp_base_url,
    )


async def token_revoke_post(request: Request) -> Response:
    store: DataStore = request.app.state.store
    try:
        _require_admin(request)
    except PermissionError:
        return Response("Forbidden", status_code=403)

    token_id = request.path_params["id"]
    store.revoke_token(token_id)
    return RedirectResponse(url="/tokens?flash=token_revoked", status_code=303)


async def token_delete_post(request: Request) -> Response:
    store: DataStore = request.app.state.store
    try:
        _require_admin(request)
    except PermissionError:
        return Response("Forbidden", status_code=403)

    token_id = request.path_params["id"]
    store.delete_token(token_id)
    return RedirectResponse(url="/tokens?flash=token_deleted", status_code=303)


async def token_detail(request: Request) -> Response:
    """GET /tokens/{id} -- show token detail / edit page."""
    env: Environment = request.app.state.jinja
    root: Path = request.app.state.root
    store: DataStore = request.app.state.store
    user = _get_user(request)

    token_id = request.path_params["id"]
    tok_raw = store.get_token(token_id)
    if tok_raw is None:
        return RedirectResponse(url="/tokens?flash=error", status_code=302)

    # Format for display
    tok = {
        "id": tok_raw.get("token_id", ""),
        "name": tok_raw.get("name", ""),
        "instances": tok_raw.get("allowed_instances", []),
        "created_by": tok_raw.get("created_by", ""),
        "created_at": tok_raw.get("created_at", ""),
        "expires_at": tok_raw.get("expires_at"),
        "status": _get_token_status(tok_raw),
        "jwt": tok_raw.get("jwt", ""),
    }

    instances = _list_instances(_instances_dir(root))
    flash = _flash_from_query(request)

    # Build MCP base URL from request
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme or "http")
    host = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost:8001"))
    mcp_base_url = f"{scheme}://{host}"

    # Build per-instance env info for local config examples
    instance_env_map: dict[str, dict[str, str]] = {}
    for inst in instances:
        inst_name = inst["name"]
        env_path = _instances_dir(root) / inst_name / ".env"
        env_vals = _read_env(env_path)
        instance_env_map[inst_name] = {
            "db_host": inst.get("db_host") or env_vals.get("DB_HOST", "localhost"),
            "db_port": str(inst.get("db_port") or env_vals.get("DB_PORT", "3306")),
            "db_name": inst.get("db_name") or env_vals.get("DB_NAME", ""),
            "db_username": env_vals.get("DB_USERNAME", ""),
            "db_password": env_vals.get("DB_PASSWORD", ""),
        }

    return _render(
        env,
        "token_detail.html",
        user=user,
        flash=flash,
        token=tok,
        instances=instances,
        mcp_base_url=mcp_base_url,
        instance_env_map=json.dumps(instance_env_map),
    )


async def token_edit_post(request: Request) -> Response:
    """POST /tokens/{id}/edit -- update token name and instances."""
    store: DataStore = request.app.state.store
    try:
        _require_admin(request)
    except PermissionError:
        return Response("Forbidden", status_code=403)

    token_id = request.path_params["id"]
    form: FormData = await request.form()

    name = str(form.get("token_name", "")).strip() or None
    instance_access = form.getlist("instance_access")
    allowed_instances = [str(i) for i in instance_access] if instance_access is not None else None

    expiry_type = str(form.get("expiry_type", "keep")).strip()
    if expiry_type == "unlimited":
        expires_at: str | None | object = None
    elif expiry_type == "custom":
        expires_at_str = str(form.get("expires_at", "")).strip()
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str).replace(tzinfo=timezone.utc).isoformat()
        else:
            expires_at = DataStore._SENTINEL  # leave unchanged
    else:
        expires_at = DataStore._SENTINEL  # leave unchanged

    store.update_token(
        token_id,
        name=name,
        allowed_instances=allowed_instances,
        expires_at=expires_at,
    )

    return RedirectResponse(url=f"/tokens/{token_id}?flash=saved", status_code=303)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

async def users_list(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    store: DataStore = request.app.state.store
    user = _get_user(request)

    is_admin = user.get("role") == "admin"
    users = store.load_users() if is_admin else []
    flash = _flash_from_query(request)
    return _render(
        env,
        "users.html",
        user=user,
        flash=flash,
        users=users,
    )


async def user_create_post(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    store: DataStore = request.app.state.store
    user = _get_user(request)
    try:
        _require_admin(request)
    except PermissionError:
        return Response("Forbidden", status_code=403)

    form: FormData = await request.form()
    username = str(form.get("username", "")).strip()
    password = str(form.get("password", ""))
    role = str(form.get("role", "viewer")).strip()

    if not username or not password:
        users = store.load_users()
        return _render(
            env,
            "users.html",
            user=user,
            users=users,
            flash={"message": "Username and password are required.", "type": "error"},
        )

    if role not in ("admin", "viewer"):
        role = "viewer"

    try:
        store.create_user(username, password, role)
    except ValueError as e:
        users = store.load_users()
        return _render(
            env,
            "users.html",
            user=user,
            users=users,
            flash={"message": str(e), "type": "error"},
        )

    return RedirectResponse(url="/users?flash=user_created", status_code=303)


async def user_delete_post(request: Request) -> Response:
    store: DataStore = request.app.state.store
    try:
        _require_admin(request)
    except PermissionError:
        return Response("Forbidden", status_code=403)

    username = request.path_params["username"]
    try:
        store.delete_user(username)
    except ValueError as e:
        logger.warning("Cannot delete user %s: %s", username, e)
        return RedirectResponse(url="/users?flash=error", status_code=303)

    return RedirectResponse(url="/users?flash=user_deleted", status_code=303)


async def user_profile_post(request: Request) -> Response:
    """Any logged-in user can change their own password."""
    store: DataStore = request.app.state.store
    user = _get_user(request)
    form: FormData = await request.form()

    new_password = str(form.get("new_password", ""))
    confirm_password = str(form.get("confirm_password", ""))

    if not new_password or len(new_password) < 4:
        return RedirectResponse(url="/users?flash=password_too_short", status_code=303)

    if new_password != confirm_password:
        return RedirectResponse(url="/users?flash=password_mismatch", status_code=303)

    store.update_user_password(user["username"], new_password)
    return RedirectResponse(url="/users?flash=password_changed", status_code=303)


async def user_edit_post(request: Request) -> Response:
    """Admin can edit any user's role and password."""
    store: DataStore = request.app.state.store
    try:
        _require_admin(request)
    except PermissionError:
        return Response("Forbidden", status_code=403)

    form: FormData = await request.form()
    username = str(form.get("edit_username", "")).strip()
    new_role = str(form.get("edit_role", "")).strip()
    new_password = str(form.get("edit_password", "")).strip()

    if not username:
        return RedirectResponse(url="/users?flash=error", status_code=303)

    # Update role
    if new_role in ("admin", "viewer"):
        try:
            store.update_user_role(username, new_role)
        except ValueError as e:
            logger.warning("Cannot change role for %s: %s", username, e)
            return RedirectResponse(url="/users?flash=error", status_code=303)

    # Update password if provided
    if new_password and len(new_password) >= 4:
        store.update_user_password(username, new_password)

    return RedirectResponse(url="/users?flash=user_updated", status_code=303)


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

_SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


def _global_skills_dir(root: Path) -> Path:
    """Return the global skills directory: <root>/skills (i.e. mcps/scada/skills/)."""
    return root / "skills"


def _instance_skills_dir(root: Path, instance_name: str) -> Path:
    return _instances_dir(root) / instance_name / "skills"


def _resolve_skill_path(root: Path, name: str) -> Path | None:
    """Resolve a skill key to its directory path.

    Naming convention:
    - "skillname" -> global: <root>/../skills/skillname/
    - "instancename:skillname" -> instance: instances/instancename/skills/skillname/
    """
    if ":" in name:
        instance_name, skill_name = name.split(":", 1)
        if not _NAME_RE.fullmatch(instance_name) or not _SKILL_NAME_RE.fullmatch(skill_name):
            return None
        return _instance_skills_dir(root, instance_name) / skill_name
    else:
        if not _SKILL_NAME_RE.fullmatch(name):
            return None
        return _global_skills_dir(root) / name


def _safe_skill_file_path(skill_dir: Path, file_path: str) -> Path | None:
    """Resolve a file path within a skill dir with traversal protection."""
    file_path = file_path.strip()
    if not file_path:
        return None
    try:
        target = (skill_dir / file_path).resolve()
    except (ValueError, OSError):
        return None
    try:
        target.relative_to(skill_dir.resolve())
    except ValueError:
        return None
    if target.suffix.lower() != ".md":
        return None
    return target


def _scan_skills(root: Path) -> list[dict]:
    """Scan global and all instance skill directories, return a list of skill dicts."""
    from ..skills.loader import _parse_frontmatter

    results: list[dict] = []

    # Global skills
    gdir = _global_skills_dir(root)
    if gdir.is_dir():
        for skill_dir in sorted(gdir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            try:
                text = skill_file.read_text(encoding="utf-8")
                meta, _ = _parse_frontmatter(text)
            except Exception:
                meta = {}
            md_files = sorted(str(f.relative_to(skill_dir)).replace("\\", "/")
                              for f in skill_dir.rglob("*.md"))
            results.append({
                "key": skill_dir.name,
                "name": meta.get("name", skill_dir.name),
                "description": meta.get("description", ""),
                "version": meta.get("version", "1.0.0"),
                "source": "global",
                "source_label": "Global",
                "file_count": len(md_files),
            })

    # Instance skills
    instances_path = _instances_dir(root)
    if instances_path.is_dir():
        for inst_dir in sorted(instances_path.iterdir()):
            if not inst_dir.is_dir() or inst_dir.name.startswith(".") or inst_dir.name == "_template":
                continue
            inst_skills = inst_dir / "skills"
            if not inst_skills.is_dir():
                continue
            for skill_dir in sorted(inst_skills.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / "SKILL.md"
                if not skill_file.exists():
                    continue
                try:
                    text = skill_file.read_text(encoding="utf-8")
                    meta, _ = _parse_frontmatter(text)
                except Exception:
                    meta = {}
                md_files = sorted(str(f.relative_to(skill_dir)).replace("\\", "/")
                                  for f in skill_dir.rglob("*.md"))
                results.append({
                    "key": f"{inst_dir.name}:{skill_dir.name}",
                    "name": meta.get("name", skill_dir.name),
                    "description": meta.get("description", ""),
                    "version": meta.get("version", "1.0.0"),
                    "source": f"instance:{inst_dir.name}",
                    "source_label": f"Instance: {inst_dir.name}",
                    "file_count": len(md_files),
                })

    return results


async def skills_list(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    root: Path = request.app.state.root
    user = _get_user(request)

    skills = _scan_skills(root)

    # Build list of instances for the create form
    instances = _list_instances(_instances_dir(root))

    flash = _flash_from_query(request)
    return _render(
        env,
        "skills.html",
        user=user,
        flash=flash,
        skills=skills,
        instances=instances,
    )


async def skill_create_post(request: Request) -> Response:
    root: Path = request.app.state.root
    try:
        _require_admin(request)
    except PermissionError:
        return RedirectResponse(url="/skills?flash=forbidden", status_code=303)

    form: FormData = await request.form()
    skill_name = str(form.get("skill_name", "")).strip().lower()
    description = str(form.get("description", "")).strip()
    version = str(form.get("version", "1.0.0")).strip() or "1.0.0"
    location = str(form.get("location", "global")).strip()

    if not _SKILL_NAME_RE.fullmatch(skill_name):
        return RedirectResponse(url="/skills?flash=error", status_code=303)

    # Determine target directory
    if location == "global":
        target_dir = _global_skills_dir(root) / skill_name
        key = skill_name
    elif location.startswith("instance:"):
        inst_name = location.split(":", 1)[1]
        if not _NAME_RE.fullmatch(inst_name):
            return RedirectResponse(url="/skills?flash=error", status_code=303)
        target_dir = _instance_skills_dir(root, inst_name) / skill_name
        key = f"{inst_name}:{skill_name}"
    else:
        return RedirectResponse(url="/skills?flash=error", status_code=303)

    if target_dir.exists():
        return RedirectResponse(url="/skills?flash=error", status_code=303)

    target_dir.mkdir(parents=True, exist_ok=True)

    # Write SKILL.md with frontmatter
    frontmatter = f"---\nname: {skill_name}\ndescription: {description}\nversion: {version}\n---\n\n# {skill_name}\n\n{description}\n"
    _write_text(target_dir / "SKILL.md", frontmatter)

    return RedirectResponse(url=f"/skills/{key}?flash=skill_created", status_code=303)


async def skill_edit(request: Request) -> Response:
    env: Environment = request.app.state.jinja
    root: Path = request.app.state.root
    user = _get_user(request)
    name = request.path_params["name"]

    skill_dir = _resolve_skill_path(root, name)
    if skill_dir is None or not skill_dir.is_dir():
        return RedirectResponse(url="/skills?flash=error", status_code=302)

    # List .md files
    skill_files = sorted(
        str(f.relative_to(skill_dir)).replace("\\", "/")
        for f in skill_dir.rglob("*.md")
    )

    # Current file
    current_file = request.query_params.get("file", "SKILL.md")
    target = _safe_skill_file_path(skill_dir, current_file)
    current_content = ""
    if target and target.is_file():
        try:
            current_content = target.read_text(encoding="utf-8")
        except Exception:
            current_content = ""
    else:
        current_file = "SKILL.md"
        main = skill_dir / "SKILL.md"
        if main.is_file():
            current_content = main.read_text(encoding="utf-8")

    # Parse frontmatter for SKILL.md
    skill_meta = {"name": name.split(":")[-1] if ":" in name else name, "description": "", "version": "1.0.0"}
    main_file = skill_dir / "SKILL.md"
    if main_file.is_file():
        try:
            from ..skills.loader import _parse_frontmatter
            meta, _ = _parse_frontmatter(main_file.read_text(encoding="utf-8"))
            if meta:
                skill_meta.update(meta)
        except Exception:
            pass

    # Determine source label
    source_label = "Global"
    if ":" in name:
        inst_name = name.split(":")[0]
        source_label = f"Instance: {inst_name}"

    flash = _flash_from_query(request)
    return _render(
        env,
        "skill_edit.html",
        user=user,
        flash=flash,
        skill_name=name,
        skill_files=skill_files,
        current_file=current_file,
        current_content=current_content,
        skill_meta=skill_meta,
        source_label=source_label,
    )


async def skill_save_post(request: Request) -> Response:
    root: Path = request.app.state.root
    try:
        _require_admin(request)
    except PermissionError:
        return RedirectResponse(url="/skills?flash=forbidden", status_code=303)

    name = request.path_params["name"]
    skill_dir = _resolve_skill_path(root, name)
    if skill_dir is None or not skill_dir.is_dir():
        return RedirectResponse(url="/skills?flash=error", status_code=303)

    form: FormData = await request.form()
    file_path = str(form.get("file_path", "SKILL.md")).strip()
    content = str(form.get("content", ""))

    target = _safe_skill_file_path(skill_dir, file_path)
    if target is None:
        return RedirectResponse(url=f"/skills/{name}?flash=error", status_code=303)

    # If SKILL.md, rebuild frontmatter from form fields
    if file_path == "SKILL.md":
        fm_name = str(form.get("meta_name", "")).strip()
        fm_desc = str(form.get("meta_description", "")).strip()
        fm_version = str(form.get("meta_version", "1.0.0")).strip()
        if fm_name or fm_desc or fm_version:
            from ..skills.loader import _parse_frontmatter
            _old_meta, body = _parse_frontmatter(content)
            frontmatter = f"---\nname: {fm_name}\ndescription: {fm_desc}\nversion: {fm_version}\n---\n"
            content = frontmatter + "\n" + body

    _write_text(target, content)
    return RedirectResponse(url=f"/skills/{name}?file={file_path}&flash=skill_saved", status_code=303)


async def skill_new_file_post(request: Request) -> Response:
    root: Path = request.app.state.root
    try:
        _require_admin(request)
    except PermissionError:
        return RedirectResponse(url="/skills?flash=forbidden", status_code=303)

    name = request.path_params["name"]
    skill_dir = _resolve_skill_path(root, name)
    if skill_dir is None or not skill_dir.is_dir():
        return RedirectResponse(url="/skills?flash=error", status_code=303)

    form: FormData = await request.form()
    file_name = str(form.get("file_name", "")).strip()

    # Ensure .md extension
    if not file_name.endswith(".md"):
        file_name += ".md"

    target = _safe_skill_file_path(skill_dir, file_name)
    if target is None:
        return RedirectResponse(url=f"/skills/{name}?flash=error", status_code=303)

    if target.exists():
        return RedirectResponse(url=f"/skills/{name}?file={file_name}&flash=error", status_code=303)

    target.parent.mkdir(parents=True, exist_ok=True)
    _write_text(target, f"# {file_name.replace('.md', '')}\n\n")
    return RedirectResponse(url=f"/skills/{name}?file={file_name}&flash=skill_file_created", status_code=303)


async def skill_delete_file_post(request: Request) -> Response:
    root: Path = request.app.state.root
    try:
        _require_admin(request)
    except PermissionError:
        return RedirectResponse(url="/skills?flash=forbidden", status_code=303)

    name = request.path_params["name"]
    skill_dir = _resolve_skill_path(root, name)
    if skill_dir is None or not skill_dir.is_dir():
        return RedirectResponse(url="/skills?flash=error", status_code=303)

    form: FormData = await request.form()
    file_path = str(form.get("file_path", "")).strip()

    # Cannot delete SKILL.md
    if file_path == "SKILL.md":
        return RedirectResponse(url=f"/skills/{name}?flash=error", status_code=303)

    target = _safe_skill_file_path(skill_dir, file_path)
    if target is None or not target.is_file():
        return RedirectResponse(url=f"/skills/{name}?flash=error", status_code=303)

    target.unlink()
    return RedirectResponse(url=f"/skills/{name}?flash=skill_file_deleted", status_code=303)


async def skill_delete_post(request: Request) -> Response:
    root: Path = request.app.state.root
    try:
        _require_admin(request)
    except PermissionError:
        return RedirectResponse(url="/skills?flash=forbidden", status_code=303)

    name = request.path_params["name"]
    skill_dir = _resolve_skill_path(root, name)
    if skill_dir is None or not skill_dir.is_dir():
        return RedirectResponse(url="/skills?flash=error", status_code=303)

    shutil.rmtree(skill_dir)
    return RedirectResponse(url="/skills?flash=skill_deleted", status_code=303)


# ---------------------------------------------------------------------------
# App builder
# ---------------------------------------------------------------------------

def build_admin_app(
    *,
    root: Path,
    store: DataStore,
    on_instances_changed: Callable[[], Awaitable[None]] | None = None,
) -> Starlette:
    """Build the admin panel Starlette application."""

    static_dir = Path(__file__).resolve().parent / "static"

    routes = [
        # Auth
        Route("/login", login_get, methods=["GET"]),
        Route("/login", login_post, methods=["POST"]),
        Route("/logout", logout_post, methods=["POST"]),
        # Dashboard
        Route("/", dashboard, methods=["GET"]),
        # Instances
        Route("/instances", instances_list, methods=["GET"]),
        Route("/instances/new", instance_create_get, methods=["GET"]),
        Route("/instances/new", instance_create_post, methods=["POST"]),
        Route("/instances/{name:str}", instance_detail, methods=["GET"]),
        Route("/instances/{name:str}/edit", instance_edit_get, methods=["GET"]),
        Route("/instances/{name:str}/edit", instance_edit_post, methods=["POST"]),
        Route("/instances/{name:str}/delete", instance_delete_post, methods=["POST"]),
        # Tokens
        Route("/tokens", tokens_list, methods=["GET"]),
        Route("/tokens/create", token_create_post, methods=["POST"]),
        Route("/tokens/{id:str}", token_detail, methods=["GET"]),
        Route("/tokens/{id:str}/edit", token_edit_post, methods=["POST"]),
        Route("/tokens/{id:str}/revoke", token_revoke_post, methods=["POST"]),
        Route("/tokens/{id:str}/delete", token_delete_post, methods=["POST"]),
        # Skills
        Route("/skills", skills_list, methods=["GET"]),
        Route("/skills/new", skill_create_post, methods=["POST"]),
        Route("/skills/{name:str}", skill_edit, methods=["GET"]),
        Route("/skills/{name:str}/save", skill_save_post, methods=["POST"]),
        Route("/skills/{name:str}/new-file", skill_new_file_post, methods=["POST"]),
        Route("/skills/{name:str}/delete-file", skill_delete_file_post, methods=["POST"]),
        Route("/skills/{name:str}/delete", skill_delete_post, methods=["POST"]),
        # Users
        Route("/users", users_list, methods=["GET"]),
        Route("/users/create", user_create_post, methods=["POST"]),
        Route("/users/profile", user_profile_post, methods=["POST"]),
        Route("/users/edit", user_edit_post, methods=["POST"]),
        Route("/users/{username:str}/delete", user_delete_post, methods=["POST"]),
        # Static files
        Mount("/static", app=StaticFiles(directory=str(static_dir)), name="static"),
    ]

    app = Starlette(
        routes=routes,
        middleware=[Middleware(AdminAuthMiddleware)],
    )

    app.state.root = root
    app.state.store = store
    app.state.jinja = _jinja_env()
    app.state.on_instances_changed = on_instances_changed

    return app
