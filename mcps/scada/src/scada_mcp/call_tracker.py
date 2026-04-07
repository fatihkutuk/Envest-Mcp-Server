"""
CallTracker -- Runtime tool call loop detection.

Detects when the same tool is called with the same parameters repeatedly.
Small models (e.g. 9B) can enter loops; this module stops them at runtime.

Usage:
    from .call_tracker import tracker
    allowed, count = tracker.check_and_record(tool_name, args, kwargs)
    if not allowed:
        return fail(tool_name, "Loop detected", error_type="LoopDetected")

Environment variables:
    MCP_MAX_IDENTICAL_CALLS  -- Max identical calls allowed (default: 3)
    MCP_CALL_TTL_SECONDS     -- Call history TTL (default: 300 = 5min)
"""
from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from collections import defaultdict

logger = logging.getLogger("scada_mcp.call_tracker")


class CallTracker:
    """Tool call history. Detects identical tool+params repetitions."""

    def __init__(self, max_identical: int = 3, ttl_seconds: int = 300) -> None:
        self.max_identical = max_identical
        self.ttl = ttl_seconds
        self._calls: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _sig(self, tool: str, args: tuple, kwargs: dict) -> str:
        """Call signature: tool name + parameters -> MD5 hash."""
        try:
            raw = f"{tool}:{args}:{sorted(kwargs.items())}"
        except Exception:
            raw = f"{tool}:{args}:{kwargs}"
        return hashlib.md5(raw.encode("utf-8", errors="replace")).hexdigest()

    def check_and_record(
        self, tool: str, args: tuple = (), kwargs: dict | None = None
    ) -> tuple[bool, int]:
        """
        Check and record a call.

        Returns:
            (allowed, call_count)
            allowed=False -> REJECT this call (loop)
            call_count -> how many times this signature has been called
        """
        if kwargs is None:
            kwargs = {}
        sig = self._sig(tool, args, kwargs)
        now = time.monotonic()

        with self._lock:
            # Clean expired entries
            self._calls[sig] = [t for t in self._calls[sig] if now - t < self.ttl]
            count = len(self._calls[sig])

            if count >= self.max_identical:
                logger.warning("Loop detected for tool=%s (count=%d)", tool, count + 1)
                return False, count + 1

            self._calls[sig].append(now)
            return True, count + 1

    def cleanup(self) -> None:
        """Clean all expired entries."""
        now = time.monotonic()
        with self._lock:
            expired = [
                k
                for k, timestamps in self._calls.items()
                if all(now - t >= self.ttl for t in timestamps)
            ]
            for k in expired:
                del self._calls[k]

    def reset(self) -> None:
        """Reset all history (for testing)."""
        with self._lock:
            self._calls.clear()

    @property
    def stats(self) -> dict[str, int]:
        """Current status statistics."""
        with self._lock:
            return {
                "tracked_signatures": len(self._calls),
                "total_entries": sum(len(v) for v in self._calls.values()),
            }


def _env_int(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# Module-level singleton
tracker = CallTracker(
    max_identical=_env_int("MCP_MAX_IDENTICAL_CALLS", 3),
    ttl_seconds=_env_int("MCP_CALL_TTL_SECONDS", 300),
)
