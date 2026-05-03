/**
 * EnrichmentPanel — sidebar panel with 4 re-run action buttons and live job status.
 *
 * Each button triggers a POST → receives 202 + job_id → polls GET /jobs every 2s.
 * A button is disabled while a job of that type is pending or running.
 * Shows a toast-like status line per job type.
 *
 * Pre-enrichment gate (CAP-P-IN-001):
 *   When the assessment form_data is sparse (< 60% filled OR missing critical fields),
 *   clicking LLM / recommendations / PDF / preview-PDF opens SparseConfirmDialog first.
 *   Scoring is exempt — it is deterministic and meaningful even with sparse data.
 *   If NOT sparse, the action fires immediately (no dialog).
 */

import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { generatePdf, previewPdf, runLlmEnrichment, runRecommendations, runScoring } from '../../api/assessments'
import type { AssessmentResponse } from '../../api/assessments'
import { useJobPolling } from '../../hooks/useJobPolling'
import { useAssessmentCompleteness } from '../../hooks/useAssessmentCompleteness'
import { SparseConfirmDialog } from './SparseConfirmDialog'

interface Props {
  assessmentId: string
  assessment: AssessmentResponse
  onPreviewReady: () => void
}

interface PendingAction {
  type: string
  fn: () => Promise<unknown>
  afterDone?: () => void
  actionLabel: string
}

export function EnrichmentPanel({ assessmentId, assessment, onPreviewReady }: Props) {
  const { jobs, isPolling } = useJobPolling(assessmentId)
  const queryClient = useQueryClient()
  const completeness = useAssessmentCompleteness(assessment)

  // Gate dialog state
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null)

  const getJobByType = (type: string) =>
    jobs.filter((j) => j.type === type)[0]

  const isRunning = (type: string) => {
    const j = getJobByType(type)
    return j?.status === 'pending' || j?.status === 'running'
  }

  const jobStatus = (type: string) => {
    const j = getJobByType(type)
    if (!j) return null
    if (j.status === 'running') return { text: 'Ejecutando...', color: 'text-yellow-600' }
    if (j.status === 'pending') return { text: 'En cola...', color: 'text-gray-500' }
    if (j.status === 'done') return { text: 'Completado', color: 'text-green-600' }
    if (j.status === 'failed') return { text: `Error: ${j.error ?? 'desconocido'}`, color: 'text-red-600' }
    return null
  }

  const fireAction = async (
    type: string,
    action: () => Promise<unknown>,
    afterDone?: () => void,
  ) => {
    try {
      await action()
      queryClient.invalidateQueries({ queryKey: ['jobs', assessmentId] })
      if (afterDone) afterDone()
    } catch {
      alert(`Error al iniciar: ${type}`)
    }
  }

  /**
   * Handles a button click for a gated action.
   * If sparse → open SparseConfirmDialog. Otherwise fire immediately.
   */
  const handleGatedAction = (
    type: string,
    action: () => Promise<unknown>,
    actionLabel: string,
    afterDone?: () => void,
  ) => {
    if (completeness.isSparse) {
      setPendingAction({ type, fn: action, afterDone, actionLabel })
    } else {
      void fireAction(type, action, afterDone)
    }
  }

  const handleDialogConfirm = () => {
    if (!pendingAction) return
    const { type, fn, afterDone } = pendingAction
    setPendingAction(null)
    void fireAction(type, fn, afterDone)
  }

  const handleDialogCancel = () => {
    setPendingAction(null)
  }

  const actions = [
    {
      label: 'Re-correr LLM',
      type: 'enrich_llm',
      action: () => runLlmEnrichment(assessmentId),
      description: 'Regenera el análisis LLM preservando campos editados manualmente',
      gated: true,
      actionLabel: 're-correr LLM',
    },
    {
      label: 'Re-correr recomendaciones',
      type: 'enrich_recommendations',
      action: () => runRecommendations(assessmentId),
      description: 'Regenera tool recommendations, preguntas de seguimiento y política de IA',
      gated: true,
      actionLabel: 're-correr recomendaciones',
    },
    {
      label: 'Re-correr scoring',
      type: 'score',
      action: () => runScoring(assessmentId),
      description: 'Recalcula madurez, riesgo y sub-scores',
      gated: false,
      actionLabel: 're-correr scoring',
    },
    {
      label: 'Generar PDF',
      type: 'generate_pdf',
      action: () => generatePdf(assessmentId),
      description: 'Genera el PDF de producción y actualiza pdf_path',
      gated: true,
      actionLabel: 'generar PDF',
    },
    {
      label: 'Previsualizar PDF',
      type: 'preview_pdf',
      action: () => previewPdf(assessmentId),
      description: 'Genera un PDF borrador watermarked para preview',
      afterDone: onPreviewReady,
      gated: true,
      actionLabel: 'previsualizar PDF',
    },
  ]

  return (
    <>
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
          Acciones de enriquecimiento
          {isPolling && (
            <span className="w-3 h-3 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
          )}
        </h3>

        <div className="space-y-3">
          {actions.map(({ label, type, action, description, afterDone, gated, actionLabel }) => {
            const running = isRunning(type)
            const status = jobStatus(type)

            return (
              <div key={type}>
                <button
                  disabled={running}
                  onClick={() => {
                    if (gated) {
                      handleGatedAction(type, action, actionLabel, afterDone)
                    } else {
                      void fireAction(type, action, afterDone)
                    }
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg border border-gray-200 text-sm font-medium text-gray-700 hover:bg-teal-50 hover:border-teal-300 hover:text-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {running && (
                    <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin mr-2 align-middle" />
                  )}
                  {label}
                </button>
                {status && (
                  <p className={`text-xs mt-0.5 px-1 ${status.color}`}>{status.text}</p>
                )}
                <p className="text-xs text-gray-400 px-1 mt-0.5">{description}</p>
              </div>
            )
          })}
        </div>
      </div>

      {/* Sparse gate dialog — rendered at root level to avoid stacking context issues */}
      <SparseConfirmDialog
        open={pendingAction !== null}
        completeness={completeness}
        actionLabel={pendingAction?.actionLabel ?? ''}
        onConfirm={handleDialogConfirm}
        onCancel={handleDialogCancel}
      />
    </>
  )
}
