"""
app/jobs/pdf_lock — Module-global asyncio.Lock for LibreOffice serialisation.

LibreOffice headless does not support concurrent conversions reliably in a
single process. This lock ensures only one PDF generation runs at a time.

Usage (in async context):
    from app.jobs.pdf_lock import pdf_lock

    async with pdf_lock:
        pdf_path = await asyncio.to_thread(_run_libreoffice, docx_path)

The lock is module-global (singleton per process). It is initialised when this
module is first imported — which happens during the FastAPI startup sequence.
Any module that imports pdf_lock will share the same instance.

Design reference: design §2.3.
"""

import asyncio

# Singleton per process. Lost on restart — acceptable (jobs restart cleanly).
pdf_lock: asyncio.Lock = asyncio.Lock()
