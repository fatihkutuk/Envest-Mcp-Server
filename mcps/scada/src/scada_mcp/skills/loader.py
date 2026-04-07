"""
Skill loader - scans skill directories for SKILL.md files and serves them.

Skills are markdown-based domain knowledge files organized as:
    <skills_dir>/<skill-name>/SKILL.md       (main file, with YAML frontmatter)
    <skills_dir>/<skill-name>/<other>.md      (additional files)

Supports merging instance-level and global-level skill directories.
Instance-level skills override global ones with the same name.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("scada_mcp.skills")


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """
    Parse YAML frontmatter from a markdown file.

    Returns (metadata_dict, content_without_frontmatter).
    If no frontmatter is found, returns ({}, full_text).
    """
    text = text.lstrip()
    if not text.startswith("---"):
        return {}, text
    try:
        end = text.index("---", 3)
    except ValueError:
        return {}, text
    raw_yaml = text[3:end]
    content = text[end + 3:].strip()
    try:
        meta = yaml.safe_load(raw_yaml)
        if not isinstance(meta, dict):
            meta = {}
    except yaml.YAMLError:
        meta = {}
    return meta, content


class SkillLoader:
    """
    Loads and indexes skill files from one or two directories.

    Parameters
    ----------
    instance_skills_dir:
        Per-instance skills directory (takes precedence).
    global_skills_dir:
        Shared/global skills directory (fallback).
    """

    def __init__(
        self,
        instance_skills_dir: Path | None = None,
        global_skills_dir: Path | None = None,
    ) -> None:
        self._instance_dir = instance_skills_dir
        self._global_dir = global_skills_dir
        # skill_name -> {meta, path}
        self._index: dict[str, dict[str, Any]] = {}
        self._build_index()

    def _build_index(self) -> None:
        """Scan directories and build the skill index. Instance overrides global."""
        # Load global first, then instance (instance overwrites)
        for skills_dir in (self._global_dir, self._instance_dir):
            if skills_dir is None or not skills_dir.is_dir():
                continue
            for skill_dir in sorted(skills_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / "SKILL.md"
                if not skill_file.exists():
                    continue
                try:
                    text = skill_file.read_text(encoding="utf-8")
                    meta, _content = _parse_frontmatter(text)
                except Exception as exc:
                    logger.warning("Failed to read skill %s: %s", skill_dir.name, exc)
                    continue

                name = meta.get("name", skill_dir.name)
                self._index[name] = {
                    "name": name,
                    "description": meta.get("description", ""),
                    "version": meta.get("version", "0.0.0"),
                    "path": skill_dir,
                    "source": "instance" if skills_dir == self._instance_dir else "global",
                }
                logger.debug("Indexed skill: %s (from %s)", name, skill_dir)

        logger.info("Loaded %d skill(s)", len(self._index))

    def list(self) -> list[dict[str, Any]]:
        """
        Return a list of all available skills with metadata.

        Each entry: {name, description, version, files: [list of .md files]}
        """
        result = []
        for name, info in sorted(self._index.items()):
            md_files = self.list_files(name)
            result.append({
                "name": info["name"],
                "description": info["description"],
                "version": info["version"],
                "files": md_files,
            })
        return result

    def get(self, name: str, file_path: str = "SKILL.md") -> str | None:
        """
        Return the content of a specific file within a skill.

        Path traversal protection: only .md files within the skill directory
        are accessible.

        Returns None if the skill or file is not found.
        """
        info = self._index.get(name)
        if info is None:
            return None

        skill_dir: Path = info["path"]

        # Path traversal protection
        file_path = file_path.strip()
        if not file_path:
            file_path = "SKILL.md"

        # Resolve and check the file is within the skill directory
        try:
            target = (skill_dir / file_path).resolve()
        except (ValueError, OSError):
            return None

        # Ensure the resolved path is within the skill directory
        try:
            target.relative_to(skill_dir.resolve())
        except ValueError:
            logger.warning(
                "Path traversal attempt blocked: %s (skill=%s)", file_path, name
            )
            return None

        # Only allow .md files
        if target.suffix.lower() != ".md":
            return None

        if not target.is_file():
            return None

        try:
            return target.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to read skill file %s/%s: %s", name, file_path, exc)
            return None

    def list_files(self, name: str) -> list[str]:
        """
        Return all .md files in the skill directory (relative paths).
        """
        info = self._index.get(name)
        if info is None:
            return []

        skill_dir: Path = info["path"]
        if not skill_dir.is_dir():
            return []

        files = []
        for f in sorted(skill_dir.rglob("*.md")):
            try:
                rel = f.relative_to(skill_dir)
                files.append(str(rel).replace("\\", "/"))
            except ValueError:
                continue
        return files

    def has_skill(self, name: str) -> bool:
        """Check if a skill exists."""
        return name in self._index
