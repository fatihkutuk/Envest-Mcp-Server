from __future__ import annotations

from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP

from .. import db as dbmod
from ..tools.core import guard, prefixed_name
from ..types import InstanceConfig

# PHP DataExchangerTools / DashboardTools ile aynı “çalışıyor” kabul edilen kodlar
_ACTIVE_STATUS_CODES = (11, 31, 41, 61, 71, 81, 91)
_FAILED_CODES = (12, 22, 32, 42, 52, 62, 72, 82, 92)


def _exchanger_db(cur: Any) -> str:
    new_time = old_time = None
    try:
        cur.execute("SELECT MAX(UpdateTime) AS t FROM dbdataexchanger.service")
        new_time = (cur.fetchone() or {}).get("t")
    except Exception:
        pass
    try:
        cur.execute("SELECT MAX(UpdateTime) AS t FROM dbkepware.service")
        old_time = (cur.fetchone() or {}).get("t")
    except Exception:
        pass
    if new_time and old_time:
        from datetime import datetime

        try:
            a = (
                datetime.fromisoformat(str(new_time).replace("Z", "+00:00"))
                if isinstance(new_time, str)
                else new_time
            )
            b = (
                datetime.fromisoformat(str(old_time).replace("Z", "+00:00"))
                if isinstance(old_time, str)
                else old_time
            )
            return "dbdataexchanger" if a >= b else "dbkepware"
        except Exception:
            return "dbdataexchanger" if new_time else "dbkepware"
    if new_time:
        return "dbdataexchanger"
    if old_time:
        return "dbkepware"
    return "dbdataexchanger"


def _extract_connection_params(device: dict[str, Any]) -> dict[str, Any]:
    import json as _json

    dj_raw = device.get("deviceJson")
    cj_raw = device.get("channelJson")
    dj = _json.loads(dj_raw) if isinstance(dj_raw, str) else (dj_raw if isinstance(dj_raw, dict) else {})
    cj = _json.loads(cj_raw) if isinstance(cj_raw, str) else (cj_raw if isinstance(cj_raw, dict) else {})
    if not isinstance(dj, dict):
        dj = {}
    if not isinstance(cj, dict):
        cj = {}
    return {
        "cihaz_ip_string": dj.get("servermain.DEVICE_ID_STRING"),
        "cihaz_port": dj.get("modbus_ethernet.DEVICE_ETHERNET_PORT_NUMBER")
        or cj.get("modbus_ethernet.CHANNEL_ETHERNET_PORT_NUMBER"),
        "baglanti_timeout_sn": dj.get("servermain.DEVICE_CONNECTION_TIMEOUT_SECONDS"),
        "istek_timeout_ms": dj.get("servermain.DEVICE_REQUEST_TIMEOUT_MILLISECONDS"),
        "tarama_hizi_ms": dj.get("servermain.DEVICE_SCAN_MODE_RATE_MS"),
        "tekrar_deneme_sayisi": dj.get("servermain.DEVICE_RETRY_ATTEMPTS"),
        "istekler_arasi_gecikme_ms": dj.get("servermain.DEVICE_INTER_REQUEST_DELAY_MILLISECONDS"),
        "veri_toplama_aktif": dj.get("servermain.DEVICE_DATA_COLLECTION"),
        "oto_pasif_timeout_sayisi": dj.get("servermain.DEVICE_AUTO_DEMOTION_DEMOTE_AFTER_SUCCESSIVE_TIMEOUTS"),
        "oto_pasif_suresi_ms": dj.get("servermain.DEVICE_AUTO_DEMOTION_PERIOD_MS"),
        "oto_pasif_aktif_mi": dj.get("servermain.DEVICE_AUTO_DEMOTION_ENABLE_ON_COMMUNICATIONS_FAILURES"),
        "driver_tipi": dj.get("servermain.MULTIPLE_TYPES_DEVICE_DRIVER") or cj.get("servermain.MULTIPLE_TYPES_DEVICE_DRIVER"),
        "simulasyon": dj.get("servermain.DEVICE_SIMULATED"),
        "tcp_timeout_kapat": dj.get("modbus_ethernet.DEVICE_ETHERNET_CLOSE_TCP_SOCKET_ON_TIMEOUT"),
    }


def _users_active_count(cur: Any) -> int | None:
    """Some DBs use uState, others state/active — try common columns."""
    for col in ("uState", "state", "uStatus", "active"):
        try:
            cur.execute(f"SELECT COUNT(*) AS c FROM kbindb.users WHERE {col} = 1")
            return int((cur.fetchone() or {})["c"] or 0)
        except Exception:
            continue
    return None


class ScadaExtendedPack:
    """PHP `eskiprojeornekicin/src/Tools/*` ile aynı isim/SQL (kbindb + dbdataexchanger/dbkepware)."""

    id = "scada_extended"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix

        # --- DashboardTools ---
        tool = prefixed_name(prefix, "get_scada_summary")

        def _get_scada_summary_impl() -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            ac = ",".join(str(x) for x in _ACTIVE_STATUS_CODES)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    ex_db = _exchanger_db(cur)
                    report: dict[str, Any] = {
                        "rapor_zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "aktif_exchanger_db": ex_db,
                    }
                    cur.execute("SELECT COUNT(*) AS c FROM kbindb.node")
                    node_total = int((cur.fetchone() or {})["c"] or 0)
                    cur.execute(
                        "SELECT nState, COUNT(*) AS sayi FROM kbindb.node GROUP BY nState ORDER BY nState"
                    )
                    node_by_state = list(cur.fetchall())
                    cur.execute(
                        "SELECT nType, COUNT(*) AS sayi FROM kbindb.node WHERE nState >= 0 GROUP BY nType ORDER BY sayi DESC"
                    )
                    node_by_type = list(cur.fetchall())
                    cur.execute(
                        """
                        SELECT pt.name AS urun_tipi, pt.category, COUNT(n.id) AS sayi
                        FROM kbindb.node n
                        LEFT JOIN kbindb.node_product_type pt ON n.nView = pt.nView
                        WHERE n.nState >= 0
                        GROUP BY pt.name, pt.category
                        ORDER BY sayi DESC
                        LIMIT 20
                        """
                    )
                    node_by_product = list(cur.fetchall())
                    report["nodeler"] = {
                        "toplam": node_total,
                        "duruma_gore": node_by_state,
                        "tipe_gore": node_by_type,
                        "urun_tipine_gore": node_by_product,
                    }
                    cur.execute("SELECT COUNT(*) AS c FROM kbindb.users")
                    user_total = int((cur.fetchone() or {})["c"] or 0)
                    user_active = _users_active_count(cur)
                    cur.execute("SELECT COUNT(*) AS c FROM kbindb.user_groups")
                    group_total = int((cur.fetchone() or {})["c"] or 0)
                    report["kullanicilar"] = {
                        "toplam": user_total,
                        "aktif": user_active,
                        "grup_sayisi": group_total,
                    }
                    cur.execute("SELECT COUNT(*) AS c FROM kbindb.alarmparameters")
                    alarm_total = int((cur.fetchone() or {})["c"] or 0)
                    alarm_active = 0
                    try:
                        cur.execute("SELECT COUNT(*) AS c FROM kbindb.alarmstate WHERE state = 1")
                        alarm_active = int((cur.fetchone() or {})["c"] or 0)
                    except Exception:
                        pass
                    cur.execute(
                        """
                        SELECT alType, COUNT(*) AS sayi FROM kbindb.alarmparameters
                        GROUP BY alType ORDER BY sayi DESC
                        """
                    )
                    alarm_by_type = list(cur.fetchall())
                    report["alarmlar"] = {
                        "toplam_parametre": alarm_total,
                        "aktif_alarm": alarm_active,
                        "tipe_gore": alarm_by_type,
                        "aciklama_tr": (
                            "toplam_parametre = alarm tanımı (alarmparameters satırı). "
                            "aktif_alarm = şu an tetiklenmiş (alarmstate.state=1) kayıt sayısı. "
                            "Bunlar «kaç alarm oldu» olayı sayısı değildir; olay geçmişi ayrı tabloda tutulmuyorsa "
                            "zaman penceresi için get_alarm_statistics kullanın."
                        ),
                    }
                    cur.execute("SELECT COUNT(*) AS c FROM kbindb.logparameters")
                    log_total = int((cur.fetchone() or {})["c"] or 0)
                    cur.execute("SELECT COUNT(*) AS c FROM kbindb.logparameters WHERE state = 1")
                    log_active = int((cur.fetchone() or {})["c"] or 0)
                    cur.execute(
                        "SELECT state, COUNT(*) AS sayi FROM kbindb.logparameters GROUP BY state ORDER BY state DESC"
                    )
                    log_by_state = list(cur.fetchall())
                    report["log_parametreleri"] = {
                        "toplam": log_total,
                        "aktif": log_active,
                        "duruma_gore": log_by_state,
                    }
                    cur.execute("SELECT COUNT(*) AS c FROM kbindb._tagoku")
                    live_tag = int((cur.fetchone() or {})["c"] or 0)
                    cur.execute("SELECT COUNT(DISTINCT devId) AS c FROM kbindb._tagoku")
                    live_dev = int((cur.fetchone() or {})["c"] or 0)
                    counter_count = 0
                    try:
                        cur.execute("SELECT COUNT(*) AS c FROM kbindb._servercounters")
                        counter_count = int((cur.fetchone() or {})["c"] or 0)
                    except Exception:
                        pass
                    report["canli_veriler"] = {
                        "toplam_tag": live_tag,
                        "cihaz_sayisi": live_dev,
                        "server_counter": counter_count,
                    }
                    tag_link = tag_clone = 0
                    try:
                        cur.execute("SELECT COUNT(*) AS c FROM kbindb.tag_link")
                        tag_link = int((cur.fetchone() or {})["c"] or 0)
                    except Exception:
                        pass
                    try:
                        cur.execute("SELECT COUNT(*) AS c FROM kbindb.tag_clone")
                        tag_clone = int((cur.fetchone() or {})["c"] or 0)
                    except Exception:
                        pass
                    report["tag_baglantilari"] = {"tag_link": tag_link, "tag_clone": tag_clone}
                    try:
                        cur.execute(f"SELECT COUNT(*) AS c FROM {ex_db}.channeldevice")
                        cd_total = int((cur.fetchone() or {})["c"] or 0)
                        cur.execute(
                            f"SELECT COUNT(*) AS c FROM {ex_db}.channeldevice WHERE statusCode IN ({ac})"
                        )
                        cd_active = int((cur.fetchone() or {})["c"] or 0)
                        cur.execute(
                            f"""
                            SELECT cd.statusCode, cds.statusDefinition AS durum, COUNT(*) AS sayi
                            FROM {ex_db}.channeldevice cd
                            LEFT JOIN {ex_db}.channeldevicestatus cds ON cd.statusCode = cds.statusCode
                            GROUP BY cd.statusCode, cds.statusDefinition
                            ORDER BY sayi DESC
                            """
                        )
                        cd_by_status = list(cur.fetchall())
                        cur.execute(
                            f"""
                            SELECT dt.typeName AS device_type, COUNT(*) AS sayi
                            FROM {ex_db}.channeldevice cd
                            LEFT JOIN {ex_db}.devicetype dt ON cd.deviceTypeId = dt.id
                            WHERE cd.statusCode IN ({ac})
                            GROUP BY dt.typeName
                            ORDER BY sayi DESC
                            LIMIT 15
                            """
                        )
                        cd_by_type = list(cur.fetchall())
                        report["channel_devices"] = {
                            "toplam": cd_total,
                            "calisan": cd_active,
                            "duruma_gore": cd_by_status,
                            "calisan_device_tipine_gore": cd_by_type,
                        }
                    except Exception as e:
                        report["channel_devices"] = {"hata": str(e)}
                    try:
                        cur.execute(
                            """
                            SELECT d.id, d.name, d.status, d.driver_state, d.is_enabled,
                                   d.connectedDeviceCount, d.DbTagCount, d.KEPActiveTagCount,
                                   d.uptime, d.lastStatusUpdate
                            FROM dbdataexchanger.driver d ORDER BY d.id
                            """
                        )
                        report["driverlar"] = list(cur.fetchall())
                    except Exception:
                        report["driverlar"] = []
                    try:
                        cur.execute(
                            """
                            SELECT si.computer_name, si.service_name, si.current_status,
                                   si.last_heartbeat, si.uptime_seconds
                            FROM dbdataexchanger.service_instances si ORDER BY si.id
                            """
                        )
                        report["servis_instancelari"] = list(cur.fetchall())
                    except Exception:
                        report["servis_instancelari"] = []
            return report

        @mcp.tool(name=tool)
        def get_scada_summary() -> str:
            """SCADA sistem özeti: node dağılımı, kullanıcılar, cihaz durumu, alarm ve log istatistikleri."""
            return guard(tool, _get_scada_summary_impl)()

        tool = prefixed_name(prefix, "get_node_distribution")

        def _get_node_distribution_impl() -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT nState, COUNT(*) AS sayi FROM kbindb.node GROUP BY nState ORDER BY nState
                        """
                    )
                    by_state = list(cur.fetchall())
                    cur.execute(
                        """
                        SELECT nType, COUNT(*) AS sayi FROM kbindb.node WHERE nState >= 0
                        GROUP BY nType ORDER BY sayi DESC
                        """
                    )
                    by_type = list(cur.fetchall())
                    cur.execute(
                        """
                        SELECT COALESCE(pt.name, 'Tanımsız') AS urun_tipi, pt.category, COUNT(n.id) AS sayi
                        FROM kbindb.node n
                        LEFT JOIN kbindb.node_product_type pt ON n.nView = pt.nView
                        WHERE n.nState >= 0
                        GROUP BY pt.name, pt.category
                        ORDER BY sayi DESC
                        """
                    )
                    by_product = list(cur.fetchall())
                    cur.execute(
                        """
                        SELECT SUBSTRING_INDEX(nPath, '/', 2) AS bolge, COUNT(*) AS sayi
                        FROM kbindb.node
                        WHERE nState >= 0 AND nPath IS NOT NULL AND nPath != ''
                        GROUP BY bolge
                        ORDER BY sayi DESC
                        LIMIT 20
                        """
                    )
                    by_path = list(cur.fetchall())
                    cur.execute("SELECT COUNT(DISTINCT nid) AS c FROM kbindb.alarmparameters")
                    with_alarm = int((cur.fetchone() or {})["c"] or 0)
                    cur.execute("SELECT COUNT(DISTINCT nid) AS c FROM kbindb.logparameters WHERE state = 1")
                    with_log = int((cur.fetchone() or {})["c"] or 0)
                    cur.execute("SELECT COUNT(DISTINCT devId) AS c FROM kbindb._tagoku")
                    with_live = int((cur.fetchone() or {})["c"] or 0)
                    with_tag_link = 0
                    try:
                        cur.execute(
                            "SELECT COUNT(DISTINCT srcDid) + COUNT(DISTINCT destDid) AS c FROM kbindb.tag_link"
                        )
                        with_tag_link = int((cur.fetchone() or {})["c"] or 0)
                    except Exception:
                        pass
            return {
                "duruma_gore": by_state,
                "tipe_gore": by_type,
                "urun_tipine_gore": by_product,
                "bolgeye_gore": by_path,
                "alarm_tanimli_node_sayisi": with_alarm,
                "log_tanimli_node_sayisi": with_log,
                "canli_tag_olan_node_sayisi": with_live,
                "tag_link_olan_node_sayisi": with_tag_link,
            }

        @mcp.tool(name=tool)
        def get_node_distribution() -> str:
            """Node dağılımı: nType ve nView bazında gruplandırma."""
            return guard(tool, _get_node_distribution_impl)()

        tool = prefixed_name(prefix, "get_channel_device_statistics")

        def _get_channel_device_statistics_impl() -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            ac = ",".join(str(x) for x in _ACTIVE_STATUS_CODES)
            fc = ",".join(str(x) for x in _FAILED_CODES)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    ex_db = _exchanger_db(cur)
                    cur.execute(f"SELECT COUNT(*) AS c FROM {ex_db}.channeldevice")
                    total = int((cur.fetchone() or {})["c"] or 0)
                    cur.execute(
                        f"SELECT COUNT(*) AS c FROM {ex_db}.channeldevice WHERE statusCode IN ({ac})"
                    )
                    active = int((cur.fetchone() or {})["c"] or 0)
                    cur.execute(
                        f"""
                        SELECT cd.statusCode, COALESCE(cds.statusDefinition, CONCAT('Kod:',cd.statusCode)) AS durum,
                               COUNT(*) AS sayi,
                               CASE WHEN cd.statusCode IN ({ac}) THEN 'Çalışıyor' ELSE 'Çalışmıyor' END AS aktiflik
                        FROM {ex_db}.channeldevice cd
                        LEFT JOIN {ex_db}.channeldevicestatus cds ON cd.statusCode = cds.statusCode
                        GROUP BY cd.statusCode, cds.statusDefinition
                        ORDER BY sayi DESC
                        """
                    )
                    by_status = list(cur.fetchall())
                    cur.execute(
                        f"""
                        SELECT dt.id AS device_type_id, dt.typeName AS device_type, ct.name AS channel_type,
                               COUNT(*) AS toplam,
                               SUM(CASE WHEN cd.statusCode IN ({ac}) THEN 1 ELSE 0 END) AS calisan,
                               SUM(CASE WHEN cd.statusCode NOT IN ({ac}) THEN 1 ELSE 0 END) AS calismayan
                        FROM {ex_db}.channeldevice cd
                        LEFT JOIN {ex_db}.devicetype dt ON cd.deviceTypeId = dt.id
                        LEFT JOIN {ex_db}.channeltypes ct ON dt.ChannelTypeId = ct.id
                        GROUP BY dt.id, dt.typeName, ct.name
                        ORDER BY toplam DESC
                        LIMIT 20
                        """
                    )
                    by_dt = list(cur.fetchall())
                    cur.execute(
                        f"""
                        SELECT clientId, COUNT(*) AS sayi FROM {ex_db}.channeldevice
                        WHERE clientId IS NOT NULL
                        GROUP BY clientId ORDER BY sayi DESC
                        """
                    )
                    by_client = list(cur.fetchall())
                    driver_dist: list[Any] = []
                    if ex_db == "dbdataexchanger":
                        cur.execute(
                            f"""
                            SELECT cd.driverId, d.name AS driver_adi,
                                   COUNT(*) AS toplam,
                                   SUM(CASE WHEN cd.statusCode IN ({ac}) THEN 1 ELSE 0 END) AS calisan
                            FROM dbdataexchanger.channeldevice cd
                            LEFT JOIN dbdataexchanger.driver d ON cd.driverId = d.id
                            WHERE cd.driverId IS NOT NULL
                            GROUP BY cd.driverId, d.name
                            ORDER BY toplam DESC
                            """
                        )
                        driver_dist = list(cur.fetchall())
                    cur.execute(
                        f"""
                        SELECT cd.statusCode, cds.statusDefinition AS durum, COUNT(*) AS sayi
                        FROM {ex_db}.channeldevice cd
                        LEFT JOIN {ex_db}.channeldevicestatus cds ON cd.statusCode = cds.statusCode
                        WHERE cd.statusCode IN ({fc})
                        GROUP BY cd.statusCode, cds.statusDefinition
                        ORDER BY sayi DESC
                        """
                    )
                    failed = list(cur.fetchall())
            return {
                "aktif_db": ex_db,
                "toplam": total,
                "calisan": active,
                "calismayan": total - active,
                "duruma_gore": by_status,
                "device_tipine_gore": by_dt,
                "client_bazinda": by_client,
                "driver_bazinda": driver_dist,
                "basarisiz_islemler": failed,
            }

        @mcp.tool(name=tool)
        def get_channel_device_statistics() -> str:
            """Kepware cihaz istatistikleri: aktif, başarısız, toplam sayılar."""
            return guard(tool, _get_channel_device_statistics_impl)()

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
                    # Aktif alarmların son güncelleme zamanına göre (olay günlüğü yoksa en iyi yaklaşım)
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
                    # Tanım bazlı: node başına kaç alarm *tanımı* var (eski alan adı uyumluluğu için korunur)
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
                    # Bugün güncellenen aktif alarmlar — node sıralaması (işe yarar özet)
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
                    # Son 24 saatte güncellenen aktif alarmlar — node sıralaması
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
                    "toplam_alarm_parametresi": "SCADA’da tanımlı alarm satırı (eşik/koşul). «Bugün kaç alarm oldu» değil.",
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

        # --- AuthTools ---
        tool = prefixed_name(prefix, "get_user_permissions")

        def _get_user_permissions_impl(userId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            uid = int(userId)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, uFirstName, uLastName, uName, gid FROM users WHERE id = %s", (uid,)
                    )
                    user = cur.fetchone()
                    if not user:
                        return {"error": f"Kullanıcı ID {uid} bulunamadı."}
                    cur.execute(
                        """
                        SELECT ua.nid, n.nName, n.nType, n.nPath, ua.yVal, ua.time
                        FROM user_auths ua
                        LEFT JOIN node n ON ua.nid = n.id
                        WHERE ua.uid = %s
                        ORDER BY n.nName
                        """,
                        (uid,),
                    )
                    direct = list(cur.fetchall())
                    cur.execute(
                        """
                        SELECT ga.nid, n.nName, n.nType, n.nPath, ga.yVal, g.gName AS grup_adi, ga.time
                        FROM user_group_auths ga
                        JOIN user_groups g ON ga.gid = g.id
                        LEFT JOIN node n ON ga.nid = n.id
                        WHERE ga.gid = %s
                        ORDER BY n.nName
                        """,
                        (user["gid"],),
                    )
                    group_perms = list(cur.fetchall())
                    cur.execute(
                        """
                        SELECT unr.nid, n.nName, n.nType, unr.typeid, unr.time
                        FROM user_node_rel unr
                        LEFT JOIN node n ON unr.nid = n.id
                        WHERE unr.uid = %s
                        ORDER BY unr.time DESC
                        LIMIT 100
                        """,
                        (uid,),
                    )
                    rel = list(cur.fetchall())
            return {
                "user": user,
                "bireysel_yetkiler": direct,
                "bireysel_yetki_sayisi": len(direct),
                "grup_yetkileri": group_perms,
                "grup_yetki_sayisi": len(group_perms),
                "node_iliskileri": rel,
                "node_iliski_sayisi": len(rel),
            }

        @mcp.tool(name=tool)
        def get_user_permissions(userId: int) -> str:
            """Kullanıcının yetki listesi (kbindb.permissions)."""
            return guard(tool, _get_user_permissions_impl)(userId)

        tool = prefixed_name(prefix, "get_node_permissions")

        def _get_node_permissions_impl(nodeId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            nid = int(nodeId)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, nName, nType, nPath FROM node WHERE id = %s", (nid,))
                    node = cur.fetchone()
                    if not node:
                        return {"error": f"Node ID {nid} bulunamadı."}
                    cur.execute(
                        """
                        SELECT ua.uid, u.uFirstName, u.uLastName, u.uName, ua.yVal, ua.time,
                               'bireysel' AS yetki_tipi
                        FROM user_auths ua
                        JOIN users u ON ua.uid = u.id
                        WHERE ua.nid = %s
                        ORDER BY u.uFirstName
                        """,
                        (nid,),
                    )
                    direct = list(cur.fetchall())
                    cur.execute(
                        """
                        SELECT ga.gid, g.gName, ga.yVal, ga.time,
                               'grup' AS yetki_tipi
                        FROM user_group_auths ga
                        JOIN user_groups g ON ga.gid = g.id
                        WHERE ga.nid = %s
                        ORDER BY g.gName
                        """,
                        (nid,),
                    )
                    groups = list(cur.fetchall())
            out = dict(node)
            out["bireysel_yetkili_kullanicilar"] = direct
            out["grup_yetkileri"] = groups
            out["toplam_bireysel"] = len(direct)
            out["toplam_grup"] = len(groups)
            return out

        @mcp.tool(name=tool)
        def get_node_permissions(nodeId: int) -> str:
            """Noktaya erişim izinleri."""
            return guard(tool, _get_node_permissions_impl)(nodeId)

        # --- TagTools ---
        tool = prefixed_name(prefix, "list_tag_links")

        def _list_tag_links_impl(deviceId: int = 0, limit: int = 100) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 500)
            where = ""
            params: list[Any] = []
            if int(deviceId) > 0:
                where = "WHERE tl.srcDid = %s OR tl.destDid = %s"
                params = [int(deviceId), int(deviceId)]
            sql = f"""
                SELECT tl.pId, tl.srcDid, tl.srcTagPath,
                       tl.destDid, tl.destTagPath,
                       tl.upInterval, tl.type,
                       CASE tl.type WHEN 0 THEN 'Remote' WHEN 1 THEN 'Local' END AS link_tipi,
                       sn.nName AS kaynak_node, dn.nName AS hedef_node,
                       tl.time, tl.createdTime
                FROM tag_link tl
                LEFT JOIN node sn ON tl.srcDid = sn.id
                LEFT JOIN node dn ON tl.destDid = dn.id
                {where}
                ORDER BY tl.pId DESC
                LIMIT %s
            """
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (*params, limit))
                    links = list(cur.fetchall())
            return {"count": len(links), "tag_links": links}

        @mcp.tool(name=tool)
        def list_tag_links(deviceId: int = 0, limit: int = 100) -> str:
            """Tag link tanımları (kaynak→hedef)."""
            return guard(tool, _list_tag_links_impl)(deviceId, limit)

        tool = prefixed_name(prefix, "list_tag_clones")

        def _list_tag_clones_impl(limit: int = 100) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 500)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT tc.id, tc.src_nid, sn.nName AS kaynak_node,
                               tc.dest_nid, dn.nName AS hedef_node,
                               tc.type, tct.name AS tip_adi,
                               CASE tc.state WHEN 0 THEN 'Pasif' WHEN 1 THEN 'Aktif' END AS durum,
                               tc.createdTime
                        FROM tag_clone tc
                        LEFT JOIN node sn ON tc.src_nid = sn.id
                        LEFT JOIN node dn ON tc.dest_nid = dn.id
                        LEFT JOIN tag_clone_type tct ON tc.type = tct.id
                        ORDER BY tc.id DESC
                        LIMIT %s
                        """,
                        (limit,),
                    )
                    clones = list(cur.fetchall())
                    for c in clones:
                        cur.execute(
                            "SELECT src_tag, dest_tag FROM tag_clone_tags WHERE cid = %s ORDER BY id",
                            (c["id"],),
                        )
                        c["tags"] = list(cur.fetchall())
            return {"count": len(clones), "tag_clones": clones}

        @mcp.tool(name=tool)
        def list_tag_clones(limit: int = 100) -> str:
            """Tag clone tanımları."""
            return guard(tool, _list_tag_clones_impl)(limit)

        # --- UserGroupTools ---
        tool = prefixed_name(prefix, "list_user_groups")

        def _list_user_groups_impl() -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT g.id, g.gName, g.gSmsKredi, g.nid,
                               CASE WHEN g.gEnable = 1 THEN 'Aktif' ELSE 'Pasif' END AS durum,
                               n.nName AS bagli_node,
                               COUNT(u.id) AS uye_sayisi,
                               SUM(CASE WHEN u.uEnable = 1 THEN 1 ELSE 0 END) AS aktif_uye,
                               g.createTime
                        FROM user_groups g
                        LEFT JOIN users u ON u.gid = g.id
                        LEFT JOIN node n ON g.nid = n.id
                        GROUP BY g.id
                        ORDER BY uye_sayisi DESC
                        """
                    )
                    groups = list(cur.fetchall())
            return {"count": len(groups), "groups": groups}

        @mcp.tool(name=tool)
        def list_user_groups() -> str:
            """Kullanıcı grupları listesi."""
            return guard(tool, _list_user_groups_impl)()

        tool = prefixed_name(prefix, "get_group_members")

        def _get_group_members_impl(groupId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            gid = int(groupId)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT g.id, g.gName, g.gSmsKredi, g.nid,
                               CASE WHEN g.gEnable = 1 THEN 'Aktif' ELSE 'Pasif' END AS durum,
                               n.nName AS bagli_node, g.createTime
                        FROM user_groups g
                        LEFT JOIN node n ON g.nid = n.id
                        WHERE g.id = %s
                        """,
                        (gid,),
                    )
                    group = cur.fetchone()
                    if not group:
                        return {"error": f"Grup ID {gid} bulunamadı."}
                    cur.execute(
                        """
                        SELECT id, uFirstName, uLastName, uName, uTel, uMail, uTitle, com_info,
                               CASE WHEN uEnable = 1 THEN 'Aktif' ELSE 'Pasif' END AS durum,
                               lastLogin
                        FROM users WHERE gid = %s ORDER BY uFirstName
                        """,
                        (gid,),
                    )
                    members = list(cur.fetchall())
            out = dict(group)
            out["uye_sayisi"] = len(members)
            out["uyeler"] = members
            return out

        @mcp.tool(name=tool)
        def get_group_members(groupId: int) -> str:
            """Grup üyeleri listesi."""
            return guard(tool, _get_group_members_impl)(groupId)

        # --- UserTools ---
        tool = prefixed_name(prefix, "list_users")

        def _list_users_impl(
            status: str = "active",
            company: str = "",
            city: str = "",
            limit: int = 25,
            offset: int = 0,
        ) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 100)
            offset = max(int(offset), 0)
            where: list[str] = []
            params: list[Any] = []
            if status == "active":
                where.append("u.uEnable = 1")
            elif status == "inactive":
                where.append("u.uEnable = 0")
            if (company or "").strip():
                where.append("u.com_info LIKE %s")
                params.append(f"%{company.strip()}%")
            if (city or "").strip():
                where.append("u.uCity LIKE %s")
                params.append(f"%{city.strip()}%")
            wh = ("WHERE " + " AND ".join(where)) if where else ""
            sql = f"""
                SELECT u.id, u.uFirstName, u.uLastName, u.uName, u.uTel, u.uMail,
                       u.uTitle, u.com_info, u.uCity, u.uLevel, u.uType, u.gid,
                       g.gName AS grup_adi,
                       CASE WHEN u.uEnable = 1 THEN 'Aktif' ELSE 'Pasif' END AS durum,
                       u.lastLogin, u.createdTime
                FROM users u
                LEFT JOIN user_groups g ON u.gid = g.id
                {wh}
                ORDER BY u.id DESC
                LIMIT %s OFFSET %s
            """
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (*params, limit, offset))
                    users = list(cur.fetchall())
                    cur.execute(f"SELECT COUNT(*) AS total FROM users u {wh}", params)
                    total = int((cur.fetchone() or {})["total"] or 0)
            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "count": len(users),
                "users": users,
            }

        @mcp.tool(name=tool)
        def list_users(
            status: str = "active",
            company: str = "",
            city: str = "",
            limit: int = 25,
            offset: int = 0,
        ) -> str:
            """Kullanıcı listesi (sayfalama destekli)."""
            return guard(tool, _list_users_impl)(status, company, city, limit, offset)

        tool = prefixed_name(prefix, "get_user")

        def _get_user_impl(userId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            uid = int(userId)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT u.id, u.gid, u.uFirstName, u.uLastName, u.uName, u.uTel, u.uMail,
                               u.uTitle, u.com_info, u.uCity, u.uLevel, u.uType, u.com_Id,
                               g.gName AS grup_adi,
                               CASE WHEN u.uEnable = 1 THEN 'Aktif' ELSE 'Pasif' END AS durum,
                               CASE WHEN u.uGender = 1 THEN 'Erkek' ELSE 'Kadın' END AS cinsiyet,
                               u.lastLogin, u.createdTime, u.bday, u.smsType, u.confAgreement, u.alwaysOn
                        FROM users u
                        LEFT JOIN user_groups g ON u.gid = g.id
                        WHERE u.id = %s
                        """,
                        (uid,),
                    )
                    user = cur.fetchone()
                    if not user:
                        return {"error": f"ID {uid} olan kullanıcı bulunamadı."}
                    cur.execute(
                        """
                        SELECT ua.nid, n.nName, n.nType, ua.yVal
                        FROM user_auths ua LEFT JOIN node n ON ua.nid = n.id
                        WHERE ua.uid = %s
                        """,
                        (uid,),
                    )
                    user = dict(user)
                    user["yetkiler"] = list(cur.fetchall())
                    cur.execute("SELECT COUNT(*) AS c FROM user_alarm WHERE uid = %s", (uid,))
                    user["alarm_abone_sayisi"] = int((cur.fetchone() or {})["c"] or 0)
            return user

        @mcp.tool(name=tool)
        def get_user(userId: int) -> str:
            """Tek kullanıcı detayı."""
            return guard(tool, _get_user_impl)(userId)

        tool = prefixed_name(prefix, "search_users")

        def _search_users_impl(query: str, limit: int = 20) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            q = (query or "").strip()
            if len(q) < 2:
                return {"error": "Arama terimi en az 2 karakter olmalıdır."}
            limit = min(max(int(limit), 1), 50)
            like = f"%{q}%"
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT u.id, u.uFirstName, u.uLastName, u.uName, u.uTel, u.uMail,
                               u.uTitle, u.com_info, u.uCity, g.gName AS grup_adi,
                               CASE WHEN u.uEnable = 1 THEN 'Aktif' ELSE 'Pasif' END AS durum,
                               u.lastLogin
                        FROM users u
                        LEFT JOIN user_groups g ON u.gid = g.id
                        WHERE u.uFirstName LIKE %s
                           OR u.uLastName LIKE %s
                           OR u.uName LIKE %s
                           OR u.uTel LIKE %s
                           OR u.uMail LIKE %s
                           OR u.uTitle LIKE %s
                        ORDER BY u.lastLogin DESC
                        LIMIT %s
                        """,
                        (like, like, like, like, like, like, limit),
                    )
                    results = list(cur.fetchall())
            return {"query": q, "count": len(results), "results": results}

        @mcp.tool(name=tool)
        def search_users(query: str, limit: int = 20) -> str:
            """Kullanıcı arama (isim, email)."""
            return guard(tool, _search_users_impl)(query, limit)

        tool = prefixed_name(prefix, "get_user_stats")

        def _get_user_stats_impl() -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT COUNT(*) AS toplam,
                               SUM(CASE WHEN uEnable=1 THEN 1 ELSE 0 END) AS aktif,
                               SUM(CASE WHEN uEnable=0 THEN 1 ELSE 0 END) AS pasif,
                               COUNT(DISTINCT com_info) AS sirket_sayisi,
                               COUNT(DISTINCT gid) AS grup_sayisi
                        FROM users
                        """
                    )
                    general = cur.fetchone()
                    cur.execute(
                        """
                        SELECT com_info AS sirket, COUNT(*) AS sayi
                        FROM users WHERE uEnable=1 AND com_info IS NOT NULL AND com_info != ''
                        GROUP BY com_info ORDER BY sayi DESC LIMIT 15
                        """
                    )
                    by_company = list(cur.fetchall())
                    cur.execute(
                        """
                        SELECT g.gName AS grup, COUNT(*) AS sayi
                        FROM users u JOIN user_groups g ON u.gid = g.id
                        WHERE u.uEnable=1
                        GROUP BY u.gid, g.gName ORDER BY sayi DESC LIMIT 15
                        """
                    )
                    by_group = list(cur.fetchall())
                    cur.execute(
                        "SELECT COUNT(*) AS c FROM users WHERE lastLogin >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
                    )
                    r7 = int((cur.fetchone() or {})["c"] or 0)
                    cur.execute(
                        "SELECT COUNT(*) AS c FROM users WHERE lastLogin >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
                    )
                    r30 = int((cur.fetchone() or {})["c"] or 0)
            return {
                "genel": general,
                "son_7_gun_giris": r7,
                "son_30_gun_giris": r30,
                "sirket_dagilimi": by_company,
                "grup_dagilimi": by_group,
            }

        @mcp.tool(name=tool)
        def get_user_stats() -> str:
            """Kullanıcı istatistikleri."""
            return guard(tool, _get_user_stats_impl)()

        # --- LogTools ---
        tool = prefixed_name(prefix, "list_log_params")

        def _list_log_params_impl(nodeId: int = 0, state: int = 1, limit: int = 100, offset: int = 0) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 500)
            offset = max(int(offset), 0)
            where: list[str] = []
            params: list[Any] = []
            if int(nodeId) > 0:
                where.append("lp.nid = %s")
                params.append(int(nodeId))
            if int(state) != -999:
                where.append("lp.state = %s")
                params.append(int(state))
            wh = ("WHERE " + " AND ".join(where)) if where else ""
            sql = f"""
                SELECT lp.id, lp.nid, n.nName AS node_adi, lp.tagPath,
                       lp.logInterval, lp.rangeMin, lp.rangeMax,
                       lp.state, lp.description, lp.time, lp.createdTime
                FROM logparameters lp
                LEFT JOIN node n ON lp.nid = n.id
                {wh}
                ORDER BY lp.id DESC
                LIMIT %s OFFSET %s
            """
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (*params, limit, offset))
                    logs = list(cur.fetchall())
                    cur.execute(f"SELECT COUNT(*) AS total FROM logparameters lp {wh}", params)
                    total = int((cur.fetchone() or {})["total"] or 0)
            return {"total": total, "count": len(logs), "log_params": logs}

        @mcp.tool(name=tool)
        def list_log_params(nodeId: int = 0, state: int = 1, limit: int = 100, offset: int = 0) -> str:
            """Log parametreleri listesi (sayfalama destekli)."""
            return guard(tool, _list_log_params_impl)(nodeId, state, limit, offset)

        # --- check_exchanger_status (DataExchangerTools) ---
        tool = prefixed_name(prefix, "check_exchanger_status")

        def _check_exchanger_status_impl() -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            ac = ",".join(str(x) for x in _ACTIVE_STATUS_CODES)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    info: dict[str, Any] = {
                        "aktif_db": None,
                        "dbdataexchanger": {"mevcut": False, "son_guncelleme": None, "client_sayisi": 0},
                        "dbkepware": {"mevcut": False, "son_guncelleme": None, "client_sayisi": 0},
                    }
                    try:
                        cur.execute("SELECT MAX(UpdateTime) AS son, COUNT(*) AS sayi FROM dbdataexchanger.service")
                        row = cur.fetchone() or {}
                        info["dbdataexchanger"]["mevcut"] = True
                        info["dbdataexchanger"]["son_guncelleme"] = row.get("son")
                        info["dbdataexchanger"]["client_sayisi"] = int(row.get("sayi") or 0)
                    except Exception:
                        pass
                    try:
                        cur.execute("SELECT MAX(UpdateTime) AS son, COUNT(*) AS sayi FROM dbkepware.service")
                        row = cur.fetchone() or {}
                        info["dbkepware"]["mevcut"] = True
                        info["dbkepware"]["son_guncelleme"] = row.get("son")
                        info["dbkepware"]["client_sayisi"] = int(row.get("sayi") or 0)
                    except Exception:
                        pass
                    new_t = info["dbdataexchanger"]["son_guncelleme"]
                    old_t = info["dbkepware"]["son_guncelleme"]
                    if new_t and old_t:
                        info["aktif_db"] = _exchanger_db(cur)
                    elif new_t:
                        info["aktif_db"] = "dbdataexchanger"
                    elif old_t:
                        info["aktif_db"] = "dbkepware"
                    active_db = info["aktif_db"]
                    if active_db:
                        try:
                            cur.execute(
                                """
                                SELECT id, computer_name, service_name, current_status, last_heartbeat, uptime_seconds
                                FROM dbdataexchanger.service_instances ORDER BY id
                                """
                            )
                            info["service_instances"] = list(cur.fetchall())
                        except Exception:
                            info["service_instances"] = []
                        try:
                            cur.execute(
                                f"""
                                SELECT COUNT(*) AS toplam,
                                       SUM(CASE WHEN statusCode IN ({ac}) THEN 1 ELSE 0 END) AS calisan
                                FROM {active_db}.channeldevice
                                """
                            )
                            d = cur.fetchone() or {}
                            info["cihaz_toplam"] = int(d.get("toplam") or 0)
                            info["cihaz_calisan"] = int(d.get("calisan") or 0)
                        except Exception:
                            pass
            return info

        @mcp.tool(name=tool)
        def check_exchanger_status() -> str:
            """DataExchanger/Kepware servis durumu."""
            return guard(tool, _check_exchanger_status_impl)()

    def manifest_groups(self, *, prefix: str) -> list[dict]:
        p = prefix
        return [
            {
                "id": "dashboard",
                "title_tr": "Dashboard / özet",
                "tools": [
                    p + "get_scada_summary",
                    p + "get_node_distribution",
                    p + "get_channel_device_statistics",
                    p + "get_alarm_statistics",
                ],
            },
            {
                "id": "admin_users",
                "title_tr": "Kullanıcı / yetki",
                "tools": [
                    p + "get_user_permissions",
                    p + "get_node_permissions",
                    p + "list_user_groups",
                    p + "get_group_members",
                    p + "list_users",
                    p + "get_user",
                    p + "search_users",
                    p + "get_user_stats",
                ],
            },
            {
                "id": "tags_meta",
                "title_tr": "Tag link / clone",
                "tools": [p + "list_tag_links", p + "list_tag_clones"],
            },
            {
                "id": "logs",
                "title_tr": "Log parametreleri",
                "tools": [p + "list_log_params"],
            },
            {
                "id": "kepware",
                "title_tr": "Kepware / veri değişim",
                "tools": [p + "check_exchanger_status"],
            },
        ]
