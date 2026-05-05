"""
app/services/synthesis_status — D2

Pure helper: derive synthesis status from existing session fields.
No new columns; status is a function of state + JSON shape.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from app.models.intake_session import IntakeSession

# States where synthesis has not been initiated yet
_PRE_SYNTHESIS_STATES = {"not_started", "in_progress", "blocks_completed"}


def compute_synthesis_status(
    session: "IntakeSession",
) -> Literal["not_started", "pending", "ready", "failed"]:
    """
    Derive synthesis status from session state and session1_synthesis content.

    Rules (per design decision D2):
    - state in {in_progress, blocks_completed}        → not_started
    - state >= deep_pending AND synthesis is None       → pending
    - state >= deep_pending AND synthesis has 'error'  → failed
    - state >= deep_pending AND synthesis populated     → ready
    """
    if session.state in _PRE_SYNTHESIS_STATES:
        return "not_started"

    synthesis = session.session1_synthesis

    if synthesis is None:
        return "pending"

    if "error" in synthesis:
        return "failed"

    return "ready"
