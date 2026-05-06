"""
tests/unit/services/ai_analysis/test_json_extractor.py — A-1

Unit tests for extract_json() following strict TDD RED-GREEN cycle.

Scenarios:
  1. Balanced JSON (fast path)
  2. Code-fenced JSON (```json ... ```)
  3. Prefaced prose + JSON object
  4. Invalid input → raises JsonExtractionError with raw attached
  5. Multiple JSON objects → only first balanced one returned
  6. Bare code fence (no 'json' language tag)
"""

from __future__ import annotations

import pytest

from app.services.ai_analysis.json_extractor import JsonExtractionError, extract_json


class TestExtractJsonFastPath:
    def test_plain_json_returns_dict(self):
        raw = '{"a": 1, "b": "hello"}'
        result = extract_json(raw)
        assert result == {"a": 1, "b": "hello"}

    def test_plain_json_with_leading_whitespace(self):
        raw = '  \n{"x": 42}\n  '
        result = extract_json(raw)
        assert result == {"x": 42}

    def test_nested_json(self):
        raw = '{"outer": {"inner": [1, 2, 3]}}'
        result = extract_json(raw)
        assert result == {"outer": {"inner": [1, 2, 3]}}


class TestExtractJsonCodeFences:
    def test_json_code_fence_with_language_tag(self):
        raw = '```json\n{"a": 1}\n```'
        result = extract_json(raw)
        assert result == {"a": 1}

    def test_json_code_fence_without_language_tag(self):
        raw = '```\n{"b": 2}\n```'
        result = extract_json(raw)
        assert result == {"b": 2}

    def test_code_fence_with_surrounding_text(self):
        raw = "Here is the result:\n```json\n{\"status\": \"ok\"}\n```\nDone."
        result = extract_json(raw)
        assert result == {"status": "ok"}

    def test_code_fence_preserves_nested_structure(self):
        raw = '```json\n{"follow_ups": [{"text": "Q1", "priority": "high"}]}\n```'
        result = extract_json(raw)
        assert result["follow_ups"][0]["text"] == "Q1"


class TestExtractJsonProseBeforeObject:
    def test_prose_then_json(self):
        raw = 'Some analysis text here.\n{"b": 2}'
        result = extract_json(raw)
        assert result == {"b": 2}

    def test_multiline_prose_before_json(self):
        raw = "Line one.\nLine two.\nLine three.\n{\"key\": \"value\"}"
        result = extract_json(raw)
        assert result == {"key": "value"}

    def test_first_object_returned_when_multiple(self):
        raw = '{"first": 1} some text {"second": 2}'
        result = extract_json(raw)
        assert result == {"first": 1}


class TestExtractJsonFailure:
    def test_invalid_json_raises_extraction_error(self):
        raw = "not json at all"
        with pytest.raises(JsonExtractionError):
            extract_json(raw)

    def test_extraction_error_carries_raw_text(self):
        raw = "completely invalid content !!!"
        with pytest.raises(JsonExtractionError) as exc_info:
            extract_json(raw)
        assert exc_info.value.raw_text == raw

    def test_empty_string_raises_extraction_error(self):
        with pytest.raises(JsonExtractionError):
            extract_json("")

    def test_only_whitespace_raises_extraction_error(self):
        with pytest.raises(JsonExtractionError):
            extract_json("   \n  ")

    def test_unclosed_brace_raises_extraction_error(self):
        raw = '{"key": "value"'
        with pytest.raises(JsonExtractionError):
            extract_json(raw)
