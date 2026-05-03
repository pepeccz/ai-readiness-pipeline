"""
app/pipeline_steps — Decomposed pipeline steps.

Each step is an independently importable function so it can be called from
both the public form submission flow and the admin re-run endpoints.

All steps are SYNC. Async callers (runners.py) wrap them in asyncio.to_thread().
generate_pdf additionally requires holding app.jobs.pdf_lock.pdf_lock to
serialise LibreOffice invocations.

Steps:
  map_form.py               — map_form_to_rec(payload: dict) -> dict
  enrich_llm.py             — enrich_llm(rec, preserve_human_fields) -> dict
  enrich_recommendations.py — enrich_recommendations(rec) -> dict
  score.py                  — score(rec) -> dict  (CPU-only, no I/O)
  generate_pdf.py           — generate_pdf(rec, draft=False) -> Path

Implemented in Phase B Batch 1 (TASK-B-01).
"""

from app.pipeline_steps.map_form import map_form_to_rec
from app.pipeline_steps.enrich_llm import enrich_llm
from app.pipeline_steps.enrich_recommendations import enrich_recommendations
from app.pipeline_steps.score import score
from app.pipeline_steps.generate_pdf import generate_pdf

__all__ = [
    "map_form_to_rec",
    "enrich_llm",
    "enrich_recommendations",
    "score",
    "generate_pdf",
]
