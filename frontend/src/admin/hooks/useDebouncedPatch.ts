/**
 * useDebouncedPatch — debounced PATCH for the assessment editor.
 *
 * Accumulates field changes from multiple rapid calls into a single PATCH
 * request fired 500ms after the last call.  Multiple fields changed before
 * the timer fires are merged and sent together (one PATCH, not N).
 *
 * Two coalescing buffers, ONE network call:
 *   - Top-level fields    → merged into the PATCH payload directly
 *   - form_data fields    → merged under `form_data_patch` in the same payload
 *
 * Example: calling debouncedPatch({ company_name: "X" }) then
 * debouncedPatch.formData("software_used", ["A", "B"]) within the 500ms
 * window produces ONE PATCH:
 *   { company_name: "X", form_data_patch: { software_used: ["A", "B"] } }
 *
 * After the PATCH completes, invalidates ["assessment", id] so the editor
 * re-renders with the server-confirmed values (including updated field_sources).
 *
 * No TS enums, no constructor parameter properties (erasableSyntaxOnly).
 */

import { useQueryClient } from '@tanstack/react-query'
import type { QueryClient } from '@tanstack/react-query'
import { patchAssessment } from '../api/assessments'

// ---------------------------------------------------------------------------
// Module-level maps shared across hook instances for the same assessment.
// These are intentionally outside React state — they must survive re-renders
// without triggering them.  Same assessmentId → same buffer.
// ---------------------------------------------------------------------------

const debounceTimers = new Map<string, ReturnType<typeof setTimeout>>()

/** Top-level flat-column changes: { company_name: "X", budget: "50k" } */
const pendingTopLevel = new Map<string, Record<string, unknown>>()

/** form_data field changes: { software_used: ["A"], has_chatbot: true } */
const pendingFormData = new Map<string, Record<string, unknown>>()

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/**
 * Flush both buffers into a single PATCH request, then clear them.
 * Called from the debounce timer; also safe to call directly in tests.
 */
function flush(assessmentId: string, queryClient: QueryClient): void {
  const top = pendingTopLevel.get(assessmentId) ?? {}
  const fd = pendingFormData.get(assessmentId) ?? {}

  // Clear BEFORE the async call to avoid double-send on fast re-renders.
  pendingTopLevel.delete(assessmentId)
  pendingFormData.delete(assessmentId)
  debounceTimers.delete(assessmentId)

  const hasTop = Object.keys(top).length > 0
  const hasFd = Object.keys(fd).length > 0

  if (!hasTop && !hasFd) return

  // Build ONE payload: top-level fields + form_data_patch (only when non-empty).
  const payload: Record<string, unknown> = { ...top }
  if (hasFd) payload.form_data_patch = fd

  patchAssessment(assessmentId, payload)
    .then(() => queryClient.invalidateQueries({ queryKey: ['assessment', assessmentId] }))
    .catch(() => {
      // Silent — editor shows stale data; user can retry by editing again.
      // Phase D will add visible save-error indicators.
    })
}

/**
 * (Re-)arm the debounce timer for an assessment.
 * Every call resets the 500ms countdown.
 */
function arm(assessmentId: string, queryClient: QueryClient): void {
  const existing = debounceTimers.get(assessmentId)
  if (existing != null) clearTimeout(existing)

  debounceTimers.set(
    assessmentId,
    setTimeout(() => flush(assessmentId, queryClient), 500),
  )
}

// ---------------------------------------------------------------------------
// Public hook
// ---------------------------------------------------------------------------

/**
 * Callable type that preserves the original call signature AND adds the
 * `formData` method for form_data fields.
 *
 * Usage:
 *   const patch = useDebouncedPatch(assessmentId)
 *   patch({ company_name: "X" })             // top-level field
 *   patch.formData("software_used", ["A"])   // form_data field
 */
export type DebouncedPatch = ((changes: Record<string, unknown>) => void) & {
  formData: (key: string, value: unknown) => void
}

export function useDebouncedPatch(assessmentId: string): DebouncedPatch {
  const queryClient = useQueryClient()

  // Accumulate top-level flat-column changes and (re-)arm the timer.
  const patchTopLevel = (changes: Record<string, unknown>): void => {
    const existing = pendingTopLevel.get(assessmentId) ?? {}
    pendingTopLevel.set(assessmentId, { ...existing, ...changes })
    arm(assessmentId, queryClient)
  }

  // Accumulate form_data changes and (re-)arm the timer.
  // Single-key variant: patchFormData("software_used", ["A"]).
  const patchFormData = (key: string, value: unknown): void => {
    const existing = pendingFormData.get(assessmentId) ?? {}
    pendingFormData.set(assessmentId, { ...existing, [key]: value })
    arm(assessmentId, queryClient)
  }

  // Attach .formData as a property on the callable so callers can use either:
  //   patch({ company_name: "X" })
  //   patch.formData("software_used", ["A"])
  // — and both accumulate into the same debounce window.
  const fn = patchTopLevel as DebouncedPatch
  fn.formData = patchFormData

  return fn
}
