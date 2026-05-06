"""
tests/test_pdf_filename.py — Unit tests for PDF filename builder.

C.3: Spanish company names → ASCII slug; null name → fallback.
"""

from __future__ import annotations

import re


def _make_lead(company_name=None, lead_id="abc-123"):
    """Create a minimal mock lead object."""
    class MockLead:
        id = lead_id
        company_name = None

    obj = MockLead()
    obj.company_name = company_name
    return obj


def test_slug_spanish_company():
    """Spanish company name with accents → valid ASCII slug."""
    from app.services.pdf.filename import build_pdf_filename

    lead = _make_lead(company_name="Diagnóstico Corp S.A.")
    filename = build_pdf_filename(lead)

    assert filename.endswith(".pdf")
    # Should contain a slugified version of the company name
    assert "diagnostico" in filename
    assert "corp" in filename
    # No accents or uppercase
    assert filename == filename.lower()


def test_slug_null_company_uses_lead_id():
    """Null company name → fallback with lead_id."""
    from app.services.pdf.filename import build_pdf_filename

    lead = _make_lead(company_name=None, lead_id="lead-42")
    filename = build_pdf_filename(lead)

    assert filename.endswith(".pdf")
    assert "lead-42" in filename
    assert "diagnostico" in filename


def test_filename_format():
    """Filename matches expected pattern: {slug}-diagnostico-{date}.pdf."""
    from app.services.pdf.filename import build_pdf_filename

    lead = _make_lead(company_name="Empresa Test")
    filename = build_pdf_filename(lead)

    # Must have YYYY-MM-DD date near end
    assert re.search(r"\d{4}-\d{2}-\d{2}", filename) is not None
    assert "diagnostico" in filename
    assert filename.endswith(".pdf")
