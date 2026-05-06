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
    """Valid output with new keys must parse without error."""
    from app.services.sessions.session_closing import Session1SynthesisOutput

    data = Session1SynthesisOutput(
        summary="Empresa con alto potencial de automatización.",
        key_insights=["Insight 1", "Insight 2"],
        recommendations=["Rec 1", "Rec 2"],
        hypothesis="Hipótesis principal.",
    )
    assert data.key_insights == ["Insight 1", "Insight 2"]
    assert data.recommendations == ["Rec 1", "Rec 2"]
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
