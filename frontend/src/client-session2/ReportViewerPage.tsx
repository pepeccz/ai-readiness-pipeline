/**
 * ReportViewerPage — public client page for session 2 report viewing.
 *
 * Accessed via signed URL: /client/report/{token}
 * No login required.
 *
 * States:
 *  - Loading: fetching status
 *  - Pending: report not yet generated → polling every 30s
 *  - Ready: shows report content + download button
 *  - Error: invalid/expired token
 */

import { useEffect, useRef, useState } from 'react'
import { getReportStatus } from './api/client'
import type { ReportStatusResponse } from './api/client'

interface Props {
  token: string
}

const POLL_INTERVAL_MS = 30_000

export function ReportViewerPage({ token }: Props) {
  const [status, setStatus] = useState<'loading' | 'pending' | 'ready' | 'error'>('loading')
  const [report, setReport] = useState<ReportStatusResponse | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  async function fetchStatus() {
    try {
      const data = await getReportStatus(token)
      setReport(data)
      if (data.status === 'ready') {
        setStatus('ready')
        if (pollRef.current) clearInterval(pollRef.current)
      } else {
        setStatus('pending')
      }
    } catch (err) {
      setStatus('error')
      setErrorMsg(
        err instanceof Error ? err.message : 'Token inválido o expirado.'
      )
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }

  useEffect(() => {
    fetchStatus()
    pollRef.current = setInterval(fetchStatus, POLL_INTERVAL_MS)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-500 text-sm">Cargando reporte...</p>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow p-6 text-center">
          <h1 className="text-xl font-semibold text-red-600 mb-2">Enlace inválido</h1>
          <p className="text-sm text-gray-600">
            {errorMsg ?? 'Este enlace no es válido o ha expirado. Por favor, contactá a tu consultor.'}
          </p>
        </div>
      </div>
    )
  }

  if (status === 'pending') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow p-8 text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <h1 className="text-xl font-semibold text-gray-800 mb-3">
            Tu reporte está siendo preparado
          </h1>
          <p className="text-sm text-gray-600">
            Tu consultor está finalizando el análisis. Esta página se actualizará automáticamente cuando esté listo.
          </p>
          <p className="text-xs text-gray-400 mt-4">Verificando cada 30 segundos...</p>
        </div>
      </div>
    )
  }

  // Ready state
  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Reporte de Diagnóstico IA</h1>
          <a
            href={`/api/client/report/${token}/download`}
            download
            className="rounded-md bg-teal-600 px-4 py-2 text-sm text-white font-medium hover:bg-teal-700 transition-colors"
          >
            Descargar PDF
          </a>
        </div>

        <div className="bg-white rounded-lg shadow p-8">
          {report?.content ? (
            <div
              className="prose max-w-none text-sm text-gray-700"
              dangerouslySetInnerHTML={{ __html: report.content }}
            />
          ) : (
            <p className="text-gray-500 text-sm">El contenido del reporte no está disponible.</p>
          )}
        </div>
      </div>
    </div>
  )
}
