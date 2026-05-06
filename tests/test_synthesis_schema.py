"""
tests/test_synthesis_schema.py — Unit tests for Session1SynthesisOutput schema.

Covers:
  B.1 — new schema parses correctly
  B.2 — legacy coercion of string recommendations
  B.3 — invalid related_service coerced to None
"""

from __future__ import annotations

import pytest


# ─── B.1 ────────────────────────────────────────────────────────────────────

def test_new_schema_parses_correctly():
    """Full new-shape fixture parses without error into Session1SynthesisOutput."""
    from app.services.sessions.synthesis_schema import (
        Session1SynthesisOutput,
        RecommendationItem,
        RoadmapBuckets,
    )

    data = {
        "summary": "Empresa con alta madurez operativa pero baja adopción IA.",
        "key_insights": ["Insight 1", "Insight 2", "Insight 3"],
        "recommendations": [
            {
                "text": "Implementar RPA en contabilidad",
                "impact": "alto",
                "effort": "medio",
                "related_service": "desarrollo_acompanamiento",
            }
        ],
        "roadmap": {
            "d30": ["Diagnóstico de procesos"],
            "d60": ["Piloto RPA"],
            "d90": ["Expansión"],
        },
        "next_steps": ["Agendar segunda sesión"],
        "hypothesis": "El cliente está listo para un piloto IA en 90 días.",
    }

    output = Session1SynthesisOutput.model_validate(data)

    assert output.summary is not None
    assert len(output.key_insights) == 3
    assert len(output.recommendations) == 1
    assert isinstance(output.recommendations[0], RecommendationItem)
    assert output.recommendations[0].related_service == "desarrollo_acompanamiento"
    assert isinstance(output.roadmap, RoadmapBuckets)
    assert output.roadmap.d30 == ["Diagnóstico de procesos"]
    assert output.hypothesis == "El cliente está listo para un piloto IA en 90 días."


def test_related_service_literal_has_three_values():
    """RelatedServiceLiteral must have exactly 3 valid values."""
    import typing
    from app.services.sessions.synthesis_schema import RelatedServiceLiteral

    values = set(typing.get_args(RelatedServiceLiteral))
    assert values == {
        "diagnostico_profundo",
        "desarrollo_acompanamiento",
        "formacion_personalizada",
    }


def test_hypothesis_field_present():
    """hypothesis field must exist on Session1SynthesisOutput."""
    from app.services.sessions.synthesis_schema import Session1SynthesisOutput
    import inspect

    fields = Session1SynthesisOutput.model_fields
    assert "hypothesis" in fields


# ─── B.2 ────────────────────────────────────────────────────────────────────

def test_lazy_coercion_legacy_strings():
    """Legacy string recommendations are coerced to RecommendationItem objects."""
    from app.services.sessions.synthesis_schema import Session1SynthesisOutput, RecommendationItem

    data = {
        "recommendations": ["Implementar RPA", "Revisar SOPs"],
    }
    output = Session1SynthesisOutput.model_validate(data)

    assert len(output.recommendations) == 2
    for rec in output.recommendations:
        assert isinstance(rec, RecommendationItem)
        assert rec.impact is None
        assert rec.effort is None
        assert rec.related_service is None

    texts = [r.text for r in output.recommendations]
    assert "Implementar RPA" in texts
    assert "Revisar SOPs" in texts


def test_lazy_coercion_missing_fields_become_none():
    """Minimal input has all optional fields as None."""
    from app.services.sessions.synthesis_schema import Session1SynthesisOutput

    output = Session1SynthesisOutput.model_validate({})
    assert output.summary is None
    assert output.key_insights is None
    assert output.recommendations is None
    assert output.roadmap is None
    assert output.next_steps is None
    assert output.hypothesis is None


# ─── B.3 ────────────────────────────────────────────────────────────────────

def test_invalid_related_service_coerced_to_none():
    """Unknown related_service value is coerced to None, not rejected."""
    from app.services.sessions.synthesis_schema import RecommendationItem

    rec = RecommendationItem.model_validate({
        "text": "Recomendación X",
        "related_service": "servicio_inventado",
    })
    assert rec.related_service is None
    assert rec.text == "Recomendación X"
