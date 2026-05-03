/**
 * EmailRetryBanner — shown at the top of the editor when email_status='failed'.
 *
 * Displays the error message and a "Reenviar" button that triggers resendEmail.
 * Hides itself once the retry job has been queued successfully.
 */

import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { resendEmail } from '../../api/assessments'
import type { AssessmentResponse } from '../../api/assessments'

interface Props {
  assessment: AssessmentResponse
}

export function EmailRetryBanner({ assessment }: Props) {
  const [loading, setLoading] = useState(false)
  const [queued, setQueued] = useState(false)
  const queryClient = useQueryClient()

  if (assessment.email_status !== 'failed' || queued) return null

  const handleRetry = async () => {
    setLoading(true)
    try {
      await resendEmail(assessment.id)
      setQueued(true)
      queryClient.invalidateQueries({ queryKey: ['jobs', assessment.id] })
    } catch {
      alert('Error al reenviar el email. Verificá la configuración SMTP.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mb-4 flex items-start gap-3 p-4 rounded-lg bg-red-50 border border-red-200">
      <div className="flex-1">
        <p className="text-sm font-semibold text-red-800">El email no se pudo enviar</p>
        {assessment.email_error && (
          <p className="text-xs text-red-600 mt-0.5">{assessment.email_error}</p>
        )}
      </div>
      <button
        onClick={handleRetry}
        disabled={loading}
        className="flex-shrink-0 px-3 py-1.5 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-700 disabled:opacity-40 transition-colors flex items-center gap-1.5"
      >
        {loading && (
          <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
        )}
        Reenviar
      </button>
    </div>
  )
}
