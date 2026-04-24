import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
BLOBS_DIR = DATA_DIR / "blobs"
DB_PATH = DATA_DIR / "distill.db"
PROMPTS_DIR = ROOT / "prompts"
PACKS_DIR = ROOT / "packs"
VALIDATION_DIR = ROOT / "validation"
DEFAULT_INGEST_SINCE = "2026-01-01"

load_dotenv(ROOT / ".env")


def env(key: str, default: str | None = None, *, required: bool = False) -> str | None:
    value = os.environ.get(key, default)
    if required and not value:
        raise RuntimeError(f"Missing required env var: {key}")
    return value


def llm_model() -> str:
    """Resolve default model based on the active LLM provider.

    OpenAI (default): reads GPT_MODEL, falls back to gpt-4o.
    Anthropic: reads ANTHROPIC_MODEL, falls back to claude-sonnet-4-5.
    """
    provider = env("LLM_PROVIDER", "openai") or "openai"
    if provider == "anthropic":
        return env("ANTHROPIC_MODEL", "claude-sonnet-4-5") or "claude-sonnet-4-5"
    return env("GPT_MODEL", "gpt-4o") or "gpt-4o"


def default_ingest_since() -> str:
    return env("INGEST_SINCE", DEFAULT_INGEST_SINCE) or DEFAULT_INGEST_SINCE


def default_ingest_until() -> str:
    return env("INGEST_UNTIL", date.today().isoformat()) or date.today().isoformat()
