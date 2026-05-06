"""
app/services/synthesis/catalog — Zanovix services catalog loader.

Loads app/config/zanovix_services.yaml once at module import.
Provides:
  get_catalog()      -> list[ServiceDef]
  get_catalog_dict() -> dict[str, ServiceDef]
  validate_catalog_keys_match_literal()  — fail-fast drift guard

Fail-fast: if YAML is missing or malformed, module import raises RuntimeError
so the app refuses to start (Scenario 7.2).
"""

from __future__ import annotations

import typing
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, ValidationError

# Path is relative to project root, resolved from this file's location
_YAML_PATH = Path(__file__).parent.parent.parent / "config" / "zanovix_services.yaml"


class ServiceDef(BaseModel):
    key: str
    nombre: str
    descripcion: str
    cuando_recomendar: list[str]
    nota_priorizacion: Optional[str] = None


def _load_catalog() -> list[ServiceDef]:
    """Load and validate the YAML catalog. Raises RuntimeError on any failure."""
    if not _YAML_PATH.exists():
        raise RuntimeError(
            f"Zanovix services catalog not found at {_YAML_PATH}. "
            "Cannot start application."
        )

    try:
        raw = yaml.safe_load(_YAML_PATH.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RuntimeError(f"Malformed YAML in services catalog: {exc}") from exc

    if not isinstance(raw, dict) or "services" not in raw:
        raise RuntimeError(
            "services catalog YAML must have a top-level 'services' key."
        )

    services_raw: dict = raw["services"]
    result: list[ServiceDef] = []

    for key, data in services_raw.items():
        if not isinstance(data, dict):
            raise RuntimeError(f"Service '{key}' must be a YAML mapping.")
        try:
            svc = ServiceDef(key=key, **data)
        except (ValidationError, TypeError) as exc:
            raise RuntimeError(
                f"Service '{key}' failed schema validation: {exc}"
            ) from exc
        result.append(svc)

    return result


# Module-level singleton — loaded once at import (fail-fast if malformed)
_CATALOG: list[ServiceDef] = _load_catalog()


def get_catalog() -> list[ServiceDef]:
    """Return the full catalog as a list of ServiceDef."""
    return _CATALOG


def get_catalog_dict() -> dict[str, ServiceDef]:
    """Return catalog keyed by service key."""
    return {s.key: s for s in _CATALOG}


def validate_catalog_keys_match_literal() -> None:
    """
    Drift guard: asserts YAML service keys exactly match RelatedServiceLiteral.

    Called at startup and in tests. Raises AssertionError on mismatch.
    Import is deferred to avoid circular import with synthesis_schema.
    """
    from app.services.sessions.synthesis_schema import RelatedServiceLiteral

    yaml_keys = {s.key for s in _CATALOG}
    # 'otro' is a sentinel for non-Zanovix recommendations (custom/external action),
    # NOT a real catalog entry. Exclude from drift comparison.
    literal_keys = set(typing.get_args(RelatedServiceLiteral)) - {"otro"}
    assert yaml_keys == literal_keys, (
        f"Catalog keys {yaml_keys} do not match RelatedServiceLiteral {literal_keys}. "
        "Update synthesis_schema.py when adding/removing services."
    )
