"""
tests/unit/test_trigger_detector — T7.1

Unit tests for app/services/deep/trigger_detector.py

Verifies that given CORE block payloads the detector returns the correct
set of deep branch IDs to activate.
"""

from __future__ import annotations

import pytest

from app.services.deep.trigger_detector import TriggerDetector


# ---------------------------------------------------------------------------
# Test: options with deep_branches in block-1-strategic
# ---------------------------------------------------------------------------


def test_detects_post_mortem_when_previous_abandoned():
    """q1_3_previous = abandoned activates post_mortem_proyecto."""
    payload = {"q1_3_previous": "abandoned"}
    branches = TriggerDetector.detect_from_block_payload("block-1-strategic", payload)
    assert "post_mortem_proyecto" in branches


def test_detects_post_mortem_when_previous_failed_production():
    """q1_3_previous = failed_production activates post_mortem_proyecto."""
    payload = {"q1_3_previous": "failed_production"}
    branches = TriggerDetector.detect_from_block_payload("block-1-strategic", payload)
    assert "post_mortem_proyecto" in branches


def test_detects_governance_when_no_sponsor():
    """q1_2_sponsor = sin_sponsor activates governance_previo_ia."""
    payload = {"q1_2_sponsor": "sin_sponsor"}
    branches = TriggerDetector.detect_from_block_payload("block-1-strategic", payload)
    assert "governance_previo_ia" in branches


def test_no_triggers_on_successful_history():
    """q1_3_previous = exitoso_produccion activates no deep branches."""
    payload = {"q1_3_previous": "exitoso_produccion"}
    branches = TriggerDetector.detect_from_block_payload("block-1-strategic", payload)
    assert "post_mortem_proyecto" not in branches


def test_no_triggers_for_empty_payload():
    """Empty payload activates no deep branches."""
    branches = TriggerDetector.detect_from_block_payload("block-1-strategic", {})
    assert isinstance(branches, set)
    assert len(branches) == 0


# ---------------------------------------------------------------------------
# Test: multi-block detection
# ---------------------------------------------------------------------------


def test_detect_from_multiple_blocks():
    """Combining payloads from multiple blocks returns union of triggered branches."""
    block_payloads = {
        "block-1-strategic": {"q1_3_previous": "abandoned"},
        "block-6-compliance": {"q6_1_gdpr_role": "controller"},  # no deep trigger for this
    }
    branches = TriggerDetector.detect_from_all_blocks(block_payloads)
    assert "post_mortem_proyecto" in branches
    assert isinstance(branches, set)


def test_deduplication_across_blocks():
    """Same branch triggered by two blocks only appears once."""
    block_payloads = {
        "block-1-strategic": {"q1_3_previous": "abandoned"},
    }
    branches = TriggerDetector.detect_from_all_blocks(block_payloads)
    # Should be a set — no duplicates by definition
    assert branches == set(branches)


def test_unknown_block_returns_empty_set():
    """Unknown block ID returns empty set (no crash)."""
    branches = TriggerDetector.detect_from_block_payload("block-99-unknown", {"any": "val"})
    assert isinstance(branches, set)
    assert len(branches) == 0
