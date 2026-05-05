"""
app/services/scoring/lead_scorer.py

Lead scoring engine for TRIAGE v1.1.

Pure function design — no side effects, no DB access, deterministic.

Scoring model:
  Dimension          | Question field              | Max pts
  -------------------|-----------------------------|---------
  Sector             | triage.q.sector             | 18
  Company size       | triage.q.company_size       | 20
  Respondent role    | triage.q.respondent_role    | 12
  AI maturity        | triage.q.ai_maturity        | 8
  Urgency            | triage.q.urgency            | 28
  AI goals           | triage.q.ai_goals (sum)     | 12 (max 2×6)
  Commitment         | triage.q.commitment         | 18
                                            TOTAL: 136

Bucket thresholds (inclusive):
  ≥85          → auto_accept
  55–84        → review
  45–54        → cold_warm
  30–44        → cold_cool
  ≤29 (0–29)   → reject_soft

Override rules are applied post-scoring via the override_rules engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.questionnaire.override_rules import apply_overrides, OverrideResult

# ---------------------------------------------------------------------------
# Scoring tables — must match triage.yaml option values + scores
# ---------------------------------------------------------------------------

_SECTOR_SCORES: dict[str, int] = {
    "finanzas": 18,
    "salud": 18,
    "tecnologia": 18,
    "legal": 15,
    "industria": 15,
    "retail": 12,
    "educacion": 10,
    "otro": 8,
}

_COMPANY_SIZE_SCORES: dict[str, int] = {
    "1_5": 4,
    "6_25": 12,
    "26_100": 20,
    "101_500": 20,
    "500_plus": 20,
}

_RESPONDENT_ROLE_SCORES: dict[str, int] = {
    "ceo_fundador": 12,
    "director_area": 10,
    "responsable_it": 10,
    "consultor_externo": 8,
    "otro_rol": 6,
}

_AI_MATURITY_SCORES: dict[str, int] = {
    "sin_ia": 3,
    "exploracion": 5,
    "pilotos": 7,
    "produccion_sin_gobierno": 6,
    "produccion_gobernada": 8,
}

_URGENCY_SCORES: dict[str, int] = {
    "critica": 28,
    "alta": 22,
    "media": 14,
    "baja": 6,
}

_AI_GOALS_SCORES: dict[str, int] = {
    "reducir_costes": 6,
    "mejorar_clientes": 6,
    "aumentar_ventas": 6,
    "automatizar_procesos": 6,
    "tomar_decisiones": 6,
    "cumplimiento_regulatorio": 6,
}

_COMMITMENT_SCORES: dict[str, int] = {
    "agendar": 18,
    "propuesta_formal": 14,
    "informacion": 8,
    "evaluacion_interna": 4,
}

# Bucket thresholds (min score inclusive)
_BUCKETS = [
    ("auto_accept", 85),
    ("review", 55),
    ("cold_warm", 45),
    ("cold_cool", 30),
    ("reject_soft", 0),
]


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ScoreResult:
    total_score: int
    bucket: str
    dimension_scores: dict[str, int] = field(default_factory=dict)
    flags: dict[str, Any] = field(default_factory=dict)
    extra_questions: list[str] = field(default_factory=list)
    disabled_fields: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# LeadScorer
# ---------------------------------------------------------------------------

class LeadScorer:
    """
    Stateless scorer. Instantiate once; call score() for each submission.
    No side effects. No DB access. Deterministic.
    """

    def score_from_total(self, total: int) -> ScoreResult:
        """
        Given a pre-computed total score, return the bucket.
        Useful for boundary tests without needing full answer dicts.
        """
        bucket = _bucket_from_score(total)
        return ScoreResult(total_score=total, bucket=bucket)

    def score(
        self,
        answers: dict,
        override_rules: list[dict] | None = None,
    ) -> ScoreResult:
        """
        Compute total score from individual answers, determine bucket,
        then apply override rules.

        answers keys: triage.q.{field_id} → str | list[str]
        override_rules: list of override rule dicts (from YAML schema)
        """
        dimension_scores = self._compute_dimensions(answers)
        total = sum(dimension_scores.values())
        base_bucket = _bucket_from_score(total)

        # Apply override rules
        if override_rules:
            override_result: OverrideResult = apply_overrides(
                answers=answers,
                base_score=total,
                base_bucket=base_bucket,
                rules=override_rules,
            )
            final_bucket = override_result.bucket
            flags = override_result.flags
            extra_questions = override_result.extra_questions
            disabled_fields = override_result.disabled_fields
        else:
            final_bucket = base_bucket
            flags = {}
            extra_questions = []
            disabled_fields = []

        return ScoreResult(
            total_score=total,
            bucket=final_bucket,
            dimension_scores=dimension_scores,
            flags=flags,
            extra_questions=extra_questions,
            disabled_fields=disabled_fields,
        )

    def _compute_dimensions(self, answers: dict) -> dict[str, int]:
        dims: dict[str, int] = {}

        # Sector (0–18)
        sector = answers.get("triage.q.sector", "")
        dims["sector"] = _SECTOR_SCORES.get(sector, 0)

        # Company size (0–20)
        size = answers.get("triage.q.company_size", "")
        dims["company_size"] = _COMPANY_SIZE_SCORES.get(size, 0)

        # Respondent role (0–12)
        role = answers.get("triage.q.respondent_role", "")
        dims["respondent_role"] = _RESPONDENT_ROLE_SCORES.get(role, 0)

        # AI maturity (0–8)
        maturity = answers.get("triage.q.ai_maturity", "")
        dims["ai_maturity"] = _AI_MATURITY_SCORES.get(maturity, 0)

        # Urgency (0–28)
        urgency = answers.get("triage.q.urgency", "")
        dims["urgency"] = _URGENCY_SCORES.get(urgency, 0)

        # AI goals — sum of selected goals scores (max 2 × 6 = 12)
        goals = answers.get("triage.q.ai_goals", [])
        if isinstance(goals, str):
            goals = [goals]
        goals_score = sum(_AI_GOALS_SCORES.get(g, 0) for g in goals[:2])
        dims["ai_goals"] = goals_score

        # Commitment (0–18)
        commitment = answers.get("triage.q.commitment", "")
        dims["commitment"] = _COMMITMENT_SCORES.get(commitment, 0)

        return dims


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _bucket_from_score(score: int) -> str:
    for name, min_score in _BUCKETS:
        if score >= min_score:
            return name
    return "reject_soft"
