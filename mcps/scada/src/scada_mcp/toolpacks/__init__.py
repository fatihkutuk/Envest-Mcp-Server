from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from mcp.server.fastmcp import FastMCP

from ..types import InstanceConfig


class ToolPack(Protocol):
    id: str

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None: ...

    def manifest_groups(self, *, prefix: str) -> list[dict]: ...


@dataclass(frozen=True)
class ToolPackSpec:
    id: str
    pack: ToolPack


def default_scada_packs() -> list[ToolPackSpec]:
    # Imported lazily to keep CLI fast.
    from .scada_core import ScadaCorePack
    from .ai_registry import AiRegistryPack
    from .scada_nodes import ScadaNodesPack
    from .scada_tags import ScadaTagsPack
    from .scada_logs import ScadaLogsPack
    from .scada_devices import ScadaDevicesPack
    from .scada_alarms import ScadaAlarmsPack
    from .scada_charts import ScadaChartsPack
    from .scada_dashboard import ScadaDashboardPack
    from .scada_dma import ScadaDmaPack
    from .scada_exports import ScadaExportsPack
    from .scada_analytics import ScadaAnalyticsPack

    packs = [
        ToolPackSpec(id="scada_core", pack=ScadaCorePack()),
        ToolPackSpec(id="scada_nodes", pack=ScadaNodesPack()),
        ToolPackSpec(id="scada_tags", pack=ScadaTagsPack()),
        ToolPackSpec(id="scada_logs", pack=ScadaLogsPack()),
        ToolPackSpec(id="scada_devices", pack=ScadaDevicesPack()),
        ToolPackSpec(id="scada_alarms", pack=ScadaAlarmsPack()),
        ToolPackSpec(id="scada_charts", pack=ScadaChartsPack()),
        ToolPackSpec(id="scada_dashboard", pack=ScadaDashboardPack()),
        ToolPackSpec(id="scada_dma", pack=ScadaDmaPack()),
        ToolPackSpec(id="scada_exports", pack=ScadaExportsPack()),
        ToolPackSpec(id="scada_analytics", pack=ScadaAnalyticsPack()),
        ToolPackSpec(id="ai_registry", pack=AiRegistryPack()),
    ]
    return packs


def korucaps_packs() -> list[ToolPackSpec]:
    """KoruCAPS pump selection toolpack."""
    from ..korucaps.toolpack import KoruCapsToolPack
    return [ToolPackSpec(id="korucaps", pack=KoruCapsToolPack())]


def database_packs() -> list[ToolPackSpec]:
    """Generic database exploration and analysis toolpack."""
    from ..database_tools.toolpack import DatabaseToolPack
    return [ToolPackSpec(id="database", pack=DatabaseToolPack())]


def skill_packs() -> list[ToolPackSpec]:
    """Skills / domain knowledge toolpack."""
    from ..skills.toolpack import SkillToolPack
    return [ToolPackSpec(id="skills", pack=SkillToolPack())]


def resolve_packs(pack_names: list[str]) -> list[ToolPackSpec]:
    """
    Resolve a list of pack names to ToolPackSpec instances.

    Known pack names:
      - "scada" -> all default SCADA packs
      - "korucaps" -> KoruCAPS pump selection pack
      - "database" -> generic database exploration pack
      - "skills" -> domain knowledge / skills pack

    If a name is not recognized it is silently skipped.
    """
    registry: dict[str, callable] = {
        "scada": default_scada_packs,
        "korucaps": korucaps_packs,
        "database": database_packs,
        "skills": skill_packs,
    }
    result: list[ToolPackSpec] = []
    seen_ids: set[str] = set()
    for name in pack_names:
        factory = registry.get(name)
        if factory is None:
            continue
        for spec in factory():
            if spec.id not in seen_ids:
                seen_ids.add(spec.id)
                result.append(spec)
    return result
