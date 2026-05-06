"""
app/services/pdf/filename — PDF export filename builder.

Uses python-slugify for Spanish company name transliteration.
Fallback: lead-{id}-diagnostico-{YYYY-MM-DD}.pdf when company name is absent.
"""

from __future__ import annotations

from datetime import datetime, timezone

from slugify import slugify


def build_pdf_filename(lead) -> str:
    """
    Build a PDF filename for a lead's session 1 export.

    Format: {company_slug}-diagnostico-{YYYY-MM-DD}.pdf
    Fallback (null/empty company_name): lead-{lead_id}-diagnostico-{YYYY-MM-DD}.pdf

    Args:
        lead: Lead model instance with .id and .company_name attributes.

    Returns:
        URL-safe filename string ending in .pdf.
    """
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

    if lead.company_name:
        company_slug = slugify(lead.company_name, max_length=60)
        return f"{company_slug}-diagnostico-{today}.pdf"
    else:
        return f"lead-{lead.id}-diagnostico-{today}.pdf"
