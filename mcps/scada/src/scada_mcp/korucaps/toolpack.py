"""
KoruCAPS ToolPack - Pump selection tools for WinCAPS database.

Registers 6 tools:
  - {prefix}search_pumps
  - {prefix}calculate_operating_point
  - {prefix}get_pump_details
  - {prefix}get_pump_curve_data
  - {prefix}list_applications
  - {prefix}list_pump_families
"""

from __future__ import annotations

from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from ..types import InstanceConfig

from .polynom_engine import calculate_efficiency
from .pump_service import evaluate_pump_at_point, get_pump_curve_dataset
from . import db as korucaps_db


def _prefixed(prefix: str, name: str) -> str:
    return f"{prefix}{name}" if prefix else name


class KoruCapsToolPack:
    id = "korucaps"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix
        db_cfg = cfg.db
        if db_cfg is None:
            raise RuntimeError("KoruCAPS requires a db config in instance.yaml")

        # ── Tool 1: search_pumps ──────────────────────────────────────────
        search_tool = _prefixed(prefix, "search_pumps")

        @mcp.tool(name=search_tool)
        def search_pumps(
            flow_m3h: float,
            head_m: float,
            frequency_hz: str = "50",
            phase: str = "3",
            voltage: str = "400",
            vfd: bool = False,
            mounting: str = "well_tankless",
            ranking_criteria: str = "energy",
            application: Optional[str] = None,
            sub_application: Optional[str] = None,
            max_results: int = 10,
        ) -> Any:
            """KoruCAPS pompa boyutlandirma araci - Grundfos WinCAPS birebir algoritmasi.

## NE YAPAR:
Verilen Q (debi) ve H (basma yuksekligi) icin en uygun pompalari bulur.
Sonuctaki her pompa GARANTILI olarak istenen H basma yuksekligini saglar.
Sonuctaki Q degeri = pompanin istenen H'de verdigi GERCEK debidir (istenen Q'dan farkli olabilir).

## KRITIK: SONUCLARI NASIL YORUMLA
- H (basma yuksekligi) = ISTENEN H. Her pompa bu H'de calisir, Hm DUSMEZ.
- Q (debi) = Pompanin bu H'de verdigi gercek debi. Istenen Q'dan BUYUK veya ESIT olur, ASLA DUSMEZ.
- Q istenen debiden buyukse -> VFD (frekans konvertor) ile frekans dusurulerek istenen debiye ayarlanir.
- Siralama = En dusuk enerji tuketimi birinci.
- search_pumps sonuclarini TEKRAR calculate_operating_point ile DOGRULAMA. Sonuclar zaten dogru.

## BIRIM CEVIRME:
- Kullanici lt/sn verdiyse -> 3.6 ile carparak m3/h'e cevir (orn: 44 lt/sn = 158.4 m3/h)
- SCADA Hm verisi = basma yuksekligi (H metre)

## UYGULAMA + ALT UYGULAMA OTOMATIK BELIRLEME:
Kullanici kelimelerinden DOGRU application VE sub_application secilmeli:

YERALTI SU (application='groundwater'):
- "sondaj kuyu" / "kuyu pompasi" / "derin kuyu" -> sub_application='WELLINS' (SP dalgic)
- "yatay montaj" / "horizontal" -> sub_application='HORINS' (SP, BM, BMB)
- "sig kuyu" / "shallow well" -> sub_application='SHALLOW' (SQ, SQE, SP kucuk)
- sadece "kuyu" -> sub_application='WELLINS' (DEFAULT: sondaj kuyu)

BASINC ARTIRMA (application='booster'):
- "terfi" / "terfi istasyonu" / "basinc artirma" -> sub_application='BOOSPUMP' (CR, TP, NB)
- "paket set" / "hazir set" -> sub_application='BOOSSET' (Hydro sistemler)

EVSEL SU (application='domestic'):
- "depo" / "hazne" / "su deposu" -> sub_application='PUMPSDO'
- "kuyu" + "ev" -> sub_application='WELLINDO'

KANALIZASYON (application='sewage'):
- "kanalizasyon" / "atiksu" / "pis su" -> sub_application='PUMPSSEW'

ISITMA (application='heating'):
- "isitma" / "kalorifer" / "sirkulasyon" -> sub_application='CIRCHEAT'

SOGUTMA (application='aircon'):
- "sogutma" / "klima" / "chiller" -> sub_application='CIRCAIR'

ENDUSTRIYEL (application='industrial'):
- "endustriyel" / "fabrika" / "proses" -> sub_application yok

## SCADA NODE'DAN SECIM:
1. Node adinda "Kuyu" -> application='groundwater', sub_application='WELLINS'
2. Node adinda "Terfi" -> application='booster', sub_application='BOOSPUMP'
3. Node adinda "Depo" -> application='domestic', sub_application='PUMPSDO'
4. np_PompaDebi -> debi (m3/h veya lt/sn, birime dikkat)
5. ToplamHm veya BasmaYukseklik -> H (metre)"""
            freq = frequency_hz or "50"

            # Map application name to ID
            app_map = {
                "heating": 1, "aircon": 2, "booster": 3, "groundwater": 4,
                "domestic": 5, "sewage": 6, "industrial": 7,
            }

            # Resolve application ID (parent or child)
            application_id: Optional[int] = None
            if application and application in app_map:
                application_id = app_map[application]
                # If sub_application specified, resolve to child app ID
                if sub_application:
                    from ..db import connect as _db_connect
                    with _db_connect(db_cfg) as conn:
                        with conn.cursor() as cur:
                            sub_app_code = sub_application.upper()
                            cur.execute(
                                "SELECT a.ID FROM application a JOIN applhier h ON a.ID = h.ID "
                                "WHERE h.PARENTID = %s AND a.CODE = %s",
                                (application_id, sub_app_code),
                            )
                            child = cur.fetchone()
                            if child:
                                application_id = child["ID"]

            results = korucaps_db.find_pumps(
                db=db_cfg,
                flow=flow_m3h,
                head=head_m,
                freq=freq,
                application_id=application_id,
                phase=phase,
                voltage=voltage or None,
                vfd=vfd,
                ranking_criteria=ranking_criteria,
            )

            top_results = results[:max_results]

            if not top_results:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Q={flow_m3h} m3/h, H={head_m} m, {freq} Hz icin uygun pompa bulunamadi. Degerleri kontrol edin.",
                    }]
                }

            lines = []
            for i, p in enumerate(top_results):
                line = (
                    f"{i + 1}. **{p['ProdName']}** ({p.get('stages', 1)} kademe) [{p.get('ProductNo', '')}]\n"
                    f"   Q={p['qActual']} m3/h | H={head_m} m (garanti) | P2={p['p2Actual']} kW | P1={p['p1Actual']} kW\n"
                    f"   eta_pompa={p['etaPump']}% | eta_toplam={p['etaTotal']}% | n={p['nActual']} rpm"
                )
                if p.get("Es") is not None:
                    line += f" | Es={p['Es']} kWh/m3"
                if p.get("energyKwh") is not None:
                    line += f" | Yillik enerji={p['energyKwh']:,} kWh"
                lines.append(line)

            text = (
                f"## KoruCAPS Pompa Boyutlandirma Sonuclari\n\n"
                f"**Istenen:** Q={flow_m3h} m3/h, H={head_m} m\n"
                f"**Ayarlar:** {freq} Hz, {phase} faz, {voltage}V, {'VFD' if vfd else 'Surucusuz'}\n"
                f"{'**Uygulama:** ' + application if application else '**Uygulama:** Tum kategoriler'}\n"
                f"**Siralama:** Enerji sarfiyati (dusuk = daha verimli)\n\n"
                f"> **NOT:** Tum pompalar H={head_m} m basma yuksekligini GARANTI eder. Hm DUSMEZ.\n"
                f"> Q degeri = pompanin H={head_m} m'de verdigi gercek debidir (istenen {flow_m3h} m3/h'den BUYUK veya ESIT).\n"
                f"> Q fazlasi VFD ile frekans dusurulerek istenen debiye ayarlanabilir.\n\n"
                f"**{len(top_results)} uygun pompa:**\n\n" + "\n\n".join(lines)
            )

            return {"content": [{"type": "text", "text": text}]}

        # ── Tool 2: calculate_operating_point ─────────────────────────────
        calc_tool = _prefixed(prefix, "calculate_operating_point")

        @mcp.tool(name=calc_tool)
        def calculate_operating_point(
            pump_name: str,
            flow_m3h: float,
            frequency_hz: float = 50,
        ) -> Any:
            """Belirli bir debide pompanin performansini hesaplar. Pompa adi ve Q (debi) verildiginde H, P2, P1, verim, RPM, NPSH doner.

DIKKAT: Bu tool SADECE egri analizi icindir.
- search_pumps sonuclarini DOGRULAMAK icin bu tool'u KULLANMA - search_pumps zaten dogru sonuc verir.
- Bu tool Q verildiginde H hesaplar (search_pumps ise H verildiginde Q hesaplar - FARKLI ISLEM).
- Kullanici "bu pompa Q=160'da kac metre basar?" diye sorarsa KULLAN.
- VFD ile farkli frekansta performans hesabi icin KULLAN."""
            from ..db import connect as _db_connect

            nominal_freq = 50 if frequency_hz <= 50 else 60

            with _db_connect(db_cfg) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT p.Id, p.CurveSetId, pn.ProdName
                           FROM products2 p
                           JOIN prodnames pn ON p.ProdNameId = pn.Id
                           WHERE pn.ProdName = %s AND p.CurveSetId > 0
                           LIMIT 1""",
                        (pump_name,),
                    )
                    prod = cur.fetchone()

                if not prod:
                    return {"content": [{"type": "text", "text": f'Pump "{pump_name}" not found. Check the name and try again. Use search_pumps to find available pumps.'}]}

                # If VFD (frequency < nominal), adjust flow for affinity law
                vfd_ratio = frequency_hz / nominal_freq
                adjusted_flow = flow_m3h / vfd_ratio if vfd_ratio < 1 else flow_m3h

                result = evaluate_pump_at_point(
                    prod["ProdName"], prod["CurveSetId"], adjusted_flow, conn, nominal_freq,
                )

            if not result:
                return {"content": [{"type": "text", "text": f'Could not evaluate pump "{pump_name}" at Q={flow_m3h} m3/h. The flow may be outside the pump\'s operating range.'}]}

            # Apply VFD affinity law if needed
            if vfd_ratio < 1:
                result["flow"] = round(flow_m3h * 100) / 100
                result["head"] = round(result["head"] * vfd_ratio * vfd_ratio * 10) / 10
                if result.get("P2_kW"):
                    result["P2_kW"] = round(result["P2_kW"] * vfd_ratio * vfd_ratio * vfd_ratio * 100) / 100
                if result.get("P1_kW"):
                    result["P1_kW"] = round(result["P1_kW"] * vfd_ratio * vfd_ratio * vfd_ratio * 100) / 100
                result["rpm"] = round(result["rpm"] * vfd_ratio)
                result["frequency_Hz"] = frequency_hz
                if result.get("P2_kW") and result["P2_kW"] > 0:
                    result["etaPump"] = round(calculate_efficiency(flow_m3h, result["head"], result["P2_kW"]) * 10) / 10

            text_parts = [
                f'## {result["pumpName"]} - Operating Point',
                "| Parameter | Value |",
                "|-----------|-------|",
                f'| Flow (Q) | {result["flow"]} m3/h |',
                f'| Head (H) | {result["head"]} m |',
                f'| Shaft Power (P2) | {result["P2_kW"]} kW |',
                f'| Input Power (P1) | {result["P1_kW"]} kW |',
                f'| Pump Efficiency | {result["etaPump"]}% |',
                f'| Total Efficiency | {result["etaTotal"]}% |',
                f'| Speed | {result["rpm"]} rpm |',
                f'| Stages | {result["stages"]} |',
            ]
            if result.get("NPSH_m") is not None:
                text_parts.append(f'| NPSH Required | {result["NPSH_m"]} m |')
            if result.get("Es_kWhPerM3") is not None:
                text_parts.append(f'| Specific Energy | {result["Es_kWhPerM3"]} kWh/m3 |')
            text_parts.append(f'| Frequency | {result["frequency_Hz"]} Hz |')
            text_parts.append(f'| Flow Range | {result["qMin"]} - {result["qMax"]} m3/h |')
            if frequency_hz < nominal_freq:
                text_parts.append(f"\n*VFD operation at {frequency_hz} Hz (ratio: {vfd_ratio:.2f})*")

            return {"content": [{"type": "text", "text": "\n".join(text_parts)}]}

        # ── Tool 3: get_pump_details ──────────────────────────────────────
        details_tool = _prefixed(prefix, "get_pump_details")

        @mcp.tool(name=details_tool)
        def get_pump_details(pump_name: str) -> Any:
            """Get technical specifications and details of a specific pump model. Returns product info, operating ranges, motor data, and material information."""
            from ..db import connect as _db_connect
            import re as _re

            with _db_connect(db_cfg) as conn:
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
                    prod = cur.fetchone()

                if not prod:
                    return {"content": [{"type": "text", "text": f'Pump "{pump_name}" not found.'}]}

                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT c.rpm, c.stages, c.qMin, c.qMax, c.speedNo
                           FROM curveindex2 ci JOIN curve2 c ON ci.curveId = c.curveId
                           WHERE ci.curveSetId = %s AND (c.freq = %s OR c.freq = '0' OR c.freq = 0)
                           ORDER BY c.speedNo DESC LIMIT 2""",
                        (prod["CurveSetId"], prod.get("Freq") or 50),
                    )
                    curve_rows = cur.fetchall()

                curve = curve_rows[0] if curve_rows else None

                # Evaluate at BEP (70% of Q range)
                bep_result = None
                if curve:
                    q_bep = curve["qMin"] + (curve["qMax"] - curve["qMin"]) * 0.7
                    bep_result = evaluate_pump_at_point(
                        prod["ProdName"], prod["CurveSetId"], q_bep, conn,
                    )

            stage_match = _re.search(r"[- ](\d+)$", pump_name)
            stages = int(stage_match.group(1)) if stage_match else (curve.get("stages", 1) if curve else 1)
            is_submersible = bool(_re.match(r"^(SP |SQ |BM )", pump_name))

            text_parts = [
                f"## {prod['ProdName']}",
                "| Specification | Value |",
                "|--------------|-------|",
                f"| Product No | {prod.get('ProductNo', 'N/A')} |",
                f"| Group | {prod.get('GroupName', 'N/A')} |",
                f"| Frequency | {prod.get('Freq', 50)} Hz |",
                f"| Stages | {stages} |",
                f"| Synchronous Speed | {curve.get('rpm', 'N/A') if curve else 'N/A'} rpm |",
                f"| Type | {'Submersible' if is_submersible else 'Standard'} |",
            ]
            if curve:
                text_parts.append(f"| Flow Range | {curve['qMin']:.1f} - {curve['qMax']:.1f} m3/h |")
            if bep_result:
                text_parts.extend([
                    "| **Best Efficiency Point (BEP)** | |",
                    f"| BEP Flow | {bep_result['flow']} m3/h |",
                    f"| BEP Head | {bep_result['head']} m |",
                    f"| BEP Efficiency | {bep_result['etaPump']}% |",
                    f"| BEP Power (P2) | {bep_result['P2_kW']} kW |",
                ])

            return {"content": [{"type": "text", "text": "\n".join(text_parts)}]}

        # ── Tool 4: get_pump_curve_data ───────────────────────────────────
        curve_tool = _prefixed(prefix, "get_pump_curve_data")

        @mcp.tool(name=curve_tool)
        def get_pump_curve_data(
            pump_name: str,
            num_points: int = 20,
            include_vfd: bool = False,
        ) -> Any:
            """Get full pump curve data (Q-H, Q-P2, Q-eta, NPSH points) for a specific pump. Returns tabular data suitable for plotting or analysis. Optionally includes VFD curves at different frequencies."""
            from ..db import connect as _db_connect

            with _db_connect(db_cfg) as conn:
                dataset = get_pump_curve_dataset(pump_name, num_points, include_vfd, conn)

            if "error" in dataset:
                return {"content": [{"type": "text", "text": dataset["error"]}]}
            return {"content": [{"type": "text", "text": dataset["markdown"]}]}

        # ── Tool 5: list_applications ─────────────────────────────────────
        apps_tool = _prefixed(prefix, "list_applications")

        @mcp.tool(name=apps_tool)
        def list_applications() -> Any:
            """List available pump application categories and sub-categories for filtering pump searches."""
            from ..db import connect as _db_connect

            with _db_connect(db_cfg) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT a.ID, a.CODE, a.Name, h.PARENTID
                           FROM application a
                           LEFT JOIN applhier h ON a.ID = h.ID
                           ORDER BY COALESCE(h.PARENTID, a.ID), a.ID"""
                    )
                    apps = cur.fetchall()

            parents = [a for a in apps if not a.get("PARENTID") or a["PARENTID"] == 0]
            children = [a for a in apps if a.get("PARENTID") and a["PARENTID"] > 0]

            name_map = {
                "HEATING": "Heating (heating)", "AIRCON": "Air Conditioning (aircon)",
                "PRESBOOS": "Pressure Boosting (booster)", "GROUNDWA": "Groundwater (groundwater)",
                "DOMES": "Domestic Water (domestic)", "SEWAGE": "Sewage (sewage)",
                "OTHER": "Industrial/Other (industrial)",
            }
            sub_name_map = {
                "WELLINS": "well_installation", "HORINS": "horizontal", "SHALLOW": "shallow_wells",
                "CIRCHEAT": "circulation_heating", "BOILSHUN": "boiler_shunt",
                "PRESSUR": "pressure", "FIREHYDR": "fire_hydrant", "PRESSSUP": "pressure_supply",
                "DOMWAT": "domestic_water", "DRAINAGE": "drainage",
                "COOLCIRC": "cooling_circulation", "CONDWAT": "condenser_water",
            }

            lines = ["## Available Applications\n"]
            for p in parents:
                lines.append(f"### {name_map.get(p['CODE'], p['Name'])}")
                subs = [c for c in children if c["PARENTID"] == p["ID"]]
                for s in subs:
                    sub_code = sub_name_map.get(s["CODE"], s["CODE"].lower())
                    lines.append(f'- {s["Name"]} (sub_application: "{sub_code}")')
                lines.append("")

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        # ── Tool 6: list_pump_families ────────────────────────────────────
        families_tool = _prefixed(prefix, "list_pump_families")

        @mcp.tool(name=families_tool)
        def list_pump_families(search: Optional[str] = None) -> Any:
            """List available pump families/product groups with product counts. Use to discover what pump types are available."""
            families = korucaps_db.get_pump_families(db_cfg, search)
            lines = [f"- **{f['name']}** ({f['productCount']} products)" for f in families]
            filter_text = f' (filter: "{search}")' if search else ""
            header = f"## Pump Families{filter_text}"
            return {"content": [{"type": "text", "text": f"{header}\n\n" + "\n".join(lines)}]}

    def manifest_groups(self, *, prefix: str) -> list[dict]:
        return [
            {
                "id": "korucaps_pump_selection",
                "title_tr": "KoruCAPS Pompa Secim",
                "tools": [
                    f"{prefix}search_pumps",
                    f"{prefix}calculate_operating_point",
                    f"{prefix}get_pump_details",
                    f"{prefix}get_pump_curve_data",
                    f"{prefix}list_applications",
                    f"{prefix}list_pump_families",
                ],
            }
        ]
