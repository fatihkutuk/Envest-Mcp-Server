"""
Multi-database connector - MySQL, PostgreSQL, MSSQL, SQLite support.
Returns a standard connection with DictCursor-like behavior.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator

logger = logging.getLogger("scada_mcp.database_tools.connector")


@dataclass
class DynamicDbConfig:
    """Database connection config with driver type."""
    driver: str  # "mysql", "postgresql", "mssql", "sqlite"
    host: str = ""
    port: int = 0
    dbname: str = ""
    username: str = ""
    password: str = ""
    charset: str = "utf8mb4"
    connect_timeout_sec: int = 10

    @property
    def default_port(self) -> int:
        return {
            "mysql": 3306,
            "postgresql": 5432,
            "mssql": 1433,
            "sqlite": 0,
        }.get(self.driver, 3306)

    @property
    def effective_port(self) -> int:
        return self.port if self.port > 0 else self.default_port


class DictRow(dict):
    """Dict-like row for drivers that don't support DictCursor natively."""
    pass


class UnifiedCursor:
    """Wraps different database cursors to provide a unified dict-row interface."""

    def __init__(self, cursor: Any, driver: str):
        self._cursor = cursor
        self._driver = driver

    def execute(self, sql: str, params: tuple | list | None = None):
        if self._driver == "mssql":
            # pymssql uses %s placeholders like pymysql
            self._cursor.execute(sql, params or ())
        elif self._driver == "postgresql":
            # psycopg2 with RealDictCursor handles it natively
            self._cursor.execute(sql, params or ())
        else:
            self._cursor.execute(sql, params or ())

    def fetchone(self) -> dict | None:
        row = self._cursor.fetchone()
        if row is None:
            return None
        if isinstance(row, dict):
            return row
        # Convert tuple to dict using column names
        if hasattr(self._cursor, 'description') and self._cursor.description:
            cols = [d[0] for d in self._cursor.description]
            return DictRow(zip(cols, row))
        return row

    def fetchall(self) -> list[dict]:
        rows = self._cursor.fetchall()
        if not rows:
            return []
        if isinstance(rows[0], dict):
            return rows
        # Convert tuples to dicts
        if hasattr(self._cursor, 'description') and self._cursor.description:
            cols = [d[0] for d in self._cursor.description]
            return [DictRow(zip(cols, r)) for r in rows]
        return rows

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class UnifiedConnection:
    """Wraps different database connections to provide a unified interface."""

    def __init__(self, conn: Any, driver: str):
        self._conn = conn
        self._driver = driver

    def cursor(self) -> UnifiedCursor:
        if self._driver == "mysql":
            cur = self._conn.cursor()
        elif self._driver == "postgresql":
            import psycopg2.extras
            cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        elif self._driver == "mssql":
            cur = self._conn.cursor(as_dict=True)
        elif self._driver == "sqlite":
            self._conn.row_factory = _sqlite_dict_factory
            cur = self._conn.cursor()
        else:
            cur = self._conn.cursor()
        return UnifiedCursor(cur, self._driver)

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _sqlite_dict_factory(cursor, row):
    return DictRow({col[0]: row[idx] for idx, col in enumerate(cursor.description)})


@contextmanager
def connect(cfg: DynamicDbConfig) -> Generator[UnifiedConnection, None, None]:
    """Connect to any supported database and return a UnifiedConnection."""
    driver = cfg.driver.lower().strip()

    if driver == "mysql":
        conn = _connect_mysql(cfg)
    elif driver == "postgresql":
        conn = _connect_postgresql(cfg)
    elif driver == "mssql":
        conn = _connect_mssql(cfg)
    elif driver == "sqlite":
        conn = _connect_sqlite(cfg)
    else:
        raise ValueError(
            f"Unsupported database driver: {driver!r}. "
            f"Supported: mysql, postgresql, mssql, sqlite"
        )

    try:
        yield conn
    finally:
        conn.close()


def _connect_mysql(cfg: DynamicDbConfig) -> UnifiedConnection:
    import pymysql
    import pymysql.cursors
    conn = pymysql.connect(
        host=cfg.host,
        port=cfg.effective_port,
        user=cfg.username,
        password=cfg.password,
        database=cfg.dbname,
        charset=cfg.charset,
        connect_timeout=cfg.connect_timeout_sec,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
    return UnifiedConnection(conn, "mysql")


def _connect_postgresql(cfg: DynamicDbConfig) -> UnifiedConnection:
    try:
        import psycopg2
    except ImportError:
        raise ImportError(
            "PostgreSQL support requires 'psycopg2-binary'. "
            "Install it: pip install psycopg2-binary"
        )
    conn = psycopg2.connect(
        host=cfg.host,
        port=cfg.effective_port,
        dbname=cfg.dbname,
        user=cfg.username,
        password=cfg.password,
        connect_timeout=cfg.connect_timeout_sec,
    )
    conn.autocommit = True
    return UnifiedConnection(conn, "postgresql")


def _connect_mssql(cfg: DynamicDbConfig) -> UnifiedConnection:
    try:
        import pymssql
    except ImportError:
        raise ImportError(
            "MSSQL support requires 'pymssql'. "
            "Install it: pip install pymssql"
        )
    conn = pymssql.connect(
        server=cfg.host,
        port=str(cfg.effective_port),
        user=cfg.username,
        password=cfg.password,
        database=cfg.dbname,
        login_timeout=cfg.connect_timeout_sec,
        as_dict=True,
    )
    return UnifiedConnection(conn, "mssql")


def _connect_sqlite(cfg: DynamicDbConfig) -> UnifiedConnection:
    import sqlite3
    # For SQLite, dbname is the file path
    conn = sqlite3.connect(cfg.dbname, timeout=cfg.connect_timeout_sec)
    return UnifiedConnection(conn, "sqlite")


# --- SQL dialect helpers ---

def get_schema_query(driver: str) -> str:
    """Return the appropriate schema query for the database type."""
    if driver == "mysql":
        return (
            "SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT, ENGINE, "
            "DATA_LENGTH, INDEX_LENGTH "
            "FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE' "
            "ORDER BY TABLE_NAME"
        )
    elif driver == "postgresql":
        return (
            "SELECT tablename AS TABLE_NAME, "
            "       0 AS TABLE_ROWS, "
            "       obj_description(c.oid) AS TABLE_COMMENT, "
            "       '' AS ENGINE, "
            "       pg_total_relation_size(c.oid) AS DATA_LENGTH, "
            "       0 AS INDEX_LENGTH "
            "FROM pg_catalog.pg_tables t "
            "JOIN pg_catalog.pg_class c ON c.relname = t.tablename "
            "WHERE t.schemaname = 'public' "
            "ORDER BY tablename"
        )
    elif driver == "mssql":
        return (
            "SELECT t.name AS TABLE_NAME, "
            "       p.rows AS TABLE_ROWS, "
            "       ep.value AS TABLE_COMMENT, "
            "       '' AS ENGINE, "
            "       0 AS DATA_LENGTH, "
            "       0 AS INDEX_LENGTH "
            "FROM sys.tables t "
            "LEFT JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id IN (0,1) "
            "LEFT JOIN sys.extended_properties ep ON t.object_id = ep.major_id AND ep.minor_id = 0 "
            "ORDER BY t.name"
        )
    elif driver == "sqlite":
        return (
            "SELECT name AS TABLE_NAME, "
            "       0 AS TABLE_ROWS, "
            "       '' AS TABLE_COMMENT, "
            "       'SQLite' AS ENGINE, "
            "       0 AS DATA_LENGTH, "
            "       0 AS INDEX_LENGTH "
            "FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        )
    return ""


def get_columns_query(driver: str) -> str:
    """Return the appropriate columns query for the database type."""
    if driver == "mysql":
        return (
            "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, "
            "COLUMN_KEY, COLUMN_DEFAULT, EXTRA "
            "FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "ORDER BY TABLE_NAME, ORDINAL_POSITION"
        )
    elif driver == "postgresql":
        return (
            "SELECT table_name AS TABLE_NAME, column_name AS COLUMN_NAME, "
            "       data_type AS COLUMN_TYPE, is_nullable AS IS_NULLABLE, "
            "       '' AS COLUMN_KEY, column_default AS COLUMN_DEFAULT, "
            "       '' AS EXTRA "
            "FROM information_schema.columns "
            "WHERE table_schema = 'public' "
            "ORDER BY table_name, ordinal_position"
        )
    elif driver == "mssql":
        return (
            "SELECT t.name AS TABLE_NAME, c.name AS COLUMN_NAME, "
            "       TYPE_NAME(c.user_type_id) AS COLUMN_TYPE, "
            "       CASE WHEN c.is_nullable = 1 THEN 'YES' ELSE 'NO' END AS IS_NULLABLE, "
            "       CASE WHEN pk.column_id IS NOT NULL THEN 'PRI' ELSE '' END AS COLUMN_KEY, "
            "       dc.definition AS COLUMN_DEFAULT, "
            "       CASE WHEN c.is_identity = 1 THEN 'auto_increment' ELSE '' END AS EXTRA "
            "FROM sys.columns c "
            "JOIN sys.tables t ON c.object_id = t.object_id "
            "LEFT JOIN (SELECT ic.object_id, ic.column_id FROM sys.index_columns ic "
            "           JOIN sys.indexes i ON ic.object_id = i.object_id AND ic.index_id = i.index_id "
            "           WHERE i.is_primary_key = 1) pk ON c.object_id = pk.object_id AND c.column_id = pk.column_id "
            "LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id "
            "ORDER BY t.name, c.column_id"
        )
    return ""


def get_table_count_query(driver: str, table_name: str) -> str:
    """Return COUNT query for a table."""
    if driver == "mssql":
        return f"SELECT COUNT(*) AS cnt FROM [{table_name}]"
    return f"SELECT COUNT(*) AS cnt FROM `{table_name}`"


def get_sample_query(driver: str, table_name: str, limit: int = 5) -> str:
    """Return sample data query."""
    if driver == "mssql":
        return f"SELECT TOP {limit} * FROM [{table_name}]"
    elif driver == "sqlite":
        return f"SELECT * FROM \"{table_name}\" LIMIT {limit}"
    return f"SELECT * FROM `{table_name}` LIMIT {limit}"


def get_test_query(driver: str) -> str:
    """Return a test query to verify connection."""
    if driver == "mysql":
        return "SELECT DATABASE() AS db, VERSION() AS ver, CURRENT_USER() AS usr"
    elif driver == "postgresql":
        return "SELECT current_database() AS db, version() AS ver, current_user AS usr"
    elif driver == "mssql":
        return "SELECT DB_NAME() AS db, @@VERSION AS ver, SUSER_SNAME() AS usr"
    elif driver == "sqlite":
        return "SELECT 'sqlite' AS db, sqlite_version() AS ver, 'local' AS usr"
    return "SELECT 1"


def get_table_count_in_schema(driver: str) -> str:
    """Return query to count tables in schema."""
    if driver == "mysql":
        return (
            "SELECT COUNT(*) AS cnt FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'"
        )
    elif driver == "postgresql":
        return (
            "SELECT COUNT(*) AS cnt FROM pg_catalog.pg_tables "
            "WHERE schemaname = 'public'"
        )
    elif driver == "mssql":
        return "SELECT COUNT(*) AS cnt FROM sys.tables"
    elif driver == "sqlite":
        return (
            "SELECT COUNT(*) AS cnt FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    return "SELECT 0 AS cnt"
