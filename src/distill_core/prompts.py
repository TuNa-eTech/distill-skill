"""Helpers for loading and rendering prompt templates."""
from __future__ import annotations

from pathlib import Path

from .config import PROMPTS_DIR
from .roles import get_role_config


def prompt_path(name: str) -> Path:
    return PROMPTS_DIR / name


def load_prompt(name: str) -> str:
    return prompt_path(name).read_text(encoding="utf-8")


def render_prompt(name: str, **kwargs: object) -> str:
    return load_prompt(name).format(**kwargs)


def role_prompt_path(role: str, name: str) -> Path:
    return PROMPTS_DIR / get_role_config(role).prompt_namespace / name


def shared_prompt_path(name: str) -> Path:
    return PROMPTS_DIR / "shared" / name


def load_role_prompt(role: str, name: str) -> str:
    candidates = [role_prompt_path(role, name), shared_prompt_path(name)]
    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8")
    tried = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Prompt not found for role {role!r}: {name}. Tried: {tried}")


def render_role_prompt(role: str, name: str, **kwargs: object) -> str:
    return load_role_prompt(role, name).format(**kwargs)
