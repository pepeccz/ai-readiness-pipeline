"""
app/services/email/triage_emails — T3.4

Email templates for the 5 TRIAGE bucket outcomes + consultant notification.

Public API:
  triage_email_for_bucket(bucket, full_name, company_name) → (subject, body)
  triage_consultant_notification(full_name, company_name, bucket, lead_id) → (subject, body)

All messages in Spanish (product language). No Jinja2 — plain f-strings.
"""

from __future__ import annotations

_BUCKET_EMAILS: dict[str, tuple[str, str]] = {}

# ---------------------------------------------------------------------------
# Per-bucket template factories
# ---------------------------------------------------------------------------


def _auto_accept(full_name: str, company_name: str) -> tuple[str, str]:
    subject = f"Tu diagnóstico IA está confirmado — {company_name}"
    body = f"""Hola {full_name},

Excelentes noticias. Tu perfil encaja con nuestro programa de transformación IA.

Un consultor de Zanovix te contactará en las próximas 24–48 horas para coordinar la primera sesión.
Te pediremos que compartas disponibilidad horaria para agendar la llamada.

Mientras tanto, si tenés preguntas, respondé este correo.

Gracias por confiar en Zanovix.

— Equipo Zanovix
"""
    return subject, body


def _review(full_name: str, company_name: str) -> tuple[str, str]:
    subject = f"Estamos revisando tu caso — {company_name}"
    body = f"""Hola {full_name},

Recibimos tu solicitud y estamos analizando tu perfil con detalle.

En 2–3 días hábiles te contactaremos con nuestra evaluación y los próximos pasos.
El proceso de revisión incluye análisis de tu sector, madurez IA y objetivos específicos.

Gracias por tu paciencia.

— Equipo Zanovix
"""
    return subject, body


def _cold_warm(full_name: str, company_name: str) -> tuple[str, str]:
    subject = f"Recursos para preparar tu estrategia IA — {company_name}"
    body = f"""Hola {full_name},

Tu perfil es interesante, aunque el momento de la transformación profunda puede ser un poco antes.

Te invitamos a nuestro webinar gratuito "IA para empresas en crecimiento":
👉 https://zanovix.com/webinar-ia

Además, en 4 meses te contactaremos para una re-evaluación: muchos de nuestros mejores clientes
empezaron exactamente en esta etapa.

Guardamos tu perfil y te avisamos cuando sea el momento.

— Equipo Zanovix
"""
    return subject, body


def _cold_cool(full_name: str, company_name: str) -> tuple[str, str]:
    subject = f"Te enviamos recursos para preparar tu madurez IA — {company_name}"
    body = f"""Hola {full_name},

Tu caso requiere un poco más de preparación antes de arrancar con un programa de transformación IA.

Te compartimos nuestro Checklist de Madurez IA, que te ayudará a identificar qué trabajar primero:
👉 https://zanovix.com/checklist-madurez-ia

Te sumaremos a nuestra lista de seguimiento trimestral con contenido exclusivo para empresas
en etapas similares a la tuya.

Cualquier consulta, respondé este correo.

— Equipo Zanovix
"""
    return subject, body


def _reject_soft(full_name: str, company_name: str) -> tuple[str, str]:
    subject = f"No es el momento, pero guardamos tu contacto — {company_name}"
    body = f"""Hola {full_name},

Gracias por completar nuestro cuestionario. En este momento nuestro programa no es el encaje
ideal para tu situación actual.

Esto no significa un "no" definitivo: el contexto cambia, y queremos que tengas acceso
a contenido formativo que te ayude a prepararte.

Te compartimos nuestro blog con recursos gratuitos:
👉 https://zanovix.com/blog

Retomamos el contacto en el futuro cuando las condiciones sean más favorables.

— Equipo Zanovix
"""
    return subject, body


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_BUCKET_FACTORIES = {
    "auto_accept": _auto_accept,
    "review": _review,
    "cold_warm": _cold_warm,
    "cold_cool": _cold_cool,
    "reject_soft": _reject_soft,
}


def triage_email_for_bucket(
    bucket: str,
    *,
    full_name: str,
    company_name: str,
) -> tuple[str, str]:
    """
    Return (subject, body) for the given bucket.

    Args:
        bucket:       One of auto_accept | review | cold_warm | cold_cool | reject_soft.
        full_name:    Lead's full name for personalisation.
        company_name: Lead's company name for subject line.

    Raises:
        ValueError: if bucket is not one of the 5 known values.
    """
    factory = _BUCKET_FACTORIES.get(bucket)
    if factory is None:
        raise ValueError(
            f"Unknown bucket: {bucket!r}. Must be one of {list(_BUCKET_FACTORIES)}"
        )
    return factory(full_name=full_name, company_name=company_name)


def triage_consultant_notification(
    *,
    full_name: str,
    company_name: str,
    bucket: str,
    lead_id: str,
) -> tuple[str, str]:
    """
    Notification email sent to the consultant when a high-priority lead arrives.

    Triggered for bucket=auto_accept (and optionally others per T3.5).
    """
    subject = f"Nuevo lead TRIAGE — {bucket.upper()} — {company_name}"
    body = f"""Nuevo lead recibido en el sistema TRIAGE.

Nombre:   {full_name}
Empresa:  {company_name}
Bucket:   {bucket}
Lead ID:  {lead_id}

Revisá el panel de administración para ver todos los detalles y coordinar el siguiente paso:
https://assess.zanovix.com/admin/leads/{lead_id}

— Sistema Zanovix
"""
    return subject, body
