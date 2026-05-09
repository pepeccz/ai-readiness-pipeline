"""
tests/services/pdf/test_session2_report_render.py

TDD tests for render_session2_pdf — PR4 (D.1 RED).

Covers:
- Non-empty PDF bytes returned (starts with %PDF header)
- BORRADOR watermark present when draft=True
- Cover contains composite_score and risk_profile
- Scorecard lists 7 blocks with their CMMI level names
- Insufficient_data blocks render "Datos pendientes — completar en Sesión 2"
- Recommendations are sorted by gap descending (largest gap first)

REQ: REQ-08, REQ-18, REQ-19, REQ-20, REQ-21
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

def _make_session_data(
    *,
    insufficient_blocks=None,
    recommendation_gaps=None,
):
    """
    Build a minimal session_data dict for render_session2_pdf.

    Parameters
    ----------
    insufficient_blocks : list[dict] | None
        Override the default insufficient_blocks list.
    recommendation_gaps : list[float] | None
        target_gap_size values for 3 recommendations (default: 0.8, 0.3, 0.6)
    """
    if insufficient_blocks is None:
        insufficient_blocks = []

    if recommendation_gaps is None:
        recommendation_gaps = [0.8, 0.3, 0.6]

    per_block = [
        {
            "block_id": "block-1-strategic",
            "block_title": "Estrategia",
            "score": 0.45,
            "level": 2,
            "level_name": "Establecido",
            "indicators_synthesized": "Estrategia moderada.",
        },
        {
            "block_id": "block-2-process-critical",
            "block_title": "Proceso Crítico",
            "score": 0.30,
            "level": 1,
            "level_name": "Emergente",
            "indicators_synthesized": "Procesos emergentes.",
        },
        {
            "block_id": "block-3-data",
            "block_title": "Datos",
            "score": 0.60,
            "level": 3,
            "level_name": "Avanzado",
            "indicators_synthesized": "Buena gestión de datos.",
        },
        {
            "block_id": "block-4-talent",
            "block_title": "Talento",
            "score": 0.20,
            "level": 1,
            "level_name": "Emergente",
            "indicators_synthesized": "Equipo en desarrollo.",
        },
        {
            "block_id": "block-5-infrastructure",
            "block_title": "Infraestructura",
            "score": 0.55,
            "level": 2,
            "level_name": "Establecido",
            "indicators_synthesized": "Infraestructura adecuada.",
        },
        {
            "block_id": "block-6-compliance",
            "block_title": "Compliance",
            "score": 0.10,
            "level": 0,
            "level_name": "Inicial",
            "indicators_synthesized": "Compliance muy inicial.",
        },
        {
            "block_id": "block-7-governance",
            "block_title": "Gobernanza",
            "score": 0.35,
            "level": 1,
            "level_name": "Emergente",
            "indicators_synthesized": "Gobernanza básica.",
        },
    ]

    recommendations = [
        {
            "text": f"Recomendación {i+1}",
            "impact": "alto",
            "effort": "medio",
            "related_service": None,
            "custom_service_label": None,
            "target_block_id": f"block-{i+1}",
            "target_gap_size": gap,
        }
        for i, gap in enumerate(recommendation_gaps)
    ]

    return {
        "company_name": "Pepe Cabeza SL",
        "sector": "legal",
        "contact_name": "Pepe Cabeza",
        "contact_email": "pepe@pepecabeza.com",
        "reference_id": "CC8C4482",
        "generation_date": "9 de mayo de 2026",
        "composite_score": 0.36,
        "composite_level": 1,
        "composite_level_name": "Emergente",
        "risk_profile": "high",
        "per_block": per_block,
        "insufficient_blocks": insufficient_blocks,
        "recommendations": recommendations,
        "roadmap": {
            "d30": ["Prioridad: definir política de compliance IA"],
            "d60": ["Contratar perfil de datos senior"],
            "d90": ["Revisar gobernanza con Comité de Dirección"],
        },
        "next_steps": [
            "Revisar hallazgos en Sesión 2",
            "Validar prioridades con sponsor",
        ],
        "hypothesis": "Esto no debe aparecer en el PDF.",
    }


# ---------------------------------------------------------------------------
# D.1 — Tests for render_session2_pdf
# ---------------------------------------------------------------------------


class TestRenderSession2PdfBytes:
    """render_session2_pdf returns non-empty PDF bytes."""

    def test_returns_bytes(self):
        from app.services.pdf.session2_report import render_session2_pdf

        session_data = _make_session_data()
        result = render_session2_pdf(session_data, draft=False)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_output_is_valid_pdf(self):
        """PDF bytes must start with the PDF magic header."""
        from app.services.pdf.session2_report import render_session2_pdf

        session_data = _make_session_data()
        result = render_session2_pdf(session_data, draft=False)

        assert result[:4] == b"%PDF", f"Expected PDF header, got: {result[:8]!r}"


class TestDraftWatermark:
    """draft=True renders BORRADOR watermark; draft=False does not."""

    def test_draft_true_includes_borrador_in_html(self):
        """HTML rendered with draft=True must contain BORRADOR text."""
        from app.services.pdf.session2_report import render_html as render_session2_html

        session_data = _make_session_data()
        html = render_session2_html(session_data, draft=True)

        assert "BORRADOR" in html

    def test_draft_false_excludes_borrador_from_html(self):
        """HTML rendered with draft=False must NOT contain BORRADOR watermark div."""
        from app.services.pdf.session2_report import render_html as render_session2_html

        session_data = _make_session_data()
        html = render_session2_html(session_data, draft=False)

        # The actual watermark div text should not appear when draft=False
        # The CSS class definition may still appear in the stylesheet — we check for the rendered div
        assert 'class="borrador-watermark"' not in html


class TestCoverPageContent:
    """Cover page must contain composite_score and risk_profile (REQ-18)."""

    def test_cover_contains_company_name(self):
        from app.services.pdf.session2_report import render_html as render_session2_html

        session_data = _make_session_data()
        html = render_session2_html(session_data, draft=False)

        assert "Pepe Cabeza SL" in html

    def test_cover_contains_composite_level_name(self):
        """Cover must include composite CMMI level name (REQ-18)."""
        from app.services.pdf.session2_report import render_html as render_session2_html

        session_data = _make_session_data()
        html = render_session2_html(session_data, draft=False)

        # composite_level_name = "Emergente"
        assert "Emergente" in html

    def test_cover_contains_risk_profile(self):
        """Cover must display risk_profile badge (REQ-18)."""
        from app.services.pdf.session2_report import render_html as render_session2_html

        session_data = _make_session_data()
        html = render_session2_html(session_data, draft=False)

        # risk_profile = "high"
        assert "high" in html or "Alto" in html

    def test_cover_contains_composite_score_value(self):
        """Cover must show composite score numerically (REQ-18)."""
        from app.services.pdf.session2_report import render_html as render_session2_html

        session_data = _make_session_data()
        html = render_session2_html(session_data, draft=False)

        # composite_score = 0.36 → "36" or "36%" in HTML
        assert "36" in html


class TestScorecardSection:
    """Scorecard lists all 7 blocks with their CMMI level (REQ-19)."""

    def test_scorecard_contains_all_7_block_titles(self):
        from app.services.pdf.session2_report import render_html as render_session2_html

        session_data = _make_session_data()
        html = render_session2_html(session_data, draft=False)

        for block in session_data["per_block"]:
            assert block["block_title"] in html, (
                f"Block title '{block['block_title']}' not found in scorecard HTML"
            )

    def test_scorecard_contains_all_7_level_names(self):
        """Each block's CMMI level name must appear in the HTML (REQ-19)."""
        from app.services.pdf.session2_report import render_html as render_session2_html

        session_data = _make_session_data()
        html = render_session2_html(session_data, draft=False)

        # Unique level names used: Establecido, Emergente, Avanzado, Inicial
        for level_name in {"Establecido", "Emergente", "Avanzado", "Inicial"}:
            assert level_name in html, f"Level name '{level_name}' not found in HTML"


class TestInsufficientDataBlocks:
    """Insufficient_data blocks render the pending-data marker (REQ-08)."""

    def test_insufficient_block_shows_datos_pendientes(self):
        from app.services.pdf.session2_report import render_html as render_session2_html

        insufficient_blocks = [
            {
                "block_id": "block-3-data",
                "block_title": "Datos",
                "missing_fields": ["q3_2_quality.q3_2_level"],
            }
        ]
        session_data = _make_session_data(insufficient_blocks=insufficient_blocks)
        html = render_session2_html(session_data, draft=False)

        assert "Datos pendientes" in html, (
            "Expected 'Datos pendientes' marker for insufficient_data block"
        )
        assert "Sesión 2" in html, (
            "Expected 'Sesión 2' reference in pending data marker"
        )

    def test_no_insufficient_blocks_no_pending_marker(self):
        """When no blocks are insufficient, no pending marker should appear."""
        from app.services.pdf.session2_report import render_html as render_session2_html

        session_data = _make_session_data(insufficient_blocks=[])
        html = render_session2_html(session_data, draft=False)

        # "Datos pendientes" should only appear if there are insufficient blocks
        # (The scorecard section title or other text is unrelated)
        assert "completar en Sesión 2" not in html


class TestRecommendationsSortedByGap:
    """Recommendations must be sorted by target_gap_size descending (REQ-20)."""

    def test_recommendations_sorted_largest_gap_first_in_html(self):
        """Given gaps [0.8, 0.3, 0.6], order in HTML must be 0.8 > 0.6 > 0.3."""
        from app.services.pdf.session2_report import render_html as render_session2_html

        # Rec 1: gap 0.8, Rec 2: gap 0.3, Rec 3: gap 0.6
        # Expected sorted order: Rec 1, Rec 3, Rec 2
        session_data = _make_session_data(recommendation_gaps=[0.8, 0.3, 0.6])
        html = render_session2_html(session_data, draft=False)

        pos_rec1 = html.find("Recomendación 1")
        pos_rec2 = html.find("Recomendación 2")
        pos_rec3 = html.find("Recomendación 3")

        assert pos_rec1 != -1, "Recomendación 1 not found in HTML"
        assert pos_rec2 != -1, "Recomendación 2 not found in HTML"
        assert pos_rec3 != -1, "Recomendación 3 not found in HTML"

        # gap order: Rec1 (0.8) > Rec3 (0.6) > Rec2 (0.3)
        assert pos_rec1 < pos_rec3, (
            f"Rec1 (gap=0.8) should appear before Rec3 (gap=0.6): pos_rec1={pos_rec1}, pos_rec3={pos_rec3}"
        )
        assert pos_rec3 < pos_rec2, (
            f"Rec3 (gap=0.6) should appear before Rec2 (gap=0.3): pos_rec3={pos_rec3}, pos_rec2={pos_rec2}"
        )

    def test_equal_gaps_preserves_order(self):
        """Equal gap sizes should not crash and maintain stable order."""
        from app.services.pdf.session2_report import render_html as render_session2_html

        session_data = _make_session_data(recommendation_gaps=[0.5, 0.5, 0.5])
        html = render_session2_html(session_data, draft=False)

        # All three recommendations should appear
        for i in range(1, 4):
            assert f"Recomendación {i}" in html
