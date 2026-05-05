"""
app/services/questionnaire/override_rules.py

Override rules engine for TRIAGE scoring.

Reads rules from the YAML schema (already loaded) and applies them
post-scoring. Pure function — no side effects, no DB access.

Public API:
  apply_overrides(answers, base_score, base_bucket, rules) → OverrideResult
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OverrideResult:
    bucket: str
    flags: dict[str, Any] = field(default_factory=dict)
    extra_questions: list[str] = field(default_factory=list)
    disabled_fields: list[str] = field(default_factory=list)


def apply_overrides(
    answers: dict,
    base_score: int,
    base_bucket: str,
    rules: list[dict],
) -> OverrideResult:
    """
    Apply all override rules in order.

    Each rule is evaluated independently. Later rules can overwrite earlier ones.
    Returns an OverrideResult with the final bucket + any flags/side-effects.
    """
    result = OverrideResult(bucket=base_bucket)

    for rule in rules:
        _apply_rule(rule, answers, base_score, result)

    return result


def _apply_rule(
    rule: dict,
    answers: dict,
    base_score: int,
    result: OverrideResult,
) -> None:
    condition = rule.get("condition", {})
    action = rule.get("action")

    if not _matches_condition(condition, answers, base_score):
        return

    if action == "force_bucket":
        target = rule["target_bucket"]
        applies_only_upgrade = rule.get("applies_only_upgrade", False)

        if applies_only_upgrade:
            # Only upgrade — never downgrade
            bucket_order = ["reject_soft", "cold_cool", "cold_warm", "review", "auto_accept"]
            current_rank = bucket_order.index(result.bucket) if result.bucket in bucket_order else -1
            target_rank = bucket_order.index(target) if target in bucket_order else -1
            if target_rank > current_rank:
                result.bucket = target
        else:
            result.bucket = target

        flag = rule.get("set_flag")
        if flag:
            result.flags[flag] = True

        extra = rule.get("requires_extra_question")
        if extra:
            result.extra_questions.append(extra)

    elif action == "disable_field":
        target_field = rule.get("target_field")
        if target_field and target_field not in result.disabled_fields:
            result.disabled_fields.append(target_field)


def _matches_condition(condition: dict, answers: dict, base_score: int) -> bool:
    """
    Evaluate all condition predicates — ALL must match (AND semantics).
    """
    for key, expected in condition.items():
        if key == "sector_in":
            sector = answers.get("triage.q.sector", "")
            if sector not in expected:
                return False

        elif key == "urgency_in":
            urgency = answers.get("triage.q.urgency", "")
            if urgency not in expected:
                return False

        elif key == "min_score":
            if base_score < expected:
                return False

        elif key == "respondent_role":
            if answers.get("triage.q.respondent_role") != expected:
                return False

        elif key == "commitment":
            if answers.get("triage.q.commitment") != expected:
                return False

        elif key == "area_mode":
            if answers.get("intake.area_mode") != expected:
                return False

    return True
