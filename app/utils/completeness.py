"""
app.utils.completeness — shared "empty" predicate and assessment completeness helper.

Used by:
  - LLM enrichment runner (logs warnings when assessment is sparse — no rejection)
  - tests for FORM_DATA_KEYS allowlist sanity
  - backend equivalent of frontend assessmentCompleteness for any future
    server-side gate (out of scope this delta but keeps the door open).

The "empty" predicate (design R4):
  None | "" | empty list/tuple/set/dict → empty.
  False, 0, 0.0 → FILLED (the user said "no" / "zero hours").

Whitespace-only strings are NOT trimmed before the check — by design.
The wizard already strips required fields via the not_empty validator in
PublicSubmissionPayload; non-required fields default to "".  A field returning
"  " is treated as filled (the user typed something).
"""
from __future__ import annotations

from typing import Any

from app.schemas.assessment import FORM_DATA_KEYS

# Critical form_data keys whose absence forces isSparse=True regardless of
# overall fill percentage (design §6, CAP-P-IN-001).
CRITICAL_FORM_DATA_KEYS: frozenset[str] = frozenset({
    "most_time_consuming_process",
    "software_used",
    "daily_queries",
    "urgency",
})

# Critical flat-column fields — checked via the flat_fields dict argument.
CRITICAL_FLAT_FIELDS: frozenset[str] = frozenset({"sector"})

# Fill-rate threshold below which the assessment is considered sparse.
# 60% of 42 = at least 26 of 42 filled required to pass.
COMPLETENESS_THRESHOLD: float = 0.6


def is_empty(value: Any) -> bool:
    """R4: None | "" | [] | {} are empty; False, 0, 0.0 are filled.

    Examples:
        is_empty(None)     → True
        is_empty("")       → True
        is_empty([])       → True
        is_empty({})       → True
        is_empty(False)    → False  # explicit "no" answer
        is_empty(0)        → False  # explicit "zero hours" answer
        is_empty(0.0)      → False
        is_empty("hello")  → False
        is_empty([1])      → False
    """
    if value is None:
        return True
    if isinstance(value, str) and value == "":
        return True
    if isinstance(value, (list, tuple, set, dict)) and len(value) == 0:
        return True
    return False


def assessment_completeness(
    form_data: dict[str, Any] | None,
    flat_fields: dict[str, Any],
) -> dict[str, Any]:
    """Compute completeness for an assessment.

    Args:
        form_data:    The assessment.form_data blob (or None).
        flat_fields:  Subset of flat columns relevant to the gate.
                      Must include 'sector' to satisfy CRITICAL_FLAT_FIELDS.

    Returns:
        dict with keys:
          filled          — number of canonical form_data keys that are filled
          total           — len(FORM_DATA_KEYS) == 42
          percentage      — filled / total  (0.0 .. 1.0)
          missing_critical — list of critical field names that are empty
          is_sparse       — True when percentage < threshold OR any critical missing
    """
    fd = form_data or {}
    filled = sum(1 for k in FORM_DATA_KEYS if not is_empty(fd.get(k)))
    total = len(FORM_DATA_KEYS)
    percentage = filled / total if total else 0.0

    missing: list[str] = []
    for k in sorted(CRITICAL_FORM_DATA_KEYS):
        if is_empty(fd.get(k)):
            missing.append(k)
    for k in sorted(CRITICAL_FLAT_FIELDS):
        if is_empty(flat_fields.get(k)):
            missing.append(k)

    is_sparse = percentage < COMPLETENESS_THRESHOLD or bool(missing)
    return {
        "filled": filled,
        "total": total,
        "percentage": percentage,
        "missing_critical": missing,
        "is_sparse": is_sparse,
    }
