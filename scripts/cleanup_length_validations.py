"""
scripts/cleanup_length_validations.py — REQ-1 one-shot YAML cleanup.

Removes max_length and min_length entries from validations lists in every
schemas/questionnaire-v2/core/*.yaml file. Drops the validations key entirely
when the list becomes empty. Preserves all other validations (pattern, etc.).

Uses PyYAML (safe_load + dump) — comments will be lost but are acceptable
for this one-shot cleanup per ADR-1.

Usage:
    python scripts/cleanup_length_validations.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

LENGTH_TYPES = {"max_length", "min_length"}

CORE_DIR = Path(__file__).parents[1] / "schemas" / "questionnaire-v2" / "core"


def _strip_length_validations(obj: object) -> object:
    """Recursively remove max_length/min_length from validations lists in-place."""
    if isinstance(obj, dict):
        if "validations" in obj and isinstance(obj["validations"], list):
            obj["validations"] = [
                v for v in obj["validations"]
                if not (isinstance(v, dict) and v.get("type") in LENGTH_TYPES)
            ]
            if obj["validations"] == []:
                del obj["validations"]
        for key in list(obj.keys()):
            obj[key] = _strip_length_validations(obj[key])
    elif isinstance(obj, list):
        return [_strip_length_validations(item) for item in obj]
    return obj


def process_file(path: Path, dry_run: bool) -> bool:
    """
    Process one YAML file.

    Returns True if the file was (or would be) changed.
    """
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if data is None:
        return False

    _strip_length_validations(data)

    new_content = yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120,
    )

    changed = (new_content != raw)

    if dry_run:
        if changed:
            print(f"[dry-run] Would modify: {path.name}")
        else:
            print(f"[dry-run] No changes:   {path.name}")
    else:
        if changed:
            path.write_text(new_content, encoding="utf-8")
            print(f"Modified: {path.name}")
        else:
            print(f"No changes: {path.name}")

    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="Strip max_length/min_length from questionnaire YAMLs.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files.")
    args = parser.parse_args()

    yaml_files = sorted(CORE_DIR.glob("*.yaml"))
    if not yaml_files:
        print(f"No YAML files found under {CORE_DIR}", file=sys.stderr)
        sys.exit(1)

    changed_count = 0
    for path in yaml_files:
        if process_file(path, dry_run=args.dry_run):
            changed_count += 1

    mode = "dry-run" if args.dry_run else "actual"
    print(f"\n[{mode}] {changed_count}/{len(yaml_files)} files would be changed.")


if __name__ == "__main__":
    main()
