"""
app/services/ai_analysis/json_extractor — Robust JSON extraction from LLM responses.

Exports:
  extract_json(raw: str) -> dict
  JsonExtractionError — raised when all extraction attempts fail; carries raw_text

Algorithm (cascading fallbacks):
  1. json.loads(raw.strip()) — fast path
  2. Strip ```json ... ``` or ``` ... ``` code fences, retry parse
  3. regex re.search(r'{...}') for outermost braces, parse
  4. Raise JsonExtractionError with full raw payload attached
"""

from __future__ import annotations

import json
import re


class JsonExtractionError(Exception):
    """Raised when no valid JSON object can be extracted from the raw LLM output."""

    def __init__(self, raw_text: str) -> None:
        self.raw_text = raw_text
        super().__init__(f"Failed to extract JSON from LLM response (len={len(raw_text)})")


# Matches ```json ... ``` or ``` ... ``` — greedy inner content
_CODE_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)

# Matches a {...} block — non-greedy so we get the FIRST complete object
_BRACE_RE = re.compile(r"\{[\s\S]*?\}")


def extract_json(raw: str) -> dict:
    """
    Extract and parse the first valid JSON object from an LLM text response.

    Tries three strategies in order:
      1. Direct json.loads on stripped input (fast path — no overhead on clean responses)
      2. Strip Markdown code fences and retry
      3. Regex search for outermost {...} block

    Raises:
        JsonExtractionError: If all strategies fail. The exception carries the
            full raw_text attribute for forensic logging.
    """
    # ── 1. Fast path ─────────────────────────────────────────────────────────
    stripped = raw.strip()
    if stripped:
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    # ── 2. Strip code fences ─────────────────────────────────────────────────
    fence_match = _CODE_FENCE_RE.search(raw)
    if fence_match:
        inner = fence_match.group(1).strip()
        try:
            return json.loads(inner)
        except json.JSONDecodeError:
            pass

    # ── 3. Regex: outermost {...} ─────────────────────────────────────────────
    brace_match = _BRACE_RE.search(raw)
    if brace_match:
        candidate = brace_match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # ── 4. Give up ────────────────────────────────────────────────────────────
    raise JsonExtractionError(raw)
