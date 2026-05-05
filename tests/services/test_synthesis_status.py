"""
tests/services/test_synthesis_status.py — TA.4

Unit tests for compute_synthesis_status(session) covering all 4 branches.
"""

from __future__ import annotations

import pytest

from app.services.synthesis_status import compute_synthesis_status


class _FakeSession:
    def __init__(self, state: str, session1_synthesis=None):
        self.state = state
        self.session1_synthesis = session1_synthesis


def test_not_started_when_not_started():
    session = _FakeSession(state="not_started")
    assert compute_synthesis_status(session) == "not_started"


def test_not_started_when_in_progress():
    session = _FakeSession(state="in_progress")
    assert compute_synthesis_status(session) == "not_started"


def test_not_started_when_blocks_completed():
    session = _FakeSession(state="blocks_completed")
    assert compute_synthesis_status(session) == "not_started"


def test_pending_when_deep_pending_and_no_synthesis():
    session = _FakeSession(state="deep_pending", session1_synthesis=None)
    assert compute_synthesis_status(session) == "pending"


def test_pending_when_deep_received_and_no_synthesis():
    """Even in deep_received, if synthesis not yet written, status is pending."""
    session = _FakeSession(state="deep_received", session1_synthesis=None)
    assert compute_synthesis_status(session) == "pending"


def test_failed_when_synthesis_has_error_key():
    session = _FakeSession(
        state="deep_pending",
        session1_synthesis={"error": "LLM timed out", "generated_at": "2026-05-06T00:00:00Z", "model": "claude-sonnet-4-6"},
    )
    assert compute_synthesis_status(session) == "failed"


def test_ready_when_synthesis_populated_no_error():
    synth = {
        "summary": "Global synthesis text",
        "key_insights": ["Insight 1"],
        "recommendations": ["Rec 1"],
        "hypothesis": "Main hypothesis",
        "generated_at": "2026-05-06T00:00:00Z",
        "model": "claude-sonnet-4-6",
    }
    session = _FakeSession(state="deep_pending", session1_synthesis=synth)
    assert compute_synthesis_status(session) == "ready"


def test_ready_when_closed_and_synthesis_populated():
    synth = {
        "summary": "Synthesis text",
        "key_insights": [],
        "recommendations": [],
        "hypothesis": "Hypothesis",
        "generated_at": "2026-05-06T00:00:00Z",
        "model": "claude-sonnet-4-6",
    }
    session = _FakeSession(state="closed", session1_synthesis=synth)
    assert compute_synthesis_status(session) == "ready"
