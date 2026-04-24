"""Interactive clustering — show extraction, prompt for cluster name, save."""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=["backend-dev", "business-analyst"])
    args = parser.parse_args()

    raise NotImplementedError(
        f"TODO (Day 5): read unclustered extractions for role={args.role}, "
        "show each, prompt for cluster name, upsert clusters + set extractions.cluster_id."
    )


if __name__ == "__main__":
    main()
