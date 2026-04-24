"""Filesystem helpers for reading skill packs under packs/<role>/<version>/."""
from pathlib import Path

from distill_core.config import PACKS_DIR


def pack_root(role: str, version: str = "v0.1") -> Path:
    return PACKS_DIR / role / version


def manifest_path(role: str, version: str = "v0.1") -> Path:
    return pack_root(role, version) / "manifest.md"


def skills_dir(role: str, version: str = "v0.1") -> Path:
    return pack_root(role, version) / "skills"


def list_skill_names(role: str, version: str = "v0.1") -> list[str]:
    d = skills_dir(role, version)
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.md"))


def read_skill(role: str, name: str, version: str = "v0.1") -> str:
    return (skills_dir(role, version) / f"{name}.md").read_text(encoding="utf-8")


def read_manifest(role: str, version: str = "v0.1") -> str:
    return manifest_path(role, version).read_text(encoding="utf-8")
