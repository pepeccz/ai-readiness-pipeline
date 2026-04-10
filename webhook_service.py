"""
AI Readiness Pipeline — Webhook Service
FastAPI app that receives assessment JSON from Google AppScript
and runs the pipeline in background.

Endpoints:
  POST /assessment  — Submit assessment (returns 202 + task_id)
  GET  /status/{id} — Check processing status
  GET  /health      — Service health check
"""

import json
import time
import uuid
import threading
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from config import settings

app = FastAPI(
    title="AI Readiness Pipeline",
    version="2.0",
    docs_url=None,
    redoc_url=None,
)

# --- In-memory task store ---
_tasks: dict[str, dict] = {}


def _verify_bearer(request: Request) -> None:
    """Validate bearer token from Authorization header."""
    secret = settings.webhook_secret.get_secret_value()
    if not secret:
        return  # No secret configured = open access (dev mode)

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = auth[7:]
    if token != secret:
        raise HTTPException(status_code=403, detail="Invalid bearer token")


def _run_pipeline(task_id: str, json_str: str) -> None:
    """Run the pipeline in a background thread. Updates task store on completion."""
    _tasks[task_id]["status"] = "processing"
    _tasks[task_id]["started_at"] = datetime.now().isoformat()

    try:
        # Import here to avoid circular imports at module level
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from pipeline import process_assessment

        result = process_assessment(json_str)

        _tasks[task_id]["status"] = "completed"
        _tasks[task_id]["result"] = result if isinstance(result, dict) else {"output": str(result)}
        _tasks[task_id]["completed_at"] = datetime.now().isoformat()

    except Exception as e:
        _tasks[task_id]["status"] = "error"
        _tasks[task_id]["error"] = str(e)
        _tasks[task_id]["completed_at"] = datetime.now().isoformat()
        print(f"[webhook] Pipeline error for task {task_id}: {e}")


@app.post("/assessment")
async def submit_assessment(request: Request):
    """
    Receive assessment JSON and start pipeline processing.
    Returns 202 Accepted immediately with a task_id for status polling.
    """
    _verify_bearer(request)

    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")

    # Validate minimum required fields
    if not body.get("access_code") and not body.get("assessment_id"):
        raise HTTPException(
            status_code=400,
            detail="Missing required field: access_code or assessment_id"
        )

    task_id = str(uuid.uuid4())[:8]
    json_str = json.dumps(body, ensure_ascii=False)

    _tasks[task_id] = {
        "status": "queued",
        "company": body.get("company_name", "unknown"),
        "access_code": body.get("access_code", ""),
        "received_at": datetime.now().isoformat(),
    }

    # Run pipeline in background thread
    thread = threading.Thread(
        target=_run_pipeline,
        args=(task_id, json_str),
        daemon=True,
    )
    thread.start()

    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "task_id": task_id,
            "message": f"Assessment queued for processing",
        },
    )


@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """Check the status of a submitted assessment."""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/health")
async def health():
    """Service health check."""
    return {
        "status": "healthy",
        "service": "ai-readiness-pipeline",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": sum(1 for t in _tasks.values() if t["status"] == "processing"),
        "total_tasks": len(_tasks),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "webhook_service:app",
        host="0.0.0.0",
        port=settings.webhook_port,
        log_level="info",
    )
