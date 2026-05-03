"""
app/pipeline_steps/enrich_recommendations — Recommendation enrichment step.

Thin wrapper around `recommendation_enricher.enrich_recommendations`.
Adds structured logging and graceful degradation (returns rec unchanged on error).

Design reference: design §1 (pipeline_steps layout).
"""

import structlog

logger = structlog.get_logger(__name__)


def enrich_recommendations(rec: dict) -> dict:
    """Run recommendation enrichment on a rec dict.

    This is a SYNC function. Async callers (runners.py) must wrap it:
        await asyncio.to_thread(enrich_recommendations, rec)

    Adds the following keys to rec (via recommendation_enricher):
        - llm_tool_recommendations: list of concrete tool recommendations
        - llm_followup_questions:   list of clarifying questions for areas with
                                    insufficient context
        - llm_ai_policy_draft:      internal AI policy draft (plain text)
        - llm_dpa_guidance:         DPA guidance for recommended tools

    Args:
        rec: Internal rec dict. Must already have LLM enrichment fields populated
             (i.e., called AFTER enrich_llm in the pipeline chain).

    Returns:
        rec dict with recommendation fields added. Returns rec UNCHANGED on any
        exception (graceful degradation — matching behaviour from pipeline.py).

    Raises:
        Does NOT raise. Errors are logged and rec is returned as-is.
    """
    # Inline import — recommendation_enricher lives at project root
    from recommendation_enricher import enrich_recommendations as _enrich  # type: ignore[import]

    logger.info(
        "enrich_recommendations_start",
        assessment_id=rec.get("assessment_id"),
    )

    try:
        rec = _enrich(rec)
        reco_count = len(rec.get("llm_tool_recommendations", []))
        questions_count = len(rec.get("llm_followup_questions", []))
        logger.info(
            "enrich_recommendations_done",
            assessment_id=rec.get("assessment_id"),
            tools_recommended=reco_count,
            followup_questions=questions_count,
            has_policy_draft=bool(rec.get("llm_ai_policy_draft")),
            has_dpa_guidance=bool(rec.get("llm_dpa_guidance")),
        )
    except Exception as exc:
        logger.error(
            "enrich_recommendations_failed",
            assessment_id=rec.get("assessment_id"),
            error=str(exc),
        )
        # Graceful degradation — recommendation enrichment is optional

    return rec
