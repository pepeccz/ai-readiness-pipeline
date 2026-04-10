import { useState, useRef } from 'react'
import type { AssessmentFormPayload, StatusResponse } from '../types/api'

export type SubmissionState = 'idle' | 'submitting' | 'polling' | 'ready' | 'downloading' | 'error'

export function useSubmission() {
  const [submissionState, setSubmissionState] = useState<SubmissionState>('idle')
  const [errorMessage, setErrorMessage] = useState<string>('')
  const [taskId, setTaskId] = useState<string>('')
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  function stopPolling() {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }

  async function submit(payload: AssessmentFormPayload) {
    setSubmissionState('submitting')
    setErrorMessage('')

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
        throw new Error(`Error al enviar: ${response.statusText}`)
      }

      const data = await response.json()
      const id: string = data.task_id

      if (!id) {
        throw new Error('No se recibió un ID de tarea válido')
      }

      setTaskId(id)
      setSubmissionState('polling')
      startPolling(id)
    } catch (err) {
      setSubmissionState('error')
      setErrorMessage(err instanceof Error ? err.message : 'Error desconocido al enviar el formulario')
    }
  }

  function startPolling(id: string) {
    pollingRef.current = setInterval(async () => {
      try {
        const response = await fetch(`/api/status/${id}`)

        if (!response.ok) {
          throw new Error(`Error al consultar estado: ${response.statusText}`)
        }

        const status: StatusResponse = await response.json()

        if (status.status === 'completed') {
          stopPolling()
          setSubmissionState('ready')
        } else if (status.status === 'failed') {
          stopPolling()
          setSubmissionState('error')
          setErrorMessage(status.error ?? 'El informe no pudo generarse. Por favor, inténtalo de nuevo.')
        }
        // For 'pending' and 'processing' we keep polling
      } catch (err) {
        stopPolling()
        setSubmissionState('error')
        setErrorMessage(err instanceof Error ? err.message : 'Error al verificar el estado del informe')
      }
    }, 3000)
  }

  async function downloadReport() {
    if (!taskId) return

    setSubmissionState('downloading')

    try {
      const response = await fetch(`/api/download/${taskId}`)

      if (!response.ok) {
        throw new Error(`Error al descargar: ${response.statusText}`)
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `ai-readiness-report-${taskId}.docx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      setSubmissionState('ready')
    } catch (err) {
      setSubmissionState('error')
      setErrorMessage(err instanceof Error ? err.message : 'Error al descargar el informe')
    }
  }

  function reset() {
    stopPolling()
    setSubmissionState('idle')
    setErrorMessage('')
    setTaskId('')
  }

  return {
    submissionState,
    errorMessage,
    taskId,
    submit,
    downloadReport,
    reset,
  }
}
