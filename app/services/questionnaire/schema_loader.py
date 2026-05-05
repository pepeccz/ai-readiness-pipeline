"""
app/services/questionnaire/schema_loader.py

Loads all YAML schema files from schemas/questionnaire-v2/ at startup.
Implements:
  - $ref resolution (relative file + optional fragment path)
  - Global question ID uniqueness validation
  - option.score >= 0 validation
  - Module-level singleton cache (load once, serve forever)

Public API:
  load_all(schema_dir=None)   → dict (root schema)
  get_schema_version()        → str
  _reset_cache()              → None  (test helper)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_LOADED_SCHEMA: dict | None = None
_DEFAULT_SCHEMA_DIR = Path(__file__).parents[3] / "schemas" / "questionnaire-v2"


def _reset_cache() -> None:
    """Reset the module-level cache. Only for use in tests."""
    global _LOADED_SCHEMA
    _LOADED_SCHEMA = None


def load_all(schema_dir: Path | None = None) -> dict:
    """
    Load and validate the full schema tree.

    Returns the cached result on subsequent calls (no file re-read).
    Raises RuntimeError on validation failure (fail-fast at startup).
    """
    global _LOADED_SCHEMA

    if _LOADED_SCHEMA is not None:
        return _LOADED_SCHEMA

    base_dir = Path(schema_dir) if schema_dir is not None else _DEFAULT_SCHEMA_DIR
    root_file = base_dir / "_root.yaml"

    if not root_file.exists():
        raise FileNotFoundError(f"Schema root not found: {root_file}")

    logger.info("schema_loader_start", path=str(root_file))

    raw = _load_yaml_file(root_file)
    resolved = _resolve_refs(raw, base_file=root_file, base_dir=base_dir)

    _validate_schema(resolved)

    # Also run the full schema_validator checks
    from app.services.questionnaire.schema_validator import validate_schema
    validate_schema(resolved, schema_dir=base_dir)

    _LOADED_SCHEMA = resolved
    logger.info(
        "schema_loader_done",
        schema_version=resolved.get("schema_version", "unknown"),
    )
    return _LOADED_SCHEMA


def get_schema_version() -> str:
    """Return schema_version from the loaded schema. Raises if not loaded."""
    if _LOADED_SCHEMA is None:
        raise RuntimeError("Schema not loaded — call load_all() first")
    return str(_LOADED_SCHEMA.get("schema_version", "unknown"))


# ---------------------------------------------------------------------------
# Internal — YAML loading
# ---------------------------------------------------------------------------

def _load_yaml_file(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise RuntimeError(f"YAML parse error in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"YAML root must be a mapping in {path}")
    return data


# ---------------------------------------------------------------------------
# Internal — $ref resolution
# ---------------------------------------------------------------------------

def _resolve_refs(obj: Any, base_file: Path, base_dir: Path) -> Any:
    """
    Recursively resolve {"$ref": "..."} nodes.

    Formats supported:
      "./path/to/file.yaml"               → entire file content
      "./path/to/file.yaml#/key/subkey"   → nested key inside file
      "#/$defs/..."                        → local definition (not yet needed but handled)
    """
    if isinstance(obj, dict):
        if "$ref" in obj and len(obj) == 1:
            return _resolve_single_ref(obj["$ref"], base_file, base_dir)
        return {k: _resolve_refs(v, base_file, base_dir) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_refs(item, base_file, base_dir) for item in obj]
    return obj


def _resolve_single_ref(ref: str, base_file: Path, base_dir: Path) -> Any:
    if ref.startswith("#"):
        raise RuntimeError(f"Local $ref not supported yet: {ref}")

    if "#" in ref:
        file_part, fragment = ref.split("#", 1)
    else:
        file_part, fragment = ref, ""

    # Resolve relative to base_file's directory
    ref_path = (base_file.parent / file_part).resolve()

    if not ref_path.exists():
        raise FileNotFoundError(
            f"$ref target not found: {ref_path} (referenced from {base_file})"
        )

    referenced = _load_yaml_file(ref_path)
    # Recursively resolve $refs inside the referenced file too
    referenced = _resolve_refs(referenced, base_file=ref_path, base_dir=base_dir)

    if fragment:
        # Navigate fragment path like "/questions/0"
        parts = [p for p in fragment.strip("/").split("/") if p]
        node = referenced
        for part in parts:
            if isinstance(node, dict):
                if part not in node:
                    raise RuntimeError(
                        f"$ref fragment /{'/'.join(parts)} not found in {ref_path}"
                    )
                node = node[part]
            elif isinstance(node, list):
                try:
                    node = node[int(part)]
                except (ValueError, IndexError) as exc:
                    raise RuntimeError(
                        f"$ref fragment index {part} invalid in {ref_path}"
                    ) from exc
            else:
                raise RuntimeError(
                    f"$ref fragment traversal failed at {part} in {ref_path}"
                )
        return node

    return referenced


# ---------------------------------------------------------------------------
# Internal — validation
# ---------------------------------------------------------------------------

def _validate_schema(schema: dict) -> None:
    """
    Validate the fully-resolved schema dict.
    Raises RuntimeError or ValueError on any failure.
    """
    all_question_ids: list[str] = []

    # Collect questions from triage layer
    triage = schema.get("triage", {})
    _collect_questions(triage.get("questions", []), all_question_ids)

    # Collect from core blocks if present
    core = schema.get("core", {})
    for block in core.get("blocks", []):
        _collect_questions(block.get("questions", []), all_question_ids)

    # Check uniqueness
    seen: set[str] = set()
    for qid in all_question_ids:
        if qid in seen:
            raise ValueError(
                f"Duplicate question id found: '{qid}'. "
                "All question ids must be globally unique."
            )
        seen.add(qid)


def _collect_questions(questions: list, all_ids: list[str]) -> None:
    """Walk a questions list, collecting ids and validating scores."""
    for q in questions:
        if not isinstance(q, dict):
            continue
        qid = q.get("id")
        if qid:
            all_ids.append(qid)

        # Validate option scores
        for opt in q.get("options", []):
            score = opt.get("score")
            if score is not None and score < 0:
                raise ValueError(
                    f"option.score must be >= 0 in question '{qid}', "
                    f"got {score} for option '{opt.get('value')}'"
                )

        # Recurse into sub_fields (composite)
        sub = q.get("sub_fields", [])
        if sub:
            _collect_questions(sub, all_ids)
