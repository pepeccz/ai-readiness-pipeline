"""
app/pipeline_steps/generate_pdf — PDF generation step.

Thin wrapper that:
  1. Calls report_generator.generate_report(rec) → .docx
  2. Invokes LibreOffice headless to convert .docx → .pdf
  3. Moves the resulting .pdf to /app/output/{assessment_id}.pdf
  4. Returns the Path of the final PDF

This is a SYNC function. Async callers (runners.py, Batch 3) MUST wrap it
inside the pdf_lock to prevent concurrent LibreOffice instances:

    from app.jobs.pdf_lock import pdf_lock

    async with pdf_lock:
        pdf_path = await asyncio.to_thread(generate_pdf, rec, draft)

The lock lives in `app.jobs.pdf_lock` (not here) so the caller controls
when to acquire it. This keeps the step itself pure and testable without
needing an event loop.

Design reference: design §2.3, §1 (pipeline_steps layout), risk #4.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

# Output dir — created in Dockerfile (RUN mkdir -p /app/output).
# Falls back to /tmp/reports in dev (matches report_generator default).
_OUTPUT_DIR = Path(os.environ.get("PDF_OUTPUT_DIR", "/app/output"))

# Watermark string injected into rec["_draft_watermark"] when draft=True.
# The report generator checks for this key and overlays the text.
# If report_generator doesn't support it yet, we embed it in company_name
# as a visible marker — harmless for production (draft PDFs are ephemeral).
_DRAFT_MARKER = "BORRADOR — NO DISTRIBUIR"


def generate_pdf(rec: dict, draft: bool = False) -> Path:
    """Generate a PDF report from a rec dict.

    This is a SYNC function — call from async code via asyncio.to_thread(),
    and hold `app.jobs.pdf_lock.pdf_lock` before calling to serialise
    LibreOffice invocations.

    Args:
        rec:
            Internal rec dict. Must have all enrichment + scoring fields.
            NOT mutated — a shallow copy is made when draft=True.
        draft:
            When True, injects a watermark marker into the rec copy before
            generating the report. The PDF is stored under a separate
            ``_draft_`` filename and is NOT persisted as the canonical pdf_path
            on the Assessment row (callers handle that distinction).

    Returns:
        Path to the generated PDF file under _OUTPUT_DIR.

    Raises:
        RuntimeError: If LibreOffice conversion fails (non-zero returncode or
                      PDF file not found after conversion).
        Any exception from report_generator.generate_report also propagates.
    """
    # Inline import — report_generator lives at project root
    from report_generator import generate_report  # type: ignore[import]

    assessment_id: str = rec.get("assessment_id", "unknown")

    # For draft mode, work on a shallow copy so the caller's rec is not affected
    work_rec = dict(rec) if draft else rec
    if draft:
        # Signal to report_generator (if supported) and embed in the doc title
        work_rec["_draft_watermark"] = _DRAFT_MARKER
        # Prepend to company_name as a visible indicator in the report header
        # This ensures the watermark is visible even if report_generator
        # doesn't handle _draft_watermark yet.
        work_rec["company_name"] = f"[{_DRAFT_MARKER}] {work_rec.get('company_name', '')}"

    logger.info(
        "generate_pdf_start",
        assessment_id=assessment_id,
        draft=draft,
        output_dir=str(_OUTPUT_DIR),
    )

    # Use a TemporaryDirectory so all intermediate files are cleaned up on any exit
    with tempfile.TemporaryDirectory(prefix="airep_") as tmpdir:
        # Step 1: generate .docx inside the temp dir
        docx_path = generate_report(work_rec, output_path=os.path.join(tmpdir, f"{assessment_id}.docx"))
        logger.debug("generate_pdf_docx_done", docx_path=docx_path)

        # Step 2: LibreOffice headless conversion
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                tmpdir,
                docx_path,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            logger.error(
                "generate_pdf_libreoffice_failed",
                assessment_id=assessment_id,
                returncode=result.returncode,
                stderr=result.stderr[:500],
            )
            raise RuntimeError(
                f"LibreOffice conversion failed (rc={result.returncode}): {result.stderr[:200]}"
            )

        # LibreOffice names the output file after the input basename
        pdf_tmp = Path(docx_path).with_suffix(".pdf")
        if not pdf_tmp.exists():
            raise RuntimeError(
                f"LibreOffice returned 0 but PDF not found at {pdf_tmp}"
            )

        # Step 3: move PDF to persistent output dir
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        prefix = "_draft_" if draft else ""
        dest = _OUTPUT_DIR / f"{prefix}{assessment_id}.pdf"
        shutil.move(str(pdf_tmp), str(dest))

    logger.info(
        "generate_pdf_done",
        assessment_id=assessment_id,
        draft=draft,
        pdf_path=str(dest),
    )
    return dest
