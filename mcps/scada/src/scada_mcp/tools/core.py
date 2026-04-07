from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import Callable
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, TypeVar

from ..call_tracker import tracker as _call_tracker
from ..config import validate_tool_name

logger = logging.getLogger("scada_mcp.tools.core")

_PREFIX_RE = re.compile(r"^[a-zA-Z0-9._/-]+$")

T = TypeVar("T")

# Default response budget is intentionally conservative to prevent LM Studio / local LLMs
# from ballooning context with large tool outputs (which can lead to "Model unloaded").
_DEFAULT_MAX_CHARS = 35_000
_DEFAULT_MAX_DEPTH = 10
_DEFAULT_MAX_LIST_ITEMS = 120
_DEFAULT_MAX_DICT_KEYS = 120
_DEFAULT_MAX_STRING_CHARS = 8_000


def _env_int(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return int(default)
    try:
        return int(raw)
    except Exception:
        return int(default)


def _truncate_string(s: str, max_chars: int) -> dict[str, Any]:
    if max_chars <= 0:
        return {"_truncated": True, "_original_len": len(s), "_kept_len": 0, "_preview": ""}
    if len(s) <= max_chars:
        return {"_truncated": False, "_original_len": len(s), "_kept_len": len(s), "_preview": s}
    keep = max(0, int(max_chars))
    return {
        "_truncated": True,
        "_original_len": len(s),
        "_kept_len": keep,
        "_preview": s[:keep],
    }


def _shrink_for_budget(
    value: Any,
    *,
    max_depth: int,
    max_list_items: int,
    max_dict_keys: int,
    max_string_chars: int,
    _depth: int = 0,
) -> Any:
    """
    Deterministic shrinker to keep tool results bounded.
    - Strings are truncated into an object { _truncated, _preview, ... } so clients can detect loss.
    - Lists/dicts are capped with stable ordering; omitted counts are reported.
    - Depth is bounded to avoid pathological nesting.
    """
    if _depth >= max_depth:
        return {"_truncated": True, "_reason": "max_depth", "_depth": _depth}

    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        if max_string_chars > 0 and len(value) > max_string_chars:
            return _truncate_string(value, max_string_chars)
        return value

    if isinstance(value, bytes):
        try:
            s = value.decode("utf-8", errors="replace")
        except Exception:
            s = str(value)
        if max_string_chars > 0 and len(s) > max_string_chars:
            return _truncate_string(s, max_string_chars)
        return s

    if isinstance(value, list | tuple):
        items = list(value)
        if max_list_items >= 0 and len(items) > max_list_items:
            kept = items[: max(0, max_list_items)]
            return {
                "_truncated": True,
                "_type": "list",
                "_kept": [
                    _shrink_for_budget(
                        v,
                        max_depth=max_depth,
                        max_list_items=max_list_items,
                        max_dict_keys=max_dict_keys,
                        max_string_chars=max_string_chars,
                        _depth=_depth + 1,
                    )
                    for v in kept
                ],
                "_omitted": len(items) - len(kept),
                "_total": len(items),
            }
        return [
            _shrink_for_budget(
                v,
                max_depth=max_depth,
                max_list_items=max_list_items,
                max_dict_keys=max_dict_keys,
                max_string_chars=max_string_chars,
                _depth=_depth + 1,
            )
            for v in items
        ]

    if isinstance(value, dict):
        keys = list(value.keys())
        # Deterministic key order
        keys_sorted = sorted(keys, key=lambda k: str(k))
        truncated = max_dict_keys >= 0 and len(keys_sorted) > max_dict_keys
        if truncated:
            keys_sorted = keys_sorted[: max(0, max_dict_keys)]
        out: dict[str, Any] = {}
        for k in keys_sorted:
            try:
                kk = str(k)
            except Exception:
                kk = repr(k)
            out[kk] = _shrink_for_budget(
                value.get(k),
                max_depth=max_depth,
                max_list_items=max_list_items,
                max_dict_keys=max_dict_keys,
                max_string_chars=max_string_chars,
                _depth=_depth + 1,
            )
        if truncated:
            out["_mcp_truncated"] = True
            out["_mcp_omitted_keys"] = len(keys) - len(keys_sorted)
            out["_mcp_total_keys"] = len(keys)
        return out

    # Fallback: stringify unknown objects (then truncate if needed)
    s = str(value)
    if max_string_chars > 0 and len(s) > max_string_chars:
        return _truncate_string(s, max_string_chars)
    return s


def _json_default(obj: Any) -> Any:
    """PyMySQL DictCursor: datetime, Decimal, bytes etc. -> JSON compatible."""
    if isinstance(obj, datetime):
        return obj.isoformat(sep=" ", timespec="seconds")
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, time):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def prefixed_name(prefix: str, base_name: str) -> str:
    base_name = base_name.strip()
    if not base_name:
        raise ValueError("base tool name is empty")
    if prefix:
        if not _PREFIX_RE.fullmatch(prefix):
            raise ValueError("prefix may only contain letters, numbers and ._/-")
        name = f"{prefix}{base_name}"
    else:
        name = base_name
    if len(name) > 64:
        raise ValueError("tool name exceeds 64 characters after prefixing")
    return validate_tool_name(name)


def ok(tool: str, result: Any) -> str:
    if isinstance(result, str):
        return result
    # Compact JSON: large indented responses can cause issues in some MCP/WebSocket clients.
    # Use MCP_TOOL_JSON_INDENT=2 for human-readable output.
    indent: int | None = 2 if (os.getenv("MCP_TOOL_JSON_INDENT") or "").strip() == "2" else None
    dump_kw: dict[str, Any] = {
        "ensure_ascii": False,
        "default": _json_default,
    }
    if indent is None:
        dump_kw["separators"] = (",", ":")
    else:
        dump_kw["indent"] = indent
    max_chars = _env_int("MCP_TOOL_MAX_CHARS", _DEFAULT_MAX_CHARS)
    max_chars = max(5_000, min(2_000_000, int(max_chars)))
    max_depth = max(2, min(50, _env_int("MCP_TOOL_MAX_DEPTH", _DEFAULT_MAX_DEPTH)))
    max_list = max(10, min(50_000, _env_int("MCP_TOOL_MAX_LIST_ITEMS", _DEFAULT_MAX_LIST_ITEMS)))
    max_keys = max(10, min(50_000, _env_int("MCP_TOOL_MAX_DICT_KEYS", _DEFAULT_MAX_DICT_KEYS)))
    max_str = max(500, min(500_000, _env_int("MCP_TOOL_MAX_STRING_CHARS", _DEFAULT_MAX_STRING_CHARS)))

    payload = {"ok": True, "tool": tool, "result": result}
    raw = json.dumps(payload, **dump_kw)
    if len(raw) <= max_chars:
        return raw

    # Iteratively shrink the *result* until it fits the budget.
    shrink_levels = [
        (max_depth, max_list, max_keys, max_str),
        (max(2, max_depth - 2), max(10, max_list // 2), max(10, max_keys // 2), max(500, max_str // 2)),
        (max(2, max_depth - 4), max(10, max_list // 5), max(10, max_keys // 5), max(500, max_str // 5)),
    ]
    note = {
        "_truncated": True,
        "max_chars": max_chars,
        "note": "Response was auto-truncated to prevent context overflow. Try a narrower query or use paging.",
    }
    for d, li, dk, ms in shrink_levels:
        shrunk = _shrink_for_budget(
            result,
            max_depth=d,
            max_list_items=li,
            max_dict_keys=dk,
            max_string_chars=ms,
        )
        if isinstance(shrunk, dict):
            shrunk.setdefault("_mcp_truncation", note)
        else:
            shrunk = {"_value": shrunk, "_mcp_truncation": note}
        payload2 = {"ok": True, "tool": tool, "result": shrunk}
        out = json.dumps(payload2, **dump_kw)
        if len(out) <= max_chars:
            return out

    # Last resort: tiny stub (always fits)
    stub = {
        "_mcp_truncation": note,
        "error": "response_too_large",
        "detail": "Response did not fit budget; content too large. Call with more specific parameters.",
    }
    return json.dumps({"ok": True, "tool": tool, "result": stub}, **dump_kw)


# Tool alternatives to suggest on error (prefix-less base name -> alternatives)
_TOOL_ALTERNATIVES: dict[str, list[str]] = {
    "search_tags": ["get_product_specs", "search_product_manual", "resolve_semantic_tag_candidates"],
    "get_device_tag_values": ["search_tags", "list_live_tag_across_nodes"],
    "get_node_all_tags": ["get_device_all_tags", "search_tags"],
    "get_device_all_tags": ["search_tags", "get_device_tag_values"],
    "analyze_dma_seasonal_demand": ["get_node_log_data", "get_chart_data"],
    "get_node_log_data": ["get_node_log_summary", "get_recent_log_chart_by_tag"],
    "get_node_log_chart_data": ["get_chart_data", "get_recent_log_chart_by_tag"],
    "find_nodes_by_keywords": ["list_nodes", "get_node"],
    "get_node": ["find_nodes_by_keywords", "list_nodes"],
    "get_node_scada_context": ["get_node", "search_tags"],
}

_LOOP_PREVENTION_HINT = (
    "LOOP PREVENTION: Do not call the same tool with the same parameters again. "
    "If you get an error: (1) try different parameters, (2) use a different tool, "
    "(3) explain the situation to the user. Node name is NOT a tool name."
)


def _extract_base_tool_name(tool: str) -> str:
    """Extract base name from prefixed tool name: 'korubin_get_node' -> 'get_node'."""
    parts = tool.split("_", 1)
    if len(parts) == 2 and not parts[0].startswith("get"):
        return parts[1]
    return tool


def fail(tool: str, message: str, *, hint: str | None = None, error_type: str | None = None) -> str:
    payload: dict[str, Any] = {
        "ok": False,
        "tool": tool,
        "error": {"message": message},
    }
    if hint:
        payload["error"]["hint"] = hint
    if error_type:
        payload["error"]["type"] = error_type

    # Alternative tool suggestions
    base = _extract_base_tool_name(tool)
    alts = _TOOL_ALTERNATIVES.get(base, [])
    if alts:
        payload["error"]["alternatives"] = f"Try instead: {', '.join(alts)}"

    # Loop prevention instruction
    payload["error"]["_model_rule"] = _LOOP_PREVENTION_HINT

    indent: int | None = 2 if (os.getenv("MCP_TOOL_JSON_INDENT") or "").strip() == "2" else None
    kw: dict[str, Any] = {"ensure_ascii": False, "default": _json_default}
    if indent is None:
        kw["separators"] = (",", ":")
    else:
        kw["indent"] = indent
    return json.dumps(payload, **kw)


def guard(tool_name: str, fn: Callable[..., T]) -> Callable[..., str]:
    def _wrapped(*args: Any, **kwargs: Any) -> str:
        # -- Loop detection --
        allowed, call_count = _call_tracker.check_and_record(tool_name, args, kwargs)
        if not allowed:
            logger.warning("Loop detected for tool=%s (call_count=%d)", tool_name, call_count)
            return fail(
                tool_name,
                f"LOOP: This tool was called with the same parameters for the {call_count}th time. DO NOT CALL AGAIN.",
                hint=(
                    "LOOP DETECTED. Results will not change with these parameters. "
                    "Use different parameters, try a different tool, or "
                    "summarize available info to the user. "
                    "Call smart_tool_select to find alternative tools."
                ),
                error_type="LoopDetected",
            )

        try:
            return ok(tool_name, fn(*args, **kwargs))
        except Exception as e:  # noqa: BLE001
            logger.exception("Tool %s raised an exception", tool_name)
            return fail(
                tool_name,
                str(e) or "unknown error",
                error_type=e.__class__.__name__,
                hint="Server-side error occurred. Try different parameters or an alternative tool.",
            )

    return _wrapped
