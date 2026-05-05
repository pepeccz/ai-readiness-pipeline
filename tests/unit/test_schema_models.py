"""
tests/unit/test_schema_models.py — RED tests for Pydantic v2 Question discriminated union (T1.3)

Covers:
  - SingleChoiceQuestion parses correctly
  - MultiChoiceQuestion parses correctly
  - TextQuestion parses correctly (type=text and type=textarea)
  - CompositeQuestion parses correctly
  - ConsentQuestion parses correctly
  - Invalid type raises ValidationError
  - Discriminated union works for all 5 variants via Question type alias
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError


class TestSingleChoiceQuestion:
    def test_parses_correctly(self):
        from app.schemas.questionnaire.core import SingleChoiceQuestion

        q = SingleChoiceQuestion(
            id="triage.q.sector",
            layer="triage",
            type="single_choice",
            label="Sector",
            required=True,
            options=[
                {"value": "tecnologia", "label": "Tecnología", "score": 18},
                {"value": "salud", "label": "Salud", "score": 15},
            ],
        )
        assert q.type == "single_choice"
        assert len(q.options) == 2
        assert q.options[0].score == 18

    def test_options_required(self):
        from app.schemas.questionnaire.core import SingleChoiceQuestion

        with pytest.raises(ValidationError):
            SingleChoiceQuestion(
                id="x",
                layer="triage",
                type="single_choice",
                label="L",
            )


class TestMultiChoiceQuestion:
    def test_parses_correctly(self):
        from app.schemas.questionnaire.core import MultiChoiceQuestion

        q = MultiChoiceQuestion(
            id="triage.q.goals",
            layer="triage",
            type="multi_choice",
            label="Objetivos",
            options=[
                {"value": "efficiency", "label": "Eficiencia", "score": 6},
            ],
            max_selections=2,
        )
        assert q.type == "multi_choice"
        assert q.max_selections == 2
        assert q.min_selections == 0


class TestTextQuestion:
    def test_type_text(self):
        from app.schemas.questionnaire.core import TextQuestion

        q = TextQuestion(
            id="triage.q.notes",
            layer="triage",
            type="text",
            label="Notas",
        )
        assert q.type == "text"

    def test_type_textarea(self):
        from app.schemas.questionnaire.core import TextQuestion

        q = TextQuestion(
            id="triage.q.notes2",
            layer="triage",
            type="textarea",
            label="Notas largas",
        )
        assert q.type == "textarea"


class TestCompositeQuestion:
    def test_parses_with_sub_fields(self):
        from app.schemas.questionnaire.core import CompositeQuestion

        q = CompositeQuestion(
            id="triage.q.identity",
            layer="triage",
            type="composite",
            label="Identidad",
            sub_fields=[
                {
                    "id": "triage.q.identity.name",
                    "layer": "triage",
                    "type": "text",
                    "label": "Nombre",
                }
            ],
        )
        assert q.type == "composite"
        assert len(q.sub_fields) == 1


class TestConsentQuestion:
    def test_parses_correctly(self):
        from app.schemas.questionnaire.core import ConsentQuestion

        q = ConsentQuestion(
            id="triage.q.privacy",
            layer="triage",
            type="consent",
            label="Acepto la política de privacidad",
            policy_version="v1.0-2026-05",
            policy_file="consents/privacy-v1.0-2026-05.md",
        )
        assert q.type == "consent"
        assert q.policy_version == "v1.0-2026-05"


class TestDiscriminatedUnion:
    def test_question_union_dispatches_single_choice(self):
        from app.schemas.questionnaire.core import parse_question

        q = parse_question({
            "id": "triage.q.sector",
            "layer": "triage",
            "type": "single_choice",
            "label": "Sector",
            "options": [{"value": "tech", "label": "Tech", "score": 18}],
        })
        from app.schemas.questionnaire.core import SingleChoiceQuestion
        assert isinstance(q, SingleChoiceQuestion)

    def test_question_union_dispatches_consent(self):
        from app.schemas.questionnaire.core import parse_question

        q = parse_question({
            "id": "triage.q.privacy",
            "layer": "triage",
            "type": "consent",
            "label": "Privacy",
            "policy_version": "v1.0-2026-05",
            "policy_file": "consents/privacy-v1.0-2026-05.md",
        })
        from app.schemas.questionnaire.core import ConsentQuestion
        assert isinstance(q, ConsentQuestion)

    def test_invalid_type_raises(self):
        from app.schemas.questionnaire.core import parse_question

        with pytest.raises((ValidationError, ValueError)):
            parse_question({
                "id": "triage.q.bad",
                "layer": "triage",
                "type": "unknown_type",
                "label": "Bad",
            })
