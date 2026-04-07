from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .. import db as dbmod
from ..export_files import (
    export_active_alarms_impl,
    export_custom_data_impl,
    export_log_data_impl,
    generate_node_report_impl,
    generate_scada_report_impl,
)
from ..tools.core import guard, prefixed_name
from ..chart_contract import koru_mind_coklu_log_chart_extras, koru_mind_log_timeseries_extras
from ..chart_hints import GRAFIK_SUNUMU_MODEL_TALIMAT_TR
from ..compare_log_metrics import compare_log_metrics_impl
from ..log_series_align import aligned_multi_log_series
from ..dma_demand import (
    analyze_dma_seasonal_demand_impl,
    analyze_seasonal_level_profile_impl,
    list_dma_station_nodes_impl,
)
from ..log_value_cleanup import fetch_log_value_bounds, outlier_filtre_ozet_tr
from ..trend_analysis import analyze_log_trend_impl
from ..types import InstanceConfig
from .scada_extended import _ACTIVE_STATUS_CODES, _exchanger_db, _extract_connection_params
from ..product_docs import instance_products_dir, list_product_doc_keys, load_product_doc, search_text

_MAX_CHART_POINTS = 100


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _products_dir(cfg: InstanceConfig | None = None) -> Path:
    # Prefer per-instance docs (generated from PDFs) if present.
    if cfg is not None:
        d = instance_products_dir(cfg.base_dir)
        if d.is_dir():
            return d
    return _project_root() / "eskiprojeornekicin" / "data" / "products"


def _load_product_json(name: str, cfg: InstanceConfig | None = None) -> dict[str, Any] | None:
    p = _products_dir(cfg) / f"{name}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _load_all_products(cfg: InstanceConfig | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    d = _products_dir(cfg)
    if not d.is_dir():
        return out
    for f in d.glob("*.json"):
        try:
            out[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
    return out


def _search_in_dict(data: Any, keyword: str, prefix: str = "") -> list[dict[str, Any]]:
    kw = keyword.lower()
    results: list[dict[str, Any]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            results.extend(_search_in_dict(value, keyword, path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            results.extend(_search_in_dict(item, keyword, f"{prefix}[{i}]"))
    elif isinstance(data, str) and (keyword in data or kw in data.lower()):
        results.append({"yol": prefix, "değer": data})
    return results


def _log_table_exists(cur: Any, node_id: int) -> bool:
    t = f"log_{int(node_id)}"
    cur.execute(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='noktalog' AND TABLE_NAME=%s",
        (t,),
    )
    return cur.fetchone() is not None


def _fetch_sampled_log(
    cur: Any, node_id: int, log_param_id: int, start: str, end: str, max_pts: int
) -> dict[str, Any]:
    tname = f"log_{int(node_id)}"
    full = f"noktalog.`{tname}`"
    where = ["l.logPId = %s"]
    params: list[Any] = [int(log_param_id)]
    if (start or "").strip():
        where.append("l.logTime >= %s")
        params.append(start.strip())
    if (end or "").strip():
        where.append("l.logTime <= %s")
        params.append(end.strip())
    wh0 = "WHERE " + " AND ".join(where)
    vb = fetch_log_value_bounds(cur, f"SELECT tagValue FROM {full} l {wh0}", tuple(params))
    if vb:
        lo, hi = vb
        where.extend(["l.tagValue >= %s", "l.tagValue <= %s"])
        params.extend([lo, hi])
    wh = "WHERE " + " AND ".join(where)
    cur.execute(f"SELECT COUNT(*) AS c, MIN(logTime) AS mn, MAX(logTime) AS mx FROM {full} l {wh}", params)
    m = cur.fetchone() or {}
    total = int(m.get("c") or 0)
    if total == 0:
        return {
            "data": [],
            "total": 0,
            "sampling": "yok",
            "log_deger_temizlik_tr": outlier_filtre_ozet_tr(),
        }
    if total <= max_pts:
        cur.execute(
            f"SELECT tagValue, logTime FROM {full} l {wh} ORDER BY logTime ASC",
            params,
        )
        return {
            "data": list(cur.fetchall()),
            "total": total,
            "sampling": "yok",
            "log_deger_temizlik_tr": outlier_filtre_ozet_tr(),
        }
    mn = m.get("mn")
    mx = m.get("mx")
    try:
        min_ts = int(datetime.fromisoformat(str(mn).replace("Z", "+00:00")).timestamp())
        max_ts = int(datetime.fromisoformat(str(mx).replace("Z", "+00:00")).timestamp())
    except Exception:
        return {
            "error": "logTime parse",
            "data": [],
            "total": total,
            "sampling": "yok",
            "log_deger_temizlik_tr": outlier_filtre_ozet_tr(),
        }
    bucket_sec = max(1, (max_ts - min_ts) // max_pts)
    cur.execute(
        f"""
        SELECT ROUND(AVG(l.tagValue),4) AS tagValue,
               ROUND(MIN(l.tagValue),4) AS bucket_min,
               ROUND(MAX(l.tagValue),4) AS bucket_max,
               MIN(l.logTime) AS logTime
        FROM {full} l {wh}
        GROUP BY FLOOR(UNIX_TIMESTAMP(l.logTime) / %s)
        ORDER BY logTime ASC
        """,
        (*params, bucket_sec),
    )
    rows = list(cur.fetchall())
    if bucket_sec < 60:
        lbl = f"{bucket_sec}sn"
    elif bucket_sec < 3600:
        lbl = f"{round(bucket_sec / 60)}dk"
    elif bucket_sec < 86400:
        lbl = f"{round(bucket_sec / 3600, 1)}sa"
    else:
        lbl = f"{round(bucket_sec / 86400, 1)}gün"
    return {
        "data": rows,
        "total": total,
        "sampling": lbl,
        "bucket_seconds": bucket_sec,
        "log_deger_temizlik_tr": outlier_filtre_ozet_tr(),
    }


class ScadaMorePack:
    """Kepware, grafik, node log, ürün JSON; dosya export ve ağır pompa SP — PHP tam sürüm veya ileri Python."""

    id = "scada_more"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix
        ac = ",".join(str(x) for x in _ACTIVE_STATUS_CODES)

        # --- list_channel_devices ---
        tool = prefixed_name(prefix, "list_channel_devices")

        def _list_channel_devices_impl(
            statusCode: int = 0,
            onlyCalisanlar: bool = False,
            deviceTypeId: int = 0,
            driverId: int = 0,
            clientId: int = 0,
            search: str = "",
            limit: int = 50,
            offset: int = 0,
        ) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 200)
            offset = max(int(offset), 0)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    ex_db = _exchanger_db(cur)
                    where: list[str] = []
                    params: list[Any] = []
                    if int(statusCode) > 0:
                        where.append("cd.statusCode = %s")
                        params.append(int(statusCode))
                    elif onlyCalisanlar:
                        where.append(f"cd.statusCode IN ({ac})")
                    if int(deviceTypeId) > 0:
                        where.append("cd.deviceTypeId = %s")
                        params.append(int(deviceTypeId))
                    if int(driverId) > 0:
                        where.append("cd.driverId = %s")
                        params.append(int(driverId))
                    if int(clientId) > 0:
                        where.append("cd.clientId = %s")
                        params.append(int(clientId))
                    if (search or "").strip():
                        where.append("(cd.channelName LIKE %s OR n.nName LIKE %s)")
                        s = f"%{search.strip()}%"
                        params.extend([s, s])
                    wh = ("WHERE " + " AND ".join(where)) if where else ""
                    drv_col = ", cd.driverId" if ex_db == "dbdataexchanger" else ""
                    sql = f"""
                        SELECT cd.id, cd.channelName, cd.deviceTypeId,
                               cd.statusCode, cds.statusDefinition,
                               dt.typeName AS device_type_name,
                               cd.clientId, cd.createTime, cd.updateTime,
                               n.nName AS node_adi, n.nType, n.nState, n.nPath,
                               JSON_UNQUOTE(JSON_EXTRACT(cd.deviceJson, '$."servermain.DEVICE_ID_STRING"')) AS cihaz_ip,
                               JSON_UNQUOTE(JSON_EXTRACT(cd.deviceJson, '$."servermain.MULTIPLE_TYPES_DEVICE_DRIVER"')) AS driver_tipi,
                               JSON_EXTRACT(cd.deviceJson, '$."modbus_ethernet.DEVICE_ETHERNET_PORT_NUMBER"') AS port,
                               JSON_EXTRACT(cd.deviceJson, '$."servermain.DEVICE_CONNECTION_TIMEOUT_SECONDS"') AS timeout_sn
                               {drv_col}
                        FROM {ex_db}.channeldevice cd
                        LEFT JOIN {ex_db}.channeldevicestatus cds ON cd.statusCode = cds.statusCode
                        LEFT JOIN {ex_db}.devicetype dt ON cd.deviceTypeId = dt.id
                        LEFT JOIN kbindb.node n ON cd.id = n.id
                        {wh}
                        ORDER BY cd.id DESC
                        LIMIT %s OFFSET %s
                    """
                    cur.execute(sql, (*params, limit, offset))
                    devices = list(cur.fetchall())
                    cur.execute(
                        f"SELECT COUNT(*) AS total FROM {ex_db}.channeldevice cd LEFT JOIN kbindb.node n ON cd.id = n.id {wh}",
                        params,
                    )
                    total = int((cur.fetchone() or {})["total"] or 0)
            return {"aktif_db": ex_db, "total": total, "count": len(devices), "channel_devices": devices}

        @mcp.tool(name=tool)
        def list_channel_devices(
            statusCode: int = 0,
            onlyCalisanlar: bool = False,
            deviceTypeId: int = 0,
            driverId: int = 0,
            clientId: int = 0,
            search: str = "",
            limit: int = 50,
            offset: int = 0,
        ) -> str:
            """Kepware cihaz listesi (filtreleme destekli). Ürün ailesi dokümanı için get_product_specs."""
            return guard(tool, _list_channel_devices_impl)(
                statusCode, onlyCalisanlar, deviceTypeId, driverId, clientId, search, limit, offset
            )

        tool = prefixed_name(prefix, "get_channel_device_detail")

        def _get_channel_device_detail_impl(deviceId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            did = int(deviceId)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    ex_db = _exchanger_db(cur)
                    cur.execute(
                        f"""
                        SELECT cd.*, cds.statusDefinition,
                               dt.typeName AS device_type_name, dt.ChannelTypeId, dt.description AS device_type_desc,
                               ct.name AS channel_type_name,
                               n.nName AS node_adi, n.nType, n.nState, n.nPath, n.nDev
                        FROM {ex_db}.channeldevice cd
                        LEFT JOIN {ex_db}.channeldevicestatus cds ON cd.statusCode = cds.statusCode
                        LEFT JOIN {ex_db}.devicetype dt ON cd.deviceTypeId = dt.id
                        LEFT JOIN {ex_db}.channeltypes ct ON dt.ChannelTypeId = ct.id
                        LEFT JOIN kbindb.node n ON cd.id = n.id
                        WHERE cd.id = %s
                        """,
                        (did,),
                    )
                    device = cur.fetchone()
                    if not device:
                        return {"error": f"Channel device ID {did} bulunamadı (DB: {ex_db})."}
                    device = dict(device)
                    device["baglanti_parametreleri"] = _extract_connection_params(device)
                    device["calisiyor_mu"] = int(device.get("statusCode") or 0) in _ACTIVE_STATUS_CODES
                    cur.execute(
                        f"SELECT COUNT(*) AS c FROM {ex_db}.devicetypetag WHERE deviceTypeId = %s",
                        (device["deviceTypeId"],),
                    )
                    device["type_tag_sayisi"] = int((cur.fetchone() or {})["c"] or 0)
                    cur.execute(
                        f"SELECT COUNT(*) AS c FROM {ex_db}.deviceindividualtag WHERE channelDeviceId = %s",
                        (did,),
                    )
                    device["individual_tag_sayisi"] = int((cur.fetchone() or {})["c"] or 0)
                    cur.execute("SELECT COUNT(*) AS c FROM kbindb._tagoku WHERE devId = %s", (did,))
                    device["canli_tag_sayisi"] = int((cur.fetchone() or {})["c"] or 0)
                    device["aktif_db"] = ex_db
            return device

        @mcp.tool(name=tool)
        def get_channel_device_detail(deviceId: int) -> str:
            """Kepware cihaz detayı."""
            return guard(tool, _get_channel_device_detail_impl)(deviceId)

        tool = prefixed_name(prefix, "get_device_connection_params")

        def _get_device_connection_params_impl(deviceId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            did = int(deviceId)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    ex_db = _exchanger_db(cur)
                    cur.execute(
                        f"""
                        SELECT cd.id, cd.channelName, cd.statusCode, cds.statusDefinition,
                               cd.deviceJson, cd.channelJson,
                               n.nName AS node_adi, n.nPath
                        FROM {ex_db}.channeldevice cd
                        LEFT JOIN {ex_db}.channeldevicestatus cds ON cd.statusCode = cds.statusCode
                        LEFT JOIN kbindb.node n ON cd.id = n.id
                        WHERE cd.id = %s
                        """,
                        (did,),
                    )
                    device = cur.fetchone()
                    if not device:
                        return {"error": f"Device ID {did} bulunamadı (DB: {ex_db})."}
                    device = dict(device)
                    params = _extract_connection_params(device)
                    cal = int(device.get("statusCode") or 0) in _ACTIVE_STATUS_CODES
            return {
                "device_id": did,
                "node_adi": device.get("node_adi"),
                "node_path": device.get("nPath"),
                "channel_name": device.get("channelName"),
                "status_code": int(device.get("statusCode") or 0),
                "status": device.get("statusDefinition"),
                "calisiyor_mu": cal,
                "baglanti_parametreleri": params,
                "aktif_db": ex_db,
            }

        @mcp.tool(name=tool)
        def get_device_connection_params(deviceId: int) -> str:
            """Cihaz baglanti parametreleri (IP, port, timeout)."""
            return guard(tool, _get_device_connection_params_impl)(deviceId)

        tool = prefixed_name(prefix, "list_channel_types")

        def _list_channel_types_impl() -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    ex_db = _exchanger_db(cur)
                    cur.execute(
                        f"""
                        SELECT ct.id, ct.name, ct.channel, ct.device, ct.createTime,
                               (SELECT COUNT(*) FROM {ex_db}.devicetype dt WHERE dt.ChannelTypeId = ct.id) AS device_type_sayisi
                        FROM {ex_db}.channeltypes ct
                        ORDER BY ct.id
                        """
                    )
                    types = list(cur.fetchall())
            return {"aktif_db": ex_db, "count": len(types), "channel_types": types}

        @mcp.tool(name=tool)
        def list_channel_types() -> str:
            """Kepware channel tipleri."""
            return guard(tool, _list_channel_types_impl)()

        tool = prefixed_name(prefix, "list_device_types")

        def _list_device_types_impl(channelTypeId: int = 0, limit: int = 50, offset: int = 0) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 200)
            offset = max(int(offset), 0)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    ex_db = _exchanger_db(cur)
                    wh = ""
                    params: list[Any] = []
                    if int(channelTypeId) > 0:
                        wh = "WHERE dt.ChannelTypeId = %s"
                        params.append(int(channelTypeId))
                    cur.execute(
                        f"""
                        SELECT dt.id, dt.ChannelTypeId, dt.typeName, dt.description,
                               ct.name AS channel_type_name,
                               dt.createTime, dt.updateTime,
                               (SELECT COUNT(*) FROM {ex_db}.devicetypetag dtt WHERE dtt.deviceTypeId = dt.id) AS tag_sayisi,
                               (SELECT COUNT(*) FROM {ex_db}.channeldevice cd WHERE cd.deviceTypeId = dt.id) AS cihaz_sayisi
                        FROM {ex_db}.devicetype dt
                        LEFT JOIN {ex_db}.channeltypes ct ON dt.ChannelTypeId = ct.id
                        {wh}
                        ORDER BY dt.id DESC
                        LIMIT %s OFFSET %s
                        """,
                        (*params, limit, offset),
                    )
                    types = list(cur.fetchall())
            return {"aktif_db": ex_db, "count": len(types), "device_types": types}

        @mcp.tool(name=tool)
        def list_device_types(channelTypeId: int = 0, limit: int = 50, offset: int = 0) -> str:
            """Kepware device tipleri."""
            return guard(tool, _list_device_types_impl)(channelTypeId, limit, offset)

        tool = prefixed_name(prefix, "get_device_type_tags")

        def _get_device_type_tags_impl(deviceTypeId: int, limit: int = 200, offset: int = 0) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 500)
            offset = max(int(offset), 0)
            dtid = int(deviceTypeId)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    ex_db = _exchanger_db(cur)
                    cur.execute(
                        f"""
                        SELECT dt.id, dt.typeName, dt.description, ct.name AS channel_type_name
                        FROM {ex_db}.devicetype dt
                        LEFT JOIN {ex_db}.channeltypes ct ON dt.ChannelTypeId = ct.id
                        WHERE dt.id = %s
                        """,
                        (dtid,),
                    )
                    device_type = cur.fetchone()
                    if not device_type:
                        return {"error": f"Device type ID {dtid} bulunamadı."}
                    cur.execute(
                        f"""
                        SELECT dtt.id, dtt.deviceTypeId,
                               JSON_UNQUOTE(JSON_EXTRACT(dtt.tagJson, '$."common.ALLTYPES_NAME"')) AS tag_adi,
                               JSON_UNQUOTE(JSON_EXTRACT(dtt.tagJson, '$."servermain.TAG_ADDRESS"')) AS tag_adresi,
                               JSON_EXTRACT(dtt.tagJson, '$."servermain.TAG_DATA_TYPE"') AS veri_tipi,
                               JSON_EXTRACT(dtt.tagJson, '$."servermain.TAG_READ_WRITE_ACCESS"') AS erisim_modu,
                               JSON_EXTRACT(dtt.tagJson, '$."servermain.TAG_SCAN_RATE_MILLISECONDS"') AS okuma_hizi_ms,
                               dtt.tagJson, dtt.createTime, dtt.updateTime
                        FROM {ex_db}.devicetypetag dtt
                        WHERE dtt.deviceTypeId = %s
                        ORDER BY dtt.id
                        LIMIT %s OFFSET %s
                        """,
                        (dtid, limit, offset),
                    )
                    tags = list(cur.fetchall())
                    cur.execute(
                        f"SELECT COUNT(*) AS total FROM {ex_db}.devicetypetag WHERE deviceTypeId = %s",
                        (dtid,),
                    )
                    total = int((cur.fetchone() or {})["total"] or 0)
            return {"aktif_db": ex_db, "device_type": device_type, "total": total, "count": len(tags), "tags": tags}

        @mcp.tool(name=tool)
        def get_device_type_tags(deviceTypeId: int, limit: int = 200, offset: int = 0) -> str:
            """Device type tag tanimlari."""
            return guard(tool, _get_device_type_tags_impl)(deviceTypeId, limit, offset)

        tool = prefixed_name(prefix, "get_device_individual_tags")

        def _get_device_individual_tags_impl(deviceId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            did = int(deviceId)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    ex_db = _exchanger_db(cur)
                    cur.execute(
                        f"""
                        SELECT cd.id, cd.channelName, cd.deviceTypeId, n.nName AS node_adi
                        FROM {ex_db}.channeldevice cd
                        LEFT JOIN kbindb.node n ON cd.id = n.id
                        WHERE cd.id = %s
                        """,
                        (did,),
                    )
                    device = cur.fetchone()
                    if not device:
                        return {"error": f"Device ID {did} bulunamadı (DB: {ex_db})."}
                    cur.execute(
                        f"""
                        SELECT dit.id, dit.channelDeviceId,
                               JSON_UNQUOTE(JSON_EXTRACT(dit.tagJson, '$."common.ALLTYPES_NAME"')) AS tag_adi,
                               JSON_UNQUOTE(JSON_EXTRACT(dit.tagJson, '$."servermain.TAG_ADDRESS"')) AS tag_adresi,
                               JSON_EXTRACT(dit.tagJson, '$."servermain.TAG_DATA_TYPE"') AS veri_tipi,
                               dit.tagJson, dit.createTime, dit.updateTime
                        FROM {ex_db}.deviceindividualtag dit
                        WHERE dit.channelDeviceId = %s
                        ORDER BY dit.id
                        """,
                        (did,),
                    )
                    tags = list(cur.fetchall())
            return {"aktif_db": ex_db, "device": device, "count": len(tags), "individual_tags": tags}

        @mcp.tool(name=tool)
        def get_device_individual_tags(deviceId: int) -> str:
            """Cihaza ozel tag tanimlari."""
            return guard(tool, _get_device_individual_tags_impl)(deviceId)

        tool = prefixed_name(prefix, "list_device_status_codes")

        def _list_device_status_codes_impl() -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    ex_db = _exchanger_db(cur)
                    cur.execute(
                        f"""
                        SELECT cds.statusCode, cds.statusDefinition,
                               (SELECT COUNT(*) FROM {ex_db}.channeldevice cd WHERE cd.statusCode = cds.statusCode) AS cihaz_sayisi
                        FROM {ex_db}.channeldevicestatus cds
                        ORDER BY cds.statusCode
                        """
                    )
                    statuses = list(cur.fetchall())
            return {
                "aktif_db": ex_db,
                "calisan_status_kodlari": ac,
                "aciklama": "X0=Yeni istek, X1=Başarılı/Çalışıyor, X2=Başarısız.",
                "count": len(statuses),
                "statuses": statuses,
            }

        @mcp.tool(name=tool)
        def list_device_status_codes() -> str:
            """Cihaz durum kodlari aciklamalari."""
            return guard(tool, _list_device_status_codes_impl)()

        tool = prefixed_name(prefix, "list_drivers")

        def _list_drivers_impl(limit: int = 50, offset: int = 0) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 200)
            offset = max(int(offset), 0)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT d.id, d.driverTypeId, drt.name AS driver_type_name,
                               d.name, d.status, d.isActive, d.is_enabled,
                               d.connectedDeviceCount, d.DbTagCount, d.KEPActiveTagCount, d.totalTagCount,
                               d.driver_state, d.control_mode, d.last_action,
                               d.startTime, d.uptime, d.lastStatusUpdate, d.lastError
                        FROM dbdataexchanger.driver d
                        LEFT JOIN dbdataexchanger.drivertype drt ON d.driverTypeId = drt.id
                        ORDER BY d.id
                        LIMIT %s OFFSET %s
                        """
                        ,
                        (limit, offset),
                    )
                    drivers = list(cur.fetchall())
            return {"count": len(drivers), "limit": limit, "offset": offset, "drivers": drivers}

        @mcp.tool(name=tool)
        def list_drivers(limit: int = 50, offset: int = 0) -> str:
            """Kepware surucu listesi."""
            return guard(tool, _list_drivers_impl)(limit, offset)

        tool = prefixed_name(prefix, "get_driver_detail")

        def _get_driver_detail_impl(driverId: int, max_related: int = 50) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            did = int(driverId)
            max_related = min(max(int(max_related), 1), 200)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT d.*, drt.name AS driver_type_name, drt.commonSettings
                        FROM dbdataexchanger.driver d
                        LEFT JOIN dbdataexchanger.drivertype drt ON d.driverTypeId = drt.id
                        WHERE d.id = %s
                        """,
                        (did,),
                    )
                    driver = cur.fetchone()
                    if not driver:
                        return {"error": f"Driver ID {did} bulunamadı."}
                    driver = dict(driver)
                    cur.execute(
                        """
                        SELECT dcr.channelTypeId, ct.name AS channel_type_name, dcr.maxCount, dcr.currentCount
                        FROM dbdataexchanger.driver_channeltype_relation dcr
                        LEFT JOIN dbdataexchanger.channeltypes ct ON dcr.channelTypeId = ct.id
                        WHERE dcr.driverId = %s
                        LIMIT %s
                        """,
                        (did, max_related),
                    )
                    driver["channel_type_relations"] = list(cur.fetchall())
                    cur.execute(
                        """
                        SELECT dn.userId, u.uFirstName, u.uLastName, u.uTel, u.uMail,
                               dn.enableSms, dn.enableMail
                        FROM dbdataexchanger.driver_notifications dn
                        LEFT JOIN kbindb.users u ON dn.userId = u.id
                        WHERE dn.driverId = %s
                        LIMIT %s
                        """,
                        (did, max_related),
                    )
                    driver["bildirim_aboneleri"] = list(cur.fetchall())
                    cur.execute(
                        "SELECT ClientId, Status, UpdateTime FROM dbdataexchanger.service WHERE driverId = %s LIMIT %s",
                        (did, max_related),
                    )
                    driver["service_clients"] = list(cur.fetchall())
                    cur.execute(
                        "SELECT COUNT(*) AS c FROM dbdataexchanger.channeldevice WHERE driverId = %s",
                        (did,),
                    )
                    driver["toplam_cihaz_sayisi"] = int((cur.fetchone() or {})["c"] or 0)
                    driver["_limits"] = {"max_related": max_related}
            return driver

        @mcp.tool(name=tool)
        def get_driver_detail(driverId: int, max_related: int = 50) -> str:
            """Surucu detayi ve iliskili cihazlar."""
            return guard(tool, _get_driver_detail_impl)(driverId, max_related)

        tool = prefixed_name(prefix, "list_service_instances")

        def _list_service_instances_impl(limit: int = 50, offset: int = 0) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 200)
            offset = max(int(offset), 0)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT si.id, si.computer_name, si.service_name, si.system_name,
                               si.current_status, si.requested_status,
                               si.startup_time, si.uptime_seconds, si.version,
                               si.last_heartbeat, si.last_command_time, si.last_command_by,
                               si.drivers, si.settings,
                               si.create_time, si.update_time
                        FROM dbdataexchanger.service_instances si
                        ORDER BY si.id
                        LIMIT %s OFFSET %s
                        """
                        ,
                        (limit, offset),
                    )
                    instances = list(cur.fetchall())
            return {"count": len(instances), "limit": limit, "offset": offset, "service_instances": instances}

        @mcp.tool(name=tool)
        def list_service_instances(limit: int = 50, offset: int = 0) -> str:
            """DataExchanger servis instance’lari."""
            return guard(tool, _list_service_instances_impl)(limit, offset)

        tool = prefixed_name(prefix, "get_service_activities")

        def _get_service_activities_impl(
            level: str = "",
            category: str = "",
            driverId: int = 0,
            deviceId: int = 0,
            limit: int = 50,
            offset: int = 0,
        ) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            limit = min(max(int(limit), 1), 200)
            offset = max(int(offset), 0)
            where: list[str] = []
            params: list[Any] = []
            if (level or "").strip():
                where.append("sa.level = %s")
                params.append(level.strip())
            if (category or "").strip():
                where.append("sa.category = %s")
                params.append(category.strip())
            if int(driverId) > 0:
                where.append("sa.driverId = %s")
                params.append(int(driverId))
            if int(deviceId) > 0:
                where.append("sa.deviceId = %s")
                params.append(int(deviceId))
            wh = ("WHERE " + " AND ".join(where)) if where else ""
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        SELECT sa.id, sa.source, sa.action, sa.message, sa.details,
                               sa.level, sa.category, sa.deviceId, sa.driverId,
                               sa.timestamp, sa.isRead, sa.summary
                        FROM dbdataexchanger.service_activities sa
                        {wh}
                        ORDER BY sa.timestamp DESC
                        LIMIT %s OFFSET %s
                        """,
                        (*params, limit, offset),
                    )
                    activities = list(cur.fetchall())
            return {"count": len(activities), "activities": activities}

        @mcp.tool(name=tool)
        def get_service_activities(
            level: str = "",
            category: str = "",
            driverId: int = 0,
            deviceId: int = 0,
            limit: int = 50,
            offset: int = 0,
        ) -> str:
            """Servis aktivite loglari."""
            return guard(tool, _get_service_activities_impl)(
                level, category, driverId, deviceId, limit, offset
            )

        tool = prefixed_name(prefix, "get_device_all_tags")

        def _get_device_all_tags_impl(deviceId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            did = int(deviceId)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    ex_db = _exchanger_db(cur)
                    cur.execute(
                        f"""
                        SELECT cd.id, cd.channelName, cd.deviceTypeId,
                               dt.typeName AS device_type_name, n.nName AS node_adi
                        FROM {ex_db}.channeldevice cd
                        LEFT JOIN {ex_db}.devicetype dt ON cd.deviceTypeId = dt.id
                        LEFT JOIN kbindb.node n ON cd.id = n.id
                        WHERE cd.id = %s
                        """,
                        (did,),
                    )
                    device = cur.fetchone()
                    if not device:
                        return {"error": f"Device ID {did} bulunamadı (DB: {ex_db})."}
                    cur.execute(
                        f"""
                        SELECT dtt.id AS tag_id, 'type' AS kaynak,
                               JSON_UNQUOTE(JSON_EXTRACT(dtt.tagJson, '$."common.ALLTYPES_NAME"')) AS tag_adi,
                               JSON_UNQUOTE(JSON_EXTRACT(dtt.tagJson, '$."servermain.TAG_ADDRESS"')) AS tag_adresi,
                               JSON_EXTRACT(dtt.tagJson, '$."servermain.TAG_DATA_TYPE"') AS veri_tipi,
                               JSON_EXTRACT(dtt.tagJson, '$."servermain.TAG_SCAN_RATE_MILLISECONDS"') AS okuma_hizi_ms
                        FROM {ex_db}.devicetypetag dtt
                        WHERE dtt.deviceTypeId = %s
                        ORDER BY dtt.id
                        """,
                        (device["deviceTypeId"],),
                    )
                    type_tag_list = list(cur.fetchall())
                    cur.execute(
                        f"""
                        SELECT dit.id AS tag_id, 'individual' AS kaynak,
                               JSON_UNQUOTE(JSON_EXTRACT(dit.tagJson, '$."common.ALLTYPES_NAME"')) AS tag_adi,
                               JSON_UNQUOTE(JSON_EXTRACT(dit.tagJson, '$."servermain.TAG_ADDRESS"')) AS tag_adresi,
                               JSON_EXTRACT(dit.tagJson, '$."servermain.TAG_DATA_TYPE"') AS veri_tipi,
                               JSON_EXTRACT(dit.tagJson, '$."servermain.TAG_SCAN_RATE_MILLISECONDS"') AS okuma_hizi_ms
                        FROM {ex_db}.deviceindividualtag dit
                        WHERE dit.channelDeviceId = %s
                        ORDER BY dit.id
                        """,
                        (did,),
                    )
                    ind_tag_list = list(cur.fetchall())
            all_tags = type_tag_list + ind_tag_list
            return {
                "aktif_db": ex_db,
                "device": device,
                "type_tag_sayisi": len(type_tag_list),
                "individual_tag_sayisi": len(ind_tag_list),
                "toplam_tag_sayisi": len(all_tags),
                "tags": all_tags,
            }

        @mcp.tool(name=tool)
        def get_device_all_tags(deviceId: int) -> str:
            """Cihazin tum tag tanimlari (Kepware/dataexchanger)."""
            return guard(tool, _get_device_all_tags_impl)(deviceId)

        # Yaygın model yanlış adı: `get_node_all_tags` — gerçek araç get_device_all_tags (deviceId = node.id).
        tool = prefixed_name(prefix, "get_node_all_tags")

        @mcp.tool(name=tool)
        def get_node_all_tags(nodeId: int) -> str:
            """Kepware/dataexchanger tag tanımları (adres, tip). `get_device_all_tags` ile aynı; nodeId = deviceId = node.id."""
            return guard(tool, _get_device_all_tags_impl)(nodeId)

        tool = prefixed_name(prefix, "get_tag_address")

        def _get_tag_address_impl(nodeNameOrId: str, tagName: str) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            data_type_map = {
                1: "Boolean",
                2: "Char",
                3: "Byte",
                4: "Short",
                5: "Word",
                6: "Long",
                7: "DWord",
                8: "Float",
                9: "Double",
                10: "String",
                11: "BCD",
            }
            raw_id = (nodeNameOrId or "").strip()
            tag_clean = (tagName or "").strip()
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    ex_db = _exchanger_db(cur)
                    if raw_id.isdigit():
                        cur.execute("SELECT id, nName FROM kbindb.node WHERE id = %s", (int(raw_id),))
                    else:
                        cur.execute(
                            "SELECT id, nName FROM kbindb.node WHERE nName LIKE %s LIMIT 1",
                            (f"%{raw_id}%",),
                        )
                    node = cur.fetchone()
                    if not node:
                        return {"hata": f"Node bulunamadı: {nodeNameOrId}"}
                    node_id = int(node["id"])
                    node_name = str(node.get("nName") or "")
                    cur.execute(f"SELECT cd.id, cd.channelName, cd.deviceTypeId, cd.statusCode FROM {ex_db}.channeldevice cd WHERE cd.id = %s", (node_id,))
                    device = cur.fetchone()
                    if not device:
                        cur.execute(
                            f"""
                            SELECT cd.id, cd.channelName, cd.deviceTypeId, cd.statusCode
                            FROM {ex_db}.channeldevice cd
                            INNER JOIN kbindb.node n ON n.id = cd.id
                            WHERE n.nName LIKE %s
                            LIMIT 1
                            """,
                            (f"%{node_name}%",),
                        )
                        device = cur.fetchone()
                    if not device:
                        return {
                            "hata": f"Node {node_id} ({node_name}) için channel device bulunamadı.",
                            "node_id": node_id,
                            "node_adı": node_name,
                        }
                    dt_id = int(device["deviceTypeId"])
                    dev_id = int(device["id"])
                    cur.execute(
                        f"""
                        SELECT dtt.id AS tag_id, 'type_tag' AS kaynak,
                               JSON_UNQUOTE(JSON_EXTRACT(dtt.tagJson, '$."common.ALLTYPES_NAME"')) AS tag_adı,
                               JSON_UNQUOTE(JSON_EXTRACT(dtt.tagJson, '$."servermain.TAG_ADDRESS"')) AS modbus_register_adresi,
                               JSON_EXTRACT(dtt.tagJson, '$."servermain.TAG_DATA_TYPE"') AS veri_tipi_kodu,
                               JSON_EXTRACT(dtt.tagJson, '$."servermain.TAG_SCAN_RATE_MILLISECONDS"') AS okuma_hızı_ms,
                               JSON_EXTRACT(dtt.tagJson, '$."servermain.TAG_READ_WRITE_ACCESS"') AS erişim_modu
                        FROM {ex_db}.devicetypetag dtt
                        WHERE dtt.deviceTypeId = %s
                          AND JSON_UNQUOTE(JSON_EXTRACT(dtt.tagJson, '$."common.ALLTYPES_NAME"')) LIKE %s
                        """,
                        (dt_id, f"%{tag_clean}%"),
                    )
                    found = list(cur.fetchall())
                    cur.execute(
                        f"""
                        SELECT dit.id AS tag_id, 'individual_tag' AS kaynak,
                               JSON_UNQUOTE(JSON_EXTRACT(dit.tagJson, '$."common.ALLTYPES_NAME"')) AS tag_adı,
                               JSON_UNQUOTE(JSON_EXTRACT(dit.tagJson, '$."servermain.TAG_ADDRESS"')) AS modbus_register_adresi,
                               JSON_EXTRACT(dit.tagJson, '$."servermain.TAG_DATA_TYPE"') AS veri_tipi_kodu,
                               JSON_EXTRACT(dit.tagJson, '$."servermain.TAG_SCAN_RATE_MILLISECONDS"') AS okuma_hızı_ms,
                               JSON_EXTRACT(dit.tagJson, '$."servermain.TAG_READ_WRITE_ACCESS"') AS erişim_modu
                        FROM {ex_db}.deviceindividualtag dit
                        WHERE dit.channelDeviceId = %s
                          AND JSON_UNQUOTE(JSON_EXTRACT(dit.tagJson, '$."common.ALLTYPES_NAME"')) LIKE %s
                        """,
                        (dev_id, f"%{tag_clean}%"),
                    )
                    found.extend(list(cur.fetchall()))
                    if not found:
                        return {
                            "hata": f"'{tagName}' tag'ı node {node_id} ({node_name}) cihazında bulunamadı.",
                            "node_id": node_id,
                            "node_adı": node_name,
                            "cihaz_adı": device.get("channelName") or "",
                            "ipucu": "Tag adını kontrol edin.",
                        }
                    names = [r.get("tag_adı") for r in found if r.get("tag_adı")]
                    live: dict[str, Any] = {}
                    if names:
                        ph = ",".join(["%s"] * len(names))
                        cur.execute(
                            f"SELECT tagName, tagValue, readTime FROM kbindb._tagoku WHERE devId = %s AND tagName IN ({ph})",
                            (node_id, *names),
                        )
                        for row in cur.fetchall():
                            live[str(row["tagName"])] = {
                                "değer": row.get("tagValue"),
                                "okuma_zamanı": row.get("readTime"),
                            }
                    results = []
                    for tag in found:
                        dt_code = tag.get("veri_tipi_kodu")
                        try:
                            dt_i = int(dt_code) if dt_code is not None else None
                        except Exception:
                            dt_i = None
                        tr = {
                            "tag_adı": tag.get("tag_adı"),
                            "modbus_register_adresi": tag.get("modbus_register_adresi"),
                            "veri_tipi": data_type_map.get(dt_i, f"Tip {dt_i}" if dt_i is not None else None),
                            "veri_tipi_kodu": dt_i,
                            "okuma_hızı_ms": int(tag["okuma_hızı_ms"]) if tag.get("okuma_hızı_ms") is not None else None,
                            "erişim": (
                                "Sadece Okuma"
                                if tag.get("erişim_modu") is not None and int(tag["erişim_modu"]) == 1
                                else (
                                    "Okuma/Yazma"
                                    if tag.get("erişim_modu") is not None
                                    else None
                                )
                            ),
                            "kaynak": tag.get("kaynak"),
                        }
                        tn = tag.get("tag_adı")
                        if tn and tn in live:
                            tr["canlı_değer"] = live[tn].get("değer")
                            tr["son_okuma"] = live[tn].get("okuma_zamanı")
                        results.append(tr)
            return {
                "node_id": node_id,
                "node_adı": node_name,
                "cihaz_adı": device.get("channelName") or "",
                "aktif_db": ex_db,
                "aranan_tag": tagName,
                "bulunan_sayısı": len(results),
                "sonuçlar": results,
            }

        @mcp.tool(name=tool)
        def get_tag_address(nodeNameOrId: str, tagName: str) -> str:
            """Tag Kepware adresi ve tipi."""
            return guard(tool, _get_tag_address_impl)(nodeNameOrId, tagName)

        # --- ChartTools (get_chart_data, get_multi_chart_data) ---
        tool = prefixed_name(prefix, "get_chart_data")

        def _get_chart_data_impl(
            nodeId: int,
            logParamId: int,
            startDate: str = "",
            endDate: str = "",
            chartType: str = "line",
        ) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            nid = int(nodeId)
            pid = int(logParamId)
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT nName FROM kbindb.node WHERE id=%s", (nid,))
                    nr = cur.fetchone()
                    node_name = str(nr["nName"]) if nr else f"Node {nid}"
                    cur.execute(
                        "SELECT id, nid, tagPath, description, rangeMin, rangeMax, logInterval FROM kbindb.logparameters WHERE id=%s",
                        (pid,),
                    )
                    pi = cur.fetchone()
                    if not pi:
                        return {"hata": f"Log parametresi {pid} bulunamadı."}
                    raw_desc = pi.get("description") or ""
                    desc = raw_desc if raw_desc and str(raw_desc)[0] != "{" else pi.get("tagPath")
                    if not _log_table_exists(cur, nid):
                        return {"hata": f"Node {nid} için log tablosu bulunamadı."}
                    res = _fetch_sampled_log(cur, nid, pid, startDate, endDate, _MAX_CHART_POINTS)
                    if res.get("error"):
                        return {"hata": res["error"]}
                    data = res.get("data") or []
                    if not data:
                        return {"hata": "Belirtilen aralıkta veri yok."}
                    labels = [r["logTime"] for r in data]
                    values = [float(r.get("tagValue") or 0) for r in data]
                    mn = min(values)
                    mx = max(values)
                    avg = round(sum(values) / len(values), 2) if values else 0.0
                    title = f"{node_name} — {desc}"
                    if startDate or endDate:
                        title += f" ({startDate or '...'} → {endDate or '...'})"
                    is_sampled = res.get("sampling") != "yok"
                    ds_label = (desc or "") + (" (ort)" if is_sampled else "")
            return {
                "_type": "chart",
                "grafik_sunumu_model_talimat_tr": GRAFIK_SUNUMU_MODEL_TALIMAT_TR,
                **koru_mind_log_timeseries_extras(chartType),
                "title": title,
                "labels": labels,
                "datasets": [
                    {
                        "label": ds_label,
                        "data": [round(v, 4) for v in values],
                        "borderColor": "#38bdf8",
                        "backgroundColor": "rgba(56,189,248,0.1)",
                        "fill": True,
                        "tension": 0.3,
                        "pointRadius": 0 if len(values) > 50 else 3,
                    }
                ],
                "stats": {
                    "min": round(mn, 2),
                    "max": round(mx, 2),
                    "avg": avg,
                    "point_count": len(values),
                    "total_records": res.get("total"),
                    "sampling": res.get("sampling"),
                },
                "y_axis_label": desc,
                "yAxisLabel": desc,
                "node": {"id": nid, "name": node_name},
                "parameter": {"id": pid, "path": pi.get("tagPath"), "desc": desc},
                "log_deger_temizlik_tr": res.get("log_deger_temizlik_tr") or outlier_filtre_ozet_tr(),
            }

        @mcp.tool(name=tool)
        def get_chart_data(
            nodeId: int,
            logParamId: int,
            startDate: str = "",
            endDate: str = "",
            chartType: str = "line",
        ) -> str:
            """Tarih eksenli ham log cizgisi (_type chart). DMA kume/scatter icin analyze_dma_seasonal_demand kullanin."""
            return guard(tool, _get_chart_data_impl)(nodeId, logParamId, startDate, endDate, chartType)

        tool = prefixed_name(prefix, "get_multi_chart_data")

        def _get_multi_chart_data_impl(
            nodeId: int,
            logParamIds: str,
            startDate: str = "",
            endDate: str = "",
            chartType: str = "line",
        ) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            ids = [int(x) for x in re.split(r"[\s,]+", logParamIds or "") if x.strip().isdigit()]
            if not ids:
                return {"hata": "logParamIds gerekli (virgülle ayrılmış)."}
            if len(ids) > 6:
                return {"hata": "En fazla 6 parametre."}
            nid = int(nodeId)
            colors = ["#38bdf8", "#f97316", "#22c55e", "#ef4444", "#a855f7", "#eab308"]
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT nName FROM kbindb.node WHERE id=%s", (nid,))
                    nr = cur.fetchone()
                    node_name = str(nr["nName"]) if nr else f"Node {nid}"
                    if not _log_table_exists(cur, nid):
                        return {"hata": f"Node {nid} için log tablosu bulunamadı."}
                    tname = f"log_{nid}"
                    full = f"noktalog.`{tname}`"
                    valid_params: list[tuple[int, str]] = []
                    for pid in ids:
                        cur.execute(
                            "SELECT id, tagPath, description FROM kbindb.logparameters WHERE id=%s",
                            (pid,),
                        )
                        pi = cur.fetchone()
                        if not pi:
                            continue
                        raw_desc = pi.get("description") or ""
                        desc = raw_desc if raw_desc and str(raw_desc)[0] != "{" else pi.get("tagPath")
                        valid_params.append((int(pid), str(desc)))
                    if not valid_params:
                        return {"hata": "Geçerli log parametresi yok."}
                    pids_u = [p for p, _ in valid_params]
                    aligned = aligned_multi_log_series(
                        cur, full, pids_u, startDate, endDate, _MAX_CHART_POINTS
                    )
                    if not aligned:
                        return {"hata": "Belirtilen aralıkta veri yok."}
                    labels_ref = aligned["labels"]
                    datasets = []
                    for i, (_pid, desc) in enumerate(valid_params):
                        vals = aligned["values_per_param"][i]
                        datasets.append(
                            {
                                "label": desc,
                                "data": [round(float(v), 4) if v is not None else None for v in vals],
                                "borderColor": colors[i % len(colors)],
                                "backgroundColor": "rgba(56,189,248,0.05)",
                                "fill": False,
                                "tension": 0.3,
                            }
                        )
            out: dict[str, Any] = {
                "_type": "chart",
                "grafik_sunumu_model_talimat_tr": GRAFIK_SUNUMU_MODEL_TALIMAT_TR,
                **koru_mind_coklu_log_chart_extras(chartType),
                "title": f"{node_name} — çoklu parametre (hizalı zaman)",
                "labels": labels_ref,
                "datasets": datasets,
                "stats": {
                    "bucket_seconds": aligned["bucket_seconds"],
                    "nokta_sayisi": len(labels_ref),
                    "toplam_log_satiri_aralik": aligned["total_rows"],
                },
                "zaman_kovasi_hizali_tr": (
                    "Tüm seriler aynı zaman kovalarında hizalandı; eksen kayması giderildi. "
                    "Pasta/halka bu veri için uygunsuz — çizgi veya zaman eksenli çubuk kullanın."
                ),
                "node": {"id": nid, "name": node_name},
                "log_deger_temizlik_tr": outlier_filtre_ozet_tr(),
            }
            if len(valid_params) == 2:
                out["iki_parametre_uyari_tr"] = (
                    "Debi ve güç gibi farklı birimlerde çift Y ekseni ve korelasyon için "
                    "compare_log_metrics aracı daha uygundur."
                )
            return out

        @mcp.tool(name=tool)
        def get_multi_chart_data(
            nodeId: int,
            logParamIds: str,
            startDate: str = "",
            endDate: str = "",
            chartType: str = "line",
        ) -> str:
            """Birden fazla log parametresi hizali zaman kovasinda. Iki farkli birim icin compare_log_metrics tercih edilir."""
            return guard(tool, _get_multi_chart_data_impl)(nodeId, logParamIds, startDate, endDate, chartType)

        tool = prefixed_name(prefix, "compare_log_metrics")

        def _compare_log_metrics_impl(
            nodeId: int = 0,
            nodeAdiAra: str = "",
            primaryTagHint: str = "",
            secondaryTagHint: str = "",
            primaryLogParamId: int = 0,
            secondaryLogParamId: int = 0,
            startDate: str = "",
            endDate: str = "",
            maxChartPoints: int = 140,
            chartType: str = "line",
            karsilastirmaAciklamasi: str = "",
        ) -> Any:
            return compare_log_metrics_impl(
                cfg,
                nodeId=nodeId,
                nodeAdiAra=nodeAdiAra,
                primaryTagHint=primaryTagHint,
                secondaryTagHint=secondaryTagHint,
                primaryLogParamId=primaryLogParamId,
                secondaryLogParamId=secondaryLogParamId,
                startDate=startDate,
                endDate=endDate,
                maxChartPoints=maxChartPoints,
                chartType=chartType,
                karsilastirmaAciklamasi=karsilastirmaAciklamasi,
            )

        @mcp.tool(name=tool)
        def compare_log_metrics(
            nodeId: int = 0,
            nodeAdiAra: str = "",
            primaryTagHint: str = "",
            secondaryTagHint: str = "",
            primaryLogParamId: int = 0,
            secondaryLogParamId: int = 0,
            startDate: str = "",
            endDate: str = "",
            maxChartPoints: int = 140,
            chartType: str = "line",
            karsilastirmaAciklamasi: str = "",
        ) -> str:
            """Iki log parametresini hizalar (orn. debi + guc). Cift Y ekseni onerilir."""
            return guard(tool, _compare_log_metrics_impl)(
                nodeId,
                nodeAdiAra,
                primaryTagHint,
                secondaryTagHint,
                primaryLogParamId,
                secondaryLogParamId,
                startDate,
                endDate,
                maxChartPoints,
                chartType,
                karsilastirmaAciklamasi,
            )

        # --- Node log (subset) ---
        tool = prefixed_name(prefix, "get_node_log_data")

        def _get_node_log_data_impl(
            nodeId: int,
            logParamId: int = 0,
            startDate: str = "",
            endDate: str = "",
            limit: int = 200,
            offset: int = 0,
        ) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            nid = int(nodeId)
            limit = min(max(int(limit), 1), 1000)
            offset = max(int(offset), 0)
            tname = f"log_{nid}"
            full = f"noktalog.`{tname}`"
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    if not _log_table_exists(cur, nid):
                        return {"error": f"Node ID {nid} için log tablosu (noktalog.{tname}) bulunamadı."}
                    where = []
                    params: list[Any] = []
                    if int(logParamId) > 0:
                        where.append("l.logPId = %s")
                        params.append(int(logParamId))
                    if (startDate or "").strip():
                        where.append("l.logTime >= %s")
                        params.append(startDate.strip())
                    if (endDate or "").strip():
                        where.append("l.logTime <= %s")
                        params.append(endDate.strip())
                    if int(logParamId) > 0 and where:
                        wh0 = "WHERE " + " AND ".join(where)
                        vb = fetch_log_value_bounds(
                            cur, f"SELECT tagValue FROM {full} l {wh0}", tuple(params)
                        )
                        if vb:
                            lo, hi = vb
                            where.extend(["l.tagValue >= %s", "l.tagValue <= %s"])
                            params.extend([lo, hi])
                    wh = ("WHERE " + " AND ".join(where)) if where else ""
                    cur.execute(
                        f"""
                        SELECT l.logPId, lp.tagPath AS parametre_yolu, lp.description AS parametre_aciklama,
                               l.tagValue, l.logTime
                        FROM {full} l
                        LEFT JOIN kbindb.logparameters lp ON l.logPId = lp.id
                        {wh}
                        ORDER BY l.logTime DESC
                        LIMIT %s OFFSET %s
                        """,
                        (*params, limit, offset),
                    )
                    logs = list(cur.fetchall())
                    if int(logParamId) <= 0 and logs:
                        pids = {int(r["logPId"]) for r in logs if r.get("logPId") is not None}
                        bounds_map: dict[int, tuple[float, float]] = {}
                        for p in pids:
                            w2 = ["l.logPId = %s"]
                            pr2: list[Any] = [p]
                            if (startDate or "").strip():
                                w2.append("l.logTime >= %s")
                                pr2.append(startDate.strip())
                            if (endDate or "").strip():
                                w2.append("l.logTime <= %s")
                                pr2.append(endDate.strip())
                            whb = "WHERE " + " AND ".join(w2)
                            b2 = fetch_log_value_bounds(
                                cur, f"SELECT tagValue FROM {full} l {whb}", tuple(pr2)
                            )
                            if b2:
                                bounds_map[p] = b2
                        clipped: list[Any] = []
                        for r in logs:
                            rr = dict(r)
                            p = int(rr.get("logPId") or 0)
                            b2 = bounds_map.get(p)
                            if b2:
                                lo, hi = b2
                                try:
                                    v = float(rr.get("tagValue") or 0)
                                    rr["tagValue"] = round(min(hi, max(lo, v)), 6)
                                except (TypeError, ValueError):
                                    pass
                            clipped.append(rr)
                        logs = clipped
                    cur.execute("SELECT id, nName, nType, nPath FROM kbindb.node WHERE id=%s", (nid,))
                    node = cur.fetchone()
            return {
                "node_id": nid,
                "node": node,
                "log_table": f"noktalog.{tname}",
                "count": len(logs),
                "logs": logs,
                "log_deger_temizlik_tr": outlier_filtre_ozet_tr(),
            }

        @mcp.tool(name=tool)
        def get_node_log_data(
            nodeId: int,
            logParamId: int = 0,
            startDate: str = "",
            endDate: str = "",
            limit: int = 200,
            offset: int = 0,
        ) -> str:
            """Node log verisi (tarih/parametre filtreli, outlier temizlikli)."""
            return guard(tool, _get_node_log_data_impl)(nodeId, logParamId, startDate, endDate, limit, offset)

        tool = prefixed_name(prefix, "get_node_log_summary")

        def _get_node_log_summary_impl(nodeId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            nid = int(nodeId)
            tname = f"log_{nid}"
            full = f"noktalog.`{tname}`"
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    if not _log_table_exists(cur, nid):
                        return {"error": f"Node ID {nid} için log tablosu (noktalog.{tname}) bulunamadı."}
                    cur.execute(
                        f"SELECT COUNT(*) AS toplam_kayit, COUNT(DISTINCT logPId) AS parametre_sayisi, MIN(logTime) AS ilk_kayit, MAX(logTime) AS son_kayit FROM {full}"
                    )
                    stats = cur.fetchone()
                    cur.execute(
                        f"""
                        SELECT l.logPId, lp.tagPath, lp.description,
                               COUNT(*) AS kayit_sayisi,
                               MIN(l.tagValue) AS min_deger,
                               MAX(l.tagValue) AS max_deger,
                               AVG(l.tagValue) AS ort_deger,
                               MIN(l.logTime) AS ilk_kayit,
                               MAX(l.logTime) AS son_kayit
                        FROM {full} l
                        LEFT JOIN kbindb.logparameters lp ON l.logPId = lp.id
                        GROUP BY l.logPId, lp.tagPath, lp.description
                        ORDER BY l.logPId
                        """
                    )
                    param_stats = list(cur.fetchall())
                    cur.execute("SELECT id, nName, nType, nPath FROM kbindb.node WHERE id=%s", (nid,))
                    node = cur.fetchone()
            return {
                "node_id": nid,
                "node": node,
                "log_table": f"noktalog.{tname}",
                "toplam_kayit": int(stats.get("toplam_kayit") or 0),
                "parametre_sayisi": int(stats.get("parametre_sayisi") or 0),
                "ilk_kayit_tarihi": stats.get("ilk_kayit"),
                "son_kayit_tarihi": stats.get("son_kayit"),
                "parametre_detaylari": param_stats,
            }

        @mcp.tool(name=tool)
        def get_node_log_summary(nodeId: int) -> str:
            """Node log parametreleri ozeti."""
            return guard(tool, _get_node_log_summary_impl)(nodeId)

        tool = prefixed_name(prefix, "get_node_log_latest_values")

        def _get_node_log_latest_values_impl(nodeId: int) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            nid = int(nodeId)
            tname = f"log_{nid}"
            full = f"noktalog.`{tname}`"
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    if not _log_table_exists(cur, nid):
                        return {"error": f"Node ID {nid} için log tablosu (noktalog.{tname}) bulunamadı."}
                    cur.execute(
                        f"""
                        SELECT l.logPId, lp.tagPath, lp.description,
                               l.tagValue, l.logTime
                        FROM {full} l
                        LEFT JOIN kbindb.logparameters lp ON l.logPId = lp.id
                        INNER JOIN (
                            SELECT logPId, MAX(logTime) AS maxTime
                            FROM {full}
                            GROUP BY logPId
                        ) latest ON l.logPId = latest.logPId AND l.logTime = latest.maxTime
                        ORDER BY l.logPId
                        """
                    )
                    results = list(cur.fetchall())
                    cur.execute("SELECT id, nName, nType, nPath FROM kbindb.node WHERE id=%s", (nid,))
                    node = cur.fetchone()
            return {"node_id": nid, "node": node, "parametre_sayisi": len(results), "son_degerler": results}

        @mcp.tool(name=tool)
        def get_node_log_latest_values(nodeId: int) -> str:
            """Node’un son log degerleri."""
            return guard(tool, _get_node_log_latest_values_impl)(nodeId)

        tool = prefixed_name(prefix, "get_node_log_chart_data")

        def _get_node_log_chart_data_impl(
            nodeId: int,
            logParamId: int,
            startDate: str = "",
            endDate: str = "",
            chartType: str = "line",
        ) -> Any:
            return _get_chart_data_impl(nodeId, logParamId, startDate, endDate, chartType)

        @mcp.tool(name=tool)
        def get_node_log_chart_data(
            nodeId: int,
            logParamId: int,
            startDate: str = "",
            endDate: str = "",
            chartType: str = "line",
        ) -> str:
            """get_chart_data ile ayni: tarih eksenli ham seri. DMA kume/scatter icin analyze_dma_seasonal_demand kullanin."""
            return guard(tool, _get_node_log_chart_data_impl)(nodeId, logParamId, startDate, endDate, chartType)

        tool = prefixed_name(prefix, "get_recent_log_chart_by_tag")

        def _get_recent_log_chart_by_tag_impl(
            nodeId: int, tagPath: str, maxPoints: int = 10, chartType: str = "line"
        ) -> Any:
            if not cfg.db:
                raise RuntimeError("DB config is missing for this instance.")
            nid = int(nodeId)
            mp = min(100, max(1, int(maxPoints)))
            ts = (tagPath or "").strip()
            if not ts:
                return {"hata": "tagPath boş olamaz."}
            with dbmod.connect(cfg.db) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, tagPath, description FROM kbindb.logparameters
                        WHERE nid = %s AND LOWER(TRIM(tagPath)) = LOWER(%s)
                        ORDER BY CHAR_LENGTH(tagPath) ASC, id ASC
                        LIMIT 1
                        """,
                        (nid, ts),
                    )
                    lp = cur.fetchone()
                    if not lp:
                        safe = re.sub(r"[%_\\]", "", ts)
                        cur.execute(
                            """
                            SELECT id, tagPath, description FROM kbindb.logparameters
                            WHERE nid = %s AND tagPath LIKE %s
                            ORDER BY CHAR_LENGTH(tagPath) ASC, id ASC
                            LIMIT 1
                            """,
                            (nid, f"%{safe}%"),
                        )
                        lp = cur.fetchone()
                    if not lp:
                        return {"hata": "log parametresi bulunamadı"}
                    pid = int(lp["id"])
                    tname = f"log_{nid}"
                    full = f"noktalog.`{tname}`"
                    if not _log_table_exists(cur, nid):
                        return {"hata": "log tablosu yok"}
                    vb = fetch_log_value_bounds(
                        cur, f"SELECT tagValue FROM {full} WHERE logPId=%s", (pid,)
                    )
                    cur.execute(
                        f"""
                        SELECT tagValue, logTime FROM {full}
                        WHERE logPId = %s
                        ORDER BY logTime DESC
                        LIMIT %s
                        """,
                        (pid, mp),
                    )
                    rows = list(cur.fetchall())
                    rows.reverse()
                    if not rows:
                        return {"hata": "Bu parametre için log yok"}
                    labels = [r["logTime"] for r in rows]
                    if vb:
                        lo, hi = vb
                        values = [
                            round(min(hi, max(lo, float(r.get("tagValue") or 0))), 4) for r in rows
                        ]
                    else:
                        values = [float(r.get("tagValue") or 0) for r in rows]
                    cur.execute("SELECT nName FROM kbindb.node WHERE id=%s", (nid,))
                    nn = (cur.fetchone() or {}).get("nName") or str(nid)
                    raw_d = lp.get("description") or ""
                    desc = raw_d if raw_d and str(raw_d)[0] != "{" else lp.get("tagPath")
            return {
                "_type": "chart",
                "grafik_sunumu_model_talimat_tr": GRAFIK_SUNUMU_MODEL_TALIMAT_TR,
                **koru_mind_log_timeseries_extras(chartType),
                "title": f"{nn} — {desc} (son {mp})",
                "labels": labels,
                "datasets": [
                    {
                        "label": str(desc),
                        "data": [round(v, 4) for v in values],
                        "borderColor": "#38bdf8",
                        "fill": True,
                    }
                ],
                "y_axis_label": str(desc),
                "yAxisLabel": str(desc),
                "node": {"id": nid, "name": nn},
                "parameter": {"id": pid, "path": lp.get("tagPath")},
                "log_deger_temizlik_tr": outlier_filtre_ozet_tr(),
            }

        @mcp.tool(name=tool)
        def get_recent_log_chart_by_tag(
            nodeId: int, tagPath: str, maxPoints: int = 10, chartType: str = "line"
        ) -> str:
            """Tag yoluna gore son N log degerinin grafigi."""
            return guard(tool, _get_recent_log_chart_by_tag_impl)(nodeId, tagPath, maxPoints, chartType)

        tool = prefixed_name(prefix, "analyze_log_trend")

        def _analyze_log_trend_impl(
            nodeId: int,
            tagHint: str = "",
            logParamId: int = 0,
            analysisMode: str = "auto",
            startDate: str = "",
            endDate: str = "",
            longTermGranularity: str = "month",
            maxChartPoints: int = 120,
        ) -> Any:
            return analyze_log_trend_impl(
                cfg,
                nodeId,
                tagHint=tagHint,
                logParamId=logParamId,
                analysisMode=analysisMode,
                startDate=startDate,
                endDate=endDate,
                longTermGranularity=longTermGranularity,
                maxChartPoints=maxChartPoints,
            )

        @mcp.tool(name=tool)
        def analyze_log_trend(
            nodeId: int,
            tagHint: str = "",
            logParamId: int = 0,
            analysisMode: str = "auto",
            startDate: str = "",
            endDate: str = "",
            longTermGranularity: str = "month",
            maxChartPoints: int = 120,
        ) -> str:
            """Trend analizi (auto/long_term/pressure_plateau). Dogal dil ile parametre secimi destekler."""
            return guard(tool, _analyze_log_trend_impl)(
                nodeId,
                tagHint,
                logParamId,
                analysisMode,
                startDate,
                endDate,
                longTermGranularity,
                maxChartPoints,
            )

        tool = prefixed_name(prefix, "list_dma_station_nodes")

        def _list_dma_station_nodes_impl(limit: int = 50) -> Any:
            return list_dma_station_nodes_impl(cfg, limit)

        @mcp.tool(name=tool)
        def list_dma_station_nodes(limit: int = 50) -> str:
            """DMA istasyon listesi (nView, ürün tipi, isim). Saatlik debi/K-Means analizi: analyze_dma_seasonal_demand."""
            return guard(tool, _list_dma_station_nodes_impl)(limit)

        tool = prefixed_name(prefix, "analyze_dma_seasonal_demand")

        def _analyze_dma_seasonal_demand_impl(
            nodeId: int = 0,
            nodeAdiAra: str = "",
            tagHint: str = "",
            logParamId: int = 0,
            kClusters: int = 12,
            minSamplesPerHour: int = 2,
            startDate: str = "",
            endDate: str = "",
            maxScatterPoints: int = 3500,
        ) -> Any:
            return analyze_dma_seasonal_demand_impl(
                cfg,
                nodeId,
                nodeAdiAra=nodeAdiAra,
                tagHint=tagHint,
                logParamId=logParamId,
                kClusters=kClusters,
                minSamplesPerHour=minSamplesPerHour,
                startDate=startDate,
                endDate=endDate,
                maxScatterPoints=maxScatterPoints,
            )

        @mcp.tool(name=tool)
        def analyze_dma_seasonal_demand(
            nodeId: int = 0,
            nodeAdiAra: str = "",
            tagHint: str = "",
            logParamId: int = 0,
            kClusters: int = 12,
            minSamplesPerHour: int = 2,
            startDate: str = "",
            endDate: str = "",
            maxScatterPoints: int = 3500,
        ) -> str:
            """DMA debi bolgeleri K-Means analizi (saatlik ortalama, yaz-kis, scatter chart). startDate/endDate ile aralik daraltma."""
            return guard(tool, _analyze_dma_seasonal_demand_impl)(
                nodeId,
                nodeAdiAra,
                tagHint,
                logParamId,
                kClusters,
                minSamplesPerHour,
                startDate,
                endDate,
                maxScatterPoints,
            )

        tool = prefixed_name(prefix, "analyze_seasonal_level_profile")

        def _analyze_seasonal_level_profile_impl(
            nodeId: int = 0,
            nodeAdiAra: str = "",
            tagHint: str = "",
            logParamId: int = 0,
            kClusters: int = 12,
            minSamplesPerHour: int = 2,
            startDate: str = "",
            endDate: str = "",
            maxScatterPoints: int = 2500,
        ) -> Any:
            return analyze_seasonal_level_profile_impl(
                cfg,
                nodeId,
                nodeAdiAra=nodeAdiAra,
                tagHint=tagHint,
                logParamId=logParamId,
                kClusters=kClusters,
                minSamplesPerHour=minSamplesPerHour,
                startDate=startDate,
                endDate=endDate,
                maxScatterPoints=maxScatterPoints,
            )

        @mcp.tool(name=tool)
        def analyze_seasonal_level_profile(
            nodeId: int = 0,
            nodeAdiAra: str = "",
            tagHint: str = "",
            logParamId: int = 0,
            kClusters: int = 12,
            minSamplesPerHour: int = 2,
            startDate: str = "",
            endDate: str = "",
            maxScatterPoints: int = 2500,
        ) -> str:
            """Seviye profili (kuyu/depo): saatlik ortalama + yaz/kis + K-Means scatter."""
            return guard(tool, _analyze_seasonal_level_profile_impl)(
                nodeId,
                nodeAdiAra,
                tagHint,
                logParamId,
                kClusters,
                minSamplesPerHour,
                startDate,
                endDate,
                maxScatterPoints,
            )

        # --- Product (JSON) ---
        tool = prefixed_name(prefix, "search_product_manual")

        def _search_product_manual_impl(aramaMetni: str, ürünFiltresi: str = "") -> Any:
            products = _load_all_products(cfg)
            if not products:
                # Fallback to instance PDF-text docs
                pdir = instance_products_dir(cfg.base_dir)
                doc_keys = list_product_doc_keys(pdir)
                if not doc_keys:
                    return {"hata": "Hiçbir ürün kılavuzu bulunamadı."}
                q = (aramaMetni or "").strip()
                filt = (ürünFiltresi or "").strip().lower()
                res = []
                for k in doc_keys:
                    if filt and filt not in k.lower():
                        continue
                    doc = load_product_doc(pdir, k)
                    if not doc:
                        continue
                    meta = json.loads(doc.meta_path.read_text(encoding="utf-8", errors="replace"))
                    method = str(meta.get("extraction_method") or "")
                    txt = doc.text_path.read_text(encoding="utf-8", errors="replace")
                    if method in {"ocr_failed", "ocr_unavailable"}:
                        # Don't pretend we have searchable text.
                        continue
                    if not txt.strip():
                        continue
                    hits = search_text(txt, q, limit=20)
                    if hits:
                        res.append({"ürün": doc.title, "doc_key": doc.key, "eşleşme_sayısı": len(hits), "sonuçlar": hits})
                return {"aranan": q, "sonuçlar": res, "not_tr": "PDF metin indeksinden arandı."}
            q = (aramaMetni or "").strip()
            filt = (ürünFiltresi or "").strip().lower()
            all_results: list[Any] = []
            for key, data in products.items():
                if filt and filt not in key.lower():
                    continue
                matches = _search_in_dict(data, q)
                if matches:
                    all_results.append(
                        {
                            "ürün": data.get("ürün_ailesi") or key,
                            "eşleşme_sayısı": len(matches),
                            "sonuçlar": matches[:20],
                        }
                    )
            if not all_results:
                return {
                    "aranan": q,
                    "sonuç": "Eşleşme bulunamadı.",
                    "ipucu": "Farklı anahtar kelimeler deneyin.",
                }
            return {
                "aranan": q,
                "toplam_eşleşme": sum(x["eşleşme_sayısı"] for x in all_results),
                "sonuçlar": all_results,
            }

        @mcp.tool(name=tool)
        def search_product_manual(aramaMetni: str, ürünFiltresi: str = "") -> str:
            """Urun kilavuzunda metin arama."""
            return guard(tool, _search_product_manual_impl)(aramaMetni, ürünFiltresi)

        tool = prefixed_name(prefix, "get_product_specs")

        def _get_product_specs_impl(ürünAdı: str = "aqua_cnt_100") -> Any:
            name = (ürünAdı or "aqua_cnt_100").replace(".json", "")
            data = _load_product_json(name, cfg)
            if not data:
                for k, p in _load_all_products(cfg).items():
                    if name.lower() in k.lower() or name.lower() in str(p.get("ürün_ailesi") or "").lower():
                        data = p
                        break
            if not data:
                # If no JSON, try PDF-text doc exists
                pdir = instance_products_dir(cfg.base_dir)
                doc = load_product_doc(pdir, name)
                if doc:
                    meta = json.loads(doc.meta_path.read_text(encoding="utf-8", errors="replace"))
                    method = str(meta.get("extraction_method") or "")
                    txt = doc.text_path.read_text(encoding="utf-8", errors="replace")
                    if method in {"ocr_failed", "ocr_unavailable"} or not txt.strip():
                        return {
                            "hata": "Doküman metni çıkarılamadı (OCR yok ya da başarısız).",
                            "doc_key": doc.key,
                            "extraction_method": method or None,
                            "ipucu_tr": "Bu PDF taranmış olabilir. OCR kurulu bir makinede yeniden ingest edin.",
                        }
                    # Return a small, useful slice + how to search
                    hits = search_text(txt, "DONANIMSAL ÖZELLİKLER", limit=10) or search_text(txt, "DONANIM", limit=10)
                    return {
                        "ürün_ailesi": doc.title,
                        "kaynak": "pdf_text",
                        "doc_key": doc.key,
                        "extraction_method": method or None,
                        "ipucu_tr": "Detay için search_product_manual ile anahtar kelime ara (örn: 'DN50', '4-20mA', 'Modbus', 'Debimetre Tip Seçimi').",
                        "ornek_bulgu": hits,
                    }
                return {"hata": f"Ürün bulunamadı: {ürünAdı}", "ipucu_tr": "JSON yoksa önce PDF'yi instance/products altına ingest edin."}
            return {
                "ürün_ailesi": data.get("ürün_ailesi"),
                "üretici": data.get("üretici"),
                "açıklama": data.get("açıklama"),
                "modeller": data.get("modeller"),
                "donanım_özellikleri": data.get("donanım_özellikleri"),
                "modbus_tcp": data.get("modbus_tcp"),
            }

        @mcp.tool(name=tool)
        def get_product_specs(ürünAdı: str = "aqua_cnt_100") -> str:
            """Urun JSON kilavuzu: modeller, donanim, Modbus TCP ozeti."""
            return guard(tool, _get_product_specs_impl)(ürünAdı)

        tool = prefixed_name(prefix, "get_product_settings")

        def _get_product_settings_impl(ürünAdı: str = "aqua_cnt_100", bölüm: str = "") -> Any:
            data = _load_product_json((ürünAdı or "aqua_cnt_100").replace(".json", ""), cfg)
            if not data:
                return {"hata": f"Ürün bulunamadı: {ürünAdı}"}
            menus = data.get("menüler") or []
            b = (bölüm or "").strip()
            if b:
                filtered = []
                for menu in menus:
                    if not isinstance(menu, dict):
                        continue
                    blob = json.dumps(menu, ensure_ascii=False)
                    if b.lower() in str(menu.get("ad") or "").lower() or b.lower() in blob.lower():
                        filtered.append(menu)
                menus = filtered if filtered else menus
            return {
                "ürün": data.get("ürün_ailesi"),
                "menüler": menus,
                "tuş_kısayolları": data.get("tuş_kısayolları"),
                "led_durumları": data.get("led_durumları"),
            }

        @mcp.tool(name=tool)
        def get_product_settings(ürünAdı: str = "aqua_cnt_100", bölüm: str = "") -> str:
            """Urun ayarlari."""
            return guard(tool, _get_product_settings_impl)(ürünAdı, bölüm)

        tool = prefixed_name(prefix, "get_product_troubleshoot")

        def _get_product_troubleshoot_impl(ürünAdı: str = "aqua_cnt_100", sorunAçıklaması: str = "") -> Any:
            data = _load_product_json((ürünAdı or "aqua_cnt_100").replace(".json", ""), cfg)
            if not data:
                return {"hata": f"Ürün bulunamadı: {ürünAdı}"}
            issues = data.get("sorun_giderme") or []
            st = (sorunAçıklaması or "").strip().lower()
            if st:
                issues = [
                    x
                    for x in issues
                    if isinstance(x, dict)
                    and (st in str(x.get("sorun") or "").lower() or st in str(x.get("çözüm") or "").lower())
                ] or (data.get("sorun_giderme") or [])
            return {
                "ürün": data.get("ürün_ailesi"),
                "sorun_giderme": issues,
                "modem_calisma_durumu_kodlari": data.get("modem_calisma_durumu_kodlari"),
                "üretici_destek": data.get("üretici_destek"),
            }

        @mcp.tool(name=tool)
        def get_product_troubleshoot(ürünAdı: str = "aqua_cnt_100", sorunAçıklaması: str = "") -> str:
            """Urun sorun giderme bilgisi."""
            return guard(tool, _get_product_troubleshoot_impl)(ürünAdı, sorunAçıklaması)

        tool = prefixed_name(prefix, "get_product_sensor_info")

        def _get_product_sensor_info_impl(ürünAdı: str = "aqua_cnt_100") -> Any:
            data = _load_product_json((ürünAdı or "aqua_cnt_100").replace(".json", ""), cfg)
            if not data:
                return {"hata": f"Ürün bulunamadı: {ürünAdı}"}
            return {
                "ürün": data.get("ürün_ailesi"),
                "dahili_debimetre": data.get("dahili_debimetre"),
                "sensörler": data.get("sensörler"),
            }

        @mcp.tool(name=tool)
        def get_product_sensor_info(ürünAdı: str = "aqua_cnt_100") -> str:
            """Urun sensor bilgisi."""
            return guard(tool, _get_product_sensor_info_impl)(ürünAdı)

        # --- Export / rapor (PHP ExportTools ile uyumlu _type:file) ---
        tool = prefixed_name(prefix, "export_log_data")

        def _export_log_data_impl(
            nodeId: int,
            format: str = "xlsx",
            startDate: str = "",
            endDate: str = "",
            logParamIds: str = "",
        ) -> Any:
            return export_log_data_impl(
                cfg, nodeId, format, startDate, endDate, logParamIds
            )

        @mcp.tool(name=tool)
        def export_log_data(
            nodeId: int,
            format: str = "xlsx",
            startDate: str = "",
            endDate: str = "",
            logParamIds: str = "",
        ) -> str:
            """Node log verisini Excel (.xlsx), CSV veya JSON dosyası olarak üretir; sonuçta _type=file ve filepath döner."""
            return guard(tool, _export_log_data_impl)(nodeId, format, startDate, endDate, logParamIds)

        tool = prefixed_name(prefix, "generate_scada_report")

        def _generate_scada_report_impl_wrapped(format: str = "pdf") -> Any:
            return generate_scada_report_impl(cfg, format)

        @mcp.tool(name=tool)
        def generate_scada_report(format: str = "pdf") -> str:
            """SCADA özet raporu PDF veya Word (.docx)."""
            return guard(tool, _generate_scada_report_impl_wrapped)(format)

        tool = prefixed_name(prefix, "generate_node_report")

        def _generate_node_report_impl_wrapped(nodeId: int, format: str = "pdf") -> Any:
            return generate_node_report_impl(cfg, nodeId, format)

        @mcp.tool(name=tool)
        def generate_node_report(nodeId: int, format: str = "pdf") -> str:
            """Tek node için detaylı rapor (PDF veya DOCX): canlı taglar, alarmlar, log parametreleri."""
            return guard(tool, _generate_node_report_impl_wrapped)(nodeId, format)

        tool = prefixed_name(prefix, "export_custom_data")

        def _export_custom_data_impl_wrapped(
            title: str,
            headers: str,
            rowsJson: str = "",
            format: str = "xlsx",
            rows_json: str = "",
        ) -> Any:
            rj = (rowsJson or rows_json or "").strip()
            return export_custom_data_impl(cfg, title, headers, rj, format)

        @mcp.tool(name=tool)
        def export_custom_data(
            title: str,
            headers: str,
            rowsJson: str = "",
            format: str = "xlsx",
            rows_json: str = "",
        ) -> str:
            """Genel amacli tablo export (Excel/CSV/JSON/PDF). headers: virgul ayrili sutun adlari, rowsJson: JSON array."""
            return guard(tool, _export_custom_data_impl_wrapped)(title, headers, rowsJson, format, rows_json)

        tool = prefixed_name(prefix, "export_active_alarms")

        def _export_active_alarms_impl_wrapped(format: str = "xlsx", limit: int = 500) -> Any:
            return export_active_alarms_impl(cfg, format, limit)

        @mcp.tool(name=tool)
        def export_active_alarms(format: str = "xlsx", limit: int = 500) -> str:
            """Aktif alarmları Excel veya CSV dosyası olarak dışa aktarır."""
            return guard(tool, _export_active_alarms_impl_wrapped)(format, limit)


    def manifest_groups(self, *, prefix: str) -> list[dict]:
        p = prefix
        return [
            {
                "id": "kepware_more",
                "title_tr": "Kepware cihaz / sürücü",
                "tools": [
                    p + "list_channel_devices",
                    p + "get_channel_device_detail",
                    p + "get_device_connection_params",
                    p + "list_channel_types",
                    p + "list_device_types",
                    p + "get_device_type_tags",
                    p + "get_device_individual_tags",
                    p + "list_device_status_codes",
                    p + "list_drivers",
                    p + "get_driver_detail",
                    p + "list_service_instances",
                    p + "get_service_activities",
                    p + "get_device_all_tags",
                    p + "get_node_all_tags",
                    p + "get_tag_address",
                ],
            },
            {
                "id": "charts",
                "title_tr": "Grafik (log)",
                "tools": [
                    p + "get_chart_data",
                    p + "get_multi_chart_data",
                    p + "compare_log_metrics",
                    p + "get_node_log_chart_data",
                    p + "get_recent_log_chart_by_tag",
                    p + "analyze_log_trend",
                    p + "list_dma_station_nodes",
                    p + "analyze_dma_seasonal_demand",
                    p + "analyze_seasonal_level_profile",
                ],
            },
            {
                "id": "node_logs",
                "title_tr": "Node log tabloları",
                "tools": [
                    p + "get_node_log_data",
                    p + "get_node_log_summary",
                    p + "get_node_log_latest_values",
                ],
            },
            {
                "id": "products",
                "title_tr": "Ürün kılavuzu (JSON)",
                "tools": [
                    p + "search_product_manual",
                    p + "get_product_specs",
                    p + "get_product_settings",
                    p + "get_product_troubleshoot",
                    p + "get_product_sensor_info",
                ],
            },
            {
                "id": "export_reports",
                "title_tr": "Export / raporlar (Excel PDF CSV)",
                "tools": [
                    p + "export_log_data",
                    p + "generate_scada_report",
                    p + "generate_node_report",
                    p + "export_custom_data",
                    p + "export_active_alarms",
                ],
            },
        ]
