"""
tests/unit/test_lead_scorer.py — RED tests for lead_scorer (T1.10)

Covers REQ-11.1 — 12 boundary cases:
  1.  Score=0    → reject_soft
  2.  Score=136  → auto_accept
  3.  Score=85   → auto_accept
  4.  Score=84   → review
  5.  Score=55   → review
  6.  Score=54   → cold_warm
  7.  Score=45   → cold_warm
  8.  Score=44   → cold_cool
  9.  Score=30   → cold_cool
  10. Score=29   → reject_soft
  11. Override: sector=salud + urgency=critica + score=60 → auto_accept
  12. Override: role=consultor_externo + commitment=agendar + score=92 → review + external_advocate=true
"""

from __future__ import annotations

import pytest


def _make_scorer():
    from app.services.scoring.lead_scorer import LeadScorer
    return LeadScorer()


class TestBucketBoundaries:
    """REQ-11.1 — 12 boundary cases."""

    def test_score_0_is_reject_soft(self):
        scorer = _make_scorer()
        result = scorer.score_from_total(0)
        assert result.bucket == "reject_soft"

    def test_score_136_is_auto_accept(self):
        scorer = _make_scorer()
        result = scorer.score_from_total(136)
        assert result.bucket == "auto_accept"

    def test_score_85_is_auto_accept(self):
        scorer = _make_scorer()
        result = scorer.score_from_total(85)
        assert result.bucket == "auto_accept"

    def test_score_84_is_review(self):
        scorer = _make_scorer()
        result = scorer.score_from_total(84)
        assert result.bucket == "review"

    def test_score_55_is_review(self):
        scorer = _make_scorer()
        result = scorer.score_from_total(55)
        assert result.bucket == "review"

    def test_score_54_is_cold_warm(self):
        scorer = _make_scorer()
        result = scorer.score_from_total(54)
        assert result.bucket == "cold_warm"

    def test_score_45_is_cold_warm(self):
        scorer = _make_scorer()
        result = scorer.score_from_total(45)
        assert result.bucket == "cold_warm"

    def test_score_44_is_cold_cool(self):
        scorer = _make_scorer()
        result = scorer.score_from_total(44)
        assert result.bucket == "cold_cool"

    def test_score_30_is_cold_cool(self):
        scorer = _make_scorer()
        result = scorer.score_from_total(30)
        assert result.bucket == "cold_cool"

    def test_score_29_is_reject_soft(self):
        scorer = _make_scorer()
        result = scorer.score_from_total(29)
        assert result.bucket == "reject_soft"


class TestOverrideIntegration:
    """Cases 11 and 12 — override rules applied during full scoring."""

    def test_regulated_urgent_override(self):
        """Case 11: sector=salud + urgency=critica + score=60 → auto_accept"""
        scorer = _make_scorer()
        answers = {
            "triage.q.sector": "salud",
            "triage.q.urgency": "critica",
            "triage.q.company_size": "26_100",
            "triage.q.ai_maturity": "pilotos",
            "triage.q.respondent_role": "ceo_fundador",
            "triage.q.commitment": "propuesta_formal",
            "triage.q.ai_goals": ["reducir_costes"],
        }
        override_rules = [
            {
                "id": "regulated_urgent_force_accept",
                "condition": {
                    "sector_in": ["salud", "legal", "finanzas"],
                    "urgency_in": ["alta", "critica"],
                    "min_score": 55,
                },
                "action": "force_bucket",
                "target_bucket": "auto_accept",
                "applies_only_upgrade": True,
            }
        ]
        result = scorer.score(answers, override_rules=override_rules)
        assert result.bucket == "auto_accept"

    def test_external_advocate_override(self):
        """Case 12: role=consultor_externo + commitment=agendar + score=92 → review + external_advocate"""
        scorer = _make_scorer()
        answers = {
            "triage.q.sector": "tecnologia",
            "triage.q.company_size": "101_500",
            "triage.q.ai_maturity": "produccion_gobernada",
            "triage.q.urgency": "critica",
            "triage.q.ai_goals": ["reducir_costes", "mejorar_clientes"],
            "triage.q.respondent_role": "consultor_externo",
            "triage.q.commitment": "agendar",
        }
        override_rules = [
            {
                "id": "external_advocate_review",
                "condition": {
                    "respondent_role": "consultor_externo",
                    "commitment": "agendar",
                },
                "action": "force_bucket",
                "target_bucket": "review",
                "set_flag": "external_advocate",
            }
        ]
        result = scorer.score(answers, override_rules=override_rules)
        assert result.bucket == "review"
        assert result.flags.get("external_advocate") is True


class TestScorerPurity:
    """Pure function — deterministic for same input."""

    def test_deterministic_for_same_input(self):
        scorer = _make_scorer()
        answers = {
            "triage.q.sector": "tecnologia",
            "triage.q.company_size": "26_100",
            "triage.q.ai_maturity": "pilotos",
            "triage.q.urgency": "alta",
            "triage.q.ai_goals": ["automatizar_procesos"],
            "triage.q.respondent_role": "ceo_fundador",
            "triage.q.commitment": "agendar",
        }
        r1 = scorer.score(answers)
        r2 = scorer.score(answers)
        assert r1.total_score == r2.total_score
        assert r1.bucket == r2.bucket
