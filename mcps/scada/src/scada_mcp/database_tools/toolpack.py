"""
Database ToolPack - Generic database exploration and analysis tools.

Registers 15 tools:
  - {prefix}connect_database
  - {prefix}describe_schema
  - {prefix}list_tables
  - {prefix}describe_table
  - {prefix}query
  - {prefix}analyze_table
  - {prefix}find_related_tables
  - {prefix}list_databases
  - {prefix}list_views
  - {prefix}list_procedures
  - {prefix}list_functions
  - {prefix}list_triggers
  - {prefix}list_events
  - {prefix}show_create
  - {prefix}switch_database
"""

from __future__ import annotations

import re
import logging
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from ..types import InstanceConfig

logger = logging.getLogger("scada_mcp.database_tools")

# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

_SAFE_TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")

_BLOCKED_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|RENAME|"
    r"GRANT|REVOKE|LOCK|UNLOCK|CALL|LOAD|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b",
    re.IGNORECASE,
)

_ALLOWED_PREFIXES = re.compile(
    r"^\s*(SELECT|SHOW|DESCRIBE|DESC|EXPLAIN)\b",
    re.IGNORECASE,
)

_LIMIT_RE = re.compile(r"\bLIMIT\s+\d+", re.IGNORECASE)


def _validate_table_name(name: str) -> str:
    """Validate and return a safe table name, or raise ValueError."""
    name = name.strip().strip("`").strip()
    if not _SAFE_TABLE_RE.fullmatch(name):
        raise ValueError(
            f"Invalid table name: {name!r}. "
            "Only letters, digits, and underscores are allowed."
        )
    return name


def _validate_readonly_sql(sql: str) -> str:
    """Ensure the SQL is a read-only statement. Raises ValueError otherwise."""
    sql = sql.strip().rstrip(";").strip()
    if not sql:
        raise ValueError("Empty SQL query.")
    if not _ALLOWED_PREFIXES.match(sql):
        raise ValueError(
            "Only SELECT, SHOW, DESCRIBE, and EXPLAIN statements are allowed."
        )
    if _BLOCKED_KEYWORDS.search(sql):
        raise ValueError(
            "Query contains blocked keywords. "
            "Only read-only statements (SELECT, SHOW, DESCRIBE, EXPLAIN) are allowed."
        )
    return sql


def _ensure_limit(sql: str, limit: int) -> str:
    """Add LIMIT clause if not already present."""
    if not _LIMIT_RE.search(sql):
        sql = sql.rstrip().rstrip(";").rstrip()
        sql = f"{sql} LIMIT {limit}"
    return sql


def _rows_to_markdown(rows: list[dict[str, Any]], max_col_width: int = 80) -> str:
    """Convert a list of dicts to a markdown table string."""
    if not rows:
        return "_No rows returned._"
    columns = list(rows[0].keys())
    # Truncate cell values for display
    def _cell(v: Any) -> str:
        s = str(v) if v is not None else "NULL"
        if len(s) > max_col_width:
            s = s[: max_col_width - 3] + "..."
        return s

    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, sep]
    for row in rows:
        cells = [_cell(row.get(c)) for c in columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _prefixed(prefix: str, name: str) -> str:
    return f"{prefix}{name}" if prefix else name


# ---------------------------------------------------------------------------
# ToolPack
# ---------------------------------------------------------------------------


class DatabaseToolPack:
    id = "database"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix
        default_db_cfg = cfg.db  # May be None if no default DB configured

        from ..db import connect as _mysql_connect
        from ..types import DbConfig
        from .connector import DynamicDbConfig, connect as _multi_connect
        from .connector import get_test_query, get_table_count_in_schema

        # Session-level dynamic DB connection (set by connect_database tool)
        _dynamic: dict[str, Any] = {}  # "cfg" → DynamicDbConfig, "driver" → str

        def _get_connection():
            """Return a context manager for the active DB connection."""
            if "cfg" in _dynamic:
                return _multi_connect(_dynamic["cfg"])
            if default_db_cfg and default_db_cfg.host:
                # Legacy: use pymysql connect for default MySQL config
                return _mysql_connect(default_db_cfg)
            raise RuntimeError(
                "No database configured. Use connect_database first to provide "
                "your database connection details (driver, host, dbname, username, password)."
            )

        def _get_driver() -> str:
            """Return active driver name."""
            if "cfg" in _dynamic:
                return _dynamic["cfg"].driver
            return "mysql"  # default

        # ── Tool 0: connect_database ─────────────────────────────────────
        connect_tool = _prefixed(prefix, "connect_database")

        @mcp.tool(name=connect_tool)
        def connect_database(
            host: str,
            dbname: str,
            username: str,
            password: str,
            driver: str = "auto",
            port: int = 0,
        ) -> Any:
            """Connect to a database. Supports MySQL, PostgreSQL, MSSQL, SQLite.

If driver is "auto" (default), the system will automatically detect the database type
by trying each driver in order. You don't need to know the database type in advance.

Supported drivers:
  - "auto" (default) - Auto-detect by trying MySQL -> PostgreSQL -> MSSQL
  - "mysql" - MySQL / MariaDB (port 3306)
  - "postgresql" - PostgreSQL (port 5432)
  - "mssql" - Microsoft SQL Server (port 1433)
  - "sqlite" - SQLite (host not needed, dbname = file path)

Parameters:
  - host: Database server IP or hostname
  - dbname: Database name or file path (SQLite)
  - username: Database username
  - password: Database password
  - driver: "auto" to detect, or specify: "mysql", "postgresql", "mssql", "sqlite"
  - port: Port (0 = use default for driver)"""
            driver_clean = driver.lower().strip()
            supported = {"auto", "mysql", "postgresql", "mssql", "sqlite"}
            if driver_clean not in supported:
                return {"content": [{"type": "text", "text":
                    f"**Unsupported driver:** {driver!r}\n\nSupported: auto, mysql, postgresql, mssql, sqlite"
                }]}

            # Auto-detect: try each driver
            if driver_clean == "auto":
                detect_order = ["mysql", "postgresql", "mssql"]
                # If port hints at a specific driver, try that first
                if port == 5432:
                    detect_order = ["postgresql", "mysql", "mssql"]
                elif port == 1433:
                    detect_order = ["mssql", "mysql", "postgresql"]

                errors = []
                for try_driver in detect_order:
                    test_cfg = DynamicDbConfig(
                        driver=try_driver,
                        host=host,
                        port=port,
                        dbname=dbname,
                        username=username,
                        password=password,
                    )
                    try:
                        with _multi_connect(test_cfg) as conn:
                            with conn.cursor() as cur:
                                cur.execute(get_test_query(try_driver))
                                info = cur.fetchone()
                                cur.execute(get_table_count_in_schema(try_driver))
                                table_count = cur.fetchone()["cnt"]
                        # Success!
                        _dynamic["cfg"] = test_cfg
                        driver_label = {"mysql": "MySQL/MariaDB", "postgresql": "PostgreSQL", "mssql": "MSSQL"}.get(try_driver, try_driver)
                        return {"content": [{"type": "text", "text":
                            f"**Connected successfully! (Auto-detected: {driver_label})**\n\n"
                            f"| Parameter | Value |\n"
                            f"|-----------|-------|\n"
                            f"| Driver | {driver_label} (auto-detected) |\n"
                            f"| Host | {host}:{test_cfg.effective_port} |\n"
                            f"| Database | {info.get('db', dbname)} |\n"
                            f"| Version | {str(info.get('ver', ''))[:80]} |\n"
                            f"| User | {info.get('usr', username)} |\n"
                            f"| Tables | {table_count} |\n\n"
                            f"You can now use the other database tools."
                        }]}
                    except ImportError:
                        errors.append(f"{try_driver}: driver not installed")
                    except Exception as exc:
                        errors.append(f"{try_driver}: {str(exc)[:100]}")

                # All failed
                error_detail = "\n".join(f"- {e}" for e in errors)
                return {"content": [{"type": "text", "text":
                    f"**Auto-detection failed.** Tried all drivers:\n\n{error_detail}\n\n"
                    f"Try specifying the driver manually: driver='mysql', 'postgresql', or 'mssql'"
                }]}

            # Explicit driver
            new_cfg = DynamicDbConfig(
                driver=driver_clean,
                host=host,
                port=port,
                dbname=dbname,
                username=username,
                password=password,
            )
            try:
                with _multi_connect(new_cfg) as conn:
                    with conn.cursor() as cur:
                        cur.execute(get_test_query(driver_clean))
                        info = cur.fetchone()
                        cur.execute(get_table_count_in_schema(driver_clean))
                        table_count = cur.fetchone()["cnt"]
            except ImportError as exc:
                return {"content": [{"type": "text", "text":
                    f"**Driver not installed:** {exc}\n\nAsk the admin to install the required package."
                }]}
            except Exception as exc:
                return {"content": [{"type": "text", "text":
                    f"**Connection failed:** {exc}\n\n"
                    f"- Driver: {driver_clean}\n- Host: {host}:{new_cfg.effective_port}\n"
                    f"- Database: {dbname}\n- User: {username}"
                }]}

            _dynamic["cfg"] = new_cfg
            driver_label = {"mysql": "MySQL/MariaDB", "postgresql": "PostgreSQL", "mssql": "MSSQL", "sqlite": "SQLite"}.get(driver_clean, driver_clean)
            return {"content": [{"type": "text", "text":
                f"**Connected successfully!**\n\n"
                f"| Parameter | Value |\n"
                f"|-----------|-------|\n"
                f"| Driver | {driver_label} |\n"
                f"| Host | {host}:{new_cfg.effective_port} |\n"
                f"| Database | {info.get('db', dbname)} |\n"
                f"| Version | {str(info.get('ver', ''))[:80]} |\n"
                f"| User | {info.get('usr', username)} |\n"
                f"| Tables | {table_count} |\n\n"
                f"You can now use the other database tools."
            }]}

        # ── Tool 1: describe_schema ──────────────────────────────────────
        schema_tool = _prefixed(prefix, "describe_schema")

        @mcp.tool(name=schema_tool)
        def describe_schema() -> Any:
            """List all tables in the database with column info, row counts, and foreign keys.
Returns a comprehensive overview of the entire database schema. Use this first to understand the database structure."""
            with _get_connection() as conn:
                with conn.cursor() as cur:
                    # Get all tables with row counts
                    cur.execute(
                        "SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT, ENGINE, "
                        "DATA_LENGTH, INDEX_LENGTH "
                        "FROM information_schema.TABLES "
                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE' "
                        "ORDER BY TABLE_NAME"
                    )
                    tables = cur.fetchall()

                    if not tables:
                        return {"content": [{"type": "text", "text": "No tables found in the database."}]}

                    # Get all columns grouped by table
                    cur.execute(
                        "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, "
                        "COLUMN_KEY, COLUMN_DEFAULT, EXTRA "
                        "FROM information_schema.COLUMNS "
                        "WHERE TABLE_SCHEMA = DATABASE() "
                        "ORDER BY TABLE_NAME, ORDINAL_POSITION"
                    )
                    all_columns = cur.fetchall()

                    # Get foreign keys
                    cur.execute(
                        "SELECT TABLE_NAME, COLUMN_NAME, "
                        "REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME "
                        "FROM information_schema.KEY_COLUMN_USAGE "
                        "WHERE TABLE_SCHEMA = DATABASE() "
                        "AND REFERENCED_TABLE_NAME IS NOT NULL "
                        "ORDER BY TABLE_NAME"
                    )
                    fks = cur.fetchall()

            # Build columns index
            cols_by_table: dict[str, list[dict]] = {}
            for col in all_columns:
                tname = col["TABLE_NAME"]
                cols_by_table.setdefault(tname, []).append(col)

            # Build FK index
            fk_by_table: dict[str, list[dict]] = {}
            for fk in fks:
                tname = fk["TABLE_NAME"]
                fk_by_table.setdefault(tname, []).append(fk)

            lines = [
                f"## Database Schema Overview",
                f"**{len(tables)} tables found**\n",
            ]

            for t in tables:
                tname = t["TABLE_NAME"]
                rows = t["TABLE_ROWS"] or 0
                comment = t["TABLE_COMMENT"] or ""
                size_mb = ((t["DATA_LENGTH"] or 0) + (t["INDEX_LENGTH"] or 0)) / (1024 * 1024)
                comment_str = f" - {comment}" if comment else ""

                lines.append(f"### `{tname}` (~{rows:,} rows, {size_mb:.1f} MB){comment_str}")

                # Columns
                tcols = cols_by_table.get(tname, [])
                if tcols:
                    lines.append("| Column | Type | Nullable | Key | Default |")
                    lines.append("|--------|------|----------|-----|---------|")
                    for c in tcols:
                        nullable = c["IS_NULLABLE"]
                        key = c["COLUMN_KEY"] or ""
                        default = str(c["COLUMN_DEFAULT"]) if c["COLUMN_DEFAULT"] is not None else ""
                        extra = c.get("EXTRA", "")
                        if extra:
                            default = f"{default} ({extra})" if default else extra
                        lines.append(
                            f"| {c['COLUMN_NAME']} | {c['COLUMN_TYPE']} | {nullable} | {key} | {default} |"
                        )

                # Foreign keys
                tfks = fk_by_table.get(tname, [])
                if tfks:
                    lines.append("\n**Foreign Keys:**")
                    for fk in tfks:
                        lines.append(
                            f"- `{fk['COLUMN_NAME']}` -> "
                            f"`{fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}`"
                        )

                lines.append("")

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        # ── Tool 2: list_tables ──────────────────────────────────────────
        list_tool = _prefixed(prefix, "list_tables")

        @mcp.tool(name=list_tool)
        def list_tables() -> Any:
            """Quick list of all tables in the database with row counts.
Use for a fast overview; use describe_schema for full column details."""
            with _get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT, ENGINE "
                        "FROM information_schema.TABLES "
                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE' "
                        "ORDER BY TABLE_NAME"
                    )
                    tables = cur.fetchall()

            if not tables:
                return {"content": [{"type": "text", "text": "No tables found."}]}

            total_rows = sum(t["TABLE_ROWS"] or 0 for t in tables)
            lines = [
                f"## Tables ({len(tables)} total, ~{total_rows:,} rows)\n",
                "| # | Table | Rows | Engine | Comment |",
                "|---|-------|------|--------|---------|",
            ]
            for i, t in enumerate(tables, 1):
                comment = (t["TABLE_COMMENT"] or "")[:60]
                lines.append(
                    f"| {i} | `{t['TABLE_NAME']}` | {t['TABLE_ROWS'] or 0:,} "
                    f"| {t['ENGINE'] or ''} | {comment} |"
                )

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        # ── Tool 3: describe_table ───────────────────────────────────────
        desc_tool = _prefixed(prefix, "describe_table")

        @mcp.tool(name=desc_tool)
        def describe_table(table_name: str) -> Any:
            """Detailed info about a specific table: columns, types, indexes, sample data (5 rows), and row count.
Use after list_tables to dive into a specific table."""
            try:
                safe_name = _validate_table_name(table_name)
            except ValueError as exc:
                return {"content": [{"type": "text", "text": str(exc)}]}

            with _get_connection() as conn:
                with conn.cursor() as cur:
                    # Row count
                    cur.execute(f"SELECT COUNT(*) AS cnt FROM `{safe_name}`")
                    row_count = cur.fetchone()["cnt"]

                    # Columns
                    cur.execute(
                        "SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, "
                        "COLUMN_DEFAULT, EXTRA, COLUMN_COMMENT "
                        "FROM information_schema.COLUMNS "
                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s "
                        "ORDER BY ORDINAL_POSITION",
                        (safe_name,),
                    )
                    columns = cur.fetchall()

                    # Indexes
                    cur.execute(f"SHOW INDEX FROM `{safe_name}`")
                    indexes = cur.fetchall()

                    # Foreign keys (outgoing)
                    cur.execute(
                        "SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME "
                        "FROM information_schema.KEY_COLUMN_USAGE "
                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s "
                        "AND REFERENCED_TABLE_NAME IS NOT NULL",
                        (safe_name,),
                    )
                    fks = cur.fetchall()

                    # Foreign keys (incoming - who references this table)
                    cur.execute(
                        "SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_COLUMN_NAME "
                        "FROM information_schema.KEY_COLUMN_USAGE "
                        "WHERE TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME = %s",
                        (safe_name,),
                    )
                    incoming_fks = cur.fetchall()

                    # Sample data (5 rows)
                    cur.execute(f"SELECT * FROM `{safe_name}` LIMIT 5")
                    sample = cur.fetchall()

            lines = [f"## Table: `{safe_name}`", f"**Row count:** {row_count:,}\n"]

            # Columns table
            lines.append("### Columns")
            lines.append("| Column | Type | Nullable | Key | Default | Extra | Comment |")
            lines.append("|--------|------|----------|-----|---------|-------|---------|")
            for c in columns:
                default = str(c["COLUMN_DEFAULT"]) if c["COLUMN_DEFAULT"] is not None else ""
                comment = (c.get("COLUMN_COMMENT") or "")[:40]
                lines.append(
                    f"| {c['COLUMN_NAME']} | {c['COLUMN_TYPE']} | {c['IS_NULLABLE']} "
                    f"| {c['COLUMN_KEY'] or ''} | {default} | {c.get('EXTRA', '')} | {comment} |"
                )

            # Indexes
            if indexes:
                lines.append("\n### Indexes")
                idx_grouped: dict[str, list[str]] = {}
                idx_unique: dict[str, bool] = {}
                for ix in indexes:
                    key_name = ix["Key_name"]
                    idx_grouped.setdefault(key_name, []).append(ix["Column_name"])
                    idx_unique[key_name] = not ix["Non_unique"]
                for name, cols in idx_grouped.items():
                    uq = " (UNIQUE)" if idx_unique.get(name) else ""
                    lines.append(f"- **{name}**{uq}: {', '.join(cols)}")

            # Foreign keys
            if fks:
                lines.append("\n### Foreign Keys (outgoing)")
                for fk in fks:
                    lines.append(
                        f"- `{fk['COLUMN_NAME']}` -> "
                        f"`{fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}`"
                    )

            if incoming_fks:
                lines.append("\n### Referenced By (incoming)")
                for fk in incoming_fks:
                    lines.append(
                        f"- `{fk['TABLE_NAME']}.{fk['COLUMN_NAME']}` -> "
                        f"`{safe_name}.{fk['REFERENCED_COLUMN_NAME']}`"
                    )

            # Sample data
            if sample:
                lines.append("\n### Sample Data (first 5 rows)")
                lines.append(_rows_to_markdown(sample))
            else:
                lines.append("\n_Table is empty._")

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        # ── Tool 4: query ────────────────────────────────────────────────
        query_tool = _prefixed(prefix, "query")

        @mcp.tool(name=query_tool)
        def query(sql: str, limit: int = 100) -> Any:
            """Execute a READ-ONLY SQL query (SELECT, SHOW, DESCRIBE, EXPLAIN only).
Returns results as a markdown table. Auto-adds LIMIT if not present.

SECURITY: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE are blocked.

Examples:
  - SELECT * FROM users WHERE active = 1
  - SELECT COUNT(*) FROM orders GROUP BY status
  - SHOW CREATE TABLE products
  - DESCRIBE customers"""
            try:
                safe_sql = _validate_readonly_sql(sql)
            except ValueError as exc:
                return {"content": [{"type": "text", "text": f"**Query blocked:** {exc}"}]}

            # Clamp limit
            if limit < 1:
                limit = 1
            elif limit > 1000:
                limit = 1000

            # Auto-add LIMIT for SELECT statements
            if _ALLOWED_PREFIXES.match(safe_sql) and safe_sql.strip().upper().startswith("SELECT"):
                safe_sql = _ensure_limit(safe_sql, limit)

            try:
                with _get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(safe_sql)
                        rows = cur.fetchall()
                        row_count = cur.rowcount
            except Exception as exc:
                return {"content": [{"type": "text", "text": f"**Query error:** {exc}"}]}

            if not rows:
                return {"content": [{"type": "text", "text": f"Query executed successfully. No rows returned.\n\n```sql\n{safe_sql}\n```"}]}

            md = _rows_to_markdown(rows)
            text = (
                f"**{row_count} row{'s' if row_count != 1 else ''} returned**\n\n"
                f"```sql\n{safe_sql}\n```\n\n{md}"
            )
            return {"content": [{"type": "text", "text": text}]}

        # ── Tool 5: analyze_table ────────────────────────────────────────
        analyze_tool = _prefixed(prefix, "analyze_table")

        @mcp.tool(name=analyze_tool)
        def analyze_table(table_name: str) -> Any:
            """Statistical analysis of a table: column stats (min, max, avg, null count, distinct count), data distribution.
Use to understand data quality and distribution patterns."""
            try:
                safe_name = _validate_table_name(table_name)
            except ValueError as exc:
                return {"content": [{"type": "text", "text": str(exc)}]}

            with _get_connection() as conn:
                with conn.cursor() as cur:
                    # Get columns and types
                    cur.execute(
                        "SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE "
                        "FROM information_schema.COLUMNS "
                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s "
                        "ORDER BY ORDINAL_POSITION",
                        (safe_name,),
                    )
                    columns = cur.fetchall()

                    if not columns:
                        return {"content": [{"type": "text", "text": f"Table `{safe_name}` not found or has no columns."}]}

                    # Row count
                    cur.execute(f"SELECT COUNT(*) AS cnt FROM `{safe_name}`")
                    total_rows = cur.fetchone()["cnt"]

                    # Numeric types for avg/min/max
                    numeric_types = {
                        "tinyint", "smallint", "mediumint", "int", "bigint",
                        "float", "double", "decimal", "numeric",
                    }
                    date_types = {"date", "datetime", "timestamp"}

                    stats: list[dict[str, Any]] = []
                    for col in columns:
                        col_name = col["COLUMN_NAME"]
                        data_type = col["DATA_TYPE"].lower()

                        # Build per-column stats query
                        parts = [
                            f"COUNT(`{col_name}`) AS non_null",
                            f"SUM(CASE WHEN `{col_name}` IS NULL THEN 1 ELSE 0 END) AS null_count",
                            f"COUNT(DISTINCT `{col_name}`) AS distinct_count",
                        ]
                        if data_type in numeric_types:
                            parts.extend([
                                f"MIN(`{col_name}`) AS min_val",
                                f"MAX(`{col_name}`) AS max_val",
                                f"ROUND(AVG(`{col_name}`), 4) AS avg_val",
                            ])
                        elif data_type in date_types:
                            parts.extend([
                                f"MIN(`{col_name}`) AS min_val",
                                f"MAX(`{col_name}`) AS max_val",
                            ])
                        else:
                            parts.extend([
                                f"MIN(CHAR_LENGTH(`{col_name}`)) AS min_len",
                                f"MAX(CHAR_LENGTH(`{col_name}`)) AS max_len",
                                f"ROUND(AVG(CHAR_LENGTH(`{col_name}`)), 1) AS avg_len",
                            ])

                        select_sql = f"SELECT {', '.join(parts)} FROM `{safe_name}`"
                        cur.execute(select_sql)
                        row = cur.fetchone()

                        stat = {
                            "column": col_name,
                            "type": col["COLUMN_TYPE"],
                            "non_null": row["non_null"],
                            "null_count": row["null_count"],
                            "null_pct": round(row["null_count"] / total_rows * 100, 1) if total_rows > 0 else 0,
                            "distinct": row["distinct_count"],
                        }

                        if data_type in numeric_types:
                            stat["min"] = row.get("min_val")
                            stat["max"] = row.get("max_val")
                            stat["avg"] = row.get("avg_val")
                        elif data_type in date_types:
                            stat["min"] = str(row.get("min_val")) if row.get("min_val") else None
                            stat["max"] = str(row.get("max_val")) if row.get("max_val") else None
                        else:
                            stat["min_len"] = row.get("min_len")
                            stat["max_len"] = row.get("max_len")
                            stat["avg_len"] = row.get("avg_len")

                        stats.append(stat)

                    # Top value distribution for low-cardinality columns (distinct < 20)
                    distributions: dict[str, list[dict]] = {}
                    for st in stats:
                        if 1 < (st["distinct"] or 0) <= 20 and total_rows > 0:
                            col_name = st["column"]
                            cur.execute(
                                f"SELECT `{col_name}` AS val, COUNT(*) AS cnt "
                                f"FROM `{safe_name}` "
                                f"GROUP BY `{col_name}` ORDER BY cnt DESC LIMIT 20"
                            )
                            distributions[col_name] = cur.fetchall()

            # Build output
            lines = [
                f"## Analysis: `{safe_name}`",
                f"**Total rows:** {total_rows:,}\n",
                "### Column Statistics",
                "| Column | Type | Non-Null | Nulls (%) | Distinct | Min | Max | Avg |",
                "|--------|------|----------|-----------|----------|-----|-----|-----|",
            ]
            for s in stats:
                min_v = s.get("min", s.get("min_len", ""))
                max_v = s.get("max", s.get("max_len", ""))
                avg_v = s.get("avg", s.get("avg_len", ""))
                min_v = str(min_v) if min_v is not None else ""
                max_v = str(max_v) if max_v is not None else ""
                avg_v = str(avg_v) if avg_v is not None else ""
                lines.append(
                    f"| {s['column']} | {s['type']} | {s['non_null']:,} "
                    f"| {s['null_count']:,} ({s['null_pct']}%) | {s['distinct']:,} "
                    f"| {min_v} | {max_v} | {avg_v} |"
                )

            if distributions:
                lines.append("\n### Value Distributions (low-cardinality columns)")
                for col_name, dist in distributions.items():
                    lines.append(f"\n**`{col_name}`:**")
                    for d in dist:
                        val = d["val"] if d["val"] is not None else "NULL"
                        pct = round(d["cnt"] / total_rows * 100, 1) if total_rows > 0 else 0
                        lines.append(f"- `{val}`: {d['cnt']:,} ({pct}%)")

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        # ── Tool 6: find_related_tables ──────────────────────────────────
        related_tool = _prefixed(prefix, "find_related_tables")

        @mcp.tool(name=related_tool)
        def find_related_tables(table_name: str) -> Any:
            """Find tables related to the given table via foreign keys or similar column names.
Useful for understanding data relationships and building JOINs."""
            try:
                safe_name = _validate_table_name(table_name)
            except ValueError as exc:
                return {"content": [{"type": "text", "text": str(exc)}]}

            with _get_connection() as conn:
                with conn.cursor() as cur:
                    # Check table exists
                    cur.execute(
                        "SELECT 1 FROM information_schema.TABLES "
                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
                        (safe_name,),
                    )
                    if not cur.fetchone():
                        return {"content": [{"type": "text", "text": f"Table `{safe_name}` not found."}]}

                    # Get columns of target table
                    cur.execute(
                        "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
                        (safe_name,),
                    )
                    target_cols = {r["COLUMN_NAME"] for r in cur.fetchall()}

                    # Outgoing FKs (this table references others)
                    cur.execute(
                        "SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME "
                        "FROM information_schema.KEY_COLUMN_USAGE "
                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s "
                        "AND REFERENCED_TABLE_NAME IS NOT NULL",
                        (safe_name,),
                    )
                    outgoing = cur.fetchall()

                    # Incoming FKs (others reference this table)
                    cur.execute(
                        "SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_COLUMN_NAME "
                        "FROM information_schema.KEY_COLUMN_USAGE "
                        "WHERE TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME = %s",
                        (safe_name,),
                    )
                    incoming = cur.fetchall()

                    # Find tables with similarly-named columns (heuristic)
                    # Look for columns named like <table>_id, <table>Id, id_<table>
                    # Also check if other tables share column names with this table
                    cur.execute(
                        "SELECT DISTINCT c.TABLE_NAME, c.COLUMN_NAME "
                        "FROM information_schema.COLUMNS c "
                        "WHERE c.TABLE_SCHEMA = DATABASE() "
                        "AND c.TABLE_NAME != %s "
                        "AND ("
                        "  c.COLUMN_NAME LIKE %s OR "
                        "  c.COLUMN_NAME LIKE %s OR "
                        "  c.COLUMN_NAME LIKE %s"
                        ") "
                        "ORDER BY c.TABLE_NAME",
                        (
                            safe_name,
                            f"{safe_name}_id",
                            f"{safe_name}Id",
                            f"{safe_name}_%%",
                        ),
                    )
                    name_matches = cur.fetchall()

                    # Also find shared column names (excluding generic ones like id, created_at)
                    generic_cols = {
                        "id", "ID", "created_at", "updated_at", "deleted_at",
                        "created_by", "updated_by", "status", "name", "description",
                        "sort_order", "is_active", "is_deleted",
                    }
                    shared_cols_filter = target_cols - generic_cols
                    shared_tables: dict[str, list[str]] = {}
                    if shared_cols_filter:
                        placeholders = ", ".join(["%s"] * len(shared_cols_filter))
                        cur.execute(
                            f"SELECT TABLE_NAME, COLUMN_NAME "
                            f"FROM information_schema.COLUMNS "
                            f"WHERE TABLE_SCHEMA = DATABASE() "
                            f"AND TABLE_NAME != %s "
                            f"AND COLUMN_NAME IN ({placeholders})",
                            (safe_name, *shared_cols_filter),
                        )
                        for r in cur.fetchall():
                            shared_tables.setdefault(r["TABLE_NAME"], []).append(r["COLUMN_NAME"])

            lines = [f"## Related Tables for `{safe_name}`\n"]

            if outgoing:
                lines.append("### References (outgoing foreign keys)")
                for fk in outgoing:
                    lines.append(
                        f"- `{safe_name}.{fk['COLUMN_NAME']}` -> "
                        f"`{fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}`"
                    )
                    lines.append(
                        f"  JOIN: `JOIN {fk['REFERENCED_TABLE_NAME']} ON "
                        f"{safe_name}.{fk['COLUMN_NAME']} = "
                        f"{fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}`"
                    )
                lines.append("")

            if incoming:
                lines.append("### Referenced By (incoming foreign keys)")
                for fk in incoming:
                    lines.append(
                        f"- `{fk['TABLE_NAME']}.{fk['COLUMN_NAME']}` -> "
                        f"`{safe_name}.{fk['REFERENCED_COLUMN_NAME']}`"
                    )
                    lines.append(
                        f"  JOIN: `JOIN {fk['TABLE_NAME']} ON "
                        f"{safe_name}.{fk['REFERENCED_COLUMN_NAME']} = "
                        f"{fk['TABLE_NAME']}.{fk['COLUMN_NAME']}`"
                    )
                lines.append("")

            if name_matches:
                lines.append("### Possible Relations (by column naming)")
                seen = set()
                for m in name_matches:
                    key = (m["TABLE_NAME"], m["COLUMN_NAME"])
                    if key not in seen:
                        seen.add(key)
                        lines.append(f"- `{m['TABLE_NAME']}` has column `{m['COLUMN_NAME']}`")
                lines.append("")

            if shared_tables:
                lines.append("### Shared Column Names")
                for tbl, cols in sorted(shared_tables.items()):
                    lines.append(f"- `{tbl}`: {', '.join(f'`{c}`' for c in cols)}")
                lines.append("")

            if not outgoing and not incoming and not name_matches and not shared_tables:
                lines.append("_No related tables found via foreign keys or naming conventions._")

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        # ── Tool 7: list_databases ──────────────────────────────────────
        list_dbs_tool = _prefixed(prefix, "list_databases")

        @mcp.tool(name=list_dbs_tool)
        def list_databases() -> Any:
            """List ALL databases on the server (not just the connected one).
Returns database names with sizes."""
            try:
                with _get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SHOW DATABASES")
                        dbs = cur.fetchall()
            except Exception as exc:
                return {"content": [{"type": "text", "text": f"**Error:** {exc}"}]}

            if not dbs:
                return {"content": [{"type": "text", "text": "_No databases found._"}]}

            lines = [
                f"## Databases ({len(dbs)} total)\n",
                "| # | Database |",
                "|---|----------|",
            ]
            for i, row in enumerate(dbs, 1):
                # SHOW DATABASES returns a single column; key name varies by driver
                db_name = list(row.values())[0]
                lines.append(f"| {i} | `{db_name}` |")

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        # ── Tool 8: list_views ──────────────────────────────────────────
        list_views_tool = _prefixed(prefix, "list_views")

        @mcp.tool(name=list_views_tool)
        def list_views() -> Any:
            """List all views in the current database with their definitions."""
            try:
                with _get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT TABLE_NAME, VIEW_DEFINITION "
                            "FROM information_schema.VIEWS "
                            "WHERE TABLE_SCHEMA = DATABASE()"
                        )
                        views = cur.fetchall()
            except Exception as exc:
                return {"content": [{"type": "text", "text": f"**Error:** {exc}"}]}

            if not views:
                return {"content": [{"type": "text", "text": "_No views found in the current database._"}]}

            lines = [f"## Views ({len(views)} total)\n"]
            for v in views:
                definition = str(v.get("VIEW_DEFINITION") or "")
                if len(definition) > 200:
                    definition = definition[:200] + "..."
                lines.append(f"### `{v['TABLE_NAME']}`")
                lines.append(f"```sql\n{definition}\n```\n")

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        # ── Tool 9: list_procedures ─────────────────────────────────────
        list_procs_tool = _prefixed(prefix, "list_procedures")

        @mcp.tool(name=list_procs_tool)
        def list_procedures() -> Any:
            """List all stored procedures in the current database."""
            try:
                with _get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT ROUTINE_NAME, ROUTINE_TYPE, CREATED, LAST_ALTERED "
                            "FROM information_schema.ROUTINES "
                            "WHERE ROUTINE_SCHEMA = DATABASE() AND ROUTINE_TYPE = 'PROCEDURE'"
                        )
                        procs = cur.fetchall()
            except Exception as exc:
                return {"content": [{"type": "text", "text": f"**Error:** {exc}"}]}

            if not procs:
                return {"content": [{"type": "text", "text": "_No stored procedures found._"}]}

            lines = [
                f"## Stored Procedures ({len(procs)} total)\n",
                "| # | Procedure | Created | Last Altered |",
                "|---|-----------|---------|--------------|",
            ]
            for i, p in enumerate(procs, 1):
                created = str(p.get("CREATED") or "")
                altered = str(p.get("LAST_ALTERED") or "")
                lines.append(f"| {i} | `{p['ROUTINE_NAME']}` | {created} | {altered} |")

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        # ── Tool 10: list_functions ─────────────────────────────────────
        list_funcs_tool = _prefixed(prefix, "list_functions")

        @mcp.tool(name=list_funcs_tool)
        def list_functions() -> Any:
            """List all stored functions in the current database."""
            try:
                with _get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT ROUTINE_NAME, ROUTINE_TYPE, CREATED "
                            "FROM information_schema.ROUTINES "
                            "WHERE ROUTINE_SCHEMA = DATABASE() AND ROUTINE_TYPE = 'FUNCTION'"
                        )
                        funcs = cur.fetchall()
            except Exception as exc:
                return {"content": [{"type": "text", "text": f"**Error:** {exc}"}]}

            if not funcs:
                return {"content": [{"type": "text", "text": "_No stored functions found._"}]}

            lines = [
                f"## Stored Functions ({len(funcs)} total)\n",
                "| # | Function | Created |",
                "|---|----------|---------|",
            ]
            for i, f in enumerate(funcs, 1):
                created = str(f.get("CREATED") or "")
                lines.append(f"| {i} | `{f['ROUTINE_NAME']}` | {created} |")

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        # ── Tool 11: list_triggers ──────────────────────────────────────
        list_triggers_tool = _prefixed(prefix, "list_triggers")

        @mcp.tool(name=list_triggers_tool)
        def list_triggers() -> Any:
            """List all triggers in the current database."""
            try:
                with _get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT TRIGGER_NAME, EVENT_MANIPULATION, "
                            "EVENT_OBJECT_TABLE, ACTION_TIMING "
                            "FROM information_schema.TRIGGERS "
                            "WHERE TRIGGER_SCHEMA = DATABASE()"
                        )
                        triggers = cur.fetchall()
            except Exception as exc:
                return {"content": [{"type": "text", "text": f"**Error:** {exc}"}]}

            if not triggers:
                return {"content": [{"type": "text", "text": "_No triggers found._"}]}

            lines = [
                f"## Triggers ({len(triggers)} total)\n",
                "| # | Trigger | Event | Table | Timing |",
                "|---|---------|-------|-------|--------|",
            ]
            for i, t in enumerate(triggers, 1):
                lines.append(
                    f"| {i} | `{t['TRIGGER_NAME']}` | {t['EVENT_MANIPULATION']} "
                    f"| `{t['EVENT_OBJECT_TABLE']}` | {t['ACTION_TIMING']} |"
                )

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        # ── Tool 12: list_events ────────────────────────────────────────
        list_events_tool = _prefixed(prefix, "list_events")

        @mcp.tool(name=list_events_tool)
        def list_events() -> Any:
            """List all scheduled events in the current database."""
            try:
                with _get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT EVENT_NAME, STATUS, INTERVAL_VALUE, "
                            "INTERVAL_FIELD, LAST_EXECUTED "
                            "FROM information_schema.EVENTS "
                            "WHERE EVENT_SCHEMA = DATABASE()"
                        )
                        events = cur.fetchall()
            except Exception as exc:
                return {"content": [{"type": "text", "text": f"**Error:** {exc}"}]}

            if not events:
                return {"content": [{"type": "text", "text": "_No scheduled events found._"}]}

            lines = [
                f"## Scheduled Events ({len(events)} total)\n",
                "| # | Event | Status | Interval | Last Executed |",
                "|---|-------|--------|----------|---------------|",
            ]
            for i, e in enumerate(events, 1):
                interval = ""
                if e.get("INTERVAL_VALUE") and e.get("INTERVAL_FIELD"):
                    interval = f"{e['INTERVAL_VALUE']} {e['INTERVAL_FIELD']}"
                last_exec = str(e.get("LAST_EXECUTED") or "Never")
                lines.append(
                    f"| {i} | `{e['EVENT_NAME']}` | {e.get('STATUS', '')} "
                    f"| {interval} | {last_exec} |"
                )

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        # ── Tool 13: show_create ────────────────────────────────────────
        show_create_tool = _prefixed(prefix, "show_create")

        @mcp.tool(name=show_create_tool)
        def show_create(object_type: str, object_name: str) -> Any:
            """Show the CREATE statement for a database object.

Parameters:
  - object_type: One of "table", "view", "procedure", "function", "trigger", "event"
  - object_name: Name of the object"""
            allowed_types = {"table", "view", "procedure", "function", "trigger", "event"}
            obj_type = object_type.strip().lower()
            if obj_type not in allowed_types:
                return {"content": [{"type": "text", "text":
                    f"**Invalid object_type:** `{object_type}`\n\n"
                    f"Allowed: {', '.join(sorted(allowed_types))}"
                }]}

            try:
                safe_name = _validate_table_name(object_name)
            except ValueError as exc:
                return {"content": [{"type": "text", "text": str(exc)}]}

            sql_keyword = obj_type.upper()
            try:
                with _get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(f"SHOW CREATE {sql_keyword} `{safe_name}`")
                        row = cur.fetchone()
            except Exception as exc:
                return {"content": [{"type": "text", "text": f"**Error:** {exc}"}]}

            if not row:
                return {"content": [{"type": "text", "text":
                    f"_{obj_type.title()} `{safe_name}` not found._"
                }]}

            # The CREATE statement column name varies by object type
            create_stmt = None
            for key in row:
                if "create" in key.lower():
                    create_stmt = row[key]
                    break
            if create_stmt is None:
                # Fallback: use the last column value
                create_stmt = list(row.values())[-1]

            return {"content": [{"type": "text", "text":
                f"## SHOW CREATE {sql_keyword} `{safe_name}`\n\n"
                f"```sql\n{create_stmt}\n```"
            }]}

        # ── Tool 14: switch_database ────────────────────────────────────
        switch_db_tool = _prefixed(prefix, "switch_database")

        @mcp.tool(name=switch_db_tool)
        def switch_database(database_name: str) -> Any:
            """Switch to a different database on the same server.
Validates the database exists before switching.

Parameters:
  - database_name: Name of the database to switch to"""
            try:
                safe_name = _validate_table_name(database_name)
            except ValueError as exc:
                return {"content": [{"type": "text", "text": str(exc)}]}

            # Verify database exists
            try:
                with _get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SHOW DATABASES")
                        dbs = cur.fetchall()
                        db_names = [list(r.values())[0] for r in dbs]
                        if safe_name not in db_names:
                            return {"content": [{"type": "text", "text":
                                f"**Database `{safe_name}` not found.**\n\n"
                                f"Available databases: {', '.join(f'`{d}`' for d in db_names)}"
                            }]}
            except Exception as exc:
                return {"content": [{"type": "text", "text": f"**Error listing databases:** {exc}"}]}

            # Switch the connection
            if "cfg" in _dynamic:
                # Update the dynamic config's dbname
                old_db = _dynamic["cfg"].dbname
                _dynamic["cfg"] = DynamicDbConfig(
                    driver=_dynamic["cfg"].driver,
                    host=_dynamic["cfg"].host,
                    port=_dynamic["cfg"].port,
                    dbname=safe_name,
                    username=_dynamic["cfg"].username,
                    password=_dynamic["cfg"].password,
                )
                return {"content": [{"type": "text", "text":
                    f"**Switched database:** `{old_db}` -> `{safe_name}`"
                }]}
            elif default_db_cfg and default_db_cfg.host:
                # Switch from default config to dynamic config
                _dynamic["cfg"] = DynamicDbConfig(
                    driver="mysql",
                    host=default_db_cfg.host,
                    port=default_db_cfg.port,
                    dbname=safe_name,
                    username=default_db_cfg.username,
                    password=default_db_cfg.password,
                )
                return {"content": [{"type": "text", "text":
                    f"**Switched database to:** `{safe_name}`"
                }]}
            else:
                return {"content": [{"type": "text", "text":
                    "**No active connection.** Use `connect_database` first."
                }]}

    def manifest_groups(self, *, prefix: str) -> list[dict]:
        return [
            {
                "id": "database_exploration",
                "title": "Database Exploration & Analysis",
                "tools": [
                    f"{prefix}connect_database",
                    f"{prefix}describe_schema",
                    f"{prefix}list_tables",
                    f"{prefix}describe_table",
                    f"{prefix}query",
                    f"{prefix}analyze_table",
                    f"{prefix}find_related_tables",
                    f"{prefix}list_databases",
                    f"{prefix}list_views",
                    f"{prefix}list_procedures",
                    f"{prefix}list_functions",
                    f"{prefix}list_triggers",
                    f"{prefix}list_events",
                    f"{prefix}show_create",
                    f"{prefix}switch_database",
                ],
            }
        ]
