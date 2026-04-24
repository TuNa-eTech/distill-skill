"""Debug: given a module, dump the source artifacts/extractions it cites."""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", required=True, help="Path to skills/<name>.md")
    args = parser.parse_args()

    raise NotImplementedError(
        f"TODO: parse [src: ...] citations in {args.module}, look up the underlying "
        "extractions + artifacts, and print the provenance chain."
    )


if __name__ == "__main__":
    main()
