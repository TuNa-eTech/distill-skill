"""Validate pack citations and token budgets for synthesized skill packs."""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

from distill_core.config import PACKS_DIR
from distill_core.roles import SUPPORTED_ROLES

SOURCE_RE = re.compile(r"\[src:\s*([^\]]+)\]")
REQUIRED_CITATION_SECTIONS = {
    "rules",
    "templates",
    "anti-patterns",
    "pitfalls",
    "hard rules",
}

try:
    import tiktoken
except Exception:  # pragma: no cover - fallback only used when optional dep fails
    tiktoken = None


def estimate_tokens(text: str) -> int:
    if tiktoken is None:
        return max(1, math.ceil(len(text) / 4))
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def parse_source_ids(text: str) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for match in SOURCE_RE.finditer(text):
        for token in match.group(1).split(","):
            source_id = token.strip()
            if source_id and source_id not in seen:
                ordered.append(source_id)
                seen.add(source_id)
    return ordered


def validate_module_text(
    text: str,
    *,
    module_name: str,
    token_cap: int = 3000,
) -> list[str]:
    errors: list[str] = []
    token_count = estimate_tokens(text)
    if token_count > token_cap:
        errors.append(f"{module_name}: exceeds the 3000-token cap (~{token_count} tokens).")

    section = ""
    for line_number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("## "):
            section = stripped[3:].strip().lower()
            continue
        is_required_bullet = stripped.startswith("- ") and section in REQUIRED_CITATION_SECTIONS
        if is_required_bullet:
            source_ids = parse_source_ids(stripped)
            if not source_ids:
                errors.append(f"{module_name}: Missing citation on line {line_number}.")
            elif len(source_ids) < 2:
                errors.append(
                    f"{module_name}: Need at least 2 distinct source IDs on line {line_number}."
                )
            continue
        if stripped.startswith("**Sources**") and not SOURCE_RE.search(stripped):
            errors.append(f"{module_name}: Missing citation on line {line_number}.")
    return errors


def validate_role_pack(
    *,
    role: str,
    packs_dir: Path = PACKS_DIR,
    total_token_cap: int = 20000,
) -> dict[str, object]:
    pack_root = packs_dir / role / "v0.1"
    skills_dir = pack_root / "skills"
    manifest_path = pack_root / "manifest.md"
    metadata_path = pack_root / "pack.yaml"
    module_paths = sorted(skills_dir.glob("*.md")) if skills_dir.exists() else []
    errors: list[str] = []
    modules: dict[str, list[str]] = {}
    total_tokens = 0

    if not manifest_path.exists():
        errors.append(f"Missing manifest at {manifest_path}.")
    if not metadata_path.exists():
        errors.append(f"Missing pack metadata at {metadata_path}.")
    if not module_paths:
        errors.append(f"No synthesized modules found under {skills_dir}.")

    for module_path in module_paths:
        text = module_path.read_text(encoding="utf-8")
        total_tokens += estimate_tokens(text)
        module_errors = validate_module_text(text, module_name=module_path.name)
        modules[module_path.name] = module_errors
        errors.extend(module_errors)

    if manifest_path.exists():
        manifest_text = manifest_path.read_text(encoding="utf-8")
        total_tokens += estimate_tokens(manifest_text)
        errors.extend(validate_module_text(manifest_text, module_name=manifest_path.name))

    if total_tokens > total_token_cap:
        errors.append(f"Pack {role}/v0.1 exceeds the 20000-token cap (~{total_tokens} tokens).")

    return {"ok": not errors, "errors": errors, "modules": modules, "total_tokens": total_tokens}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=list(SUPPORTED_ROLES))
    args = parser.parse_args()

    result = validate_role_pack(role=args.role)
    if not result["ok"]:
        for error in result["errors"]:
            print(error)
        sys.exit(1)
    print(
        f"Validation passed for {args.role}: {len(result['modules'])} modules, "
        f"~{result['total_tokens']} tokens total."
    )


if __name__ == "__main__":
    main()
