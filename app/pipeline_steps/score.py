"""
app/pipeline_steps/score — Scoring step.

Thin wrapper around `scoring_engine.enrich_with_scoring` + `fix_employee_range`.
This step is CPU-only (no I/O, no LLM calls) so it stays SYNC — no asyncio.to_thread
needed when called from sync contexts. Async callers MAY wrap it if needed:
    await asyncio.to_thread(score, rec)

Design reference: design §1 (pipeline_steps layout).
"""

import structlog

logger = structlog.get_logger(__name__)


def score(rec: dict) -> dict:
    """Run scoring on a rec dict.

    This is a SYNC function (CPU-only, no I/O).

    Populates the following keys in rec:
        Flat scores (also stored as columns in the Assessment model):
            maturity_score, maturity_level, risk_score, risk_level,
            priority_score, priority_level

        Sub-score pts_* fields (stored flat in Assessment model):
            pts_tools, pts_automation, pts_area_usage, pts_governance,
            pts_goal_clarity, pts_data_risk, pts_ai_personal_data,
            pts_dpa, pts_dpia, pts_automated_decisions, pts_sector,
            pts_incident

    Args:
        rec: Internal rec dict. Must have LLM enrichment fields populated
             (scoring engine reads llm_scoring_answers). Also needs
             employee_range (fixed internally via fix_employee_range).

    Returns:
        rec dict with all scoring fields populated.

    Raises:
        Any exception from scoring_engine propagates — callers (runners.py)
        are responsible for catching and marking the job as failed.
    """
    # Inline import — scoring_engine lives at project root
    from scoring_engine import enrich_with_scoring, fix_employee_range  # type: ignore[import]

    logger.info(
        "score_start",
        assessment_id=rec.get("assessment_id"),
        employee_range_raw=rec.get("employee_range"),
    )

    # Fix employee_range before scoring (may contain serial-date strings from Sheets)
    rec["employee_range"] = fix_employee_range(rec.get("employee_range"))

    # Extract llm_scoring_answers — scoring engine consumes it as a separate arg
    # and it must be restored afterward so it flows into the JSON blob storage.
    llm_answers = rec.pop("llm_scoring_answers", None)

    rec = enrich_with_scoring(rec, llm_answers, sheet_id=None)

    # Restore scoring answers for JSON blob storage (llm_enriched_data)
    rec["llm_scoring_answers"] = llm_answers

    logger.info(
        "score_done",
        assessment_id=rec.get("assessment_id"),
        maturity_score=rec.get("maturity_score"),
        risk_score=rec.get("risk_score"),
        priority_score=rec.get("priority_score"),
    )
    return rec
