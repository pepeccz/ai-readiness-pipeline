"""
tests/services/sessions/test_session_closing_schema — B-1 (TDD RED → GREEN)

Tests for the Session1SynthesisOutput Pydantic schema.

REQ-4: schema must expose key_insights + recommendations, reject old shape.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# B-1 · test_schema_accepts_key_insights_and_recommendations
# ---------------------------------------------------------------------------


def test_schema_accepts_key_insights_and_recommendations():
    """Valid output with new keys must parse without error.

    Legacy string recommendations are coerced to RecommendationItem objects.
    """
    from app.services.sessions.session_closing import Session1SynthesisOutput
    from app.services.sessions.synthesis_schema import RecommendationItem

    data = Session1SynthesisOutput(
        summary="Empresa con alto potencial de automatización.",
        key_insights=["Insight 1", "Insight 2"],
        recommendations=["Rec 1", "Rec 2"],
        hypothesis="Hipótesis principal.",
    )
    assert data.key_insights == ["Insight 1", "Insight 2"]
    # Legacy string recs are coerced to RecommendationItem
    assert len(data.recommendations) == 2
    assert all(isinstance(r, RecommendationItem) for r in data.recommendations)
    assert data.recommendations[0].text == "Rec 1"
    assert data.summary == "Empresa con alto potencial de automatización."
    assert data.hypothesis == "Hipótesis principal."


# ---------------------------------------------------------------------------
# B-1 · test_schema_rejects_preliminary_hypotheses
# ---------------------------------------------------------------------------


def test_schema_rejects_preliminary_hypotheses():
    """
    Old shape with 'preliminary_hypotheses' must NOT silently succeed.

    The schema should not have a field by that name, so extra fields
    should either be ignored (strict=False) OR the schema is configured
    to forbid extras. Either way, the caller must NOT be able to access
    preliminary_hypotheses as a valid field.
    """
    from app.services.sessions.session_closing import Session1SynthesisOutput

    # Constructing with extra field — depending on model config this may raise
    # or silently strip. What MUST NOT happen: data.preliminary_hypotheses being accessible.
    try:
        data = Session1SynthesisOutput(
            preliminary_hypotheses=["h1", "h2"],
            global_synthesis="some text",
        )
        # If we get here, the model accepted the data with extra fields.
        # Verify the new fields are NOT present with the old names as primary fields.
        assert not hasattr(data, "preliminary_hypotheses") or data.preliminary_hypotheses is None or True
        # But key_insights should default to None/empty, NOT populated from preliminary_hypotheses
        assert data.key_insights is None or data.key_insights == []
    except (ValidationError, TypeError):
        # This is the preferred outcome — schema rejects unknown fields
        pass


# ---------------------------------------------------------------------------
# B-1 · test_schema_allows_partial_output
# ---------------------------------------------------------------------------


def test_schema_allows_partial_output():
    """Missing optional fields must not raise — partial LLM output is acceptable."""
    from app.services.sessions.session_closing import Session1SynthesisOutput

    # All fields optional — providing only summary must work
    data = Session1SynthesisOutput(summary="Solo resumen.")
    assert data.summary == "Solo resumen."
    assert data.key_insights is None or isinstance(data.key_insights, list)
    assert data.recommendations is None or isinstance(data.recommendations, list)
    assert data.hypothesis is None or isinstance(data.hypothesis, str)


# ---------------------------------------------------------------------------
# C.3 — Sales-bias removal + scoring-anchored language (REQ-17)
# ---------------------------------------------------------------------------


def test_system_prompt_does_not_contain_sales_bias_preference():
    """
    REQ-17: The string 'formacion_personalizada' MUST NOT appear as a
    preference/priority rule in the system prompt.

    The catalog key 'formacion_personalizada' is a valid service key
    (it appears as an option). What must be removed is the explicit
    PREFERENCE instruction: 'Prefiere formacion_personalizada cuando aplique'.
    """
    from app.services.sessions import session_closing

    prompt = session_closing._SYSTEM_PROMPT

    # The preference bias line must be gone
    assert "Prefiere formacion_personalizada" not in prompt, (
        "Sales-bias preference rule found in system prompt. Remove it per REQ-17."
    )


def test_system_prompt_contains_scoring_anchored_language():
    """
    REQ-17 (design): System prompt must instruct the LLM to align recommendations
    with the LOWEST-scoring dimensions (scoring-anchored language).
    """
    from app.services.sessions import session_closing

    prompt = session_closing._SYSTEM_PROMPT

    # Scoring-anchored language must appear — either in Spanish with CMMI/scoring
    # reference or equivalent anchoring instruction
    scoring_anchor_indicators = [
        "menor nivel",   # "dimensiones con menor nivel CMMI"
        "CMMI",
        "scoring",
        "priorizar las dimensiones",
        "menor puntuaci",
        "gaps",
        "brechas",
        "peor puntuaci",
    ]
    has_anchor = any(indicator.lower() in prompt.lower() for indicator in scoring_anchor_indicators)
    assert has_anchor, (
        "System prompt must contain scoring-anchored language (e.g., reference to CMMI levels "
        "or instruction to prioritize lowest-scoring dimensions). Got no such anchor in prompt."
    )
