/**
 * useAssessmentCompleteness — memoised completeness state for an assessment.
 *
 * Wraps `assessmentCompleteness()` from completeness.ts in a React hook so
 * consuming components get a stable object reference that only recomputes
 * when the assessment changes (TanStack Query keeps the object referentially
 * stable across renders, so useMemo fires only on real server updates).
 *
 * Usage:
 *   const c = useAssessmentCompleteness(assessment)
 *   if (c.isSparse) { ... }
 *
 * Takes `assessment` as a prop so the hook is decoupled from any specific
 * query key.  The caller wires the query; this hook just computes.
 *
 * No TS enums, no constructor parameter properties (erasableSyntaxOnly).
 */

import { useMemo } from 'react'
import type { AssessmentResponse } from '../api/assessments'
import { assessmentCompleteness } from '../utils/completeness'
import type { CompletenessResult } from '../utils/completeness'

// Re-export so consumers only need to import from this hook file.
export type { CompletenessResult }

/**
 * Compute and memoise the completeness state of an assessment.
 *
 * @param assessment - Full AssessmentResponse from TanStack Query,
 *                     or undefined while the query is loading.
 * @returns CompletenessResult — referentially stable until `assessment` changes.
 *
 * Shape:
 *   filledKeys      number   — count of canonical form_data keys with a filled value
 *   totalKeys       number   — always 42 (len(FORM_DATA_KEYS))
 *   percentage      number   — filledKeys / totalKeys (0..1)
 *   missingCritical string[] — names of critical fields that are empty
 *   isSparse        boolean  — true when percentage < 0.6 OR any critical field missing
 */
export function useAssessmentCompleteness(
  assessment: AssessmentResponse | undefined,
): CompletenessResult {
  return useMemo(() => assessmentCompleteness(assessment), [assessment])
}
