"""
app/api/legacy_routes — Legacy v1 endpoints, returning 410 Gone.

Router prefix: /api  (registered in webhook_service.py as
  app.include_router(router, prefix="/api"))

These endpoints existed in the original threading-based pipeline:
  GET /api/status/{task_id}   — Poll async task status
  GET /api/download/{task_id} — Download generated .docx report by task_id

Both have been superseded by the Phase C public form rewire:
  - Submissions now return {assessment_id, status, message} — no task_id.
  - Downloads are now delivered via signed URL: GET /api/assessment/{id}/download?token=...

Keeping these routes registered (as 410 Gone) ensures that any older client
(browser cached page, third-party integration, bookmarked URL) gets a meaningful
response rather than a React SPA HTML page or a generic 404.

Design reference: design §2.6 (legacy endpoint behaviour).
"""

from fastapi import APIRouter

from app.schemas.common import ApiException

router = APIRouter(tags=["legacy"])

DEPRECATION_MESSAGE = (
    "Este endpoint fue deprecado. Contactá admin@zanovix.com para soporte."
)


@router.get("/status/{task_id}", include_in_schema=False)
async def status_legacy(task_id: str) -> None:
    """
    Legacy polling endpoint — deprecated.

    Replaced by: enrichment_chain runs in background; no polling needed.
    Submissions now return a confirmation message directly.
    """
    raise ApiException(
        status_code=410,
        code="deprecated",
        detail=DEPRECATION_MESSAGE,
    )


@router.get("/download/{task_id}", include_in_schema=False)
async def download_legacy(task_id: str) -> None:
    """
    Legacy download endpoint — deprecated.

    Replaced by: GET /api/assessment/{id}/download?token={signed_token}
    Signed download URLs are delivered by email when the report is approved.
    """
    raise ApiException(
        status_code=410,
        code="deprecated",
        detail=DEPRECATION_MESSAGE,
    )
