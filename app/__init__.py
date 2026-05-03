"""
app — Admin platform package.

This package contains the admin platform modules that extend the existing
AI Readiness Pipeline (webhook_service.py). The existing entrypoint
(webhook_service.py at repo root) stays in place; this package provides
all new admin functionality as importable modules.

Structure:
  db/          — Async SQLAlchemy engine, session factory, SQLite pragmas
  models/      — SQLAlchemy ORM models
  schemas/     — Pydantic request/response schemas
  auth/        — Password hashing, sessions, rate limiting, reset tokens, middleware
  api/         — FastAPI routers (admin auth, admin assessments, public, legacy)
  pipeline_steps/ — Decomposed pipeline steps (map_form, enrich_llm, etc.)
  jobs/        — JobRegistry, PDF lock, async job runners
  email/       — aiosmtplib sender + email templates
"""
