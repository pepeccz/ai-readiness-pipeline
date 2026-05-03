/**
 * completeness.ts — shared "empty" predicate and assessment completeness helper.
 *
 * Mirrors app/utils/completeness.py (design R4 + §6 + §7).
 * The predicate semantics MUST stay identical to the Python side.
 *
 * R4 contract:
 *   null | undefined | ""    → empty
 *   []                       → empty  (no items selected)
 *   {}                       → empty  (empty object — treated like missing)
 *   false                    → FILLED (explicit "no" answer)
 *   0                        → FILLED (explicit "zero hours" answer)
 *   0.0 (number)             → FILLED
 *
 * Whitespace-only strings are NOT trimmed — "  " is filled by design.
 */

import type { AssessmentResponse } from '../api/assessments'
import { FORM_DATA_KEYS } from './formDataKeys'

// ---------------------------------------------------------------------------
// Critical fields (must be filled to avoid isSparse regardless of fill rate)
// ---------------------------------------------------------------------------

/** Critical form_data keys — absence overrides fill-rate threshold. */
const CRITICAL_FORM_DATA: readonly string[] = [
  'most_time_consuming_process',
  'software_used',
  'daily_queries',
  'urgency',
] as const

/** Critical flat-column keys on AssessmentResponse. */
const CRITICAL_FLAT: readonly (keyof AssessmentResponse)[] = [
  'sector',
] as const

/** Fill-rate threshold: < 60% (26/42) → sparse. */
const COMPLETENESS_THRESHOLD = 0.6

// ---------------------------------------------------------------------------
// isEmpty predicate
// ---------------------------------------------------------------------------

/**
 * Returns true when `value` is considered "empty" per design R4.
 *
 * @example
 *   isEmpty(null)      // true
 *   isEmpty(undefined) // true
 *   isEmpty('')        // true
 *   isEmpty([])        // true
 *   isEmpty({})        // true
 *   isEmpty(false)     // false  ← explicit "no" answer
 *   isEmpty(0)         // false  ← explicit "zero" answer
 *   isEmpty('hello')   // false
 *   isEmpty([1])       // false
 */
export function isEmpty(value: unknown): boolean {
  if (value == null) return true
  if (typeof value === 'string' && value === '') return true
  if (Array.isArray(value) && value.length === 0) return true
  if (
    typeof value === 'object' &&
    value !== null &&
    !Array.isArray(value) &&
    Object.keys(value as Record<string, unknown>).length === 0
  ) {
    return true
  }
  return false
}

// ---------------------------------------------------------------------------
// assessmentCompleteness
// ---------------------------------------------------------------------------

export interface CompletenessResult {
  /** Number of canonical form_data keys that have a filled value. */
  filledKeys: number
  /** Total canonical keys — always FORM_DATA_KEYS.length (42). */
  totalKeys: number
  /** filledKeys / totalKeys (0..1). */
  percentage: number
  /** Critical field names that are empty (form_data keys + flat keys). */
  missingCritical: string[]
  /** True when percentage < 0.6 OR any critical field is missing. */
  isSparse: boolean
}

/**
 * Compute completeness for an assessment.
 *
 * Mirrors Python `assessment_completeness(form_data, flat_fields)`.
 *
 * @param assessment - Full AssessmentResponse (or undefined for safe zero-state).
 * @returns CompletenessResult
 */
export function assessmentCompleteness(
  assessment: AssessmentResponse | undefined,
): CompletenessResult {
  if (assessment == null) {
    return {
      filledKeys: 0,
      totalKeys: FORM_DATA_KEYS.length,
      percentage: 0,
      missingCritical: [...CRITICAL_FORM_DATA, ...CRITICAL_FLAT],
      isSparse: true,
    }
  }

  const fd = (assessment.form_data ?? {}) as Record<string, unknown>

  const filledKeys = FORM_DATA_KEYS.filter((k) => !isEmpty(fd[k])).length
  const totalKeys = FORM_DATA_KEYS.length
  const percentage = filledKeys / totalKeys

  const missingCritical: string[] = []
  for (const k of CRITICAL_FORM_DATA) {
    if (isEmpty(fd[k])) missingCritical.push(k)
  }
  for (const k of CRITICAL_FLAT) {
    if (isEmpty(assessment[k])) missingCritical.push(k as string)
  }

  const isSparse = percentage < COMPLETENESS_THRESHOLD || missingCritical.length > 0

  return { filledKeys, totalKeys, percentage, missingCritical, isSparse }
}
