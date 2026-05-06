"""
tests/test_catalog.py — Unit tests for Zanovix services catalog loader.
"""

from __future__ import annotations


def test_catalog_loads_three_services():
    """get_catalog() returns exactly 3 services."""
    from app.services.synthesis.catalog import get_catalog

    services = get_catalog()
    assert len(services) == 3


def test_catalog_schema_valid():
    """Each service has required fields with correct types."""
    from app.services.synthesis.catalog import get_catalog

    services = get_catalog()
    for svc in services:
        assert isinstance(svc.key, str) and svc.key
        assert isinstance(svc.nombre, str) and svc.nombre
        assert isinstance(svc.descripcion, str) and svc.descripcion
        assert isinstance(svc.cuando_recomendar, list)


def test_catalog_known_keys():
    """YAML keys match the expected three services."""
    from app.services.synthesis.catalog import get_catalog

    keys = {s.key for s in get_catalog()}
    assert keys == {
        "diagnostico_profundo",
        "desarrollo_acompanamiento",
        "formacion_personalizada",
    }


def test_catalog_keys_match_literal():
    """Drift guard: YAML keys match RelatedServiceLiteral exactly."""
    import typing

    from app.services.synthesis.catalog import get_catalog
    from app.services.sessions.synthesis_schema import RelatedServiceLiteral

    yaml_keys = {s.key for s in get_catalog()}
    literal_keys = set(typing.get_args(RelatedServiceLiteral))
    assert yaml_keys == literal_keys
