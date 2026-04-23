import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
BLOBS_DIR = DATA_DIR / "blobs"
DB_PATH = DATA_DIR / "distill.db"
PROMPTS_DIR = ROOT / "prompts"
PACKS_DIR = ROOT / "packs"
VALIDATION_DIR = ROOT / "validation"

load_dotenv(ROOT / ".env")


def env(key: str, default: str | None = None, *, required: bool = False) -> str | None:
    value = os.environ.get(key, default)
    if required and not value:
        raise RuntimeError(f"Missing required env var: {key}")
    return value


def llm_model() -> str:
    return env("LLM_MODEL", "claude-sonnet-4-5") or "claude-sonnet-4-5"
