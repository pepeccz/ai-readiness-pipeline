"""
app.utils — shared utility helpers for the AI Readiness Pipeline backend.

Exports:
  is_empty             — empty predicate (R4: None | "" | [] → empty; False/0/0.0 → filled)
  assessment_completeness — compute fill-rate and sparse gate for an assessment
  FORM_DATA_KEYS       — canonical frozenset of 42 form_data keys (from schemas.assessment)
  FORM_DATA_TO_FLAT_SYNC — R5 mapping: investment_budget → budget, urgency → priority_text
"""

from app.schemas.assessment import FORM_DATA_KEYS, FORM_DATA_TO_FLAT_SYNC
from app.utils.completeness import assessment_completeness, is_empty

__all__ = [
    "FORM_DATA_KEYS",
    "FORM_DATA_TO_FLAT_SYNC",
    "assessment_completeness",
    "is_empty",
]
