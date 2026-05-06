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


def render_html(
    synthesis: "Session1SynthesisOutput",
    lead,
    catalog: "list[ServiceDef]",
) -> str:
    """
    Render the HTML string from the Jinja2 template.

    hypothesis is deliberately NOT passed to the template — it must never
    appear in any rendered output.
    """
    template = _jinja_env.get_template("session1_report.html.j2")

    catalog_by_key = {svc.key: svc for svc in catalog}
    logo_path = _STATIC_DIR / "zanovix-logo.png"
    # Use file:// URI for WeasyPrint local asset resolution
    logo_uri = logo_path.as_uri() if logo_path.exists() else ""

    fecha = datetime.now(tz=timezone.utc).strftime("%d de %B de %Y")

    # Pass synthesis WITHOUT hypothesis — template must not receive it
    class _SynthesisView:
        """Synthesis proxy that exposes all fields except hypothesis."""
        summary = synthesis.summary
        key_insights = synthesis.key_insights
        recommendations = synthesis.recommendations
        roadmap = synthesis.roadmap
        next_steps = synthesis.next_steps

    return template.render(
        synthesis=_SynthesisView(),
        company_name=getattr(lead, "company_name", None),
        fecha=fecha,
        catalog=catalog,
        catalog_by_key=catalog_by_key,
        logo_path=logo_uri,
    )


def render_session1_pdf(
    synthesis: "Session1SynthesisOutput",
    lead,
    catalog: "list[ServiceDef]",
) -> bytes:
    """
    Render session 1 synthesis as PDF bytes.

    Requires WeasyPrint and its OS-level C dependencies (libpango, libcairo, etc.).
    Raises ImportError if WeasyPrint is not installed.
    """
    import weasyprint  # noqa: PLC0415 — intentional late import for testability

    html = render_html(synthesis, lead, catalog)
    doc = weasyprint.HTML(string=html, base_url=str(_STATIC_DIR))
    return doc.write_pdf()
