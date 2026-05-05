"""
app/schemas/triage — Pydantic v2 schemas for TRIAGE public endpoints.

T3.1 schemas:
  ConsentEntry      — one consent record (privacy | marketing)
  TriageAnswers     — validated TRIAGE form answers
  TriagePayload     — full submission body (answers + consents)
  TriageResponse    — 201 response body
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Consent
# ---------------------------------------------------------------------------

VALID_CONSENT_TYPES = {"privacy", "marketing", "data_processing"}


class ConsentEntry(BaseModel):
    type: str
    accepted: bool
    policy_version: str

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_CONSENT_TYPES:
            raise ValueError(f"consent type must be one of {VALID_CONSENT_TYPES}, got {v!r}")
        return v


# ---------------------------------------------------------------------------
# TRIAGE Answers
# ---------------------------------------------------------------------------

VALID_AI_MATURITY = {
    "sin_ia", "exploracion", "pilotos", "produccion_sin_gobierno", "produccion_gobernada"
}

VALID_SECTORS = {
    "finanzas", "salud", "tecnologia", "legal", "industria", "retail", "educacion", "otro"
}

VALID_COMPANY_SIZES = {"1_5", "6_25", "26_100", "101_500", "500_plus"}

VALID_RESPONDENT_ROLES = {
    "ceo_fundador", "director_area", "responsable_it", "consultor_externo", "otro_rol"
}

VALID_URGENCY = {"critica", "alta", "media", "baja"}

VALID_AI_GOALS = {
    "reducir_costes", "mejorar_clientes", "aumentar_ventas",
    "automatizar_procesos", "tomar_decisiones", "cumplimiento_regulatorio"
}

VALID_COMMITMENT = {"agendar", "propuesta_formal", "informacion", "evaluacion_interna"}


class TriageAnswers(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    company_name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=50)

    sector: str
    company_size: str
    respondent_role: str
    ai_maturity: str
    urgency: str
    ai_goals: Annotated[list[str], Field(max_length=2)]
    commitment: str

    @field_validator("sector")
    @classmethod
    def validate_sector(cls, v: str) -> str:
        if v not in VALID_SECTORS:
            raise ValueError(f"invalid sector: {v!r}")
        return v

    @field_validator("company_size")
    @classmethod
    def validate_company_size(cls, v: str) -> str:
        if v not in VALID_COMPANY_SIZES:
            raise ValueError(f"invalid company_size: {v!r}")
        return v

    @field_validator("respondent_role")
    @classmethod
    def validate_respondent_role(cls, v: str) -> str:
        if v not in VALID_RESPONDENT_ROLES:
            raise ValueError(f"invalid respondent_role: {v!r}")
        return v

    @field_validator("ai_maturity")
    @classmethod
    def validate_ai_maturity(cls, v: str) -> str:
        if v not in VALID_AI_MATURITY:
            raise ValueError(f"invalid ai_maturity: {v!r}")
        return v

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        if v not in VALID_URGENCY:
            raise ValueError(f"invalid urgency: {v!r}")
        return v

    @field_validator("ai_goals", mode="before")
    @classmethod
    def validate_ai_goals(cls, v: list) -> list:
        if len(v) > 2:
            raise ValueError("ai_goals: max 2 items allowed")
        for goal in v:
            if goal not in VALID_AI_GOALS:
                raise ValueError(f"invalid ai_goal: {goal!r}")
        return v

    @field_validator("commitment")
    @classmethod
    def validate_commitment(cls, v: str) -> str:
        if v not in VALID_COMMITMENT:
            raise ValueError(f"invalid commitment: {v!r}")
        return v


# ---------------------------------------------------------------------------
# TriagePayload
# ---------------------------------------------------------------------------


class TriagePayload(BaseModel):
    answers: TriageAnswers
    consents: list[ConsentEntry]

    @model_validator(mode="after")
    def privacy_consent_required(self) -> "TriagePayload":
        privacy = next(
            (c for c in self.consents if c.type == "privacy"),
            None,
        )
        if privacy is None or not privacy.accepted:
            raise ValueError(
                "privacy consent is required: consents must contain an accepted privacy entry"
            )
        return self


# ---------------------------------------------------------------------------
# TriageResponse
# ---------------------------------------------------------------------------


class TriageResponse(BaseModel):
    lead_id: str
    bucket: str
    message: str
