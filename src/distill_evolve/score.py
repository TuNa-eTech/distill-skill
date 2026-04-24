"""Compute composite quality scores per artifact for the given role."""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=["backend-dev", "business-analyst"])
    args = parser.parse_args()

    raise NotImplementedError(
        f"TODO (Day 3): implement composite score formula for role={args.role}, "
        "populate scores table with score + breakdown JSON."
    )


if __name__ == "__main__":
    main()
