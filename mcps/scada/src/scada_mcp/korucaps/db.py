"""
KoruCAPS WinCAPS Database layer.

Ported from wincapsDb.ts - Grundfos WinCAPS pump selection algorithm.
Uses pymysql with DictCursor, same connection pool as SCADA MCP (scada_mcp.db).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from ..db import connect as db_connect
from ..types import DbConfig

from .polynom_engine import (
    calculate_efficiency,
    evaluate_polynomial,
    extract_stage_count,
    extract_pump_family,
    parse_polynomial,
)
from .pump_service import (
    MOTOR_ETA_STD,
    MOTOR_ETA_SUB,
    calculate_iterative_slip,
    lookup_motor_eta,
)

logger = logging.getLogger("scada_mcp.korucaps.db")

# --- Application to filter table mapping ---
APP_FILTER_MAP: Dict[int, int] = {
    1: 1,  # HEATING -> pumps_filter_XX_1
    2: 2,  # AIRCON -> pumps_filter_XX_2
    3: 3,  # PRESBOOS -> pumps_filter_XX_3
    4: 4,  # GROUNDWA -> pumps_filter_XX_4
    5: 5,  # DOMES -> pumps_filter_XX_5
    6: 6,  # SEWAGE -> pumps_filter_XX_6
    7: 7,  # OTHER -> pumps_filter_XX_7
    9: 9,  # Special
}

# Child application CODE -> column name in the filter table
APP_COLUMN_MAP: Dict[str, str] = {
    # Heating children
    "CIRCHEAT": "CIRCHEAT", "BOILSHUN": "BOILSHUN", "FLOWFILT": "FLOWFILT",
    "COUPHEAT": "COUPHEAT", "HOTWATER": "HOTWATER",
    # Air-conditioning children
    "CIRCAIR": "CIRCAIR", "CHILL": "CHILL", "COOLTOW": "COOLTOW", "COUPBAT": "COUPBAT",
    # Pressure boosting children
    "BOOSSET": "BOOSSET", "BOOSPUMP": "BOOSPUMP",
    # Groundwater children
    "WELLINS": "WELLINS", "HORINS": "HORINS", "SHALLOW": "SHALLOW",
    # Domestic water children
    "WELLINDO": "WELLINDO", "PACBOOS": "PACBOOS", "PUMPSDO": "PUMPSDO",
    # Sewage children
    "PUMPSSEW": "PUMPSSEW", "SYSSEW": "SYSSEW",
    # Other/Industrial children
    "COOLOTH": "COOLOTH", "BOILFOTH": "BOILFOTH", "IMMEROTH": "IMMEROTH",
}


def get_applications(db: DbConfig) -> List[Dict[str, Any]]:
    """Get all application types."""
    with db_connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ID, CODE, NAME, DESCRIPTION, TREEPLACE, HASQC, PGFLAG "
                "FROM application ORDER BY TREEPLACE"
            )
            return cur.fetchall()


def get_pump_families(db: DbConfig, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """List available pump families/product groups with product counts."""
    with db_connect(db) as conn:
        with conn.cursor() as cur:
            query = (
                "SELECT COALESCE(pg.NAME, pg.INTERNALNAME) as name, "
                "COUNT(DISTINCT pn.ProdName) as productCount "
                "FROM pg "
                "JOIN products2 p ON p.Treeplace LIKE CONCAT(pg.TREEPLACE, '%%') "
                "JOIN prodnames pn ON p.ProdNameId = pn.Id "
                "WHERE p.CurveSetId > 0"
            )
            params: List[Any] = []
            if search:
                query += " AND (pg.NAME LIKE %s OR pg.INTERNALNAME LIKE %s)"
                params.extend([f"%{search}%", f"%{search}%"])
            query += " GROUP BY pg.ID, pg.NAME, pg.INTERNALNAME HAVING productCount > 0 ORDER BY name LIMIT 50"
            cur.execute(query, params)
            return cur.fetchall()


def get_product_by_name(db: DbConfig, pump_name: str) -> Optional[Dict[str, Any]]:
    """Get product details by pump name."""
    with db_connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT p.Id, p.ProductNo, p.CurveSetId, p.Freq, p.Treeplace,
                          pn.ProdName, COALESCE(pg.NAME, pg.INTERNALNAME) as GroupName
                   FROM products2 p
                   JOIN prodnames pn ON p.ProdNameId = pn.Id
                   LEFT JOIN pg ON p.Treeplace LIKE CONCAT(pg.TREEPLACE, '%%') AND LENGTH(pg.TREEPLACE) = (
                     SELECT MAX(LENGTH(pg2.TREEPLACE)) FROM pg pg2 WHERE p.Treeplace LIKE CONCAT(pg2.TREEPLACE, '%%')
                   )
                   WHERE pn.ProdName = %s AND p.CurveSetId > 0
                   LIMIT 1""",
                (pump_name,),
            )
            return cur.fetchone()


def get_curve_data(db: DbConfig, curve_set_id: int, freq: int = 50) -> List[Dict[str, Any]]:
    """Get curve data for a given curve set."""
    with db_connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.rpm, c.stages, c.qMin, c.qMax, c.speedNo
                   FROM curveindex2 ci JOIN curve2 c ON ci.curveId = c.curveId
                   WHERE ci.curveSetId = %s AND (c.freq = %s OR c.freq = '0' OR c.freq = 0)
                   ORDER BY c.speedNo DESC LIMIT 2""",
                (curve_set_id, freq),
            )
            return cur.fetchall()


def find_pumps(
    db: DbConfig,
    flow: float,
    head: float,
    freq: str = "50",
    application_id: Optional[int] = None,
    phase: str = "3",
    voltage: Optional[str] = None,
    vfd: bool = False,
    number_of_pumps: int = 1,
    ranking_criteria: str = "energy",
) -> List[Dict[str, Any]]:
    """
    Pump Sizing - Find matching pumps (WinCAPS birebir algorithm).
    This is the full 700+ line algorithm ported exactly from wincapsDb.ts.
    """
    # WinCAPS: paralel pompalarda debi esit bolunur
    effective_flow = flow / number_of_pumps
    freq_prefix = "pumps_filter_50" if freq == "50" else "pumps_filter_60"

    with db_connect(db) as conn:
        # --- Stage 1: Filter tablo secimi (WinCAPS: Pumps_Filter_{freq}_{app}) ---
        filter_configs: List[Dict[str, Optional[str]]] = []

        if application_id and application_id > 0:
            with conn.cursor() as cur:
                cur.execute("SELECT ID, CODE FROM application WHERE ID = %s", (application_id,))
                app = cur.fetchone()
            if not app:
                return []

            with conn.cursor() as cur:
                cur.execute(
                    "SELECT h.ID, a.CODE FROM applhier h JOIN application a ON a.ID = h.ID WHERE h.PARENTID = %s",
                    (application_id,),
                )
                children = cur.fetchall()

            if children:
                filter_num = APP_FILTER_MAP.get(application_id)
                if filter_num:
                    filter_configs.append({"table": f"{freq_prefix}_{filter_num}", "column": None})
            else:
                with conn.cursor() as cur:
                    cur.execute("SELECT PARENTID FROM applhier WHERE ID = %s", (application_id,))
                    parent = cur.fetchone()
                if parent:
                    filter_num = APP_FILTER_MAP.get(parent["PARENTID"])
                    col_name = APP_COLUMN_MAP.get(app["CODE"])
                    if filter_num and col_name:
                        filter_configs.append({"table": f"{freq_prefix}_{filter_num}", "column": col_name})
        else:
            for num in [1, 2, 3, 4, 5, 6, 7]:
                filter_configs.append({"table": f"{freq_prefix}_{num}", "column": None})

        if not filter_configs:
            return []

        # --- Stage 2: Filter tablodan aday pompalari al ---
        all_results: List[Dict[str, Any]] = []
        seen_ids: Set[int] = set()

        for fc in filter_configs:
            try:
                where_extra = ""
                if fc["column"]:
                    where_extra = f" AND pf.{fc['column']} = 1"

                query = f"""SELECT MIN(pf.Id) as Id, MIN(pf.QH) as QH,
                                   MIN(pf.qMin) as qMin, MAX(pf.qMax) as qMax,
                                   MIN(pf.hMin) as hMin, MAX(pf.hMax) as hMax,
                                   MIN(p.ProductNo) as ProductNo,
                                   MAX(p.CurveSetId) as CurveSetId,
                                   MIN(p.Treeplace) as Treeplace,
                                   MIN(p.Freq) as Freq,
                                   pn.ProdName,
                                   MIN(p.ProdNameId) as ProdNameId
                            FROM {fc['table']} pf
                            JOIN products2 p ON pf.Id = p.Id
                            LEFT JOIN prodnames pn ON p.ProdNameId = pn.Id
                            WHERE pf.qMin <= %s AND pf.qMax >= %s AND pf.hMin <= %s AND pf.hMax >= %s
                              {where_extra}
                            GROUP BY pn.ProdName
                            ORDER BY ABS((MIN(pf.qMin) + MAX(pf.qMax))/2 - %s) + ABS((MIN(pf.hMin) + MAX(pf.hMax))/2 - %s) ASC
                            LIMIT 200"""

                with conn.cursor() as cur:
                    cur.execute(query, (effective_flow, effective_flow, head, head, effective_flow, head))
                    rows = cur.fetchall()
                for row in rows:
                    if row["Id"] not in seen_ids:
                        seen_ids.add(row["Id"])
                        all_results.append(row)
            except Exception:
                # Filter tablo yoksa atla
                pass

        if not all_results:
            return []

        # --- Batch curve data lookup ---
        curve_set_ids = list(set(r["CurveSetId"] for r in all_results if r.get("CurveSetId")))
        curve_map: Dict[int, List[Dict[str, Any]]] = {}

        if curve_set_ids:
            batch_size = 100
            for i in range(0, len(curve_set_ids), batch_size):
                batch = curve_set_ids[i : i + batch_size]
                placeholders = ",".join(["%s"] * len(batch))
                with conn.cursor() as cur:
                    cur.execute(
                        f"""SELECT ci.curveSetId, c.curveId, c.freq, c.speedNo, c.stages, c.rpm,
                                   c.qMin, c.qMax, c.P1P2, c.noQH, c.noQP,
                                   ph.polyString AS qhPoly, pp.polyString AS qpPoly
                            FROM curveindex2 ci
                            JOIN curve2 c ON ci.curveId = c.curveId
                            LEFT JOIN polynom ph ON c.noQH = ph.polyId
                            LEFT JOIN polynom pp ON c.noQP = pp.polyId
                            WHERE ci.curveSetId IN ({placeholders})
                              AND (c.freq = %s OR c.freq = '0' OR c.freq = 0)""",
                        (*batch, freq),
                    )
                    for cr in cur.fetchall():
                        csid = cr["curveSetId"]
                        if csid not in curve_map:
                            curve_map[csid] = []
                        curve_map[csid].append(cr)

        # --- Batch motor data lookup for iterative slip ---
        product_ids = [r["Id"] for r in all_results if r.get("Id")]
        motor_data_map: Dict[int, Dict[str, float]] = {}

        if product_ids:
            batch_size = 100
            for i in range(0, len(product_ids), batch_size):
                batch = product_ids[i : i + batch_size]
                placeholders = ",".join(["%s"] * len(batch))
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            f"""SELECT p.Id, p.ProdNameId, ct42.Txt AS motorSpeed, ct44.Txt AS motorP2
                                FROM products2 p
                                LEFT JOIN coltext ct42 ON p.col42 = ct42.Id
                                LEFT JOIN coltext ct44 ON p.col44 = ct44.Id
                                WHERE p.Id IN ({placeholders})""",
                            batch,
                        )
                        motor_rows = cur.fetchall()

                    missing_p2: List[Dict[str, Any]] = []
                    for mr in motor_rows:
                        n_np = float(str(mr["motorSpeed"]).replace(",", ".")) if mr.get("motorSpeed") else 0.0
                        p2_nom = float(str(mr["motorP2"]).replace(",", ".")) if mr.get("motorP2") else 0.0
                        if n_np > 0 and p2_nom > 0:
                            motor_data_map[mr["Id"]] = {"nNameplate": n_np, "p2NomMotor": p2_nom}
                        elif n_np > 0 and mr.get("ProdNameId"):
                            missing_p2.append({"id": mr["Id"], "prodNameId": mr["ProdNameId"], "nNp": n_np})

                    # col44=0 olanlar: ayni ProdName'deki col44>0 olan urunun P2'sini kullan
                    if missing_p2:
                        unique_pn_ids = list(set(m["prodNameId"] for m in missing_p2))
                        try:
                            pn_ph = ",".join(["%s"] * len(unique_pn_ids))
                            with conn.cursor() as cur:
                                cur.execute(
                                    f"""SELECT p.ProdNameId, MIN(CAST(REPLACE(ct.Txt, ',', '.') AS DECIMAL(10,2))) as p2Nom
                                        FROM products2 p JOIN coltext ct ON p.col44 = ct.Id
                                        WHERE p.ProdNameId IN ({pn_ph}) AND p.col44 > 0
                                        GROUP BY p.ProdNameId""",
                                    unique_pn_ids,
                                )
                                fb_rows = cur.fetchall()
                            fb_map: Dict[int, float] = {}
                            for fb in fb_rows:
                                if fb.get("p2Nom") and float(fb["p2Nom"]) > 0:
                                    fb_map[fb["ProdNameId"]] = float(fb["p2Nom"])
                            for missing in missing_p2:
                                p2 = fb_map.get(missing["prodNameId"])
                                if p2:
                                    motor_data_map[missing["id"]] = {"nNameplate": missing["nNp"], "p2NomMotor": p2}
                        except Exception:
                            pass
                except Exception:
                    pass

        # --- Evaluate each pump at the operating point ---
        evaluated_results: List[Dict[str, Any]] = []

        for row in all_results:
            curves = curve_map.get(row["CurveSetId"], [])
            if not curves:
                evaluated_results.append({
                    **row, "hActual": None, "p2Actual": None,
                    "etaPump": None, "etaTotal": None, "p1Actual": None,
                })
                continue

            # --- Curve Selection ---
            speed_nos = set(int(c.get("speedNo", 0)) for c in curves)
            has_sp_tolerance = 237 in speed_nos or 236 in speed_nos
            has_cre_tolerance = any(sn in speed_nos for sn in [109, 110, 111, 112, 113, 114])
            has_208 = 208 in speed_nos
            has_225 = 225 in speed_nos
            has_234 = 234 in speed_nos
            has_sqflex = any(sn >= 1002 and sn <= 1120 for sn in speed_nos)

            primary_curve: Optional[Dict[str, Any]] = None
            tolerance_curve: Optional[Dict[str, Any]] = None
            trim_curve: Optional[Dict[str, Any]] = None
            p1p2_flag = 2

            if has_sp_tolerance:
                c237 = next((c for c in curves if c["speedNo"] == 237), None)
                c236 = next((c for c in curves if c["speedNo"] == 236), None)
                c239 = next((c for c in curves if c["speedNo"] == 239 and (c.get("stages") or 0) >= 65), None)
                c238 = next((c for c in curves if c["speedNo"] == 238 and (c.get("stages") or 0) >= 65), None)

                if c237:
                    primary_curve = c237
                    tolerance_curve = c236 if c236 and c236 is not c237 else None
                    trim_curve = c239 or c238 or None
                elif c239:
                    primary_curve = c239
                    tolerance_curve = c236 or None
                elif c238:
                    primary_curve = c238
                    tolerance_curve = c236 or None
                else:
                    primary_curve = c236
                p1p2_flag = int(primary_curve.get("P1P2") or 2) if primary_curve else 2
            elif has_cre_tolerance:
                primary_curve = (
                    next((c for c in curves if c["speedNo"] == 109), None)
                    or next((c for c in curves if c["speedNo"] == 111), None)
                    or next((c for c in curves if c["speedNo"] == 113), None)
                )
                tolerance_curve = (
                    next((c for c in curves if c["speedNo"] == 110), None)
                    or next((c for c in curves if c["speedNo"] == 112), None)
                    or next((c for c in curves if c["speedNo"] == 114), None)
                )
                p1p2_flag = int(primary_curve.get("P1P2") or 1) if primary_curve else 1
            elif has_208:
                primary_curve = next((c for c in curves if c["speedNo"] == 208), None)
                p1p2_flag = int(primary_curve.get("P1P2") or 2) if primary_curve else 2
            elif has_225:
                primary_curve = next((c for c in curves if c["speedNo"] == 225), None)
                p1p2_flag = int(primary_curve.get("P1P2") or 2) if primary_curve else 2
            elif has_234:
                primary_curve = next((c for c in curves if c["speedNo"] == 234), None)
                p1p2_flag = int(primary_curve.get("P1P2") or 2) if primary_curve else 2
            elif has_sqflex:
                sqf_curves = sorted(
                    [c for c in curves if c["speedNo"] >= 1002],
                    key=lambda c: c["speedNo"],
                    reverse=True,
                )
                primary_curve = sqf_curves[0] if sqf_curves else (curves[0] if curves else None)
                p1p2_flag = int(primary_curve.get("P1P2") or 9) if primary_curve else 9
            else:
                primary_curve = next((c for c in curves if c["speedNo"] == 1), None) or (curves[0] if curves else None)
                p1p2_flag = int(primary_curve.get("P1P2") or 2) if primary_curve else 2

            if not primary_curve or not primary_curve.get("qhPoly"):
                evaluated_results.append({
                    **row, "hActual": None, "p2Actual": None,
                    "etaPump": None, "etaTotal": None, "p1Actual": None, "qActual": None,
                })
                continue

            qh_poly = parse_polynomial(primary_curve["qhPoly"])
            qp_poly = parse_polynomial(primary_curve["qpPoly"]) if primary_curve.get("qpPoly") else None
            if not qh_poly:
                evaluated_results.append({
                    **row, "hActual": None, "p2Actual": None,
                    "etaPump": None, "etaTotal": None, "p1Actual": None, "qActual": None,
                })
                continue

            # Tolerans polinomlari
            tol_qh_poly = parse_polynomial(tolerance_curve["qhPoly"]) if tolerance_curve and tolerance_curve.get("qhPoly") else None
            tol_qp_poly = parse_polynomial(tolerance_curve["qpPoly"]) if tolerance_curve and tolerance_curve.get("qpPoly") else None
            has_tolerance = tol_qh_poly is not None

            # Trim curve (SP -A/-AA only)
            trim_qh_poly = parse_polynomial(trim_curve["qhPoly"]) if trim_curve and trim_curve.get("qhPoly") else None
            has_trim = trim_qh_poly is not None

            # Stage multiplier
            prod_name = row.get("ProdName") or ""
            actual_stages = extract_stage_count(prod_name)
            db_stages = primary_curve.get("stages") or 0
            is_per_stage = db_stages <= 1 or db_stages >= 65
            stage_multiplier = actual_stages if (actual_stages > 1 and is_per_stage) else 1

            # Motor slip - iterative calculation (WinCAPS DLL: 5 iterations)
            n_sync = primary_curve.get("rpm") or 3000
            motor_data = motor_data_map.get(row["Id"])
            n_nameplate = (motor_data["nNameplate"] if motor_data else None) or (2900 if n_sync == 3000 else n_sync * 0.967)
            p2_nom_motor = (motor_data["p2NomMotor"] if motor_data else None) or 0.0
            r_slip = n_nameplate / n_sync if n_nameplate < n_sync else 1.0

            # --- BLENDED H: WinCAPS DLL algorithm (r parametric) ---
            def eval_blended_h_at_q_with_r(q: float, r: float) -> Optional[float]:
                qs = q / r
                h = evaluate_polynomial(qh_poly, qs)
                if h is None:
                    return None
                if has_trim:
                    trim_h = evaluate_polynomial(trim_qh_poly, qs)
                    if trim_h is not None:
                        h = (h + trim_h) * 0.5
                    if has_tolerance:
                        th = evaluate_polynomial(tol_qh_poly, qs)
                        if th is not None:
                            h = h * 0.8 + th * 0.2
                elif has_tolerance:
                    th = evaluate_polynomial(tol_qh_poly, qs)
                    if th is not None:
                        h = h * 0.8 + th * 0.2
                return h * stage_multiplier * r * r

            def eval_blended_h_at_q(q: float) -> Optional[float]:
                return eval_blended_h_at_q_with_r(q, r_slip)

            # --- Binary search - filter table bounds + convergence check ---
            q_min_search = row.get("qMin") or primary_curve["qMin"] * r_slip
            q_max_search = row.get("qMax") or primary_curve["qMax"] * r_slip
            h_at_min = eval_blended_h_at_q(q_min_search)
            h_at_max = eval_blended_h_at_q(q_max_search)

            if h_at_min is None or h_at_max is None:
                evaluated_results.append({
                    **row, "hActual": None, "p2Actual": None,
                    "etaPump": None, "etaTotal": None, "p1Actual": None, "qActual": None,
                })
                continue

            # Pump max head (H at qMin) less than target H -> pump insufficient
            if head > h_at_min * 1.05:
                continue

            lo, hi = q_min_search, q_max_search
            actual_flow = effective_flow
            converged = False
            for _ in range(60):
                mid = (lo + hi) / 2.0
                h_mid = eval_blended_h_at_q(mid)
                if h_mid is None:
                    break
                if abs(h_mid - head) < 0.1:
                    actual_flow = mid
                    converged = True
                    break
                if h_mid > head:
                    lo = mid
                else:
                    hi = mid
                actual_flow = mid

            if not converged:
                continue

            # --- Iterative motor slip (WinCAPS DLL: 5 iterations) ---
            if p2_nom_motor > 0 and n_nameplate < n_sync:
                s_nominal = (n_sync - n_nameplate) / n_sync
                q_sync_iter = actual_flow / r_slip
                p_per_stage = evaluate_polynomial(qp_poly, q_sync_iter) if qp_poly else None
                if p_per_stage is not None:
                    p2_at_sync = p_per_stage * stage_multiplier
                    slip = s_nominal
                    for _ in range(5):
                        r = 1.0 - slip
                        p2_actual_val = p2_at_sync * r * r * r
                        slip = s_nominal * (p2_actual_val / p2_nom_motor)
                    new_r = 1.0 - slip
                    if abs(new_r - r_slip) > 0.0001:
                        r_slip = new_r
                        # Re-run binary search with new r
                        lo = primary_curve["qMin"] * r_slip
                        hi = primary_curve["qMax"] * r_slip
                        converged = False
                        for _ in range(60):
                            mid = (lo + hi) / 2.0
                            h_mid = eval_blended_h_at_q_with_r(mid, r_slip)
                            if h_mid is None:
                                break
                            if abs(h_mid - head) < 0.1:
                                actual_flow = mid
                                converged = True
                                break
                            if h_mid > head:
                                lo = mid
                            else:
                                hi = mid
                            actual_flow = mid
                        if not converged:
                            continue

            # --- NOMINAL values at operating point (for eta calculation) ---
            q_sync = actual_flow / r_slip
            nom_h = evaluate_polynomial(qh_poly, q_sync)
            nom_p = evaluate_polynomial(qp_poly, q_sync) if qp_poly else None
            if nom_h is None:
                evaluated_results.append({
                    **row, "hActual": None, "p2Actual": None,
                    "etaPump": None, "etaTotal": None, "p1Actual": None, "qActual": None,
                })
                continue

            h_nom = nom_h * stage_multiplier * r_slip * r_slip
            p_nom = nom_p * stage_multiplier * r_slip * r_slip * r_slip if nom_p is not None else None

            # --- BLENDED P: same logic (trim: blend+tolerance, else tolerance only) ---
            display_power = nom_p
            if has_trim and trim_curve and trim_curve.get("qpPoly"):
                trim_qp_poly2 = parse_polynomial(trim_curve["qpPoly"])
                if trim_qp_poly2 and display_power is not None:
                    trim_p = evaluate_polynomial(trim_qp_poly2, q_sync)
                    if trim_p is not None:
                        display_power = (display_power + trim_p) * 0.5
                if has_tolerance and tol_qp_poly and display_power is not None:
                    tol_p = evaluate_polynomial(tol_qp_poly, q_sync)
                    if tol_p is not None:
                        display_power = display_power * 0.8 + tol_p * 0.2
            elif has_tolerance and tol_qp_poly:
                if display_power is not None:
                    tol_p = evaluate_polynomial(tol_qp_poly, q_sync)
                    if tol_p is not None:
                        display_power = display_power * 0.8 + tol_p * 0.2

            p_display = display_power * stage_multiplier * r_slip * r_slip * r_slip if display_power is not None else None
            h_actual = round(head * 10) / 10
            n_actual = round(n_sync * r_slip)

            # --- Oversizing + Motor power checks (WinCAPS DLL) ---
            if actual_flow < effective_flow:
                continue
            if actual_flow > effective_flow * 1.5:
                continue

            actual_power_for_motor_test = p_display if p_display is not None else (p_nom or 0)
            if p2_nom_motor > 0 and actual_power_for_motor_test > p2_nom_motor * 1.15:
                continue
            if vfd and p2_nom_motor > 0 and p2_nom_motor < 0.37:
                continue

            # --- eta calculation: BLENDED (display) values (WinCAPS DLL verified) ---
            h_for_eta = h_actual if p_display is not None else 0
            eta_pump = 0.0
            motor_eff = 0.78
            p1_actual: Optional[float] = None
            p2_actual = p_display

            is_submersible = bool(re.match(r"^(SP |SQ |BM |7S|MS )", prod_name))
            eta_table = MOTOR_ETA_SUB if is_submersible else MOTOR_ETA_STD

            if p1p2_flag == 1:
                # P1P2=1: Polynomial gives P1 -> CRE, CRNE, TPE, CHIE, ALPHA, MAGNA
                p1_actual = p_display
                eta_total_direct = (
                    calculate_efficiency(actual_flow, head, p_display)
                    if p_display and p_display > 0 and head > 0
                    else 0.0
                )
                p2_nom_lookup = p2_nom_motor if p2_nom_motor > 0 else (p_display * 0.85 if p_display else 0)
                motor_eff = lookup_motor_eta(p2_nom_lookup, eta_table) if p2_nom_lookup > 0 else 0.85
                eta_pump = eta_total_direct / motor_eff if motor_eff > 0 else eta_total_direct
                p2_actual = p1_actual * motor_eff if p1_actual and motor_eff > 0 else p1_actual
            else:
                # P1P2=2: Polynomial gives P2 -> SP, CR, TP, NB, CV, CPV, NK
                eta_pump = (
                    calculate_efficiency(actual_flow, head, p_display)
                    if p_display and p_display > 0 and head > 0
                    else 0.0
                )
                p2_actual = p_display
                p2_nom_lookup = p2_nom_motor if p2_nom_motor > 0 else (p2_actual or 0)
                motor_eff = lookup_motor_eta(p2_nom_lookup, eta_table) if p2_nom_lookup > 0 else 0.78
                p1_actual = p2_actual / motor_eff if p2_actual and motor_eff > 0 else None

            eta_total = (eta_pump / 100.0) * motor_eff * 100.0 if eta_pump > 0 else 0.0

            # Es (specific energy) and annual energy consumption
            es = round((p1_actual / actual_flow) * 10000) / 10000 if p1_actual and actual_flow > 0 else None
            energy_kwh = round(p1_actual * 3650) if p1_actual else None

            evaluated_results.append({
                **row,
                "qActual": round(actual_flow * number_of_pumps),
                "qPerPump": round(actual_flow),
                "hActual": round(h_actual * 10) / 10,
                "p2Actual": round(p2_actual * 100) / 100 if p2_actual is not None else None,
                "p1Actual": round(p1_actual * 100) / 100 if p1_actual is not None else None,
                "etaPump": round(eta_pump * 10) / 10,
                "etaTotal": round(eta_total * 10) / 10,
                "nActual": n_actual,
                "Es": es,
                "energyKwh": energy_kwh * number_of_pumps if energy_kwh else None,
                "stages": actual_stages,
                "numberOfPumps": number_of_pumps,
            })

        # --- Treeplace (PGTP) based dedup + ENERGY sorting (WinCAPS birebir) ---
        # Step 1: Group by ProdName, select lowest ENERGY variant
        name_map: Dict[str, Dict[str, Any]] = {}
        for r in evaluated_results:
            if r.get("qActual") is None or r.get("energyKwh") is None:
                continue
            name = r.get("ProdName") or f"#{r['Id']}"
            existing = name_map.get(name)
            if not existing or (r.get("energyKwh") or 999999) < (existing.get("energyKwh") or 999999):
                name_map[name] = r

        # Step 2: Group by Treeplace (PGTP), select lowest ENERGY pump
        pgtp_map: Dict[str, List[Dict[str, Any]]] = {}
        for r in name_map.values():
            pgtp = r.get("Treeplace") or "unknown"
            if pgtp not in pgtp_map:
                pgtp_map[pgtp] = []
            pgtp_map[pgtp].append(r)

        pgtp_best: List[Dict[str, Any]] = []
        for candidates in pgtp_map.values():
            candidates.sort(key=lambda a: a.get("energyKwh") or 999999)
            pgtp_best.append(candidates[0])

        # --- Stage 4: Sort by ENERGY (WinCAPS "Enerji sarfiyati") ---
        def energy_sort_key(a: Dict[str, Any]) -> Tuple[int, float]:
            e = a.get("energyKwh")
            if e is not None:
                return (0, e)
            return (1, 0.0)

        pgtp_best.sort(key=energy_sort_key)

        return pgtp_best[:50]
