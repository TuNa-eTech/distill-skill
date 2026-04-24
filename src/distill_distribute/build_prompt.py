"""Build a single system prompt from a pack (manifest + trigger-matched modules)."""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True)
    parser.add_argument("--task", required=True, help="Free-text task description")
    parser.add_argument("--version", default="v0.1")
    args = parser.parse_args()

    raise NotImplementedError(
        f"TODO: load packs/{args.role}/{args.version}/manifest.md, match triggers "
        "against --task, concat matching skill modules, print to stdout."
    )


if __name__ == "__main__":
    main()
