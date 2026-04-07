"""
Skills ToolPack - Serves markdown-based domain knowledge alongside tools.

Registers 2 tools:
  - {prefix}list_skills
  - {prefix}get_skill

This toolpack can be added to any instance's toolpack list to provide
skill/knowledge access. Skills are loaded from:
  1. Instance-level: <instance_dir>/skills/
  2. Global-level: <project_root>/skills/   (project root = 2 levels up from instance)

Instance-level skills override global ones with the same name.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..types import InstanceConfig
from .loader import SkillLoader


def _prefixed(prefix: str, name: str) -> str:
    return f"{prefix}{name}" if prefix else name


class SkillToolPack:
    id = "skills"

    def register(self, mcp: FastMCP, cfg: InstanceConfig) -> None:
        prefix = cfg.tool_prefix

        # Skills from instance dir
        instance_skills_dir = cfg.base_dir / "skills"

        # Skills from project root (2 levels up from instance dir)
        # instance dir = <project>/instances/<name>
        # project root = <project>
        global_skills_dir = cfg.base_dir.parent.parent / "skills"

        loader = SkillLoader(
            instance_skills_dir=instance_skills_dir,
            global_skills_dir=global_skills_dir,
        )

        # ── Tool 1: list_skills ──────────────────────────────────────────
        list_tool = _prefixed(prefix, "list_skills")

        @mcp.tool(name=list_tool)
        def list_skills() -> Any:
            """List all available skills (domain knowledge documents).
Skills provide best practices, guides, and reference material.
Use get_skill to read a specific skill's content.

Returns name, description, and available files for each skill.
Progressive disclosure: content is NOT included - use get_skill to read."""
            skills = loader.list()

            if not skills:
                return {
                    "content": [{
                        "type": "text",
                        "text": "No skills available. Skills can be added to the "
                                "`skills/` directory in the instance or project root.",
                    }]
                }

            lines = [f"## Available Skills ({len(skills)})\n"]
            for s in skills:
                desc = s["description"]
                if isinstance(desc, str):
                    # Trim to first line for listing
                    desc = desc.strip().split("\n")[0]
                files_str = ", ".join(f"`{f}`" for f in s["files"])
                lines.append(f"### {s['name']} (v{s['version']})")
                lines.append(f"{desc}")
                lines.append(f"**Files:** {files_str}\n")

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        # ── Tool 2: get_skill ────────────────────────────────────────────
        get_tool = _prefixed(prefix, "get_skill")

        @mcp.tool(name=get_tool)
        def get_skill(skill_name: str, file_path: str = "SKILL.md") -> Any:
            """Read a skill file's content. Skills are domain knowledge documents (markdown).

Args:
    skill_name: Name of the skill (from list_skills).
    file_path: File within the skill to read (default: SKILL.md).
               Use list_skills to see available files."""
            if not loader.has_skill(skill_name):
                available = [s["name"] for s in loader.list()]
                avail_str = ", ".join(f"`{n}`" for n in available) if available else "none"
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Skill `{skill_name}` not found. Available skills: {avail_str}",
                    }]
                }

            content = loader.get(skill_name, file_path)
            if content is None:
                files = loader.list_files(skill_name)
                files_str = ", ".join(f"`{f}`" for f in files) if files else "none"
                return {
                    "content": [{
                        "type": "text",
                        "text": (
                            f"File `{file_path}` not found in skill `{skill_name}`. "
                            f"Available files: {files_str}"
                        ),
                    }]
                }

            return {"content": [{"type": "text", "text": content}]}

    def manifest_groups(self, *, prefix: str) -> list[dict]:
        return [
            {
                "id": "skills",
                "title": "Domain Knowledge & Skills",
                "tools": [
                    f"{prefix}list_skills",
                    f"{prefix}get_skill",
                ],
            }
        ]
