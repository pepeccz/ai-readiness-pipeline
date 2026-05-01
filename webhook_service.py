"""
AI Readiness Pipeline — Web Service
FastAPI app serving the React assessment form and processing pipeline.

Endpoints:
  GET  /             → React SPA (static files)
  POST /api/assessment    → Submit assessment form (returns 202 + task_id)
  GET  /api/status/{id}  → Check processing status
  GET  /api/download/{id} → Download generated .docx report
  GET  /api/health       → Service health check
"""

import os
import json
import uuid
import threading
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from typing import Optional

from fastapi import Request
from config import settings

app = FastAPI(
    title="AI Readiness Platform",
    version="2.0",
    docs_url=None,
    redoc_url=None,
)

# --- CORS ---
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# --- Pydantic Models ---


class AssessmentFormPayload(BaseModel):
    # Section 1 — Empresa
    company_name: str = ""
    sector: str
    employee_range: str
    contact_name: str
    revenue_range: str = ""
    contact_role: str = ""
    tech_decision_maker: str = ""
    # Section 2 — Stack
    software_used: list[str] = []
    ai_tools_used: list[str] = []
    has_chatbot: bool = False
    chatbot_desc: str = ""
    has_automations: bool = False
    automations_desc: str = ""
    # Section 3 — Atención al cliente
    contact_channels: list[str] = []
    daily_queries: str = ""
    support_team_desc: str = ""
    top_repetitive_queries: str = ""
    avg_resolution_time: str = ""
    # Section 4 — Marketing y ventas
    content_generation: list[str] = []
    lead_acquisition: list[str] = []
    has_lead_tracking: bool = False
    lead_tracking_desc: str = ""
    monthly_marketing_budget: str = ""
    # Section 5 — Operaciones
    most_time_consuming_process: str
    process_people_count: str = ""
    process_hours_per_week: str = ""
    data_entry_channels: list[str] = []
    process_pain_points: list[str] = []
    # Section 6 — Finanzas
    invoicing_method: str = ""
    has_cash_flow_control: bool = False
    cash_flow_desc: str = ""
    admin_hours_per_week: str = ""
    # Section 7 — RRHH
    is_hiring: bool = False
    hiring_desc: str = ""
    hr_management_method: str = ""
    hr_hours_per_week: str = ""
    # Section 8 — Compliance
    collects_personal_data: bool = False
    personal_data_types: str = ""
    knows_ai_gdpr: str = ""
    has_dpa: str = ""
    dpa_with_whom: str = ""
    knows_ai_act: str = ""
    has_ai_policy: str = ""
    # Section 9 — Presupuesto
    investment_budget: str
    urgency: str
    additional_notes: str = ""

    @field_validator("company_name", "sector", "employee_range", "contact_name",
                     "most_time_consuming_process", "investment_budget", "urgency")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Este campo es obligatorio")
        return v.strip()


# --- In-memory task store ---
_tasks: dict[str, dict] = {}


def _run_pipeline(task_id: str, form_data: dict) -> None:
    """Run the pipeline in a background thread."""
    _tasks[task_id]["status"] = "processing"
    _tasks[task_id]["started_at"] = datetime.now().isoformat()

    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from pipeline import process_assessment_v2

        docx_path = process_assessment_v2(form_data)

        _tasks[task_id]["status"] = "completed"
        _tasks[task_id]["docx_path"] = docx_path
        _tasks[task_id]["download_available"] = True
        _tasks[task_id]["completed_at"] = datetime.now().isoformat()

    except Exception as e:
        _tasks[task_id]["status"] = "error"
        _tasks[task_id]["error"] = str(e)
        _tasks[task_id]["completed_at"] = datetime.now().isoformat()
        print(f"[webhook] Pipeline error for task {task_id}: {e}")


# --- API Endpoints ---


def _verify_auth(request_or_header: str) -> None:
    """Validate bearer token. Raises 403 if invalid."""
    secret = settings.webhook_secret.get_secret_value()
    if not secret:
        return  # No secret = dev mode (open)
    token = request_or_header.replace("Bearer ", "") if request_or_header.startswith("Bearer ") else request_or_header
    if token != secret:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")


@app.post("/api/assessment", status_code=202)
async def submit_assessment(payload: AssessmentFormPayload, request: Request):
    """Receive assessment form and start pipeline processing. Requires bearer token."""
    auth = request.headers.get("Authorization", "")
    _verify_auth(auth)

    task_id = str(uuid.uuid4())[:8]

    _tasks[task_id] = {
        "status": "queued",
        "company": payload.contact_name,
        "received_at": datetime.now().isoformat(),
    }

    thread = threading.Thread(
        target=_run_pipeline,
        args=(task_id, payload.model_dump()),
        daemon=True,
    )
    thread.start()

    return {
        "status": "accepted",
        "task_id": task_id,
        "message": "Assessment en cola de procesamiento",
    }


@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """Check processing status."""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Don't expose internal fields
    return {
        "status": task["status"],
        "received_at": task.get("received_at"),
        "started_at": task.get("started_at"),
        "completed_at": task.get("completed_at"),
        "download_available": task.get("download_available", False),
        "error": task.get("error"),
    }


@app.get("/api/download/{task_id}")
async def download_report(task_id: str):
    """Download the generated report (PDF or DOCX)."""
    task = _tasks.get(task_id)
    if not task or task["status"] != "completed":
        raise HTTPException(status_code=404, detail="Report not ready")

    report_path = task.get("docx_path")
    if not report_path or not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report file not found")

    company = task.get("company", "informe").replace(" ", "_")
    is_pdf = report_path.endswith(".pdf")
    filename = f"AIR-Informe-{company}.{'pdf' if is_pdf else 'docx'}"
    media_type = "application/pdf" if is_pdf else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return FileResponse(report_path, filename=filename, media_type=media_type)


@app.get("/api/health")
async def health():
    """Service health check."""
    return {
        "status": "healthy",
        "service": "ai-readiness-pipeline",
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": sum(1 for t in _tasks.values() if t["status"] == "processing"),
        "total_tasks": len(_tasks),
    }


# --- Static files (React SPA) — mount LAST ---
frontend_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "webhook_service:app",
        host="0.0.0.0",
        port=settings.webhook_port,
        log_level="info",
    )
