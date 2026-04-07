"""Alarm statistics and extended alarm tools from scada_extended."""
from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from .. import db as dbmod
from ..tools.core import guard, prefixed_name
from ..types import InstanceConfig

log = logging.getLogger(__name__)


class ScadaAlarmsPack:
    """Alarm queries, alarm groups, alarm history."""

    id = "scada_alarms"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix

        # --- get_alarm_statistics ---
        tool = prefixed_name(prefix, "get_alarm_statistics")

        def _get_alarm_statistics_impl() -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) AS c FROM kbindb.alarmparameters")
                    total = int((cur.fetchone() or {})["c"] or 0)
                    active_alarms = 0
                    try:
                        cur.execute("SELECT COUNT(*) AS c FROM kbindb.alarmstate WHERE state = 1")
                        active_alarms = int((cur.fetchone() or {})["c"] or 0)
                    except Exception:
                        pass
                    aktif_son_1s = aktif_son_24s = aktif_bugun = None
                    try:
                        cur.execute(
                            """
                            SELECT COUNT(*) AS c FROM kbindb.alarmstate
                            WHERE state = 1 AND `time` >= NOW() - INTERVAL 1 HOUR
                            """
                        )
                        aktif_son_1s = int((cur.fetchone() or {})["c"] or 0)
                    except Exception:
                        pass
                    try:
                        cur.execute(
                            """
                            SELECT COUNT(*) AS c FROM kbindb.alarmstate
                            WHERE state = 1 AND `time` >= NOW() - INTERVAL 24 HOUR
                            """
                        )
                        aktif_son_24s = int((cur.fetchone() or {})["c"] or 0)
                    except Exception:
                        pass
                    try:
                        cur.execute(
                            """
                            SELECT COUNT(*) AS c FROM kbindb.alarmstate
                            WHERE state = 1 AND DATE(`time`) = CURDATE()
                            """
                        )
                        aktif_bugun = int((cur.fetchone() or {})["c"] or 0)
                    except Exception:
                        pass
                    cur.execute(
                        """
                        SELECT alType, COUNT(*) AS sayi FROM kbindb.alarmparameters
                        GROUP BY alType ORDER BY sayi DESC
                        """
                    )
                    by_type = list(cur.fetchall())
                    cur.execute(
                        """
                        SELECT ap.nid, n.nName AS node_adi, COUNT(*) AS alarm_tanim_sayisi
                        FROM kbindb.alarmparameters ap
                        LEFT JOIN kbindb.node n ON ap.nid = n.id
                        GROUP BY ap.nid, n.nName
                        ORDER BY alarm_tanim_sayisi DESC
                        LIMIT 15
                        """
                    )
                    top_nodes = list(cur.fetchall())
                    top_nodes_bugun: list[Any] = []
                    try:
                        cur.execute(
                            """
                            SELECT ap.nid, n.nName AS node_adi, COUNT(*) AS aktif_alarm_sayisi
                            FROM kbindb.alarmstate ast
                            JOIN kbindb.alarmparameters ap ON ast.pId = ap.pId
                            LEFT JOIN kbindb.node n ON ap.nid = n.id
                            WHERE ast.state = 1 AND DATE(ast.`time`) = CURDATE()
                            GROUP BY ap.nid, n.nName
                            ORDER BY aktif_alarm_sayisi DESC
                            LIMIT 15
                            """
                        )
                        top_nodes_bugun = list(cur.fetchall())
                    except Exception:
                        pass
                    top_nodes_son_24s: list[Any] = []
                    try:
                        cur.execute(
                            """
                            SELECT ap.nid, n.nName AS node_adi, COUNT(*) AS aktif_alarm_sayisi
                            FROM kbindb.alarmstate ast
                            JOIN kbindb.alarmparameters ap ON ast.pId = ap.pId
                            LEFT JOIN kbindb.node n ON ap.nid = n.id
                            WHERE ast.state = 1 AND ast.`time` >= NOW() - INTERVAL 24 HOUR
                            GROUP BY ap.nid, n.nName
                            ORDER BY aktif_alarm_sayisi DESC
                            LIMIT 15
                            """
                        )
                        top_nodes_son_24s = list(cur.fetchall())
                    except Exception:
                        pass
                    active_list: list[Any] = []
                    try:
                        cur.execute(
                            """
                            SELECT ast.pId, ap.name, ap.nid, n.nName AS node_adi,
                                   ap.tagPath, ast.lastVal, ast.time AS alarm_zamani
                            FROM kbindb.alarmstate ast
                            JOIN kbindb.alarmparameters ap ON ast.pId = ap.pId
                            LEFT JOIN kbindb.node n ON ap.nid = n.id
                            WHERE ast.state = 1
                            ORDER BY ast.time DESC
                            LIMIT 20
                            """
                        )
                        active_list = list(cur.fetchall())
                    except Exception:
                        pass
                    subscriber_count = 0
                    try:
                        cur.execute("SELECT COUNT(DISTINCT uid) AS c FROM kbindb.user_alarm")
                        subscriber_count = int((cur.fetchone() or {})["c"] or 0)
                    except Exception:
                        pass
            return {
                "aciklama_tr": {
                    "toplam_alarm_parametresi": "SCADA'da tanımlı alarm satırı (eşik/koşul). «Bugün kaç alarm oldu» değil.",
                    "aktif_alarm_sayisi": "Şu an tetiklenmiş (alarmstate.state=1) kayıt sayısı.",
                    "aktif_guncelleme_pencereleri": (
                        "alarmstate.time üzerinden: son 1 saat / 24 saat / bugün (CURDATE) içinde "
                        "güncellenmiş *aktif* alarmlar. Gerçek olay sayımı için ayrı alarm geçmişi tablosu gerekir; "
                        "yoksa bu metrikler operasyonel «tazelik» özetidir."
                    ),
                    "en_cok_alarmli_nodeler": "Eski alan adı: node başına alarm *tanım* sayısı (alarmparameters).",
                    "bugun_en_cok_aktif_alarm_olan_nodeler": "Bugün time güncellenmiş aktif alarmların node dağılımı.",
                    "son_24s_en_cok_aktif_alarm_olan_nodeler": "Son 24 saatte time güncellenmiş aktif alarmların node dağılımı.",
                },
                "toplam_alarm_parametresi": total,
                "aktif_alarm_sayisi": active_alarms,
                "aktif_alarm_son_1_saat_guncelleme": aktif_son_1s,
                "aktif_alarm_son_24_saat_guncelleme": aktif_son_24s,
                "aktif_alarm_bugun_guncelleme": aktif_bugun,
                "alarm_abonesi_kullanici_sayisi": subscriber_count,
                "tipe_gore": by_type,
                "en_cok_alarm_tanimi_olan_nodeler": top_nodes,
                "en_cok_alarmli_nodeler": top_nodes,
                "bugun_en_cok_aktif_alarm_olan_nodeler": top_nodes_bugun,
                "son_24s_en_cok_aktif_alarm_olan_nodeler": top_nodes_son_24s,
                "aktif_alarmlar": active_list,
            }

        @mcp.tool(name=tool)
        def get_alarm_statistics() -> str:
            """Alarm istatistikleri: aktif/geçmiş sayılar, tag ve node bazlı dağılım."""
            return guard(tool, _get_alarm_statistics_impl)()

    def manifest_groups(self, *, prefix: str) -> list[dict]:
        p = prefix
        return [
            {
                "id": "alarms_stats",
                "title_tr": "Alarm istatistikleri",
                "tools": [p + "get_alarm_statistics"],
            },
        ]
