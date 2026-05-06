"""
app/services/pdf/session1_report — Pure PDF rendering for Session 1 synthesis.

Exports:
  render_html(synthesis, lead, catalog) -> str     — Jinja2 render only (testable without WeasyPrint)
  render_session1_pdf(synthesis, lead, catalog) -> bytes  — full PDF via WeasyPrint

Design (ADR-3): pure function, no DB or side effects.
Side effects (export_count, last_exported_at) are handled by the route.

hypothesis field is NEVER passed to the template context — it stays invisible in PDFs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, select_autoescape

if TYPE_CHECKING:
    from app.services.sessions.synthesis_schema import Session1SynthesisOutput
    from app.services.synthesis.catalog import ServiceDef

# Template environment — scoped to this module
_TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates" / "pdf"
_STATIC_DIR = Path(__file__).parent.parent.parent / "static"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "j2"]),
)


_MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def _format_fecha_es(dt: datetime) -> str:
    return f"{dt.day} de {_MESES_ES[dt.month]} de {dt.year}"


def render_html(
    synthesis: "Session1SynthesisOutput",
    lead,
    catalog: "list[ServiceDef]",
    session=None,
    consultor_name: str = "Equipo Zanovix",
    consultor_email: str = "hola@zanovix.com",
) -> str:
    """
    Render the HTML string from the Jinja2 template.

    hypothesis is deliberately NOT passed to the template — it must never
    appear in any rendered output.
    """
    template = _jinja_env.get_template("session1_report.html.j2")

    catalog_by_key = {svc.key: svc for svc in catalog}
    logo_path = _STATIC_DIR / "zanovix-logo.png"
    logo_uri = logo_path.as_uri() if logo_path.exists() else ""
    logo_white = _STATIC_DIR / "zanovix-logo-white.png"
    logo_white_uri = logo_white.as_uri() if logo_white.exists() else logo_uri

    now = datetime.now(tz=timezone.utc)
    fecha = _format_fecha_es(now)

    # Pass synthesis WITHOUT hypothesis — template must not receive it
    class _SynthesisView:
        summary = synthesis.summary
        key_insights = synthesis.key_insights
        recommendations = synthesis.recommendations
        roadmap = synthesis.roadmap
        next_steps = synthesis.next_steps

    # Lead identification block
    lead_view = {
        "company_name": getattr(lead, "company_name", None) or "Empresa cliente",
        "contact_name": getattr(lead, "full_name", None),
        "contact_email": getattr(lead, "email", None),
        "sector": getattr(lead, "sector", None),
        "company_size": getattr(lead, "company_size", None),
        "lead_id_short": (getattr(lead, "id", "") or "")[:8].upper(),
    }

    # Session-derived areas
    primary_area = getattr(session, "primary_area", None) if session else None
    secondary_area = getattr(session, "secondary_area", None) if session else None
    areas_involved = getattr(session, "areas_involved", None) if session else None
    if primary_area == "not_set":
        primary_area = None

    return template.render(
        synthesis=_SynthesisView(),
        lead=lead_view,
        primary_area=primary_area,
        secondary_area=secondary_area,
        areas_involved=areas_involved or [],
        fecha=fecha,
        catalog=catalog,
        catalog_by_key=catalog_by_key,
        logo_path=logo_uri,
        logo_white_path=logo_white_uri,
        consultor_name=consultor_name,
        consultor_email=consultor_email,
    )


def render_session1_pdf(
    synthesis: "Session1SynthesisOutput",
    lead,
    catalog: "list[ServiceDef]",
    session=None,
    consultor_name: str = "Equipo Zanovix",
    consultor_email: str = "hola@zanovix.com",
) -> bytes:
    """
    Render session 1 synthesis as PDF bytes.

    Requires WeasyPrint and its OS-level C dependencies (libpango, libcairo, etc.).
    Raises ImportError if WeasyPrint is not installed.
    """
    import weasyprint  # noqa: PLC0415 — intentional late import for testability

    html = render_html(
        synthesis, lead, catalog,
        session=session,
        consultor_name=consultor_name,
        consultor_email=consultor_email,
    )
    doc = weasyprint.HTML(string=html, base_url=str(_STATIC_DIR))
    return doc.write_pdf()
