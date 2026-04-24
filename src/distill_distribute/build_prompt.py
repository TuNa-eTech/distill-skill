"""Build a single MVP prompt from a pack (manifest + all modules) and a task."""

from __future__ import annotations

import argparse
import sys

from distill_distribute import pack


def build_prompt_text(role: str, task: str, version: str = "v0.1") -> str:
    manifest = pack.read_manifest(role, version).strip()
    sections = [
        "# Distill Skill Pack",
        f"Role: {role}",
        f"Version: {version}",
        "",
        "## Manifest",
        manifest,
    ]

    for skill_name in pack.list_skill_names(role, version):
        sections.extend(
            [
                "",
                f"## Skill Module: {skill_name}",
                pack.read_skill(role, skill_name, version).strip(),
            ]
        )

    sections.extend(
        [
            "",
            "## Task",
            task.strip(),
            "",
        ]
    )
    return "\n".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True)
    parser.add_argument("--task", required=True, help="Free-text task description")
    parser.add_argument("--version", default="v0.1")
    args = parser.parse_args()

    try:
        sys.stdout.write(build_prompt_text(args.role, args.task, args.version))
    except pack.PackNotFoundError as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
