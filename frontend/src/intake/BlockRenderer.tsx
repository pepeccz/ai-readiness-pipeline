/**
 * BlockRenderer — renders a full CORE block from schema.
 *
 * Orchestrates:
 * - FieldRenderer per visible question (show_if evaluated by useSchemaForm)
 * - Submit button with loading state
 * - Auto-save restoration from localStorage
 * - Progress indicator (X of Y questions answered)
 *
 * REQ-5 / ADR-3: The inner form is keyed by `${schema.id}:${payloadFingerprint}`.
 * Changing block OR receiving an updated payload forces a full remount, which
 * discards stale useState and re-seeds from `initialPayload`. This is the
 * canonical React idiom for "this is a different form instance".
 */

import { useEffect, useMemo, useRef } from 'react'
import type { BlockSchema } from './types/schema'
import { FieldRenderer } from './FieldRenderer'
import { useSchemaForm } from './hooks/useSchemaForm'
import { useBlockSubmit } from './api/intake'

interface BlockRendererProps {
  leadId: string
  schema: BlockSchema
  initialPayload?: Record<string, unknown>
  onSubmitSuccess?: (blockAnalysisId: string) => void
}

const LOCAL_STORAGE_KEY = (sessionId: string, blockId: string) =>
  `intake_session_${sessionId}_block_${blockId}`

/**
 * Produces a short stable fingerprint of the payload so React's key prop can
 * detect identity changes without an expensive deep-equal on every render.
 * Uses JSON.stringify sorted by key for determinism.
 */
function payloadFingerprint(payload: Record<string, unknown> | undefined): string {
  if (!payload) return 'empty'
  const sorted = Object.keys(payload)
    .sort()
    .reduce<Record<string, unknown>>((acc, k) => { acc[k] = payload[k]; return acc }, {})
  return JSON.stringify(sorted)
}

export function BlockRenderer({
  leadId,
  schema,
  initialPayload,
  onSubmitSuccess,
}: BlockRendererProps) {
  const formKey = useMemo(
    () => `${schema.id}:${payloadFingerprint(initialPayload)}`,
    [schema.id, initialPayload],
  )

  return (
    <BlockForm
      key={formKey}
      leadId={leadId}
      schema={schema}
      initialPayload={initialPayload}
      onSubmitSuccess={onSubmitSuccess}
    />
  )
}

/**
 * BlockForm is the actual stateful form. It is always mounted fresh when
 * BlockRenderer's key changes (i.e. on block navigation or payload update).
 */
function BlockForm({
  leadId,
  schema,
  initialPayload,
  onSubmitSuccess,
}: BlockRendererProps) {
  const form = useSchemaForm(schema)
  const submitMutation = useBlockSubmit(leadId, schema.id)
  const autoSaveTimer = useRef<ReturnType<typeof setInterval> | null>(null)
  const storageKey = LOCAL_STORAGE_KEY(leadId, schema.id)

  // Restore from localStorage on mount
  useEffect(() => {
    if (initialPayload) {
      // Server payload takes precedence
      Object.entries(initialPayload).forEach(([k, v]) => form.setValue(k, v))
      return
    }
    const saved = localStorage.getItem(storageKey)
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as Record<string, unknown>
        Object.entries(parsed).forEach(([k, v]) => form.setValue(k, v))
      } catch {
        // Ignore malformed cache
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [schema.id])

  // Auto-save every 30s
  useEffect(() => {
    autoSaveTimer.current = setInterval(() => {
      if (form.isDirty) {
        localStorage.setItem(storageKey, JSON.stringify(form.values))
      }
    }, 30_000)
    return () => {
      if (autoSaveTimer.current) clearInterval(autoSaveTimer.current)
    }
  }, [form.isDirty, form.values, storageKey])

  const visibleQuestions = form.getVisibleQuestions()
  const answeredCount = visibleQuestions.filter(
    (q) => form.values[q.id] !== undefined && form.values[q.id] !== '',
  ).length

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const valid = form.validate()
    if (!valid) return

    const payload = form.buildPayload()
    try {
      const result = await submitMutation.mutateAsync(payload)
      // Clear localStorage on success
      localStorage.removeItem(storageKey)
      form.reset()
      onSubmitSuccess?.(result.block_analysis_id)
    } catch {
      // Error handled by mutation state
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b pb-4">
        <h2 className="text-lg font-semibold text-neutral-900">{schema.title}</h2>
        <div className="flex items-center gap-4 mt-2 text-xs text-neutral-500">
          <span>~{schema.estimated_minutes} min</span>
          <span>
            {answeredCount} / {visibleQuestions.length} preguntas respondidas
          </span>
        </div>
        {/* Progress bar */}
        <div className="mt-2 h-1.5 bg-neutral-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full transition-all"
            style={{
              width: visibleQuestions.length > 0
                ? `${(answeredCount / visibleQuestions.length) * 100}%`
                : '0%',
            }}
          />
        </div>
      </div>

      {/* Questions */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {visibleQuestions.map((question) => (
          <FieldRenderer
            key={question.id}
            question={question}
            values={form.values}
            errors={form.errors}
            onChange={form.setValue}
          />
        ))}

        {/* Submit */}
        <div className="flex justify-end pt-4 border-t">
          <button
            type="submit"
            disabled={submitMutation.isPending}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {submitMutation.isPending ? 'Guardando...' : 'Guardar bloque'}
          </button>
        </div>

        {/* Error feedback */}
        {submitMutation.isError && (
          <p className="text-sm text-red-600 text-center">
            Error al guardar. Intentá de nuevo.
          </p>
        )}
      </form>
    </div>
  )
}
