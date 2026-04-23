#!/usr/bin/env python3
"""Crawl Jira issues + changelog + comments in the given window (days) into SQLite."""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", type=int, default=90, help="Days to look back")
    args = parser.parse_args()

    raise NotImplementedError(
        f"TODO (Day 1): crawl Jira issues for last {args.window}d, "
        "upsert artifacts + jira_events, save blobs under data/blobs/jira/."
    )


if __name__ == "__main__":
    main()
