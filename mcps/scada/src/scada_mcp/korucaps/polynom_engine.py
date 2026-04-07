"""
WinCAPS Polynomial Engine
Parses and evaluates WinCAPS polynomial strings in f() and d() formats.

Format: f([qMin, qMax], [s([a0, a1, a2, ...])])
Multi-segment: f([0, q1, q2, qMax], [s([...]), s([...]), s([...])])

Evaluation: y(Q) = a0 + a1*Q + a2*Q^2 + a3*Q^3 + ...

Algorithm source: xkgpi32.dll reverse engineering (WinCAPS 7.52)
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PolynomSegment:
    coefficients: List[float] = field(default_factory=list)


@dataclass
class ParsedPolynomial:
    type: str  # "f" or "d"
    ranges: List[float] = field(default_factory=list)
    segments: List[PolynomSegment] = field(default_factory=list)


def parse_polynomial(poly_string: Optional[str]) -> Optional[ParsedPolynomial]:
    """Parse a WinCAPS polynomial string into structured data."""
    if not poly_string:
        return None
    try:
        if poly_string.startswith("f("):
            ptype = "f"
        elif poly_string.startswith("d("):
            ptype = "d"
        else:
            return None

        # Extract the content inside the outer parentheses
        inner = poly_string[2:-1]

        # Parse ranges: [0, qMax] or [0, q1, q2, qMax]
        range_match = re.search(r"\[([^\]]+)\]", inner)
        if not range_match:
            return None
        ranges = [float(s.strip()) for s in range_match.group(1).split(",")]

        # Parse segments: s([a0, a1, ...])
        segments: List[PolynomSegment] = []
        for seg_match in re.finditer(r"s\(\[([^\]]+)\]\)", inner):
            coefficients = [float(s.strip()) for s in seg_match.group(1).split(",")]
            segments.append(PolynomSegment(coefficients=coefficients))

        if len(segments) == 0:
            return None

        return ParsedPolynomial(type=ptype, ranges=ranges, segments=segments)
    except Exception:
        return None


def evaluate_polynomial(poly: Optional[ParsedPolynomial], q: float) -> Optional[float]:
    """Evaluate a polynomial at a given Q value."""
    if poly is None or len(poly.segments) == 0:
        return None

    # Find the correct segment for this Q value
    segment_index = 0

    if len(poly.segments) > 1 and len(poly.ranges) > 2:
        # Multi-segment polynomial - find which segment Q falls into
        for i in range(len(poly.ranges) - 1):
            if q >= poly.ranges[i] and q <= poly.ranges[i + 1]:
                segment_index = min(i, len(poly.segments) - 1)
                break
        # If Q is beyond all ranges, use the last segment
        if q > poly.ranges[-1]:
            segment_index = len(poly.segments) - 1

    segment = poly.segments[segment_index]
    if segment is None:
        return None

    # Evaluate: y = a0 + a1*Q + a2*Q^2 + a3*Q^3 + ...
    result = 0.0
    for i, coeff in enumerate(segment.coefficients):
        result += coeff * math.pow(q, i)

    return result


def generate_curve_points(
    poly_string: str,
    q_min: float,
    q_max: float,
    num_points: int = 50,
) -> List[dict]:
    """Generate curve points from a polynomial string."""
    poly = parse_polynomial(poly_string)
    if poly is None:
        return []

    points: List[dict] = []
    step = (q_max - q_min) / (num_points - 1) if num_points > 1 else 0

    for i in range(num_points):
        q = q_min + step * i
        value = evaluate_polynomial(poly, q)
        if value is not None and math.isfinite(value):
            points.append({"q": q, "value": value})

    return points


def calculate_efficiency(q: float, head: float, power: float, p1p2: int = 2) -> float:
    """
    Calculate efficiency from Q-H and Q-P curves.
    For P2 (shaft power): eta = (rho * g * Q * H) / (P2 * 1000) * 100
    For P1 (input power): eta = (rho * g * Q * H) / (P1 * 1000) * 100
    where Q in m3/h, H in m, P in kW

    P1P2 flag: 1 = P1 (input power), 2 = P2 (shaft power)
    When P1P2=2 (shaft power), efficiency is hydraulic efficiency
    When P1P2=1 (input power), efficiency includes motor losses

    WinCAPS DLL constants (xkgpi32.dll offset 0x1007a868: g/3600 = 0.002724069444)
    rho = 998.2 kg/m3 (water at 20C), g = 9.80665 m/s2 (standard gravity)
    """
    if power <= 0 or q <= 0 or head <= 0:
        return 0.0
    rho = 998.2
    g = 9.80665
    eta = (rho * g * (q / 3600.0) * head) / (power * 1000.0) * 100.0
    return min(max(eta, 0.0), 100.0)  # Clamp 0-100%


def extract_stage_count(prod_name: str) -> int:
    """
    Extract stage count from pump product name.
    "SP 160-5" -> 5, "SP 215-4-AA" -> 4, "SP 270-3V G" -> 3, "CR 15-3" -> 3
    """
    if not prod_name:
        return 1
    # Match family-stageCount pattern: "SP 160-5", "SP 215-4-AA", "SP 270-3V G"
    match = re.match(
        r"^(?:SP|CR|CRN|CRI|CRE|SQ|BM|NK|NB)\s+\d+[A-Z]*\s*-\s*(\d+)",
        prod_name,
        re.IGNORECASE,
    )
    if match:
        return int(match.group(1))
    # Fallback: trailing digits after hyphen or space
    fallback = re.search(r"[- ](\d+)(?:[- ][A-Za-z].*)?$", prod_name)
    if fallback:
        return int(fallback.group(1))
    return 1


def extract_pump_family(prod_name: str) -> str:
    """
    Extract pump family name (without stage count and suffix).
    "SP 160-5" -> "SP 160", "SP 215-4-AA" -> "SP 215", "SP 270-3V G" -> "SP 270"
    """
    if not prod_name:
        return prod_name
    match = re.match(
        r"^((?:SP|CR|CRN|CRI|CRE|SQ|BM|NK|NB)\s+\d+[A-Z]*)\s*-",
        prod_name,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    return prod_name


def find_operating_point(
    qh_poly_string: str,
    q_min: float,
    q_max: float,
    target_q: float,
    target_h: float,
) -> Optional[dict]:
    """
    Find the operating point (intersection with system curve).
    System curve: H_sys = H_static + k * Q^2
    """
    poly = parse_polynomial(qh_poly_string)
    if poly is None:
        return None

    h = evaluate_polynomial(poly, target_q)
    if h is None:
        return None

    return {"q": target_q, "h": h}
