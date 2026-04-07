"""
KoruCAPS MCP + UI: WinCAPS MySQL pump curve and operating point evaluation.

Algorithm source: xkgpi32.dll reverse engineering (WinCAPS 7.52)
- Efficiency (eta): BLENDED (display) values (tolerance-mixed H and P2)
- Motor slip: Iterative calculation (5 iterations), P2_nominal motor and n_plate from DB
- Gravity constant: g = 9.80665 m/s2 (DLL offset 0x1007a868)
- Density: rho = 998.2 kg/m3 (20C water, WinCAPS Curve Settings default)
- Tolerance blend (SP): 80% nominal + 20% minimum -> only for H and P2 DISPLAY values
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from .polynom_engine import (
    ParsedPolynomial,
    calculate_efficiency,
    evaluate_polynomial,
    extract_stage_count,
    parse_polynomial,
)

# --- Motor Efficiency Tables (xkgpi32.dll offset 0x7BEA0 / 0x7C1B8) ---
MOTOR_ETA_STD: List[Tuple[float, float]] = [
    (0.25, 0.65), (0.37, 0.67), (0.55, 0.71), (0.75, 0.73), (1.1, 0.77),
    (1.5, 0.78), (2.2, 0.80), (3, 0.82), (4, 0.85), (5.5, 0.86),
    (7.5, 0.87), (11, 0.88), (15, 0.89), (18.5, 0.89), (22, 0.90),
    (26, 0.90), (30, 0.91), (37, 0.92), (45, 0.92), (55, 0.93),
    (75, 0.93), (90, 0.94), (110, 0.95), (132, 0.95), (160, 0.95),
    (200, 0.95), (250, 0.95), (315, 0.96), (355, 0.96), (400, 0.96),
    (500, 0.97), (630, 0.97),
]

MOTOR_ETA_SUB: List[Tuple[float, float]] = [
    (0.25, 0.56), (0.37, 0.60), (0.55, 0.63), (0.75, 0.70), (1.1, 0.70),
    (1.5, 0.71), (2.2, 0.73), (3, 0.75), (4, 0.76), (5.5, 0.76),
    (7.5, 0.78), (11, 0.80), (15, 0.80), (18.5, 0.80), (22, 0.81),
    (26, 0.81), (30, 0.82), (37, 0.83), (45, 0.85), (55, 0.86),
    (75, 0.86), (90, 0.86), (110, 0.86), (132, 0.86), (160, 0.86),
    (200, 0.86), (250, 0.86), (315, 0.86), (355, 0.86),
]


def lookup_motor_eta(p2kw: float, table: List[Tuple[float, float]]) -> float:
    """Interpolate motor efficiency from lookup table."""
    if p2kw <= table[0][0]:
        return table[0][1]
    if p2kw >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        if p2kw >= table[i][0] and p2kw <= table[i + 1][0]:
            t = (p2kw - table[i][0]) / (table[i + 1][0] - table[i][0])
            return table[i][1] + t * (table[i + 1][1] - table[i][1])
    return 0.78


def _get_motor_data(conn: Any, product_id: int) -> Optional[Dict[str, float]]:
    """Fetch motor nameplate data (col42/col44 -> coltext)."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT p.col42, p.col44,
                          ct42.Txt AS motorSpeed, ct44.Txt AS motorP2
                   FROM products2 p
                   LEFT JOIN coltext ct42 ON p.col42 = ct42.Id
                   LEFT JOIN coltext ct44 ON p.col44 = ct44.Id
                   WHERE p.Id = %s""",
                (product_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            n_nameplate = float(row["motorSpeed"].replace(",", ".")) if row.get("motorSpeed") else 0.0
            p2_nom_motor = float(row["motorP2"].replace(",", ".")) if row.get("motorP2") else 0.0
            if n_nameplate > 0 and p2_nom_motor > 0:
                return {"nNameplate": n_nameplate, "p2NomMotor": p2_nom_motor}
            return None
    except Exception:
        return None


def calculate_iterative_slip(
    p2_actual: float,
    p2_nom_motor: float,
    n_sync: float,
    n_nameplate: float,
    iterations: int = 5,
) -> float:
    """
    Iterative motor slip calculation (xkgpi32.dll algorithm).
    Returns r (speed ratio = 1 - slip).
    """
    s_nominal = (n_sync - n_nameplate) / n_sync
    slip = s_nominal
    for _ in range(iterations):
        r = 1.0 - slip
        p2_at_speed = p2_actual * r * r * r
        slip = s_nominal * (p2_at_speed / p2_nom_motor)
    return 1.0 - slip  # return r (speed ratio)


def _select_curves(curves: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    General curve selection algorithm - handles all pump types.
    Returns dict with 'primary', 'tolerance', 'trim' curves.
    """
    speed_nos = set(int(c.get("speedNo", 0)) for c in curves)
    has_sp_tolerance = 237 in speed_nos or 236 in speed_nos
    has_cre_tolerance = any(sn in speed_nos for sn in [109, 110, 111, 112, 113, 114])
    has_208 = 208 in speed_nos
    has_225 = 225 in speed_nos
    has_234 = 234 in speed_nos

    primary = None
    tolerance = None
    trim = None

    if has_sp_tolerance:
        c237 = next((c for c in curves if c["speedNo"] == 237), None)
        c236 = next((c for c in curves if c["speedNo"] == 236), None)
        c239 = next((c for c in curves if c["speedNo"] == 239 and (c.get("stages") or 0) >= 65), None)
        c238 = next((c for c in curves if c["speedNo"] == 238 and (c.get("stages") or 0) >= 65), None)

        if c237:
            primary = c237
            tolerance = c236 if c236 and c236 is not c237 else None
            trim = c239 or c238 or None
        elif c239:
            primary = c239
            tolerance = c236 or None
        elif c238:
            primary = c238
            tolerance = c236 or None
        else:
            primary = c236
    elif has_cre_tolerance:
        primary = (
            next((c for c in curves if c["speedNo"] == 109), None)
            or next((c for c in curves if c["speedNo"] == 111), None)
            or next((c for c in curves if c["speedNo"] == 113), None)
        )
        tolerance = (
            next((c for c in curves if c["speedNo"] == 110), None)
            or next((c for c in curves if c["speedNo"] == 112), None)
            or next((c for c in curves if c["speedNo"] == 114), None)
        )
    elif has_208:
        primary = next((c for c in curves if c["speedNo"] == 208), None)
    elif has_225:
        primary = next((c for c in curves if c["speedNo"] == 225), None)
    elif has_234:
        primary = next((c for c in curves if c["speedNo"] == 234), None)
    else:
        primary = next((c for c in curves if c["speedNo"] == 1), None) or (curves[0] if curves else None)

    return {"primary": primary, "tolerance": tolerance, "trim": trim}


def evaluate_pump_at_point(
    prod_name: str,
    curve_set_id: int,
    flow: float,
    conn: Any,
    freq: int = 50,
    target_head: Optional[float] = None,
    product_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Single pump + curve set operating point calculation.
    WinCAPS exact algorithm:
    1. Tolerance blend (80/20) for Q calculation (sizing)
    2. H and P2 display values are tolerance-blended
    3. eta calculated from NOMINAL curve only
    4. Motor slip iterative (from DB col42/col44)
    """
    with conn.cursor() as cur:
        cur.execute(
            """SELECT c.curveId, c.speedNo, c.stages, c.rpm, c.qMin, c.qMax, c.P1P2,
                      ph.polyString AS qhPoly, pp.polyString AS qpPoly, pn.polyString AS qnpshPoly
               FROM curveindex2 ci
               JOIN curve2 c ON ci.curveId = c.curveId
               LEFT JOIN polynom ph ON c.noQH = ph.polyId
               LEFT JOIN polynom pp ON c.noQP = pp.polyId
               LEFT JOIN polynom pn ON c.noQNPSH = pn.polyId
               WHERE ci.curveSetId = %s AND (c.freq = %s OR c.freq = '0' OR c.freq = 0)""",
            (curve_set_id, freq),
        )
        curves = cur.fetchall()

    if not curves:
        return None

    sel = _select_curves(curves)
    primary_curve = sel["primary"]
    tolerance_curve = sel["tolerance"]
    trim_curve = sel["trim"]

    if not primary_curve or not primary_curve.get("qhPoly"):
        return None

    p1p2_flag = int(primary_curve.get("P1P2") or 2)

    # --- Polynomial parse ---
    qh_poly = parse_polynomial(primary_curve["qhPoly"])
    qp_poly = parse_polynomial(primary_curve.get("qpPoly")) if primary_curve.get("qpPoly") else None
    qnpsh_poly = parse_polynomial(primary_curve.get("qnpshPoly")) if primary_curve.get("qnpshPoly") else None
    if qh_poly is None:
        return None

    # Tolerance and trim polynomials
    tol_qh_poly = parse_polynomial(tolerance_curve["qhPoly"]) if tolerance_curve and tolerance_curve.get("qhPoly") else None
    tol_qp_poly = parse_polynomial(tolerance_curve["qpPoly"]) if tolerance_curve and tolerance_curve.get("qpPoly") else None
    trim_qh_poly = parse_polynomial(trim_curve["qhPoly"]) if trim_curve and trim_curve.get("qhPoly") else None
    trim_qp_poly = parse_polynomial(trim_curve["qpPoly"]) if trim_curve and trim_curve.get("qpPoly") else None
    has_trim = trim_qh_poly is not None

    # --- Stage multiplier ---
    actual_stages = extract_stage_count(prod_name)
    db_stages = primary_curve.get("stages") or 0
    is_per_stage = db_stages <= 1 or db_stages >= 65
    stage_mul = actual_stages if (actual_stages > 1 and is_per_stage) else 1

    # --- Motor slip (from DB or fallback) ---
    n_sync = primary_curve.get("rpm") or 3000
    motor_data = _get_motor_data(conn, product_id) if product_id else None
    n_nameplate = (motor_data["nNameplate"] if motor_data else None) or (2900 if n_sync == 3000 else n_sync * 0.967)
    p2_nom_motor = (motor_data["p2NomMotor"] if motor_data else None) or 0.0

    r_slip = n_nameplate / n_sync if n_nameplate < n_sync else 1.0

    # --- BLENDED H calculation ---
    def eval_blended_h_at_q(q: float, r: float) -> Optional[float]:
        qs = q / r
        h = evaluate_polynomial(qh_poly, qs)
        if h is None:
            return None
        if has_trim:
            th = evaluate_polynomial(trim_qh_poly, qs)
            if th is not None:
                h = (h + th) * 0.5
            if tol_qh_poly:
                mh = evaluate_polynomial(tol_qh_poly, qs)
                if mh is not None:
                    h = h * 0.8 + mh * 0.2
        elif tol_qh_poly:
            th = evaluate_polynomial(tol_qh_poly, qs)
            if th is not None:
                h = h * 0.8 + th * 0.2
        return h * stage_mul * r * r

    # --- Binary search: if targetHead given, find Q ---
    actual_flow = flow
    if target_head is not None and target_head > 0:
        q_min_actual = primary_curve["qMin"] * r_slip
        q_max_actual = primary_curve["qMax"] * r_slip
        h_at_min = eval_blended_h_at_q(q_min_actual, r_slip)
        if h_at_min is None:
            return None
        if target_head > h_at_min * 1.05:
            return None

        lo, hi = q_min_actual, q_max_actual
        for _ in range(50):
            mid = (lo + hi) / 2.0
            h_mid = eval_blended_h_at_q(mid, r_slip)
            if h_mid is None:
                break
            if abs(h_mid - target_head) < 0.01:
                actual_flow = mid
                break
            if h_mid > target_head:
                lo = mid
            else:
                hi = mid
            actual_flow = mid

    # --- Nominal values (for eta calculation) ---
    q_sync = actual_flow / r_slip
    nom_head_per_stage = evaluate_polynomial(qh_poly, q_sync)
    nom_power_per_stage = evaluate_polynomial(qp_poly, q_sync) if qp_poly else None
    npsh = evaluate_polynomial(qnpsh_poly, q_sync) if qnpsh_poly else None

    if nom_head_per_stage is None:
        return None

    # --- Iterative motor slip (P2_nom_motor from DB if available) ---
    if p2_nom_motor > 0 and nom_power_per_stage is not None and nom_power_per_stage > 0:
        new_r = calculate_iterative_slip(
            nom_power_per_stage * stage_mul,
            p2_nom_motor,
            n_sync,
            n_nameplate,
            5,
        )
        if abs(new_r - r_slip) > 0.0001:
            r_slip = new_r
            # Recalculate with new r_slip
            if target_head is not None and target_head > 0:
                q_min_actual = primary_curve["qMin"] * r_slip
                q_max_actual = primary_curve["qMax"] * r_slip
                lo, hi = q_min_actual, q_max_actual
                for _ in range(50):
                    mid = (lo + hi) / 2.0
                    h_mid = eval_blended_h_at_q(mid, r_slip)
                    if h_mid is None:
                        break
                    if abs(h_mid - target_head) < 0.01:
                        actual_flow = mid
                        break
                    if h_mid > target_head:
                        lo = mid
                    else:
                        hi = mid
                    actual_flow = mid

    # --- Final calculation (with updated r_slip) ---
    q_sync_final = actual_flow / r_slip
    final_nom_h = evaluate_polynomial(qh_poly, q_sync_final)
    final_nom_p = evaluate_polynomial(qp_poly, q_sync_final) if qp_poly else None
    final_npsh = evaluate_polynomial(qnpsh_poly, q_sync_final) if qnpsh_poly else None

    if final_nom_h is None:
        return None

    # BLENDED display values: trim -> blend+tolerance, else tolerance only
    h_blend = final_nom_h
    p_blend = final_nom_p

    if has_trim:
        trim_h = evaluate_polynomial(trim_qh_poly, q_sync_final)
        trim_p = evaluate_polynomial(trim_qp_poly, q_sync_final) if trim_qp_poly else None
        if trim_h is not None:
            h_blend = (final_nom_h + trim_h) * 0.5
        if trim_p is not None and p_blend is not None:
            p_blend = (p_blend + trim_p) * 0.5
        # Then apply tolerance
        if tol_qh_poly:
            mh = evaluate_polynomial(tol_qh_poly, q_sync_final)
            if mh is not None:
                h_blend = h_blend * 0.8 + mh * 0.2
        if tol_qp_poly and p_blend is not None:
            mp = evaluate_polynomial(tol_qp_poly, q_sync_final)
            if mp is not None:
                p_blend = p_blend * 0.8 + mp * 0.2
    else:
        if tol_qh_poly:
            th = evaluate_polynomial(tol_qh_poly, q_sync_final)
            if th is not None:
                h_blend = final_nom_h * 0.8 + th * 0.2
        if tol_qp_poly and p_blend is not None:
            tp = evaluate_polynomial(tol_qp_poly, q_sync_final)
            if tp is not None:
                p_blend = final_nom_p * 0.8 + tp * 0.2

    h_final_display = h_blend * stage_mul * r_slip * r_slip
    p2_final_display = p_blend * stage_mul * r_slip * r_slip * r_slip if p_blend is not None else None

    n_actual = round(n_sync * r_slip)

    # --- eta calculation: BLENDED (display) values (WinCAPS DLL verified) ---
    is_submersible = bool(re.match(r"^(SP |SQ |BM |7S|MS )", prod_name))
    motor_eta_table = MOTOR_ETA_SUB if is_submersible else MOTOR_ETA_STD
    eta_pump = 0.0
    motor_eff = 0.78
    p1: Optional[float] = None

    if p1p2_flag == 1:
        # P1P2=1: Polynomial gives P1
        eta_total_direct = (
            calculate_efficiency(actual_flow, h_final_display, p2_final_display)
            if p2_final_display and p2_final_display > 0 and h_final_display > 0
            else 0.0
        )
        p1 = p2_final_display
        p2_nom_lookup = p2_nom_motor if p2_nom_motor > 0 else (p2_final_display * 0.85 if p2_final_display else 0)
        motor_eff = lookup_motor_eta(p2_nom_lookup, motor_eta_table) if p2_nom_lookup > 0 else 0.85
        eta_pump = eta_total_direct / motor_eff if motor_eff > 0 else eta_total_direct
    else:
        # P1P2=2: Polynomial gives P2 -> eta from BLENDED display
        eta_pump = (
            calculate_efficiency(actual_flow, h_final_display, p2_final_display)
            if p2_final_display and p2_final_display > 0 and h_final_display > 0
            else 0.0
        )
        p2_for_motor_lookup = p2_nom_motor if p2_nom_motor > 0 else (p2_final_display or 0)
        motor_eff = lookup_motor_eta(p2_for_motor_lookup, motor_eta_table) if p2_for_motor_lookup > 0 else 0.78
        p1 = p2_final_display / motor_eff if p2_final_display and motor_eff > 0 else None

    eta_total = (eta_pump / 100.0) * motor_eff * 100.0 if eta_pump > 0 else 0.0
    es = p1 / actual_flow if p1 and actual_flow > 0 else None

    return {
        "pumpName": prod_name,
        "flow": round(actual_flow * 100) / 100,
        "head": round(h_final_display * 10) / 10,
        "P2_kW": round(p2_final_display * 100) / 100 if p2_final_display is not None else None,
        "P1_kW": round(p1 * 100) / 100 if p1 is not None else None,
        "etaPump": round(eta_pump * 10) / 10,
        "etaTotal": round(eta_total * 10) / 10,
        "rpm": n_actual,
        "stages": actual_stages,
        "NPSH_m": round(final_npsh * 100) / 100 if final_npsh is not None else None,
        "Es_kWhPerM3": round(es * 10000) / 10000 if es is not None else None,
        "qMin": primary_curve["qMin"],
        "qMax": primary_curve["qMax"],
        "frequency_Hz": freq,
    }


def get_pump_curve_dataset(
    pump_name: str,
    num_points: int,
    include_vfd: bool,
    conn: Any,
) -> Dict[str, Any]:
    """Chart + MCP markdown table for a pump's full curve data."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT p.Id, p.CurveSetId, pn.ProdName, p.col42, p.col44
               FROM products2 p JOIN prodnames pn ON p.ProdNameId = pn.Id
               WHERE pn.ProdName = %s AND p.CurveSetId > 0 LIMIT 1""",
            (pump_name,),
        )
        prod = cur.fetchone()

    if not prod:
        return {"error": f'Pump "{pump_name}" not found.'}

    # Motor data (col42 -> nameplate RPM, col44 -> P2 nominal)
    motor_n_nameplate = 0.0
    motor_p2_nom = 0.0
    if prod.get("col42") or prod.get("col44"):
        motor_data = _get_motor_data(conn, prod["Id"])
        if motor_data:
            motor_n_nameplate = motor_data["nNameplate"]
            motor_p2_nom = motor_data["p2NomMotor"]

    with conn.cursor() as cur:
        cur.execute(
            """SELECT c.speedNo, c.stages, c.rpm, c.qMin, c.qMax, c.P1P2,
                      ph.polyString AS qhPoly, pp.polyString AS qpPoly, pn.polyString AS qnpshPoly
               FROM curveindex2 ci JOIN curve2 c ON ci.curveId = c.curveId
               LEFT JOIN polynom ph ON c.noQH = ph.polyId
               LEFT JOIN polynom pp ON c.noQP = pp.polyId
               LEFT JOIN polynom pn ON c.noQNPSH = pn.polyId
               WHERE ci.curveSetId = %s AND (c.freq = 50 OR c.freq = '0' OR c.freq = 0)
               ORDER BY c.speedNo DESC""",
            (prod["CurveSetId"],),
        )
        curves = cur.fetchall()

    if not curves:
        return {"error": f'No curve data for "{pump_name}".'}

    sel = _select_curves(curves)
    primary = sel["primary"]
    tolerance = sel["tolerance"]

    if not primary:
        return {"error": f'Invalid curve data for "{pump_name}".'}

    qh_poly = parse_polynomial(primary.get("qhPoly"))
    qp_poly = parse_polynomial(primary.get("qpPoly")) if primary.get("qpPoly") else None
    qnpsh_poly = parse_polynomial(primary.get("qnpshPoly")) if primary.get("qnpshPoly") else None
    if qh_poly is None:
        return {"error": f'Invalid curve data for "{pump_name}".'}

    # Tolerance polynomials
    tol_qh_poly = parse_polynomial(tolerance["qhPoly"]) if tolerance and tolerance.get("qhPoly") else None
    tol_qp_poly = parse_polynomial(tolerance["qpPoly"]) if tolerance and tolerance.get("qpPoly") else None

    stage_match = re.search(r"[- ](\d+)$", pump_name)
    stages = int(stage_match.group(1)) if stage_match else 1
    stage_mul = stages if stages > 1 and (primary.get("stages") or 0) == 1 else 1
    n_sync = primary.get("rpm") or 3000

    # Motor slip
    n_np = motor_n_nameplate or (2900 if n_sync == 3000 else n_sync * 0.967)
    r_slip = n_np / n_sync if n_np < n_sync else 1.0

    n = max(5, min(50, num_points))
    step = (primary["qMax"] - primary["qMin"]) / (n - 1)
    md_lines: List[str] = []
    points: List[Dict[str, Any]] = []

    if include_vfd:
        header = "| Q (m3/h) | H (m) | P2 (kW) | eta (%) | NPSH (m) | H@20Hz | H@30Hz | H@40Hz |"
        sep = "|----------|-------|---------|-------|----------|--------|--------|--------|"
    else:
        header = "| Q (m3/h) | H (m) | P2 (kW) | eta (%) | NPSH (m) |"
        sep = "|----------|-------|---------|-------|----------|"
    md_lines.append(header)
    md_lines.append(sep)

    vfd_ratios = [0.4, 0.6, 0.8] if include_vfd else []
    vfd_hz = [20, 30, 40] if include_vfd else []

    for i in range(n):
        q_sync = primary["qMin"] + step * i

        # NOMINAL values
        h_nom = evaluate_polynomial(qh_poly, q_sync)
        p_nom = evaluate_polynomial(qp_poly, q_sync) if qp_poly else None
        npsh_val = evaluate_polynomial(qnpsh_poly, q_sync) if qnpsh_poly else None
        if h_nom is None:
            continue

        # Tolerance-blended DISPLAY values
        h_display = h_nom
        p_display = p_nom
        if tol_qh_poly:
            th = evaluate_polynomial(tol_qh_poly, q_sync)
            if th is not None:
                h_display = h_nom * 0.8 + th * 0.2
        if tol_qp_poly and p_nom is not None:
            tp = evaluate_polynomial(tol_qp_poly, q_sync)
            if tp is not None:
                p_display = p_nom * 0.8 + tp * 0.2

        Q = round(q_sync * r_slip * 100) / 100
        H = round(h_display * stage_mul * r_slip * r_slip * 10) / 10
        P2 = round(p_display * stage_mul * r_slip * r_slip * r_slip * 100) / 100 if p_display is not None else 0
        eta = round(calculate_efficiency(Q, H, P2) * 10) / 10 if P2 > 0 and H > 0 else 0
        NPSH = round(npsh_val * 100) / 100 if npsh_val is not None else None

        pt: Dict[str, Any] = {"q": Q, "h": H, "p2": P2, "eta": eta}
        if NPSH is not None:
            pt["npsh"] = NPSH

        cells: List[Any] = [Q, H, P2 or "-", eta or "-", NPSH if NPSH is not None else "-"]

        for vi in range(len(vfd_ratios)):
            r = vfd_ratios[vi]
            h_vfd = round(H * r * r * 10) / 10
            cells.append(h_vfd)
            pt[f"vfd_{vfd_hz[vi]}"] = h_vfd

        md_lines.append("| " + " | ".join(str(c) for c in cells) + " |")
        points.append(pt)

    markdown = f"## {pump_name} - Curve Data ({stages} stages, {n_sync} rpm sync)\n\n" + "\n".join(md_lines)

    return {
        "pumpName": prod["ProdName"],
        "stages": stages,
        "syncRpm": n_sync,
        "markdown": markdown,
        "points": points,
    }
