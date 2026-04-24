"""Filesystem helpers for reading skill packs under packs/<role>/<version>/."""
from __future__ import annotations

from pathlib import Path

from distill_core.config import PACKS_DIR


class PackNotFoundError(FileNotFoundError):
    """Raised when a generated pack is missing required files."""


def pack_root(role: str, version: str = "v0.1") -> Path:
    return PACKS_DIR / role / version


def manifest_path(role: str, version: str = "v0.1") -> Path:
    return pack_root(role, version) / "manifest.md"


def skills_dir(role: str, version: str = "v0.1") -> Path:
    return pack_root(role, version) / "skills"


def require_manifest(role: str, version: str = "v0.1") -> Path:
    path = manifest_path(role, version)
    if not path.is_file():
        raise PackNotFoundError(f"Pack not found: missing manifest at {path}")
    return path


def list_skill_paths(role: str, version: str = "v0.1") -> list[Path]:
    directory = skills_dir(role, version)
    if not directory.is_dir():
        raise PackNotFoundError(f"Pack not found: missing skills directory at {directory}")
    paths = sorted(directory.glob("*.md"))
    if not paths:
        raise PackNotFoundError(f"Pack not found: no skill modules under {directory}")
    return paths


def list_skill_names(role: str, version: str = "v0.1") -> list[str]:
    return [path.stem for path in list_skill_paths(role, version)]


def read_skill(role: str, name: str, version: str = "v0.1") -> str:
    path = skills_dir(role, version) / f"{name}.md"
    if not path.is_file():
        raise PackNotFoundError(f"Pack not found: missing module at {path}")
    return path.read_text(encoding="utf-8")


def read_manifest(role: str, version: str = "v0.1") -> str:
    return require_manifest(role, version).read_text(encoding="utf-8")
