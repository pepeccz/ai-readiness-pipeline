"""
tests/services/test_prompt_builder.py — B-2 (REQ-3)

Asserts that SYSTEM_PROMPT contains the 3-criteria falsifiable follow-up text
and the PROHIBIDO clauses per the design spec.

Tests are string-presence only — NO LLM output assertions.
"""

from __future__ import annotations

from app.services.ai_analysis.prompt_builder import SYSTEM_PROMPT


class TestSystemPromptFalsifiableCriteria:
    """B-2 — REQ-3: SYSTEM_PROMPT bullet 3 contains the 3 criteria + PROHIBIDO list."""

    def test_anchoring_criterion_present(self):
        """Anclada a tensión específica — question must cite the tension it resolves."""
        assert "Anclada a tensión específica" in SYSTEM_PROMPT

    def test_decision_altering_criterion_present(self):
        """Cambia la recomendación — answer must be a decision, not a definition."""
        assert "Cambia la recomendación" in SYSTEM_PROMPT

    def test_explicit_rationale_criterion_present(self):
        """Rationale explícito — each question must include an explicit rationale."""
        assert "Rationale explícito" in SYSTEM_PROMPT

    def test_prohibido_clause_present(self):
        """PROHIBIDO block must be present in SYSTEM_PROMPT."""
        assert "PROHIBIDO" in SYSTEM_PROMPT

    def test_prohibited_rephrase_pattern_present(self):
        """'¿podrías contarme más sobre' must be in the prohibited list."""
        assert "¿podrías contarme más sobre" in SYSTEM_PROMPT

    def test_prohibited_define_pattern_present(self):
        """'¿qué entendés por' must be in the prohibited list."""
        assert "¿qué entendés por" in SYSTEM_PROMPT
