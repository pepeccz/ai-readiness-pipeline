"""
app/services/intake/session_service.py

Pure service helpers for IntakeSession lifecycle.

No DB dependencies — these are pure functions for state management logic.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

VALID_SESSION_STATES = [
    "not_started",
    "in_progress",
    "blocks_completed",
    "deep_pending",
    "deep_received",
    "closed",
]

# Valid forward transitions only
_ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "not_started": ["in_progress"],
    "in_progress": ["blocks_completed"],
    "blocks_completed": ["deep_pending"],
    "deep_pending": ["deep_received"],
    "deep_received": ["closed"],
    "closed": [],
}

# Minimum required blocks for session 1 to be complete
_REQUIRED_BLOCKS_SESSION1 = {"block-1-strategic"}


def can_transition_to(current_state: str, target_state: str) -> bool:
    """Return True if the transition from current → target is valid."""
    allowed = _ALLOWED_TRANSITIONS.get(current_state, [])
    return target_state in allowed


# ---------------------------------------------------------------------------
# Session creation payload builder
# ---------------------------------------------------------------------------

VALID_PRIMARY_AREAS = {
    "attention",
    "marketing",
    "sales",
    "operations",
    "finance",
    "hr",
    "product",
    "cross_area_communication",
    "other",
}


def build_session_payload(
    lead_id: str,
    primary_area: str,
    secondary_area: str | None = None,
    areas_involved: list[str] | None = None,
) -> dict:
    """
    Build the dict payload for creating an IntakeSession row.

    Rules:
    - When primary_area is cross_area_communication, secondary_area is always None.
    - areas_involved only meaningful for cross_area_communication.
    - state defaults to in_progress.
    - blocks_completed defaults to empty list.
    """
    is_cross_area = primary_area == "cross_area_communication"

    return {
        "lead_id": lead_id,
        "primary_area": primary_area,
        "secondary_area": None if is_cross_area else secondary_area,
        "areas_involved": areas_involved or [],
        "state": "in_progress",
        "blocks_completed": [],
    }


# ---------------------------------------------------------------------------
# Block completion helpers
# ---------------------------------------------------------------------------

def mark_block_completed(blocks_completed: list[str], block_id: str) -> list[str]:
    """
    Return a new list with block_id added if not already present.

    Idempotent — adding a block twice results in a single entry.
    """
    if block_id in blocks_completed:
        return list(blocks_completed)
    return list(blocks_completed) + [block_id]


def is_session1_complete(blocks_completed: list[str], primary_area: str) -> bool:
    """
    Return True when all required blocks for session 1 are completed.

    Minimum requirements:
    - block-1-strategic is always required.
    - block-2-process-critical-full is required for non-cross-area sessions
      (block-2-process-critical-cross-area for cross-area).
    """
    required = set(_REQUIRED_BLOCKS_SESSION1)

    if primary_area == "cross_area_communication":
        required.add("block-2-process-critical-cross-area")
    else:
        required.add("block-2-process-critical-full")

    return required.issubset(set(blocks_completed))
