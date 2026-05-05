"""
tests/unit/test_override_rules.py — RED tests for override_rules (T1.8)

Covers:
  - regulated_urgent_force_accept: sector=salud + urgency=critica + score>=55 → auto_accept
  - external_advocate_review: role=consultor_externo + commitment=agendar → review + flag
  - secondary_area_disabled_when_cross: cross-area mode → secondary_area disabled
"""

from __future__ import annotations

import pytest


# Override rules engine signature:
#   apply_overrides(answers: dict, base_score: int, base_bucket: str, rules: list[dict])
#     → OverrideResult(bucket, flags, extra_questions)


class TestRegulatedUrgentForceAccept:
    def test_salud_critica_score_60_becomes_auto_accept(self):
        from app.services.questionnaire.override_rules import apply_overrides

        answers = {
            "triage.q.sector": "salud",
            "triage.q.urgency": "critica",
        }
        rules = [
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
        result = apply_overrides(answers, base_score=60, base_bucket="review", rules=rules)

        assert result.bucket == "auto_accept"

    def test_regulated_score_below_55_does_not_upgrade(self):
        from app.services.questionnaire.override_rules import apply_overrides

        answers = {
            "triage.q.sector": "salud",
            "triage.q.urgency": "critica",
        }
        rules = [
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
        result = apply_overrides(answers, base_score=40, base_bucket="cold_cool", rules=rules)

        # Score < 55 → rule does NOT apply
        assert result.bucket == "cold_cool"

    def test_non_regulated_sector_not_affected(self):
        from app.services.questionnaire.override_rules import apply_overrides

        answers = {
            "triage.q.sector": "retail",
            "triage.q.urgency": "critica",
        }
        rules = [
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
        result = apply_overrides(answers, base_score=70, base_bucket="review", rules=rules)

        assert result.bucket == "review"


class TestExternalAdvocateReview:
    def test_consultor_externo_agendar_forces_review(self):
        from app.services.questionnaire.override_rules import apply_overrides

        answers = {
            "triage.q.respondent_role": "consultor_externo",
            "triage.q.commitment": "agendar",
        }
        rules = [
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
        result = apply_overrides(answers, base_score=92, base_bucket="auto_accept", rules=rules)

        assert result.bucket == "review"
        assert result.flags.get("external_advocate") is True

    def test_consultor_externo_no_agendar_not_affected(self):
        from app.services.questionnaire.override_rules import apply_overrides

        answers = {
            "triage.q.respondent_role": "consultor_externo",
            "triage.q.commitment": "informacion",
        }
        rules = [
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
        result = apply_overrides(answers, base_score=92, base_bucket="auto_accept", rules=rules)

        assert result.bucket == "auto_accept"
        assert not result.flags.get("external_advocate")


class TestSecondaryAreaDisabledWhenCross:
    def test_cross_area_disables_secondary_selection(self):
        from app.services.questionnaire.override_rules import apply_overrides

        answers = {
            "intake.area_mode": "cross_area",
        }
        rules = [
            {
                "id": "secondary_area_disabled_when_cross",
                "condition": {
                    "area_mode": "cross_area",
                },
                "action": "disable_field",
                "target_field": "secondary_area",
            }
        ]
        result = apply_overrides(answers, base_score=0, base_bucket="review", rules=rules)

        assert "secondary_area" in result.disabled_fields
