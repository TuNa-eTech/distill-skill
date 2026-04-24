"""Validate pack: every rule has [src: ...], module < 3000 tokens, total < 20000."""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=["backend-dev", "business-analyst"])
    args = parser.parse_args()

    raise NotImplementedError(
        f"TODO (Day 7): scan packs/{args.role}/v0.1/skills/*.md — verify citations, "
        "per-module and total token budget; report pass/fail per module."
    )


if __name__ == "__main__":
    main()
