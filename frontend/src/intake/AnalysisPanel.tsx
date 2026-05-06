/**
 * AnalysisPanel — displays LLM block analysis output with suggestion action buttons.
 *
 * Replaces AnalysisPlaceholder from B5.
 *
 * States:
 *   - pending_analysis → skeleton loader
 *   - ready → suggestions with Hecha/Descartar/Irrelevante buttons
 *   - failed → error message
 */

import { useEffect, useRef } from 'react'
import { useBlockAnalysisPolling } from '../shared/hooks/useBlockAnalysisPolling'
import { useSuggestionAction, type Suggestion } from './api/intake'

interface AnalysisPanelProps {
  leadId: string
  blockId: string
}

interface SuggestionCardProps {
  suggestion: Suggestion
  leadId: string
  onAction: (suggestionId: string, action: string) => void
  isLoading: boolean
}

function SuggestionCard({ suggestion, onAction, isLoading }: SuggestionCardProps) {
  const priorityColor = {
    high: 'border-red-300 bg-red-50',
    med: 'border-amber-300 bg-amber-50',
    low: 'border-gray-200 bg-gray-50',
  }[suggestion.priority] ?? 'border-gray-200 bg-gray-50'

  const isDone = suggestion.consultant_action !== 'pending'

  return (
    <div
      data-testid="suggestion-card"
      className={`p-3 rounded-lg border ${priorityColor} ${isDone ? 'opacity-60' : ''}`}
    >
      <p className="text-sm font-medium text-gray-800">{suggestion.text}</p>
      {suggestion.rationale && (
        <p className="mt-1 text-xs text-gray-500">{suggestion.rationale}</p>
      )}
      <div className="mt-2 flex gap-2">
        <button
          data-testid="btn-done"
          onClick={() => onAction(suggestion.id, 'done')}
          disabled={isLoading || isDone}
          className="text-xs px-2 py-1 rounded bg-green-100 text-green-700 hover:bg-green-200 disabled:opacity-50"
        >
          Hecha
        </button>
        <button
          data-testid="btn-discard"
          onClick={() => onAction(suggestion.id, 'discarded')}
          disabled={isLoading || isDone}
          className="text-xs px-2 py-1 rounded bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50"
        >
          Descartar
        </button>
        <button
          data-testid="btn-irrelevant"
          onClick={() => onAction(suggestion.id, 'irrelevant')}
          disabled={isLoading || isDone}
          className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600 hover:bg-gray-200 disabled:opacity-50"
        >
          Irrelevante
        </button>
      </div>
    </div>
  )
}

function AnalysisSkeleton() {
  return (
    <div data-testid="analysis-skeleton" className="mt-4 space-y-3 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-1/3" />
      <div className="h-3 bg-gray-200 rounded w-full" />
      <div className="h-3 bg-gray-200 rounded w-5/6" />
      <div className="h-8 bg-gray-100 rounded" />
      <div className="h-8 bg-gray-100 rounded" />
    </div>
  )
}

export function AnalysisPanel({ leadId, blockId }: AnalysisPanelProps) {
  const { data: analysis, isLoading, isError } = useBlockAnalysisPolling(leadId, blockId)
  const actionMutation = useSuggestionAction(leadId, blockId)
  const panelRef = useRef<HTMLDivElement>(null)

  // A-3: scroll panel into view 100ms after analysis arrives (covers React commit + layout pass)
  useEffect(() => {
    if (analysis?.status === 'ready') {
      const id = setTimeout(() => {
        panelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 100)
      return () => clearTimeout(id)
    }
  }, [analysis?.status])

  if (isLoading || !analysis) return null

  if (analysis.status === 'pending_analysis') {
    return <AnalysisSkeleton />
  }

  if (analysis.status === 'skipped') {
    return (
      <div data-testid="analysis-skipped" className="mt-4 p-3 bg-neutral-50 border border-neutral-200 rounded text-sm text-neutral-500">
        Análisis IA omitido para este bloque.
      </div>
    )
  }

  if (analysis.status === 'failed' || isError) {
    return (
      <div data-testid="analysis-error" className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
        El análisis IA no pudo completarse. Podés re-dispararlo desde el panel de administración.
      </div>
    )
  }

  if (analysis.status !== 'ready') return null

  const { llm_output, suggestions } = analysis

  const handleAction = (suggestionId: string, action: string) => {
    actionMutation.mutate({ suggestionId, action })
  }

  return (
    <div ref={panelRef} data-testid="analysis-panel" className="mt-4 space-y-4">
      {llm_output?.synthesis && (
        <div className="p-3 bg-teal-50 border border-teal-200 rounded">
          <p className="text-xs font-semibold text-teal-700 mb-1">Síntesis</p>
          <p className="text-sm text-teal-900">{llm_output.synthesis}</p>
        </div>
      )}

      {suggestions.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-gray-600">
            Preguntas de seguimiento sugeridas
          </p>
          {suggestions.map((sug) => (
            <SuggestionCard
              key={sug.id}
              suggestion={sug}
              leadId={leadId}
              onAction={handleAction}
              isLoading={actionMutation.isPending}
            />
          ))}
        </div>
      )}

      {suggestions.length === 0 && (
        <p className="text-xs text-gray-400 italic">
          No hay sugerencias de seguimiento para este bloque.
        </p>
      )}
    </div>
  )
}
