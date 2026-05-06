"""
app/services/deep/generator — Generates DEEP branch questions via LLM.

DeepGenerator.generate_for_branch():
  1. Load prompt template from schemas/questionnaire-v2/deep/prompts/{branch_id}.md
  2. Build context: TRIAGE payload + block payloads + block syntheses
  3. Call LLM (Sonnet for compliance/governance, Haiku for others)
  4. Parse output: {questions: [...], reasoning: str}
  5. Persist DeepBranch.generated_questions, status → pending_review

Called by generate_all_branches() which dispatches branches concurrently via asyncio.gather.

Structured log events: deep_generation_started, deep_generation_completed, deep_generation_failed
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.block_analysis import BlockAnalysis
from app.models.deep_branch import DeepBranch
from app.models.intake_session import IntakeSession
from app.models.lead import Lead

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates path
# ---------------------------------------------------------------------------

_PROMPTS_DIR = Path(__file__).parents[3] / "schemas" / "questionnaire-v2" / "deep" / "prompts"

# ---------------------------------------------------------------------------
# LLM model selection per branch
# ---------------------------------------------------------------------------

_COMPLIANCE_BRANCHES = {
    "dpia_obligatorio",
    "dpia_inicial",
    "auditoria_tratamiento",
    "obligaciones_ai_act",
    "capacitacion_ai_act",
    "transparencia_ai_act",
    "procedimiento_arco",
    "ai_act_supervision",
    "gestion_riesgo_ia",
    "governance_previo_ia",
    "governance_minimo",
    "post_mortem_proyecto",
}

_DEFAULT_MODEL = "claude-haiku-4-5"
_SONNET_MODEL = "claude-sonnet-4-6"

_SYSTEM_PROMPT_BASE = """Sos un consultor senior de IA generando preguntas de profundización para la sesión 2 de un diagnóstico de madurez IA.

Reglas:
- Generá entre 5 y 15 preguntas específicas y respondibles sin ayuda técnica especializada
- Cada pregunta debe tener: id (ej. dq1, dq2...), text, rationale, type (textarea|single_choice|multi_choice), options (null si textarea), required (true|false)
- El razonamiento (reasoning) debe explicar qué información busca este conjunto de preguntas
- Respondé SOLO con JSON válido, sin texto adicional

Output schema:
{
  "questions": [
    {
      "id": "string",
      "text": "string",
      "rationale": "string",
      "type": "textarea|single_choice|multi_choice",
      "options": null | [{"value": "string", "label": "string"}],
      "required": true
    }
  ],
  "reasoning": "string"
}"""


def _get_model_for_branch(branch_id: str) -> str:
    return _SONNET_MODEL if branch_id in _COMPLIANCE_BRANCHES else _DEFAULT_MODEL


def _load_prompt_template(branch_id: str) -> str | None:
    """Load prompt template .md file for a branch. Returns None if not found."""
    path = _PROMPTS_DIR / f"{branch_id}.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _build_context_message(
    branch_id: str,
    template: str,
    lead_triage_payload: dict,
    block_payloads: dict[str, dict],
    block_syntheses: dict[str, str],
) -> str:
    """Build the user message for the LLM call."""
    parts = [f"## Contexto del branch: {branch_id}", "", template, ""]

    if lead_triage_payload:
        parts.append("## Datos TRIAGE del cliente")
        parts.append(json.dumps(lead_triage_payload, ensure_ascii=False, indent=2))
        parts.append("")

    if block_payloads:
        parts.append("## Respuestas CORE por bloque")
        for block_id, payload in block_payloads.items():
            parts.append(f"### {block_id}")
            parts.append(json.dumps(payload, ensure_ascii=False, indent=2))
        parts.append("")

    if block_syntheses:
        parts.append("## Síntesis IA por bloque")
        for block_id, synthesis in block_syntheses.items():
            parts.append(f"### {block_id}")
            parts.append(synthesis)
        parts.append("")

    parts.append("## Tu tarea")
    parts.append("Generá el JSON de preguntas según el schema especificado.")

    return "\n".join(parts)


async def _call_llm_for_branch(branch_id: str, user_message: str) -> str:
    """Call Anthropic SDK and return raw text response."""
    from app.services.llm.client_factory import get_anthropic_client

    model = _get_model_for_branch(branch_id)
    client = get_anthropic_client()

    response = await client.messages.create(
        model=model,
        max_tokens=2000,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT_BASE,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text.strip()


async def generate_for_branch(
    db: AsyncSession,
    deep_branch_id: str,
    branch_name: str,
    lead_triage_payload: dict,
    block_payloads: dict[str, dict],
    block_syntheses: dict[str, str],
) -> None:
    """
    Generate questions for a single DEEP branch and persist to DB.

    Args:
        db: Async SQLAlchemy session.
        deep_branch_id: UUID of the DeepBranch row.
        branch_name: Branch identifier (e.g. "post_mortem_proyecto").
        lead_triage_payload: TRIAGE answers for context.
        block_payloads: CORE block answers for context.
        block_syntheses: LLM syntheses from BlockAnalysis rows.
    """
    logger.info("deep_generation_started", branch_name=branch_name, branch_id=deep_branch_id)

    # Load template
    template = _load_prompt_template(branch_name)
    if template is None:
        logger.warning("deep_generation_no_template", branch_name=branch_name)
        template = f"Generá preguntas de profundización sobre el tema: {branch_name}"

    user_message = _build_context_message(
        branch_name, template, lead_triage_payload, block_payloads, block_syntheses
    )

    try:
        raw_text = await _call_llm_for_branch(branch_name, user_message)
        data = json.loads(raw_text)
        questions = data.get("questions", [])

        if not (5 <= len(questions) <= 15):
            logger.warning(
                "deep_generation_question_count_out_of_range",
                branch_name=branch_name,
                count=len(questions),
            )

    except (json.JSONDecodeError, Exception) as exc:
        logger.error("deep_generation_failed", branch_name=branch_name, error=str(exc))
        # Mark as failed — don't block other branches
        stmt = select(DeepBranch).where(DeepBranch.id == deep_branch_id)
        result = await db.execute(stmt)
        branch = result.scalar_one_or_none()
        if branch:
            branch.generated_questions = []
            branch.status = "generation_failed"
            await db.commit()
        return

    # Persist
    stmt = select(DeepBranch).where(DeepBranch.id == deep_branch_id)
    result = await db.execute(stmt)
    branch = result.scalar_one_or_none()

    if branch:
        branch.generated_questions = questions
        branch.status = "pending_review"
        await db.commit()
        logger.info(
            "deep_generation_completed",
            branch_name=branch_name,
            question_count=len(questions),
        )


async def generate_all_branches(
    db: AsyncSession,
    intake_session_id: str,
) -> None:
    """
    Generate questions for all pending_generation DeepBranch rows concurrently.

    Called as a BackgroundTask after session1/close.
    """
    # Load session + lead triage payload
    session_stmt = select(IntakeSession).where(IntakeSession.id == intake_session_id)
    session_result = await db.execute(session_stmt)
    session = session_result.scalar_one_or_none()
    if session is None:
        logger.error("deep_generation_all_session_not_found", session_id=intake_session_id)
        return

    lead_stmt = select(Lead).where(Lead.id == session.lead_id)
    lead_result = await db.execute(lead_stmt)
    lead = lead_result.scalar_one_or_none()
    lead_triage = lead.triage_payload if lead else {}

    # Load block payloads and syntheses
    ba_stmt = select(BlockAnalysis).where(
        BlockAnalysis.intake_session_id == intake_session_id
    )
    ba_result = await db.execute(ba_stmt)
    block_analyses = ba_result.scalars().all()

    block_payloads = {ba.block_id: ba.payload for ba in block_analyses}
    block_syntheses = {
        ba.block_id: (ba.llm_output or {}).get("synthesis", "")
        for ba in block_analyses
        if ba.status == "ready" and ba.llm_output
    }

    # Load pending_generation branches
    branches_stmt = select(DeepBranch).where(
        DeepBranch.intake_session_id == intake_session_id,
        DeepBranch.status == "pending_generation",
    )
    branches_result = await db.execute(branches_stmt)
    branches = branches_result.scalars().all()

    if not branches:
        logger.info("deep_generation_all_no_branches", session_id=intake_session_id)
        return

    # Launch all concurrently
    tasks = [
        generate_for_branch(
            db=db,
            deep_branch_id=branch.id,
            branch_name=branch.branch_id,
            lead_triage_payload=lead_triage,
            block_payloads=block_payloads,
            block_syntheses=block_syntheses,
        )
        for branch in branches
    ]

    await asyncio.gather(*tasks, return_exceptions=True)

    logger.info(
        "deep_generation_all_completed",
        session_id=intake_session_id,
        branch_count=len(branches),
    )
