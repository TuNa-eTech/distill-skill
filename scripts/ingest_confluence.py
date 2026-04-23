#!/usr/bin/env python3
"""Crawl Confluence pages in the given window (days) into SQLite (BA role)."""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", type=int, default=90, help="Days to look back")
    args = parser.parse_args()

    raise NotImplementedError(
        f"TODO (Day 2): crawl Confluence pages for last {args.window}d, "
        "upsert artifacts, save blobs under data/blobs/confluence/."
    )


if __name__ == "__main__":
    main()
