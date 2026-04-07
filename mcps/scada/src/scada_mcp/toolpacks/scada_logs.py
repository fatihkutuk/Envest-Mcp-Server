"""Log/schema/alarm tools from scada_ported: get_database_schema, get_table_info,
run_safe_query, list_alarms, get_active_alarms, get_alarm_subscribers.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..tools.core import guard, prefixed_name
from ..types import InstanceConfig
from .. import db as dbmod

log = logging.getLogger(__name__)


class ScadaLogsPack:
    """DB schema inspection, safe queries and alarm parameter tools."""

    id = "scada_logs"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix

        # --- list_alarms ---
        tool = prefixed_name(prefix, "list_alarms")

        def _list_alarms_impl(nodeId: int = 0, limit: int = 50, offset: int = 0) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 200)
            offset = max(int(offset), 0)
            params: list[Any] = []
            where = ""
            if int(nodeId) > 0:
                where = "WHERE ap.nid = %s"
                params.append(int(nodeId))
            sql = f"""
                SELECT ap.pId, ap.name, ap.nid, n.nName AS node_adi, ap.tagPath,
                       ap.minVal, ap.maxVal, ap.scanRate, ap.stayTime,
                       ap.alType, ap.alGroup, ap.alGroupPath,
                       CASE WHEN ap.alertAlarm = 1 THEN 'Evet' ELSE 'Hayır' END AS bildirim_alarm,
                       CASE WHEN ap.logAlarm = 1 THEN 'Evet' ELSE 'Hayır' END AS log_alarm,
                       ap.comment,
                       ast.state AS aktif_mi, ast.lastVal, ast.time AS son_durum_zamani
                FROM alarmparameters ap
                LEFT JOIN node n ON ap.nid = n.id
                LEFT JOIN alarmstate ast ON ap.pId = ast.pId
                {where}
                ORDER BY ap.pId DESC
                LIMIT %s OFFSET %s
            """
            count_sql = f"SELECT COUNT(*) AS total FROM alarmparameters ap {where}"
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, tuple(params + [limit, offset]))
                    alarms = list(cur.fetchall())
                    cur.execute(count_sql, tuple(params))
                    total = int(cur.fetchone()["total"])
            return {"total": total, "count": len(alarms), "alarms": alarms}

        @mcp.tool(name=tool)
        def list_alarms(nodeId: int = 0, limit: int = 50, offset: int = 0) -> str:
            """Alarm parametreleri listesi."""
            return guard(tool, _list_alarms_impl)(nodeId, limit, offset)

        # --- get_active_alarms ---
        tool = prefixed_name(prefix, "get_active_alarms")

        def _get_active_alarms_impl(limit: int = 100) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 500)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT ast.pId, ap.name, ap.nid, n.nName AS node_adi, ap.tagPath,
                               ap.minVal, ap.maxVal, ast.lastVal, ast.time AS alarm_zamani,
                               ap.alType, ap.alGroup, ap.alGroupPath, ap.comment,
                               CASE WHEN ast.isLoud = 1 THEN 'Sesli' ELSE 'Sessiz' END AS ses_durumu
                        FROM alarmstate ast
                        JOIN alarmparameters ap ON ast.pId = ap.pId
                        LEFT JOIN node n ON ap.nid = n.id
                        WHERE ast.state = 1
                        ORDER BY ast.time DESC
                        LIMIT %s
                        """,
                        (limit,),
                    )
                    alarms = list(cur.fetchall())
            return {"count": len(alarms), "active_alarms": alarms}

        @mcp.tool(name=tool)
        def get_active_alarms(limit: int = 100) -> str:
            """Aktif alarm listesi (state=1)."""
            return guard(tool, _get_active_alarms_impl)(limit)

        # --- get_alarm_subscribers ---
        tool = prefixed_name(prefix, "get_alarm_subscribers")

        def _get_alarm_subscribers_impl(alarmId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            aid = int(alarmId)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT pId, name, nid, tagPath, minVal, maxVal, comment FROM alarmparameters WHERE pId = %s",
                        (aid,),
                    )
                    alarm = cur.fetchone()
                    if not alarm:
                        return {"error": f"Alarm ID {aid} bulunamadı."}
                    cur.execute(
                        """
                        SELECT ua.uid, u.uFirstName, u.uLastName, u.uName, u.uTel, u.uMail,
                               ua.stype,
                               CASE ua.stype WHEN 0 THEN 'Alarm' WHEN 1 THEN 'SMS' WHEN 2 THEN 'Mail' WHEN 3 THEN 'SMS+Mail' END AS bildirim_tipi
                        FROM user_alarm ua
                        JOIN users u ON ua.uid = u.id
                        WHERE ua.al_Id = %s
                        ORDER BY u.uFirstName
                        """,
                        (aid,),
                    )
                    subscribers = list(cur.fetchall())
                    cur.execute(
                        "SELECT type, msgTo, title, toUrl, server FROM user_notifications WHERE alarmParameterId = %s",
                        (aid,),
                    )
                    notifications = list(cur.fetchall())
            alarm["abone_sayisi"] = len(subscribers)
            alarm["aboneler"] = subscribers
            alarm["bildirimler"] = notifications
            return alarm

        @mcp.tool(name=tool)
        def get_alarm_subscribers(alarmId: int) -> str:
            """Alarm abonelikleri."""
            return guard(tool, _get_alarm_subscribers_impl)(alarmId)

        # --- get_database_schema ---
        tool = prefixed_name(prefix, "get_database_schema")

        def _get_database_schema_impl() -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT TABLE_NAME, TABLE_ROWS, ENGINE, TABLE_COMMENT
                        FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_SCHEMA = 'kbindb'
                        ORDER BY TABLE_NAME
                        """
                    )
                    tables = list(cur.fetchall())
                    cur.execute(
                        """
                        SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME, CONSTRAINT_NAME
                        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                        WHERE TABLE_SCHEMA = 'kbindb' AND REFERENCED_TABLE_NAME IS NOT NULL
                        ORDER BY TABLE_NAME
                        """
                    )
                    fks = list(cur.fetchall())
            fk_map: dict[str, list[dict[str, str]]] = {}
            for fk in fks:
                t = fk.get("TABLE_NAME")
                if not t:
                    continue
                fk_map.setdefault(str(t), []).append(
                    {
                        "column": str(fk.get("COLUMN_NAME")),
                        "references": f"{fk.get('REFERENCED_TABLE_NAME')}.{fk.get('REFERENCED_COLUMN_NAME')}",
                    }
                )
            result: list[dict[str, Any]] = []
            for t in tables:
                name = str(t.get("TABLE_NAME"))
                entry: dict[str, Any] = {
                    "table": name,
                    "rows": int(t.get("TABLE_ROWS") or 0),
                    "engine": t.get("ENGINE"),
                }
                if name in fk_map and fk_map[name]:
                    entry["foreign_keys"] = fk_map[name]
                result.append(entry)

            relationships = [
                "users.gid -> user_groups.id : Kullanıcı hangi gruba ait",
                "user_auths(uid -> users.id, nid -> node.id) : Kullanıcının node üzerindeki bireysel yetkileri",
                "user_group_auths(gid -> user_groups.id, nid -> node.id) : Grubun node üzerindeki yetkileri",
                "user_alarm(uid -> users.id, al_Id -> alarmparameters.pId) : Kullanıcının alarm abonelikleri",
                "user_node_rel(uid -> users.id, nid -> node.id) : Kullanıcı-node ilişkileri",
                "alarmparameters.nid -> node.id : Alarm hangi node'a ait",
                "alarmstate.pId -> alarmparameters.pId : Alarm anlık durum bilgisi",
                "node_param.nodeId -> node.id : Node parametreleri (key-value)",
                "node.nView -> node_product_type.nView : Node ürün tipi",
                "logparameters.nid -> node.id : Log parametreleri hangi node'a ait",
                "tag_link(srcDid, destDid -> node.id) : Cihazlar arası tag bağlantıları",
                "tag_clone(src_nid, dest_nid -> node.id) : Node'lar arası tag klonlama",
                "tag_clone_tags.cid -> tag_clone.id : Klonlanan tag detayları",
                "tag_clone.type -> tag_clone_type.id : Klonlama tipleri",
                "user_notifications.alarmParameterId -> alarmparameters.pId : Alarm bildirim ayarları",
                "_tagoku.devId -> node.id : Anlık SCADA tag okuma değerleri (MEMORY)",
                "_servercounters.devId -> node.id : Sunucu sayaçları",
            ]
            return {"database": "kbindb", "table_count": len(result), "tables": result, "relationships": relationships}

        @mcp.tool(name=tool)
        def get_database_schema() -> str:
            """Veritabanı şema bilgisi: tablolar, kolonlar."""
            return guard(tool, _get_database_schema_impl)()

        # --- get_table_info ---
        tool = prefixed_name(prefix, "get_table_info")

        def _get_table_info_impl(tableName: str) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            t = (tableName or "").strip()
            if not t:
                return {"error": "tableName gerekli"}
            forbidden_fields = {"uPass", "passMD5", "passText"}
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'kbindb' AND TABLE_NAME = %s",
                        (t,),
                    )
                    if not cur.fetchone():
                        return {"error": f"'{t}' tablosu kbindb'de bulunamadı."}
                    cur.execute(
                        """
                        SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY, COLUMN_COMMENT, EXTRA
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = 'kbindb' AND TABLE_NAME = %s
                        ORDER BY ORDINAL_POSITION
                        """,
                        (t,),
                    )
                    cols = [c for c in cur.fetchall() if str(c.get("COLUMN_NAME")) not in forbidden_fields]
                    cur.execute(
                        """
                        SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                        WHERE TABLE_SCHEMA = 'kbindb' AND TABLE_NAME = %s AND REFERENCED_TABLE_NAME IS NOT NULL
                        """,
                        (t,),
                    )
                    fks = list(cur.fetchall())
                    cur.execute(
                        """
                        SELECT INDEX_NAME, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS idx_columns, NON_UNIQUE
                        FROM INFORMATION_SCHEMA.STATISTICS
                        WHERE TABLE_SCHEMA = 'kbindb' AND TABLE_NAME = %s
                        GROUP BY INDEX_NAME, NON_UNIQUE
                        """,
                        (t,),
                    )
                    idx = list(cur.fetchall())
            return {"table": t, "columns": cols, "foreign_keys": fks, "indexes": idx}

        @mcp.tool(name=tool)
        def get_table_info(tableName: str) -> str:
            """Tablo detayı: kolonlar ve örnek veri."""
            return guard(tool, _get_table_info_impl)(tableName)

        # --- run_safe_query ---
        tool = prefixed_name(prefix, "run_safe_query")

        def _run_safe_query_impl(query: str) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            normalized = re.sub(r"\s+", " ", (query or "").strip())
            if not re.match(r"^\s*SELECT\b", normalized, flags=re.IGNORECASE):
                return {"error": "Yalnızca SELECT sorguları çalıştırılabilir."}
            forbidden_keywords = [
                "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
                "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE",
                "INTO OUTFILE", "INTO DUMPFILE", "LOAD_FILE",
            ]
            forbidden_fields = ["uPass", "passMD5", "passText"]
            for w in forbidden_keywords:
                if w.lower() in normalized.lower():
                    return {"error": f"Güvenlik: '{w}' ifadesi kullanılamaz."}
            for f in forbidden_fields:
                if f.lower() in normalized.lower():
                    return {"error": f"Güvenlik: '{f}' alanı sorgulanamaz."}
            if " limit " not in (" " + normalized.lower() + " "):
                normalized = normalized + " LIMIT 100"
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(normalized)
                    results = list(cur.fetchall())
            return {"query": normalized, "row_count": len(results), "results": results}

        @mcp.tool(name=tool)
        def run_safe_query(query: str) -> str:
            """Güvenli SELECT sorgusu (sadece okuma)."""
            return guard(tool, _run_safe_query_impl)(query)

    def manifest_groups(self, *, prefix: str) -> list[dict]:
        p = prefix
        return [
            {
                "id": "alarms",
                "title_tr": "Alarmlar",
                "tools": [p + "list_alarms", p + "get_active_alarms", p + "get_alarm_subscribers"],
            },
            {
                "id": "schema",
                "title_tr": "DB şema / güvenli sorgu",
                "tools": [p + "get_database_schema", p + "get_table_info", p + "run_safe_query"],
            },
        ]
