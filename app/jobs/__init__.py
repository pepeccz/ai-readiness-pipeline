"""
app/jobs — Background job infrastructure.

  registry.py  — In-memory JobRegistry singleton (asyncio-safe).
  pdf_lock.py  — Module-global asyncio.Lock for LibreOffice (one conversion at a time).
  runners.py   — Async job runners that update the registry and persist results.

Implemented in Phase B (TASK-B-06).
"""
