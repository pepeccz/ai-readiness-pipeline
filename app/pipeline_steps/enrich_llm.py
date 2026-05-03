"""
app/pipeline_steps/enrich_llm — LLM enrichment step.

Thin wrapper around `llm_enricher.enrich_assessment`. The key addition is
`preserve_human_fields`: any field whose source is 'human' in `field_sources`
will NOT be overwritten even if the LLM returns a new value for it.

Design reference: design §2.7, §3.5.
"""

import asyncio

import structlog

logger = structlog.get_logger(__name__)


def enrich_llm(
    rec: dict,
    preserve_human_fields: dict[str, str] | None = None,
) -> dict:
    """Run LLM enrichment on a rec dict, optionally preserving human-edited fields.

    This is a SYNC function. Async callers (runners.py) must wrap it:
        await asyncio.to_thread(enrich_llm, rec, field_sources)

    Args:
        rec:
            Internal rec dict. Must contain the form-derived fields produced by
            `map_form_to_rec`. Mutated in place AND returned.
        preserve_human_fields:
            Optional field-source mapping, e.g. ``{"llm_executive_summary": "human"}``.
            Any key whose value is ``"human"`` will NOT be overwritten by the LLM
            result, even if the LLM produces a new value for it.
            Pass `assessment.field_sources` directly here.
            If ``None`` (default), all LLM output fields are written unconditionally.

    Returns:
        rec dict with ``llm_*`` fields populated (or preserved when human-edited).

    Raises:
        Any exception raised by ``llm_enricher.enrich_assessment`` propagates
        unchanged — callers (runners.py) are responsible for catching and
        marking the job as failed.

    Preservation logic (design §3.5):
        After the LLM call, iterate through every key in the enriched result.
        For each key that is already present in `rec`:
            - If ``preserve_human_fields.get(key) == "human"``: skip (keep existing)
            - Otherwise: overwrite rec[key] with the LLM value

        Fields returned by the LLM that are NOT yet in rec are always written
        (they are new keys, not overrides).
    """
    # Inline import — llm_enricher lives at project root, not under app/
    from llm_enricher import enrich_assessment  # type: ignore[import]

    human_fields: set[str] = set()
    if preserve_human_fields:
        human_fields = {
            field
            for field, source in preserve_human_fields.items()
            if source == "human"
        }

    logger.info(
        "enrich_llm_start",
        assessment_id=rec.get("assessment_id"),
        human_fields_count=len(human_fields),
    )

    # The enricher returns a new dict (or mutated rec — implementation detail
    # of llm_enricher). We capture it as `enriched`.
    enriched = enrich_assessment(rec)

    if not human_fields:
        # Fast path: no preservation needed — accept all LLM output
        logger.info(
            "enrich_llm_done",
            assessment_id=enriched.get("assessment_id"),
            llm_fields=len([k for k in enriched if k.startswith("llm_") and enriched[k]]),
        )
        return enriched

    # Selective merge: only write llm_* fields that are NOT human-edited
    overwritten = 0
    preserved = 0
    for key, value in enriched.items():
        if key in human_fields:
            # Keep the existing value in rec; do not apply LLM override
            preserved += 1
            continue
        rec[key] = value
        if key.startswith("llm_"):
            overwritten += 1

    logger.info(
        "enrich_llm_done_selective",
        assessment_id=rec.get("assessment_id"),
        llm_fields_overwritten=overwritten,
        llm_fields_preserved=preserved,
    )
    return rec
