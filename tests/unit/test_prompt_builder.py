"""
tests/unit/test_prompt_builder.py — T6.1

Tests for app/services/ai_analysis/prompt_builder.py:
  - system prompt has cache_control=ephemeral
  - schema block has cache_control=ephemeral
  - user message (responses) has NO cache_control
  - _scrub_pii replaces nombre/email/teléfono with placeholders
"""

from __future__ import annotations

import pytest

from app.services.ai_analysis.prompt_builder import PromptBuilder, _scrub_pii


BLOCK_SCHEMA = {
    "id": "block-1-strategic",
    "title": "Estrategia",
    "questions": [
        {"id": "q1", "type": "text", "label": "¿Cuál es el objetivo principal?"},
    ],
}

SIMPLE_PAYLOAD = {
    "q1": "Mejorar eficiencia operativa",
}

PAYLOAD_WITH_PII = {
    "q1": "Mi nombre es Juan García, llámame al 612345678 o escríbeme a juan@empresa.com",
}

PREV_ANALYSES = [
    {
        "block_id": "block-1-strategic",
        "synthesis": "La empresa busca automatizar procesos repetitivos.",
    }
]


class TestPromptBuilderCacheControl:
    """T6.1 — system and schema content have cache_control=ephemeral."""

    def setup_method(self):
        self.builder = PromptBuilder()

    def test_system_content_has_cache_control_ephemeral(self):
        messages = self.builder.build(BLOCK_SCHEMA, SIMPLE_PAYLOAD, [])
        # The first content block should be the system prompt with cache_control
        user_message = messages[0]
        assert user_message["role"] == "user"
        content_blocks = user_message["content"]
        system_block = content_blocks[0]
        assert system_block.get("cache_control") == {"type": "ephemeral"}

    def test_schema_content_has_cache_control_ephemeral(self):
        messages = self.builder.build(BLOCK_SCHEMA, SIMPLE_PAYLOAD, [])
        user_message = messages[0]
        content_blocks = user_message["content"]
        schema_block = content_blocks[1]
        assert schema_block.get("cache_control") == {"type": "ephemeral"}

    def test_user_responses_block_has_no_cache_control(self):
        messages = self.builder.build(BLOCK_SCHEMA, SIMPLE_PAYLOAD, [])
        user_message = messages[0]
        content_blocks = user_message["content"]
        responses_block = content_blocks[-1]
        assert "cache_control" not in responses_block

    def test_block_schema_id_in_schema_content(self):
        messages = self.builder.build(BLOCK_SCHEMA, SIMPLE_PAYLOAD, [])
        user_message = messages[0]
        schema_block = user_message["content"][1]
        assert "block-1-strategic" in schema_block["text"]


class TestScrubPii:
    """T6.1 — _scrub_pii removes nombre/email/teléfono."""

    def test_scrub_email(self):
        text = "Contáctame en usuario@dominio.com para más info"
        result = _scrub_pii(text)
        assert "usuario@dominio.com" not in result
        assert "[EMAIL]" in result

    def test_scrub_phone_spanish_format(self):
        text = "Llámame al 612 345 678 cuando puedas"
        result = _scrub_pii(text)
        assert "612 345 678" not in result
        assert "[TEL]" in result

    def test_scrub_phone_international(self):
        text = "Mi teléfono es +34 91 234 56 78"
        result = _scrub_pii(text)
        assert "+34 91 234 56 78" not in result
        assert "[TEL]" in result

    def test_scrub_pii_in_payload_dict(self):
        """_scrub_pii applied to full payload dict removes PII from values."""
        payload = {"q1": "juan@empresa.com", "q2": "612345678"}
        scrubbed = _scrub_pii(payload)
        assert "juan@empresa.com" not in str(scrubbed)
        assert "612345678" not in str(scrubbed)
        assert "[EMAIL]" in str(scrubbed)
        assert "[TEL]" in str(scrubbed)
