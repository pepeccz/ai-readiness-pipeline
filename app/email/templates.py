"""
app/email/templates — Plain-text email templates for the Zanovix admin platform.

All messages are in Spanish (product language). Templates are Python f-strings —
no Jinja2 dependency needed. Each function returns a (subject, body) tuple so the
caller can pass them directly to send_email(to, subject, body).

Templates (design §2.5):
  password_reset_email(reset_url)              — account recovery link
  new_submission_email(company_name, id, url)  — consultant notification on new form submission
  client_report_email(company_name, url)       — client download link after approval

These are the ONLY three outbound email types in Phase A–C. If a fourth type is
added, add it here — do NOT inline template strings in route handlers.
"""


def password_reset_email(reset_url: str) -> tuple[str, str]:
    """
    Generate the password reset email sent to an admin who requested a reset link.

    Args:
        reset_url: The full reset URL including the ?token= query parameter.
                   Example: https://assess.zanovix.com/admin/reset-password?token=abc123

    Returns:
        (subject, body) tuple — both plain-text strings.
    """
    subject = "Restablecer tu contraseña — Admin Zanovix"
    body = f"""Hola,

Recibimos una solicitud para restablecer tu contraseña en el panel de administración.

Para crear una nueva, hacé click en este enlace (válido durante 1 hora):

{reset_url}

Si no fuiste vos, ignorá este mensaje. Tu contraseña actual sigue vigente.

— Zanovix
"""
    return subject, body


def new_submission_email(
    company_name: str,
    assessment_id: str,
    admin_url: str,
) -> tuple[str, str]:
    """
    Notification email sent to consultants when a new assessment arrives via the
    public form and is waiting for review.

    Args:
        company_name:  The company name from the submitted form.
        assessment_id: The UUID of the newly created Assessment row.
        admin_url:     Full URL to the assessment editor, e.g.:
                       https://assess.zanovix.com/admin/assessments/{id}

    Returns:
        (subject, body) tuple — both plain-text strings.
    """
    subject = f"Nuevo assessment recibido — {company_name}"
    body = f"""Acaba de entrar un nuevo assessment al panel.

Empresa: {company_name}
ID: {assessment_id}

Está en estado pending_review esperando tu revisión:
{admin_url}

— Sistema Zanovix
"""
    return subject, body


def get_lead_accepted_email(lead: "Lead") -> tuple[str, str]:  # noqa: F821
    """
    Acceptance email sent to a lead after admin accepts their TRIAGE submission.

    Args:
        lead: Lead model instance.

    Returns:
        (subject, body) tuple — both plain-text strings.
    """
    subject = "Tu diagnóstico IA está en camino — Zanovix"
    body = (
        f"Hola {lead.full_name},\n\n"
        "Nos complace informarte que hemos revisado tu caso y hemos decidido avanzar.\n\n"
        "En los próximos días un consultor de Zanovix se pondrá en contacto contigo para\n"
        "coordinar la primera sesión de diagnóstico.\n\n"
        f"Empresa: {lead.company_name}\n\n"
        "Mientras tanto, si tenés alguna pregunta no dudes en responder este email.\n\n"
        "— Equipo Zanovix\n"
    )
    return subject, body


def get_lead_rejected_email(lead: "Lead") -> tuple[str, str]:  # noqa: F821
    """
    Soft rejection email sent to a lead after admin rejects their TRIAGE submission.

    Args:
        lead: Lead model instance.

    Returns:
        (subject, body) tuple — both plain-text strings.
    """
    subject = "Actualización sobre tu solicitud — Zanovix"
    body = (
        f"Hola {lead.full_name},\n\n"
        "Gracias por tu interés en nuestros servicios de diagnóstico de IA.\n\n"
        "Tras revisar tu caso, en este momento no podemos ofrecerte el servicio que necesitás.\n"
        "Esto no significa que tu empresa no tenga potencial — simplemente que el ajuste con\n"
        "nuestra oferta actual no es el adecuado en este momento.\n\n"
        "Si tu situación cambia o querés explorar otras opciones en el futuro, no dudes en\n"
        "contactarnos nuevamente.\n\n"
        "Un saludo cordial,\n\n"
        "— Equipo Zanovix\n"
    )
    return subject, body


def get_lead_extra_info_email(lead: "Lead") -> tuple[str, str]:  # noqa: F821
    """
    Email requesting additional information from a lead.

    Args:
        lead: Lead model instance.

    Returns:
        (subject, body) tuple — both plain-text strings.
    """
    subject = "Necesitamos un poco más de información — Zanovix"
    body = (
        f"Hola {lead.full_name},\n\n"
        "Hemos revisado tu solicitud y antes de continuar necesitamos un poco más de\n"
        "contexto sobre tu situación.\n\n"
        "Por favor, respondé este email con cualquier información adicional que pueda\n"
        "ayudarnos a entender mejor tus necesidades y el estado actual de vuestra empresa.\n\n"
        "Gracias por tu tiempo.\n\n"
        "— Equipo Zanovix\n"
    )
    return subject, body


def client_report_email(company_name: str, download_url: str) -> tuple[str, str]:
    """
    Email sent to the client with a signed download link for their IA Readiness report,
    triggered when a consultant approves and sends the assessment.

    Args:
        company_name:  The client company's name, used in the greeting and subject.
        download_url:  HMAC-signed URL for the PDF download (7-day TTL by default).
                       Generated by app/signed_urls.py.

    Returns:
        (subject, body) tuple — both plain-text strings.
    """
    subject = f"Tu reporte de IA Readiness — {company_name}"
    body = f"""Hola,

Adjuntamos tu reporte de assessment de madurez en IA.

Lo podés descargar desde el siguiente enlace (válido durante 7 días):

{download_url}

Si tenés dudas o querés discutir el contenido, respondé este email y coordinamos una llamada.

Gracias por confiar en nosotros.

— Equipo Zanovix
"""
    return subject, body
