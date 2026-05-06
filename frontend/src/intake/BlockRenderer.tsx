/**
 * BlockRenderer — renders a full CORE block from schema.
 *
 * Orchestrates:
 * - FieldRenderer per visible question (show_if evaluated by useSchemaForm)
 * - Submit button with loading state
 * - Draft autosave via useDraftAutosave (REQ-5)
 * - Restoration from backend draft/submitted answer via useBlockPayload (REQ-6)
 * - Progress indicator (X of Y questions answered)
 * - Read-only mode when block is already submitted, with "Editar respuestas" escape hatch
 *
 * REQ-5 / ADR-3: The inner form is keyed by `${schema.id}:${payloadFingerprint}`.
 * Changing block OR receiving an updated payload forces a full remount, which
 * discards stale useState and re-seeds from `initialPayload`. This is the
 * canonical React idiom for "this is a different form instance".
 */

import { useEffect, useMemo, useState } from 'react'
import type { BlockSchema } from './types/schema'
import { FieldRenderer } from './FieldRenderer'
import { useSchemaForm, getAnsweredQuestions } from './hooks/useSchemaForm'
import { useBlockSubmit } from './api/intake'
import { useDraftAutosave } from './hooks/useDraftAutosave'

interface BlockRendererProps {
  leadId: string
  schema: BlockSchema
  initialPayload?: Record<string, unknown>
  /** 'submitted' | 'draft' | 'none' — from useBlockPayload */
  source?: 'submitted' | 'draft' | 'none'
  onSubmitSuccess?: (blockAnalysisId: string) => void
}

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
  source,
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
      source={source}
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
  source,
  onSubmitSuccess,
}: BlockRendererProps) {
  const form = useSchemaForm(schema)
  const submitMutation = useBlockSubmit(leadId, schema.id)

  // REQ-4: local submit error state for banner
  const [localError, setLocalError] = useState<string | null>(null)

  // REQ-6: read-only mode when block is submitted; user can unlock via "Editar respuestas"
  const [isReadOnly, setIsReadOnly] = useState(source === 'submitted')

  // REQ-5: autosave — enabled only when form is dirty and not in read-only mode
  const autosave = useDraftAutosave(
    leadId,
    schema.id,
    form.values,
    form.isDirty,
    !isReadOnly,
  )

  // Restore initial payload on mount
  useEffect(() => {
    if (initialPayload) {
      Object.entries(initialPayload).forEach(([k, v]) => form.setValue(k, v))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [schema.id])

  const visibleQuestions = form.getVisibleQuestions()
  // REQ-1: use shared helper so composite questions count correctly
  const answeredCount = getAnsweredQuestions({ ...schema, questions: visibleQuestions }, form.values).length

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const valid = form.validate()
    if (!valid) return

    const payload = form.buildPayload()
    try {
      setLocalError(null)
      const result = await submitMutation.mutateAsync(payload)
      // Clear localStorage draft on success
      localStorage.removeItem(`draft_${leadId}_${schema.id}`)
      form.reset()
      onSubmitSuccess?.(result.block_analysis_id)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al guardar. Intentá de nuevo.'
      console.error('[BlockRenderer] submit error:', err)
      setLocalError(message)
    }
  }

  function handleEdit() {
    setIsReadOnly(false)
  }

  // Format savedAt as HH:MM
  const savedAtLabel = autosave.savedAt
    ? autosave.savedAt.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
    : null

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b pb-4">
        <div className="flex items-start justify-between">
          <h2 className="text-lg font-semibold text-neutral-900">{schema.title}</h2>
          {/* REQ-6: unlock button for submitted blocks */}
          {isReadOnly && (
            <button
              type="button"
              onClick={handleEdit}
              className="text-xs text-blue-600 hover:text-blue-700 underline-offset-2 hover:underline ml-4 flex-shrink-0"
            >
              Editar respuestas
            </button>
          )}
        </div>
        <div className="flex items-center gap-4 mt-2 text-xs text-neutral-500">
          <span>~{schema.estimated_minutes} min</span>
          <span>
            {answeredCount} / {visibleQuestions.length} preguntas respondidas
          </span>
          {/* REQ-5: subtle autosave indicator */}
          {savedAtLabel && autosave.status === 'saved' && (
            <span className="text-neutral-400">Guardado {savedAtLabel}</span>
          )}
          {autosave.status === 'saving' && (
            <span className="text-neutral-400">Guardando...</span>
          )}
          {autosave.status === 'error' && (
            <span className="text-amber-500">Sin conexión — borrador local</span>
          )}
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
        {/* Submitted banner */}
        {isReadOnly && (
          <p className="mt-2 text-xs text-green-700 bg-green-50 rounded px-2 py-1">
            Este bloque ya fue enviado. Las respuestas son de solo lectura.
          </p>
        )}
      </div>

      {/* REQ-4: submit error banner — top of form, clears on next successful submit */}
      {localError && (
        <div
          role="alert"
          className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700"
        >
          <span className="font-medium">Error al enviar:</span> {localError}
        </div>
      )}

      {/* Questions */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {visibleQuestions.map((question) => (
          <FieldRenderer
            key={question.id}
            question={question}
            values={form.values}
            errors={form.errors}
            onChange={isReadOnly ? () => {} : form.setValue}
          />
        ))}

        {/* Submit — hidden when read-only */}
        {!isReadOnly && (
          <div className="flex justify-end pt-4 border-t">
            <button
              type="submit"
              disabled={submitMutation.isPending}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {submitMutation.isPending ? 'Guardando...' : 'Guardar bloque'}
            </button>
          </div>
        )}

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
