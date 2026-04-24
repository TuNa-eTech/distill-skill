"""Synthesize one skill module per cluster; write packs/<role>/v0.1/skills/*.md."""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=["backend-dev", "business-analyst"])
    args = parser.parse_args()

    raise NotImplementedError(
        f"TODO (Day 6): for each cluster of role={args.role}, call LLM with "
        "prompts/synthesize.system.md, enforce citation format [src: ...], write "
        f"packs/{args.role}/v0.1/skills/<cluster>.md."
    )


if __name__ == "__main__":
    main()
