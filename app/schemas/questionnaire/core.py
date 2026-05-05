"""
app/schemas/questionnaire/core.py

Pydantic v2 models for questionnaire schema (NOT the YAML files on disk —
these are models used to validate and type-check the loaded schema data).

Uses discriminated unions on the `type` field for Question variants.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field, TypeAdapter, model_validator


# ---------------------------------------------------------------------------
# Option
# ---------------------------------------------------------------------------

class Option(BaseModel):
    value: str
    label: str
    score: Optional[float] = None
    deep_branches: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# ShowIfRule
# ---------------------------------------------------------------------------

class ShowIfRule(BaseModel):
    field: str
    op: Literal["eq", "neq", "in", "not_in", "gt", "lt", "any_of", "all_of"] = "eq"
    value: Union[str, int, float, list[str]]


# ---------------------------------------------------------------------------
# ValidationRule
# ---------------------------------------------------------------------------

class ValidationRule(BaseModel):
    type: Literal["required", "min_length", "max_length", "pattern", "min", "max"]
    value: Optional[Union[int, str]] = None
    message: Optional[str] = None


# ---------------------------------------------------------------------------
# BaseQuestion — common fields for all question variants
# ---------------------------------------------------------------------------

class BaseQuestion(BaseModel):
    id: str
    layer: Literal["triage", "core", "deep"]
    block: Optional[str] = None
    required: bool = False
    label: str
    helper_text: Optional[str] = None
    hint_didactic: Optional[str] = None
    hint_commercial: Optional[str] = None
    show_if: Optional[ShowIfRule] = None
    validations: list[ValidationRule] = Field(default_factory=list)
    ai_context: Optional[str] = None


# ---------------------------------------------------------------------------
# Concrete Question variants
# ---------------------------------------------------------------------------

class SingleChoiceQuestion(BaseQuestion):
    type: Literal["single_choice"]
    options: list[Option]
    scoring_strategy: Optional[Literal["sum", "max", "weighted"]] = None


class MultiChoiceQuestion(BaseQuestion):
    type: Literal["multi_choice"]
    options: list[Option]
    min_selections: int = 0
    max_selections: Optional[int] = None


class TextQuestion(BaseQuestion):
    type: Literal["text", "textarea"]
    placeholder: Optional[str] = None


class CompositeQuestion(BaseQuestion):
    type: Literal["composite"]
    sub_fields: list["Question"] = Field(default_factory=list)


class ConsentQuestion(BaseQuestion):
    type: Literal["consent"]
    policy_version: str
    policy_file: str  # relative path to consents/*.md


# ---------------------------------------------------------------------------
# Discriminated union — Question
# ---------------------------------------------------------------------------

Question = Annotated[
    Union[
        SingleChoiceQuestion,
        MultiChoiceQuestion,
        TextQuestion,
        CompositeQuestion,
        ConsentQuestion,
    ],
    Field(discriminator="type"),
]

# Rebuild forward references (needed for CompositeQuestion.sub_fields)
CompositeQuestion.model_rebuild()

# TypeAdapter for parsing arbitrary dicts into the union
_question_adapter: TypeAdapter[Question] = TypeAdapter(Question)


def parse_question(data: dict) -> Question:
    """Parse a raw dict into the correct Question variant via discriminated union."""
    return _question_adapter.validate_python(data)


# ---------------------------------------------------------------------------
# Block-level models
# ---------------------------------------------------------------------------

class ClosingAnalysis(BaseModel):
    trigger_event: Literal["block_completed", "session_closing"]
    llm_model: Literal["sonnet", "haiku"]
    output_schema: dict = Field(default_factory=dict)
    filters: list[str] = Field(default_factory=list)


class DeepTrigger(BaseModel):
    condition: ShowIfRule
    activates_branch: str


class BlockSchema(BaseModel):
    id: str
    layer: Literal["core"]
    order: int
    estimated_minutes: int
    title: str
    questions: list[Question] = Field(default_factory=list)
    closing_analysis: Optional[ClosingAnalysis] = None
    deep_triggers: list[DeepTrigger] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Triage scoring buckets
# ---------------------------------------------------------------------------

class ScoringBucket(BaseModel):
    name: str
    min: int
    max: int


class TriageScoring(BaseModel):
    buckets: list[ScoringBucket]


# ---------------------------------------------------------------------------
# Triage schema
# ---------------------------------------------------------------------------

class TriageSchema(BaseModel):
    id: Literal["triage"]
    layer: Literal["triage"]
    title: str
    questions: list[Question] = Field(default_factory=list)
    scoring: TriageScoring
    override_rules: list[Any] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Core schema
# ---------------------------------------------------------------------------

class CoreSchema(BaseModel):
    blocks_order: list[str] = Field(default_factory=list)
    block_2_variants: dict[str, Any] = Field(default_factory=dict)
    area_overlays: dict[str, Any] = Field(default_factory=dict)
    blocks: list[BlockSchema] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Root schema
# ---------------------------------------------------------------------------

class RootSchema(BaseModel):
    schema_version: str
    locale: str = "es_ES"
    triage: TriageSchema
    core: CoreSchema
    deep: dict[str, Any] = Field(default_factory=dict)
    override_rules: list[Any] = Field(default_factory=list)
