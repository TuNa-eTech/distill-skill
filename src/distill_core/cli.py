"""Console-script entry points for distill_core."""
from .config import DB_PATH
from .db import init_schema


def init_db() -> None:
    init_schema()
    print(f"Schema ready at {DB_PATH}")
