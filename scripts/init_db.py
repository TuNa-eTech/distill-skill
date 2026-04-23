#!/usr/bin/env python3
"""Initialize SQLite schema. Idempotent — safe to re-run."""
from distill.config import DB_PATH
from distill.db import init_schema


def main() -> None:
    init_schema()
    print(f"Schema ready at {DB_PATH}")


if __name__ == "__main__":
    main()
