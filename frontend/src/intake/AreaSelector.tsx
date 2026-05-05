/**
 * AreaSelector — first step of the intake flow.
 *
 * Renders the area_selector questions from the CORE schema index.
 * Handles primary_area, secondary_area (optional), and areas_involved (cross-area).
 */

import { useState } from 'react'
import type { AreaSelectorSchema } from './types/schema'
import { useAreaSelection } from './api/intake'

interface AreaSelectorProps {
  leadId: string
  schema: AreaSelectorSchema
  onSuccess?: () => void
}

export function AreaSelector({ leadId, schema, onSuccess }: AreaSelectorProps) {
  const [primaryArea, setPrimaryArea] = useState('')
  const [secondaryArea, setSecondaryArea] = useState('')
  const [areasInvolved, setAreasInvolved] = useState<string[]>([])
  const [error, setError] = useState('')

  const mutation = useAreaSelection(leadId)
  const isCrossArea = primaryArea === 'cross_area_communication'

  const primaryQuestion = schema.questions.find((q) => q.id === 'primary_area')
  const secondaryQuestion = schema.questions.find((q) => q.id === 'secondary_area')
  const areasInvolvedQuestion = schema.questions.find((q) => q.id === 'areas_involved')

  function toggleAreaInvolved(area: string) {
    setAreasInvolved((prev) =>
      prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area],
    )
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (!primaryArea) {
      setError('Seleccioná un área principal')
      return
    }

    if (isCrossArea && areasInvolved.length < 2) {
      setError('Seleccioná al menos 2 áreas involucradas')
      return
    }

    try {
      await mutation.mutateAsync({
        primary_area: primaryArea,
        secondary_area: !isCrossArea && secondaryArea ? secondaryArea : undefined,
        areas_involved: isCrossArea ? areasInvolved : [],
      })
      onSuccess?.()
    } catch {
      setError('Error al guardar el área. Intentá de nuevo.')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-neutral-900">
          {primaryQuestion?.label ?? '¿Cuál es el área principal?'}
        </h2>
        {primaryQuestion?.helper_text && (
          <p className="text-sm text-neutral-500 mt-1">{primaryQuestion.helper_text}</p>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Primary area */}
        {primaryQuestion && 'options' in primaryQuestion && (
          <div className="grid grid-cols-2 gap-2">
            {primaryQuestion.options.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => {
                  setPrimaryArea(opt.value)
                  setSecondaryArea('')
                  setAreasInvolved([])
                }}
                className={`p-3 rounded-lg border text-sm text-left transition-colors ${
                  primaryArea === opt.value
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-neutral-200 hover:border-neutral-300'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}

        {/* Secondary area (non-cross only) */}
        {!isCrossArea && primaryArea && secondaryQuestion && 'options' in secondaryQuestion && (
          <div>
            <h3 className="text-sm font-medium text-neutral-700 mb-2">
              {secondaryQuestion.label}
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {secondaryQuestion.options
                .filter((o) => o.value !== primaryArea)
                .map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() =>
                      setSecondaryArea((prev) => (prev === opt.value ? '' : opt.value))
                    }
                    className={`p-3 rounded-lg border text-sm text-left transition-colors ${
                      secondaryArea === opt.value
                        ? 'border-green-500 bg-green-50 text-green-700'
                        : 'border-neutral-200 hover:border-neutral-300'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
            </div>
          </div>
        )}

        {/* Areas involved (cross-area only) */}
        {isCrossArea && areasInvolvedQuestion && 'options' in areasInvolvedQuestion && (
          <div>
            <h3 className="text-sm font-medium text-neutral-700 mb-2">
              {areasInvolvedQuestion.label}
            </h3>
            <p className="text-xs text-neutral-500 mb-2">{areasInvolvedQuestion.helper_text}</p>
            <div className="grid grid-cols-2 gap-2">
              {areasInvolvedQuestion.options.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => toggleAreaInvolved(opt.value)}
                  className={`p-3 rounded-lg border text-sm text-left transition-colors ${
                    areasInvolved.includes(opt.value)
                      ? 'border-purple-500 bg-purple-50 text-purple-700'
                      : 'border-neutral-200 hover:border-neutral-300'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!primaryArea || mutation.isPending}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {mutation.isPending ? 'Guardando...' : 'Continuar'}
          </button>
        </div>
      </form>
    </div>
  )
}
