"""
app/schemas/admin_leads — Pydantic v2 models for admin leads API.

Includes:
  LeadSummaryDTO      — list item (GET /api/admin/leads)
  LeadDetailDTO       — full detail (GET /api/admin/leads/{id})
  ConsentDTO          — consent audit entry embedded in detail
  LeadActionRequest   — PATCH /api/admin/leads/{id} body
  LeadActionResponse  — PATCH response
  LeadListResponse    — paginated list response
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums as string literals (no TS-style enums — consistent with assessments.py)
# ---------------------------------------------------------------------------

LeadStatus = Literal["pending_review", "accepted", "rejected", "converted"]
LeadBucket = Literal["auto_accept", "review", "cold_warm", "cold_cool", "reject_soft"]
LeadAction = Literal["accept", "reject", "request_extra_info", "assign_consultant"]

VALID_REJECT_REASONS = frozenset(
    {
        "not_qualified_size",
        "out_of_sector",
        "no_decision_authority",
        "not_aligned_with_offering",
        "not_a_real_lead",
        "other",
    }
)


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


class ConsentDTO(BaseModel):
    """Consent audit entry embedded in LeadDetailDTO."""

    id: str
    type: str
    accepted: bool
    timestamp: datetime
    policy_version: str

    model_config = {"from_attributes": True}


class LeadSummaryDTO(BaseModel):
    """List item returned by GET /api/admin/leads."""

    id: str
    full_name: str
    email: str
    company_name: str
    sector: str
    triage_bucket: str
    triage_score: int
    status: str
    created_at: datetime
    assigned_consultant_id: str | None

    model_config = {"from_attributes": True}

    @field_validator("assigned_consultant_id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v: Any) -> str | None:
        """SQLAlchemy returns UUID objects for FK columns — coerce to str."""
        if v is None:
            return None
        return str(v)


class LeadDetailDTO(BaseModel):
    """Full detail returned by GET /api/admin/leads/{id}."""

    id: str
    full_name: str
    email: str
    company_name: str
    phone: str | None
    sector: str
    company_size: str
    respondent_role: str
    ai_maturity: str
    ai_goals: list
    urgency: str
    commitment: str
    triage_payload: dict
    triage_score: int
    triage_bucket: str
    status: str
    rejected_reason: str | None
    assigned_consultant_id: str | None
    client_id: str | None
    created_at: datetime
    accepted_at: datetime | None
    consents: list[ConsentDTO]

    model_config = {"from_attributes": True}

    @field_validator("assigned_consultant_id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v: Any) -> str | None:
        """SQLAlchemy returns UUID objects for FK columns — coerce to str."""
        if v is None:
            return None
        return str(v)


# ---------------------------------------------------------------------------
# Request / response
# ---------------------------------------------------------------------------


class LeadActionRequest(BaseModel):
    """PATCH /api/admin/leads/{id} request body."""

    action: LeadAction
    reason: str | None = None
    consultant_id: str | None = None

    @model_validator(mode="after")
    def validate_action_requirements(self) -> "LeadActionRequest":
        if self.action == "accept" and not self.consultant_id:
            raise ValueError("consultant_id is required when action=accept")
        if self.action == "reject":
            if not self.reason:
                raise ValueError("reason is required when action=reject")
            if self.reason not in VALID_REJECT_REASONS:
                raise ValueError(
                    f"reason must be one of: {', '.join(sorted(VALID_REJECT_REASONS))}"
                )
        if self.action == "assign_consultant" and not self.consultant_id:
            raise ValueError("consultant_id is required when action=assign_consultant")
        return self


class SideEffect(BaseModel):
    """Describes a side effect triggered by an action."""

    type: str
    description: str


class LeadActionResponse(BaseModel):
    """PATCH /api/admin/leads/{id} response."""

    lead: LeadDetailDTO
    side_effects: list[SideEffect]


class LeadListResponse(BaseModel):
    """Paginated list response for GET /api/admin/leads."""

    items: list[LeadSummaryDTO]
    total: int
    page: int
    page_size: int
    pages: int
