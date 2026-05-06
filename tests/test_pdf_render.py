"""
tests/test_pdf_render.py — Tests for render_session1_pdf pure function.

C.5: render returns PDF bytes; hypothesis absent; null roadmap graceful.

WeasyPrint requires OS-level C libraries. Tests requiring actual PDF bytes
are marked with @pytest.mark.requires_weasyprint. Tests that only check
HTML rendering (no bytes conversion) run always.
"""

from __future__ import annotations

import pytest


# ─── Fixtures ──────────────────────────────────────────────────────────────

def _make_synthesis(**overrides):
    from app.services.sessions.synthesis_schema import Session1SynthesisOutput

    defaults = {
        "summary": "Empresa con alto potencial.",
        "key_insights": ["Insight 1", "Insight 2"],
        "recommendations": [
            {
                "text": "Implementar RPA",
                "impact": "alto",
                "effort": "medio",
                "related_service": "desarrollo_acompanamiento",
            }
        ],
        "roadmap": {"d30": ["Paso 1"], "d60": [], "d90": ["Paso 3"]},
        "next_steps": ["Siguiente paso"],
        "hypothesis": "Este es el hypothesis interno que NO debe aparecer en el PDF.",
    }
    defaults.update(overrides)
    return Session1SynthesisOutput.model_validate(defaults)


def _make_lead(company_name="Test Corp SA", lead_id="lead-test-01"):
    class MockLead:
        id = lead_id

    obj = MockLead()
    obj.company_name = company_name
    return obj


def _get_catalog():
    from app.services.synthesis.catalog import get_catalog
    return get_catalog()


# ─── Tests that check HTML rendering (always run) ──────────────────────────

def test_render_html_contains_summary():
    """Rendered HTML contains the summary text."""
    from app.services.pdf.session1_report import render_html

    synthesis = _make_synthesis()
    html = render_html(synthesis, _make_lead(), _get_catalog())

    assert "Empresa con alto potencial." in html


def test_render_hypothesis_absent_from_html():
    """hypothesis field NEVER appears in rendered HTML output."""
    from app.services.pdf.session1_report import render_html

    synthesis = _make_synthesis()
    html = render_html(synthesis, _make_lead(), _get_catalog())

    # The hypothesis value itself must not appear
    assert "hypothesis interno" not in html
    # The word "hypothesis" should not appear as a label either
    assert "hypothesis" not in html.lower()


def test_render_null_roadmap_graceful():
    """Synthesis with null roadmap renders without error."""
    from app.services.pdf.session1_report import render_html

    synthesis = _make_synthesis(roadmap=None)
    html = render_html(synthesis, _make_lead(), _get_catalog())

    assert html  # non-empty
    assert "None" not in html  # no Python None literals visible


def test_render_null_synthesis_sections_graceful():
    """All optional sections can be null without crashing."""
    from app.services.pdf.session1_report import render_html

    synthesis = _make_synthesis(
        summary=None,
        key_insights=None,
        recommendations=None,
        roadmap=None,
        next_steps=None,
    )
    html = render_html(synthesis, _make_lead(), _get_catalog())
    assert html  # must render without exception
    assert "None" not in html


def test_render_html_contains_catalog():
    """Rendered HTML contains catalog service names in footer section."""
    from app.services.pdf.session1_report import render_html

    synthesis = _make_synthesis()
    html = render_html(synthesis, _make_lead(), _get_catalog())

    assert "Diagnóstico Profundo de Procesos" in html
    assert "Formación Personalizada en IA" in html


# ─── Tests that require WeasyPrint (skip if libs absent) ───────────────────

def _weasyprint_available() -> bool:
    try:
        import weasyprint  # noqa: F401
        return True
    except ImportError:
        return False


requires_weasyprint = pytest.mark.skipif(
    not _weasyprint_available(),
    reason="WeasyPrint C libraries not installed — skipping PDF bytes tests"
)


@requires_weasyprint
def test_render_returns_pdf_bytes():
    """render_session1_pdf returns bytes starting with PDF magic number."""
    from app.services.pdf.session1_report import render_session1_pdf

    synthesis = _make_synthesis()
    pdf_bytes = render_session1_pdf(synthesis, _make_lead(), _get_catalog())

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b"%PDF"
    assert len(pdf_bytes) > 1000  # sanity check — valid PDF is never tiny
