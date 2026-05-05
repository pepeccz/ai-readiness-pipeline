"""
AI Readiness Pipeline — Web Service
FastAPI app serving the React assessment form and processing pipeline.

ENTRYPOINT: This is the FastAPI application entrypoint. All routers must be
registered HERE, and the StaticFiles mount MUST remain the absolute last
registration (TASK-X-01). FastAPI resolves routes in registration order —
if StaticFiles is mounted first, it catches every request before the API
routes can match, causing silent 404s on all API calls.

Route registration order (CRITICAL — do not change):
  1. app.include_router(auth_routes.router, prefix="/api/admin")       ← admin auth API
  2. app.include_router(admin_leads_routes.router, prefix="/api/admin") ← admin leads API
  3. app.include_router(public_routes.router, prefix="/api")           ← public API (v1)
  4. app.include_router(intake_routes.router, prefix="/api")           ← TRIAGE v2 public
  5. app.include_router(client_routes.router, prefix="/api")           ← client session 2
  6. SPA fallback GET /admin/{path:path}                               ← React Router
  7. app.mount("/", StaticFiles(...))                                   ← React SPA LAST

Endpoints (current — Phase D complete):
  GET  /                          → React SPA (static files)
  POST /api/assessment            → Submit assessment form (public_routes.py)
  GET  /api/assessment/{id}/download → Download PDF via signed URL (public_routes.py)
  GET  /api/health                → Service health check


Startup lifecycle (Phase D — app/startup.py):
  1. prune_login_attempts()        — hygiene DELETE of rows > 7 days old
  2. resume_orphaned_assessments() — re-enqueue pending_review rows with null llm_enriched_data
  3. session_cleanup_loop()        — spawned as background task, prunes expired sessions hourly
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import settings

# ---------------------------------------------------------------------------
# Startup / shutdown lifecycle
# ---------------------------------------------------------------------------

# Holds background tasks spawned at startup so we can cancel them on shutdown.
_background_tasks: set[asyncio.Task] = set()

# Uptime tracking — set at startup
_startup_time: float = time.monotonic()


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """
    FastAPI lifespan handler (replaces deprecated @app.on_event("startup")).

    Startup phase:
      - Prune stale login_attempts (hygiene sweep, design §0 A5)
      - Re-enqueue orphaned pending_review assessments (design §0 A4)
      - Spawn hourly session cleanup loop as a background task

    Shutdown phase:
      - Cancel all background tasks and await their completion.
    """
    # Logging must be configured before startup.py runs (configure_logging()
    # is called at module level below, before FastAPI() is constructed).
    from app import startup as startup_hooks  # noqa: PLC0415

    # ── Startup ──────────────────────────────────────────────────────────────
    # Load questionnaire v2 schema (fail-fast on invalid YAML)
    from app.services.questionnaire import schema_loader  # noqa: PLC0415
    import structlog as _structlog  # noqa: PLC0415
    _sl_logger = _structlog.get_logger("schema_loader_startup")
    try:
        schema_loader.load_all()
        _sl_logger.info("schema_v2_loaded", version=schema_loader.get_schema_version())
    except Exception as _exc:
        _sl_logger.error("schema_v2_load_failed", error=str(_exc))
        raise

    await startup_hooks.prune_login_attempts()
    await startup_hooks.resume_orphaned_assessments()

    cleanup_task = asyncio.create_task(
        startup_hooks.session_cleanup_loop(),
        name="session_cleanup_loop",
    )
    _background_tasks.add(cleanup_task)
    # Remove from set when done (prevents set growing forever if task exits).
    cleanup_task.add_done_callback(_background_tasks.discard)

    yield  # ← application runs here

    # ── Shutdown ─────────────────────────────────────────────────────────────
    for task in list(_background_tasks):
        task.cancel()
    if _background_tasks:
        await asyncio.gather(*_background_tasks, return_exceptions=True)


app = FastAPI(
    title="AI Readiness Platform",
    version="2.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

# --- Logging (TASK-X-03) ---
# Configure structured logging before anything else so all subsequent
# imports and request handlers use the same logger.
from app.logging_config import configure_logging, RequestIdMiddleware

configure_logging()

# --- Error envelope (TASK-X-02) ---
from app.schemas.common import add_error_handlers

add_error_handlers(app)

# --- CORS ---
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# --- Request ID middleware (TASK-X-03) ---
# Added AFTER CORSMiddleware so CORS headers still apply on error responses.
app.add_middleware(RequestIdMiddleware)

# --- API Endpoints ---


def _get_git_sha() -> str:
    """Resolve git SHA from GIT_SHA env var or .git/HEAD file."""
    git_sha = os.environ.get("GIT_SHA", "")
    if git_sha:
        return git_sha
    try:
        git_head = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".git", "HEAD")
        with open(git_head) as f:
            head_content = f.read().strip()
        if head_content.startswith("ref: "):
            ref_path = head_content[5:]
            ref_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".git", ref_path)
            with open(ref_file) as f:
                return f.read().strip()[:7]
        return head_content[:7]
    except Exception:
        return "unknown"


async def _check_db_connection() -> str:
    """Ping DB with a lightweight query. Returns 'ok' or 'fail'."""
    try:
        from app.db.session import async_session_factory  # noqa: PLC0415
        from sqlalchemy import text  # noqa: PLC0415
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "fail"


@app.get("/api/health")
async def health():
    """Enriched service health check (T10.3)."""
    from app.services.questionnaire import schema_loader as _sl  # noqa: PLC0415

    try:
        schema_version = _sl.get_schema_version()
    except RuntimeError:
        schema_version = None

    db_status = await _check_db_connection()
    overall_status = "ok" if db_status == "ok" else "degraded"
    uptime_seconds = int(time.monotonic() - _startup_time)
    git_sha = _get_git_sha()

    from app.observability import get_counters  # noqa: PLC0415
    counters = get_counters()

    return {
        "status": overall_status,
        "schema_version": schema_version or "unknown",
        "db_connection": db_status,
        "llm_availability": "unknown",  # not pinged on every health check to avoid cost
        "uptime_seconds": uptime_seconds,
        "git_sha": git_sha,
        # Observability metrics (T10.4)
        "rate_limit_hits": counters.get("rate_limit_hits", 0),
        "rate_limit_blocks": counters.get("rate_limit_blocks", 0),
    }


# --- API routers ---
# CRITICAL: all include_router() calls MUST appear before the StaticFiles mount.
# Registration order matters — FastAPI matches routes in the order they were registered.
# Legacy routes go AFTER public routes: different paths so no conflict, but discipline
# ensures /api/assessment/{id}/download is never shadowed by /api/download/{task_id}.
from app.api import auth_routes  # noqa: E402
from app.api import public_routes  # noqa: E402 — Phase C Batch 1 (TASK-C-01..C-03, C-09)

from app.api import intake_routes  # noqa: E402 — B3 TRIAGE público
from app.api.admin import leads_routes as admin_leads_routes  # noqa: E402 — B4
from app.api import client_routes  # noqa: E402 — B8 client session 2

app.include_router(auth_routes.router, prefix="/api/admin")
app.include_router(admin_leads_routes.router, prefix="/api/admin")  # B4 leads
app.include_router(public_routes.router, prefix="/api")

app.include_router(intake_routes.router, prefix="/api")  # TRIAGE público (B3)
app.include_router(client_routes.router, prefix="/api")  # B8 client session 2

# --- Static files (React SPA) ---
# IMPORTANT: StaticFiles MUST be the LAST registration (TASK-X-01).
# FastAPI resolves routes in registration order. The static mount matches
# every path ("/*"), so any API route registered after it would be silently
# shadowed. All include_router() calls must appear ABOVE this block.
frontend_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")

# SPA client-side routing fallback: any /admin/* path that isn't a real file
# must return index.html so React Router can resolve the route on the client.
# Registered BEFORE the StaticFiles mount because routes win over mounts.
if os.path.exists(frontend_dist):
    @app.get("/admin/{path:path}", include_in_schema=False)
    async def spa_admin_fallback(path: str):
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/triage", include_in_schema=False)
    async def spa_triage_fallback():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/intake/{path:path}", include_in_schema=False)
    async def spa_intake_fallback(path: str):
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/client/{path:path}", include_in_schema=False)
    async def spa_client_fallback(path: str):
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "webhook_service:app",
        host="0.0.0.0",
        port=settings.webhook_port,
        log_level="info",
    )
