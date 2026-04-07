"""
Database connection module with simple connection pooling.

Uses a dictionary of connection pools keyed by (host, port, dbname).
A threading.Lock ensures thread safety. PyMySQL remains synchronous.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from typing import Any

import pymysql

from .types import DbConfig

logger = logging.getLogger("scada_mcp.db")

# ---------------------------------------------------------------------------
# Connection Pool
# ---------------------------------------------------------------------------

_pool_lock = threading.Lock()

# Keyed by (host, port, dbname) -> deque of (connection, last_used_timestamp)
_pools: dict[tuple[str, int, str], deque[tuple[pymysql.connections.Connection, float]]] = {}

# Pool configuration
_MAX_POOL_SIZE = 5          # max idle connections per (host, port, dbname)
_MAX_CONN_AGE_SEC = 300.0   # recycle connections older than 5 minutes


def _pool_key(db: DbConfig) -> tuple[str, int, str]:
    return (db.host, db.port, db.dbname)


def _create_connection(db: DbConfig) -> pymysql.connections.Connection:
    """Create a fresh PyMySQL connection."""
    logger.debug("Creating new DB connection to %s:%d/%s", db.host, db.port, db.dbname)
    return pymysql.connect(
        host=db.host,
        port=db.port,
        user=db.username,
        password=db.password,
        database=db.dbname,
        charset=db.charset,
        connect_timeout=max(1, min(30, int(db.connect_timeout_sec))),
        read_timeout=max(1, min(120, int((db.query_timeout_ms + 999) / 1000))),
        write_timeout=max(1, min(120, int((db.query_timeout_ms + 999) / 1000))),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def _is_connection_alive(conn: pymysql.connections.Connection) -> bool:
    """Check if a pooled connection is still usable."""
    try:
        conn.ping(reconnect=False)
        return True
    except Exception:
        return False


def _get_from_pool(db: DbConfig) -> pymysql.connections.Connection | None:
    """Try to get a healthy connection from the pool."""
    key = _pool_key(db)
    now = time.monotonic()
    with _pool_lock:
        pool = _pools.get(key)
        if not pool:
            return None
        while pool:
            conn, ts = pool.popleft()
            if now - ts > _MAX_CONN_AGE_SEC:
                # Too old, close and skip
                try:
                    conn.close()
                except Exception:
                    pass
                logger.debug("Discarded stale pooled connection for %s:%d/%s", *key)
                continue
            if _is_connection_alive(conn):
                logger.debug("Reusing pooled connection for %s:%d/%s", *key)
                return conn
            else:
                try:
                    conn.close()
                except Exception:
                    pass
                logger.debug("Discarded dead pooled connection for %s:%d/%s", *key)
    return None


def _return_to_pool(db: DbConfig, conn: pymysql.connections.Connection) -> None:
    """Return a connection to the pool if there is room."""
    key = _pool_key(db)
    with _pool_lock:
        pool = _pools.setdefault(key, deque())
        if len(pool) < _MAX_POOL_SIZE:
            pool.append((conn, time.monotonic()))
            logger.debug("Returned connection to pool for %s:%d/%s (size=%d)", *key, len(pool))
        else:
            try:
                conn.close()
            except Exception:
                pass
            logger.debug("Pool full for %s:%d/%s, closed connection", *key)


class _PooledConnection:
    """Context manager that borrows from the pool and returns on exit."""

    def __init__(self, db: DbConfig) -> None:
        self._db = db
        self._conn: pymysql.connections.Connection | None = None

    def __enter__(self) -> pymysql.connections.Connection:
        conn = _get_from_pool(self._db)
        if conn is None:
            conn = _create_connection(self._db)
        self._conn = conn
        return conn

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        conn = self._conn
        self._conn = None
        if conn is None:
            return
        if exc_type is not None:
            # On error, close instead of returning to pool
            try:
                conn.close()
            except Exception:
                pass
            return
        _return_to_pool(self._db, conn)


def connect(db: DbConfig) -> _PooledConnection:
    """
    Get a database connection (pooled).

    Usage:
        with db.connect(cfg.db) as conn:
            with conn.cursor() as cur:
                cur.execute(...)
    """
    return _PooledConnection(db)


def close_all_pools() -> None:
    """Close all pooled connections. Call on shutdown."""
    with _pool_lock:
        for key, pool in _pools.items():
            while pool:
                conn, _ = pool.popleft()
                try:
                    conn.close()
                except Exception:
                    pass
            logger.debug("Closed pool for %s:%d/%s", *key)
        _pools.clear()
    logger.info("All connection pools closed")
