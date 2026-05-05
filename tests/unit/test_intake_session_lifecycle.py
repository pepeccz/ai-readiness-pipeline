"""
tests/unit/test_intake_session_lifecycle.py — T5.2 (TDD RED)

Tests for IntakeSession state machine and lifecycle helpers.
"""

from __future__ import annotations

import pytest


class TestIntakeSessionStates:
    """IntakeSession valid states and transitions."""

    VALID_STATES = [
        "in_progress",
        "blocks_completed",
        "deep_pending",
        "deep_received",
        "closed",
    ]

    def test_valid_states_defined(self):
        from app.services.intake.session_service import VALID_SESSION_STATES
        for state in self.VALID_STATES:
            assert state in VALID_SESSION_STATES

    def test_transition_in_progress_to_blocks_completed(self):
        from app.services.intake.session_service import can_transition_to
        assert can_transition_to("in_progress", "blocks_completed") is True

    def test_transition_blocks_completed_to_deep_pending(self):
        from app.services.intake.session_service import can_transition_to
        assert can_transition_to("blocks_completed", "deep_pending") is True

    def test_transition_deep_pending_to_deep_received(self):
        from app.services.intake.session_service import can_transition_to
        assert can_transition_to("deep_pending", "deep_received") is True

    def test_transition_deep_received_to_closed(self):
        from app.services.intake.session_service import can_transition_to
        assert can_transition_to("deep_received", "closed") is True

    def test_invalid_transition_closed_to_in_progress(self):
        from app.services.intake.session_service import can_transition_to
        assert can_transition_to("closed", "in_progress") is False

    def test_invalid_transition_in_progress_to_deep_pending(self):
        from app.services.intake.session_service import can_transition_to
        assert can_transition_to("in_progress", "deep_pending") is False

    def test_invalid_transition_to_same_state(self):
        from app.services.intake.session_service import can_transition_to
        assert can_transition_to("in_progress", "in_progress") is False


class TestIntakeSessionCreation:
    """IntakeSession creation payload builder."""

    def test_build_session_payload_requires_lead_id(self):
        from app.services.intake.session_service import build_session_payload
        result = build_session_payload(
            lead_id="lead-123",
            primary_area="marketing",
        )
        assert result["lead_id"] == "lead-123"
        assert result["primary_area"] == "marketing"
        assert result["state"] == "in_progress"
        assert result["blocks_completed"] == []

    def test_build_session_payload_cross_area(self):
        from app.services.intake.session_service import build_session_payload
        result = build_session_payload(
            lead_id="lead-456",
            primary_area="cross_area_communication",
            areas_involved=["sales", "marketing", "operations"],
        )
        assert result["primary_area"] == "cross_area_communication"
        assert result["areas_involved"] == ["sales", "marketing", "operations"]
        assert result.get("secondary_area") is None

    def test_build_session_payload_cross_area_blocks_secondary(self):
        """When primary is cross_area, secondary_area must not be set."""
        from app.services.intake.session_service import build_session_payload
        result = build_session_payload(
            lead_id="lead-789",
            primary_area="cross_area_communication",
            secondary_area="marketing",  # should be ignored
            areas_involved=["sales", "marketing"],
        )
        assert result.get("secondary_area") is None


class TestBlockCompletionHelpers:
    """Helpers for tracking block completion."""

    def test_mark_block_completed(self):
        from app.services.intake.session_service import mark_block_completed
        blocks = []
        result = mark_block_completed(blocks, "block-1-strategic")
        assert "block-1-strategic" in result

    def test_mark_block_completed_idempotent(self):
        from app.services.intake.session_service import mark_block_completed
        blocks = ["block-1-strategic"]
        result = mark_block_completed(blocks, "block-1-strategic")
        assert result.count("block-1-strategic") == 1

    def test_is_session1_complete_requires_strategic(self):
        from app.services.intake.session_service import is_session1_complete
        # strategic + primary process = minimum required
        assert is_session1_complete(
            blocks_completed=["block-1-strategic", "block-2-process-critical-full"],
            primary_area="marketing",
        ) is True

    def test_is_session1_incomplete_without_strategic(self):
        from app.services.intake.session_service import is_session1_complete
        assert is_session1_complete(
            blocks_completed=["block-2-process-critical-full"],
            primary_area="marketing",
        ) is False
