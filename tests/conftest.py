from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from distill_core.db import connect, init_schema  # noqa: E402


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "distill.db"
    init_schema(db_path)
    return db_path


@pytest.fixture
def temp_blobs(tmp_path: Path) -> Path:
    blobs_dir = tmp_path / "blobs"
    blobs_dir.mkdir(parents=True, exist_ok=True)
    return blobs_dir


@pytest.fixture
def temp_packs(tmp_path: Path) -> Path:
    packs_dir = tmp_path / "packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    return packs_dir


@pytest.fixture
def db_conn(temp_db: Path):
    with connect(temp_db) as conn:
        yield conn
