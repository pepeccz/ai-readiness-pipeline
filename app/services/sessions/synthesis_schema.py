"""
app/services/sessions/synthesis_schema — Pydantic models for Session 1 synthesis.

Key types:
  RelatedServiceLiteral  — Literal of valid Zanovix service keys (mirrors YAML)
  RecommendationItem     — structured recommendation with impact/effort/related_service
  RoadmapBuckets         — 30/60/90-day roadmap
  Session1SynthesisOutput — full synthesis shape with lazy coercion for legacy rows

Backward compatibility:
  model_validator(mode='before') on Session1SynthesisOutput:
    - recommendations: list[str] → list[RecommendationItem]
    - unknown related_service values → None (handled on RecommendationItem itself)
  This coercion is read-time only; DB values are never mutated.

Drift guard:
  app/services/synthesis/catalog.py::validate_catalog_keys_match_literal()
  asserts the YAML service keys equal the Literal members. Called at startup.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, model_validator

# Mirrors the 3 service keys in app/config/zanovix_services.yaml exactly.
# If services are added/removed, update this AND the YAML AND run the drift-guard test.
RelatedServiceLiteral = Literal[
    "diagnostico_profundo",
    "desarrollo_acompanamiento",
    "formacion_personalizada",
]

_VALID_RELATED_SERVICES = {
    "diagnostico_profundo",
    "desarrollo_acompanamiento",
    "formacion_personalizada",
}

_VALID_IMPACT_EFFORT = {"alto", "medio", "bajo"}


class RecommendationItem(BaseModel):
    """
    A single structured recommendation.

    related_service: validated at field level — invalid values coerced to None.
    """

    text: str
    impact: Optional[Literal["alto", "medio", "bajo"]] = None
    effort: Optional[Literal["alto", "medio", "bajo"]] = None
    related_service: Optional[RelatedServiceLiteral] = None

    @model_validator(mode="before")
    @classmethod
    def coerce_invalid_related_service(cls, values: dict) -> dict:
        """Strip unknown related_service values to None instead of raising."""
        if isinstance(values, dict):
            rs = values.get("related_service")
            if rs is not None and rs not in _VALID_RELATED_SERVICES:
                values = {**values, "related_service": None}
        return values


class RoadmapBuckets(BaseModel):
    """30/60/90-day roadmap buckets."""

    d30: list[str] = []
    d60: list[str] = []
    d90: list[str] = []


class Session1SynthesisOutput(BaseModel):
    """
    Structured output from the session 1 synthesis LLM call.

    All fields are Optional so partial LLM output is handled gracefully.
    hypothesis is stored in DB but NEVER surfaced in PDF or public endpoints.
    """

    summary: Optional[str] = None
    key_insights: Optional[list[str]] = None
    recommendations: Optional[list[RecommendationItem]] = None
    roadmap: Optional[RoadmapBuckets] = None
    next_steps: Optional[list[str]] = None
    hypothesis: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def coerce_legacy_shape(cls, values: object) -> object:
        """
        Coerce legacy DB rows to the new schema shape.

        Legacy shape: recommendations = list[str]
        New shape:    recommendations = list[{text, impact, effort, related_service}]

        This runs at parse time only — DB values are never modified.
        """
        if not isinstance(values, dict):
            return values

        recs = values.get("recommendations")
        if isinstance(recs, list) and recs and isinstance(recs[0], str):
            values = {
                **values,
                "recommendations": [
                    {
                        "text": s,
                        "impact": None,
                        "effort": None,
                        "related_service": None,
                    }
                    for s in recs
                ],
            }

        return values
