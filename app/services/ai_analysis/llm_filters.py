"""
app/services/ai_analysis/llm_filters — 5-layer post-LLM suggestion filter pipeline.

Layers (applied in order):
  1. Confidence threshold  — discard if confidence < threshold (default 0.65)
  2. Dedup                 — discard near-duplicates via n-gram overlap
  3. Scope                 — discard suggestions outside block domain
  4. Similarity to questions — discard restatements of existing questions
  5. Length                — discard < min_len chars; truncate > max_len chars

After all layers: cap at 3 suggestions (max per spec).
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Layer 1 — Confidence threshold
# ---------------------------------------------------------------------------

def apply_confidence_filter(
    items: list[dict],
    threshold: float = 0.65,
) -> list[dict]:
    """Discard items with confidence below threshold."""
    return [item for item in items if item.get("confidence", 0.0) >= threshold]


# ---------------------------------------------------------------------------
# Layer 2 — Dedup (n-gram overlap similarity)
# ---------------------------------------------------------------------------

def _ngrams(text: str, n: int = 3) -> set[str]:
    """Generate character n-grams for a normalized text."""
    normalized = re.sub(r"\s+", " ", text.lower().strip())
    return {normalized[i:i+n] for i in range(len(normalized) - n + 1)}


def _ngram_similarity(a: str, b: str, n: int = 3) -> float:
    """
    Compute similarity between two strings via character n-gram overlap (Jaccard).

    Returns float 0-1.
    """
    if not a or not b:
        return 0.0
    ngrams_a = _ngrams(a, n)
    ngrams_b = _ngrams(b, n)
    if not ngrams_a or not ngrams_b:
        return 0.0
    intersection = len(ngrams_a & ngrams_b)
    union = len(ngrams_a | ngrams_b)
    return intersection / union if union > 0 else 0.0


def apply_dedup_filter(
    items: list[dict],
    similarity_threshold: float = 0.70,
) -> list[dict]:
    """Discard items that are too similar to already-kept items."""
    kept: list[dict] = []
    for item in items:
        text = item.get("text", "")
        is_duplicate = any(
            _ngram_similarity(text, kept_item.get("text", "")) > similarity_threshold
            for kept_item in kept
        )
        if not is_duplicate:
            kept.append(item)
    return kept


# ---------------------------------------------------------------------------
# Layer 3 — Scope filter (keyword blocklist per block domain)
# ---------------------------------------------------------------------------

# Block-level out-of-scope keyword blocklists.
# Keys: block_id prefix. Values: list of keywords that indicate scope breach.
_OUT_OF_SCOPE_KEYWORDS: dict[str, list[str]] = {
    "block-1-strategic": [
        "servidor", "cpu", "ram", "memoria", "kubernetes",
        "docker", "container", "vpc", "firewall",
    ],
    "block-2-process": [
        "gdpr", "rgpd", "dpia", "lopd", "regulación", "cumplimiento normativo",
    ],
    "block-3-data": [
        "servidor", "kubernetes", "docker",
    ],
    "block-4-talent": [
        "servidor", "infraestructura", "kubernetes",
    ],
    "block-5-infrastructure": [],  # infrastructure can discuss almost anything
    "block-6-compliance": [
        "servidor", "kubernetes", "docker",
    ],
    "block-7-governance": [],
}


def apply_scope_filter(items: list[dict], block_id: str) -> list[dict]:
    """Discard suggestions mentioning topics outside the block domain."""
    # Find matching blocklist prefix
    blocklist: list[str] = []
    for prefix, keywords in _OUT_OF_SCOPE_KEYWORDS.items():
        if block_id.startswith(prefix):
            blocklist = keywords
            break

    if not blocklist:
        return items  # No restrictions for this block

    def is_in_scope(text: str) -> bool:
        lower = text.lower()
        return not any(kw in lower for kw in blocklist)

    return [item for item in items if is_in_scope(item.get("text", ""))]


# ---------------------------------------------------------------------------
# Layer 4 — Similarity to questions in block schema
# ---------------------------------------------------------------------------

def apply_similarity_to_questions_filter(
    items: list[dict],
    block_schema: dict,
    threshold: float = 0.70,
) -> list[dict]:
    """Discard suggestions that are restatements of questions already in the block."""
    questions = block_schema.get("questions", [])
    question_texts = [q.get("label", "") for q in questions if q.get("label")]

    def is_novel(text: str) -> bool:
        return not any(
            _ngram_similarity(text, q_text) > threshold
            for q_text in question_texts
        )

    return [item for item in items if is_novel(item.get("text", ""))]


# ---------------------------------------------------------------------------
# Layer 5 — Length filter
# ---------------------------------------------------------------------------

def apply_length_filter(
    items: list[dict],
    min_len: int = 15,
    max_len: int = 280,
) -> list[dict]:
    """Discard suggestions shorter than min_len. Truncate those longer than max_len."""
    result = []
    for item in items:
        text = item.get("text", "")
        if len(text) < min_len:
            continue
        if len(text) > max_len:
            item = {**item, "text": text[:max_len]}
        result.append(item)
    return result


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------

def apply_all_filters(
    items: list[dict],
    context: dict,
    confidence_threshold: float = 0.65,
    max_suggestions: int = 3,
) -> list[dict]:
    """
    Apply all 5 layers in order and cap at max_suggestions.

    context: {
        "block_schema": dict,   # required for layers 3 + 4
        "prev_suggestions": [], # reserved for future use
    }
    """
    block_schema = context.get("block_schema", {})
    block_id = block_schema.get("id", "")

    # Layer 1 — Confidence
    items = apply_confidence_filter(items, threshold=confidence_threshold)
    # Layer 2 — Dedup
    items = apply_dedup_filter(items)
    # Layer 3 — Scope
    items = apply_scope_filter(items, block_id=block_id)
    # Layer 4 — Similarity to questions
    items = apply_similarity_to_questions_filter(items, block_schema=block_schema)
    # Layer 5 — Length
    items = apply_length_filter(items)

    # Cap at max_suggestions
    return items[:max_suggestions]
