"""Run LLM extraction over top-scored artifacts; persist JSON extractions."""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=["backend-dev", "business-analyst"])
    parser.add_argument("--limit", type=int, default=50, help="Max top-scored artifacts to process")
    args = parser.parse_args()

    raise NotImplementedError(
        f"TODO (Day 4): call LLM (distill_core.llm.complete) with prompts/extract.*.md "
        f"on top {args.limit} scored artifacts for role={args.role}, validate against "
        "Extraction schema, insert into extractions table."
    )


if __name__ == "__main__":
    main()
