"""
tests/test_requirements.py — Verifies required Python packages are importable.
"""

from __future__ import annotations


def test_python_slugify_importable():
    """python-slugify must be installed and work with Spanish strings."""
    from slugify import slugify

    result = slugify("Diagnóstico")
    assert result == "diagnostico"


def test_python_slugify_handles_spaces_and_accents():
    """Slugify handles common Spanish company name patterns."""
    from slugify import slugify

    assert slugify("Empresa Española S.A.") == "empresa-espanola-s-a"
    assert slugify("Manufactura Ñoña") == "manufactura-nona"
