import { useState } from 'react'
import type { AssessmentFormPayload, SubmissionResponse } from '../types/api'

/**
 * Submission hook — Phase C fire-and-forget flow.
 *
 * POST /api/assessment returns {assessment_id, status, message} immediately.
 * The enrichment chain and PDF generation run in the background on the server.
 * The consultant reviews the submission; the client receives the PDF by email
 * when the report is approved and the signed download URL is delivered.
 *
 * No polling. No client-side download. The success screen shows the message
 * from the server response.
 */

export type SubmissionState = 'idle' | 'submitting' | 'success' | 'error'

export function useSubmission() {
  const [submissionState, setSubmissionState] = useState<SubmissionState>('idle')
  const [errorMessage, setErrorMessage] = useState<string>('')
  const [successMessage, setSuccessMessage] = useState<string>('')

  async function submit(payload: AssessmentFormPayload) {
    setSubmissionState('submitting')
    setErrorMessage('')
    setSuccessMessage('')

    try {
      const response = await fetch('/api/assessment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${payload._token || ''}`,
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}))
        throw new Error(
          errorBody.detail
            ? String(errorBody.detail)
            : `Error al enviar: ${response.statusText}`
        )
      }

      const data: SubmissionResponse = await response.json()
      setSuccessMessage(data.message || 'Recibido. Te enviaremos el reporte por email.')
      setSubmissionState('success')
    } catch (err) {
      setSubmissionState('error')
      setErrorMessage(
        err instanceof Error ? err.message : 'Error desconocido al enviar el formulario'
      )
    }
  }

  function reset() {
    setSubmissionState('idle')
    setErrorMessage('')
    setSuccessMessage('')
  }

  return {
    submissionState,
    errorMessage,
    successMessage,
    submit,
    reset,
  }
}
