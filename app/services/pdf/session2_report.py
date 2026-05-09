"""
app/services/pdf/session2_report — Pure PDF rendering for Session 2 AIR report.

Exports:
  render_html(session_data, draft=False) -> str   — Jinja2 render only (testable without WeasyPrint)
  render_session2_pdf(session_data, draft=False) -> bytes  — full PDF via WeasyPrint

Design (ADR-8):
  - Pure function, no DB or side effects.
  - session_data is a dict (or dataclass) with all fields pre-computed.
  - draft=True adds BORRADOR watermark to the rendered output.
  - Recommendations are sorted by target_gap_size descending (REQ-20) here,
    so callers don't need to pre-sort.
  - hypothesis field is NEVER passed to the template context.

session_data shape:
  company_name, sector, contact_name, contact_email, reference_id, generation_date
  composite_score (float 0-1), composite_level (int 0-4),
  composite_level_name (str), risk_profile (str)
  per_block: list of {block_id, block_title, score, level, level_name, indicators_synthesized}
  insufficient_blocks: list of {block_id, block_title, missing_fields}
  recommendations: list of {text, impact, effort, related_service,
                             custom_service_label, target_block_id, target_gap_size}
  roadmap: dict with d30, d60, d90 lists
  next_steps: list of strings
  hypothesis: str (NEVER forwarded to template)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Template environment — scoped to this module
_TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates" / "pdf"
_STATIC_DIR = Path(__file__).parent.parent.parent / "static"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "j2"]),
)


def _get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Get a key from a dict or an attribute from an object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _build_session_view(session_data: Any) -> dict:
    """
    Build a sanitised dict view of session_data for the template.

    hypothesis is deliberately excluded — must never appear in rendered output.
    Recommendations are sorted by target_gap_size descending (REQ-20).
    """
    # Sort recommendations by target_gap_size descending
    raw_recs = _get_attr(session_data, "recommendations", []) or []
    sorted_recs = sorted(
        raw_recs,
        key=lambda r: _get_attr(r, "target_gap_size", 0.0) or 0.0,
        reverse=True,
    )

    insufficient_blocks_raw = _get_attr(session_data, "insufficient_blocks", []) or []
    # Build a set of insufficient block_ids for O(1) lookup in the template
    insufficient_block_ids = {
        _get_attr(b, "block_id", "")
        for b in insufficient_blocks_raw
    }

    return {
        "company_name": _get_attr(session_data, "company_name", "Empresa cliente"),
        "sector": _get_attr(session_data, "sector"),
        "contact_name": _get_attr(session_data, "contact_name"),
        "contact_email": _get_attr(session_data, "contact_email"),
        "reference_id": _get_attr(session_data, "reference_id"),
        "generation_date": _get_attr(session_data, "generation_date", ""),
        "composite_score": _get_attr(session_data, "composite_score", 0.0),
        "composite_level": _get_attr(session_data, "composite_level", 0),
        "composite_level_name": _get_attr(session_data, "composite_level_name", "Inicial"),
        "risk_profile": _get_attr(session_data, "risk_profile", "low"),
        "per_block": _get_attr(session_data, "per_block", []) or [],
        "insufficient_blocks": insufficient_blocks_raw,
        "insufficient_block_ids": insufficient_block_ids,
        "recommendations": sorted_recs,
        "roadmap": _get_attr(session_data, "roadmap") or {},
        "next_steps": _get_attr(session_data, "next_steps", []) or [],
        # hypothesis intentionally omitted
    }


def render_html(
    session_data: Any,
    draft: bool = False,
    consultor_name: str = "Equipo Zanovix",
    consultor_email: str = "hola@zanovix.com",
    catalog: list | None = None,
) -> str:
    """
    Render the Session 2 report HTML from the Jinja2 template.

    hypothesis is deliberately NOT passed to the template.

    Parameters
    ----------
    session_data : dict or dataclass
        Pre-computed session data. See module docstring for expected shape.
    draft : bool
        If True, adds BORRADOR watermark (for consultor preview only).
    consultor_name : str
        Name shown in the closing block.
    consultor_email : str
        Email shown in the closing block.
    catalog : list | None
        Optional list of ServiceDef objects for service tag resolution.
        If None, an empty catalog is used (recommendations show no service tags).
    """
    template = _jinja_env.get_template("session2_report.html.j2")

    if catalog is None:
        catalog = []

    catalog_by_key = {}
    for svc in catalog:
        key = _get_attr(svc, "key") or _get_attr(svc, "id")
        if key:
            catalog_by_key[key] = svc

    logo_path = _STATIC_DIR / "zanovix-logo.png"
    logo_uri = logo_path.as_uri() if logo_path.exists() else ""
    logo_white = _STATIC_DIR / "zanovix-logo-white.png"
    logo_white_uri = logo_white.as_uri() if logo_white.exists() else logo_uri

    session_view = _build_session_view(session_data)

    return template.render(
        session=session_view,
        draft=draft,
        logo_path=logo_uri,
        logo_white_path=logo_white_uri,
        consultor_name=consultor_name,
        consultor_email=consultor_email,
        catalog=catalog,
        catalog_by_key=catalog_by_key,
    )


def render_session2_pdf(
    session_data: Any,
    draft: bool = False,
    consultor_name: str = "Equipo Zanovix",
    consultor_email: str = "hola@zanovix.com",
    catalog: list | None = None,
) -> bytes:
    """
    Render Session 2 AIR report as PDF bytes.

    Requires WeasyPrint and its OS-level C dependencies (libpango, libcairo, etc.).
    Raises ImportError if WeasyPrint is not installed.

    Parameters
    ----------
    session_data : dict or dataclass
        Pre-computed session data.
    draft : bool
        If True, adds BORRADOR watermark (preview mode — never persisted to report_content).
    consultor_name : str
        Consultant name shown in the closing block.
    consultor_email : str
        Consultant email shown in the closing block.
    catalog : list | None
        Optional service catalog for recommendation service tags.
    """
    import weasyprint  # noqa: PLC0415 — intentional late import for testability

    html = render_html(
        session_data,
        draft=draft,
        consultor_name=consultor_name,
        consultor_email=consultor_email,
        catalog=catalog,
    )
    doc = weasyprint.HTML(string=html, base_url=str(_STATIC_DIR))
    return doc.write_pdf()
