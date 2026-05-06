"""
app/observability — In-memory observability counters (T10.4).

Lightweight counters exposed via GET /api/health.
Single-process only (acceptable for MVP single-instance deployment).

Counters:
  rate_limit_hits        — total rate-limited requests processed (before block decision)
  rate_limit_blocks      — total requests blocked by rate limit (429 responses)
  llm_output_field_missing — LLM response missing a declared output field
  llm_output_unparseable — LLM response could not be parsed as JSON at all
"""

from __future__ import annotations

import threading

_lock = threading.Lock()

_counters: dict[str, int] = {
    "rate_limit_hits": 0,
    "rate_limit_blocks": 0,
}


def increment(key: str, amount: int = 1, tags: dict[str, str] | None = None) -> None:
    """Thread-safe counter increment.

    `tags` is accepted for semantic labeling (e.g. block_id, field) but
    in this in-memory implementation all labeled increments map to the
    same base counter. This keeps things simple while preserving the
    call-site API that could later be swapped for a real metrics backend.
    """
    with _lock:
        _counters[key] = _counters.get(key, 0) + amount


def get_counters() -> dict[str, int]:
    """Return a snapshot of all counters."""
    with _lock:
        return dict(_counters)


def get(key: str) -> int:
    """Return a single counter value."""
    with _lock:
        return _counters.get(key, 0)
