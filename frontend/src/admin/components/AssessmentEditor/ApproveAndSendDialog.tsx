/**
 * ApproveAndSendDialog — modal to confirm and trigger approve-and-send.
 *
 * Pre-flight checks (button is disabled unless all pass):
 *   1. status === 'pending_review'
 *   2. llm_enriched_data !== null
 *   3. respondent_email is truthy
 *
 * Sparse gate (CAP-P-IN-001):
 *   When isSparse === true, clicking "Confirmar" shows an inline warning banner
 *   with a second "Sí, continuar" button before the POST fires.  This avoids
 *   chaining two full-screen modals.  The warning is additive — the pre-flight
 *   checks above still block when not met.
 *
 * On final confirm: POST /approve-and-send → poll jobs → navigate to list.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { approveAndSend } from '../../api/assessments'
import type { AssessmentResponse } from '../../api/assessments'
import { useAssessmentCompleteness } from '../../hooks/useAssessmentCompleteness'

interface Props {
  assessment: AssessmentResponse
}

export function ApproveAndSendDialog({ assessment }: Props) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  /** When true, shows the sparse warning banner. User must confirm a second time. */
  const [sparseAcknowledged, setSparseAcknowledged] = useState(false)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const completeness = useAssessmentCompleteness(assessment)

  const canApprove =
    assessment.status === 'pending_review' &&
    assessment.llm_enriched_data != null &&
    Boolean(assessment.respondent_email)

  const disabledReason = !canApprove
    ? assessment.status !== 'pending_review'
      ? `Estado actual: ${assessment.status}. Solo assessments en pending_review pueden aprobarse.`
      : assessment.llm_enriched_data == null
      ? 'El enriquecimiento LLM no ha corrido aún. Ejecutá "Re-correr LLM" primero.'
      : 'El assessment no tiene email de contacto. Completá el campo respondent_email.'
    : null

  const handleOpen = () => {
    if (!canApprove) return
    setSparseAcknowledged(false)
    setError(null)
    setOpen(true)
  }

  const handleCancel = () => {
    setOpen(false)
    setSparseAcknowledged(false)
    setError(null)
  }

  /**
   * First confirm click.
   * - If sparse and not yet acknowledged: show sparse warning banner (don't POST yet).
   * - If sparse and already acknowledged, OR not sparse: fire the POST.
   */
  const handleFirstConfirm = () => {
    if (completeness.isSparse && !sparseAcknowledged) {
      setSparseAcknowledged(true)
      return
    }
    void doApprove()
  }

  const doApprove = async () => {
    setLoading(true)
    setError(null)
    try {
      await approveAndSend(assessment.id)
      setOpen(false)
      queryClient.invalidateQueries({ queryKey: ['jobs', assessment.id] })
      setTimeout(() => navigate('/admin/assessments'), 500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al aprobar y enviar.')
    } finally {
      setLoading(false)
    }
  }

  const percentDisplay = Math.round(completeness.percentage * 100)

  return (
    <>
      {/* Trigger button */}
      <div className="relative group inline-block">
        <button
          onClick={handleOpen}
          disabled={!canApprove}
          className="px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Aprobar y enviar
        </button>
        {disabledReason && (
          <div className="absolute bottom-full left-0 mb-1 w-72 bg-gray-800 text-white text-xs rounded p-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
            {disabledReason}
          </div>
        )}
      </div>

      {/* Modal */}
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Aprobar y enviar reporte</h3>
            <p className="text-sm text-gray-600 mb-4">
              Vas a generar el PDF de producción y enviarlo a{' '}
              <strong>{assessment.respondent_email}</strong>. Esta acción cambiará el estado a{' '}
              <strong>aprobado</strong>.
            </p>

            {/* Sparse warning banner — shown after first confirm when isSparse */}
            {sparseAcknowledged && (
              <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3">
                <p className="text-xs font-semibold text-amber-800 mb-1 flex items-center gap-1">
                  <span>⚠</span> Datos incompletos
                </p>
                <p className="text-xs text-amber-700 mb-2">
                  El assessment tiene{' '}
                  <strong>
                    {completeness.filledKeys} de {completeness.totalKeys} campos ({percentDisplay}%)
                  </strong>
                  . El reporte va a salir limitado.
                </p>
                {completeness.missingCritical.length > 0 && (
                  <p className="text-xs text-amber-700">
                    Faltan datos críticos: {completeness.missingCritical.join(', ')}.
                  </p>
                )}
              </div>
            )}

            {error && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="flex justify-end gap-3">
              <button
                onClick={handleCancel}
                disabled={loading}
                className="px-4 py-2 rounded-lg border border-gray-300 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-40 transition-colors"
              >
                Cancelar
              </button>
              <button
                // eslint-disable-next-line jsx-a11y/no-autofocus
                autoFocus={sparseAcknowledged}
                onClick={handleFirstConfirm}
                disabled={loading}
                className={`px-4 py-2 rounded-lg text-white text-sm font-medium disabled:opacity-40 transition-colors flex items-center gap-2 ${
                  sparseAcknowledged
                    ? 'bg-amber-500 hover:bg-amber-600'
                    : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                {loading && (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                )}
                {loading
                  ? 'Procesando...'
                  : sparseAcknowledged
                  ? 'Sí, continuar de todas formas'
                  : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
