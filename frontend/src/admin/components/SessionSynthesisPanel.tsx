/**
 * SessionSynthesisPanel — Displays Session 1 synthesis result.
 *
 * Renders when intake state >= deep_pending.
 * Polls via useIntakeState (5s interval when pending).
 * Shows soft-timeout warning after 3 minutes if still pending.
 */

import { useState, useEffect } from 'react'
import { useIntakeState } from '../../intake/api/intake'
import { useSession1Synthesize } from '../../intake/hooks/useSession1Synthesize'

const PRE_SYNTHESIS_STATES = new Set(['not_started', 'in_progress', 'blocks_completed'])
const SOFT_TIMEOUT_MS = 3 * 60 * 1000 // 3 minutes

interface Props {
  leadId: string
}

export function SessionSynthesisPanel({ leadId }: Props) {
  const { data } = useIntakeState(leadId)
  const synthesizeMutation = useSession1Synthesize(leadId)
  const [firstPendingAt, setFirstPendingAt] = useState<number | null>(null)
  const [now, setNow] = useState<number>(Date.now())

  const status = data?.session1_synthesis_status
  const state = data?.state

  // Track when polling starts
  useEffect(() => {
    if (status === 'pending') {
      setFirstPendingAt((prev) => prev ?? Date.now())
    } else {
      setFirstPendingAt(null)
    }
  }, [status])

  // Advance timer every second while pending
  useEffect(() => {
    if (status !== 'pending') return
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [status])

  // Don't render for pre-synthesis states
  if (!data || !state || PRE_SYNTHESIS_STATES.has(state)) return null
  if (status === 'not_started') return null

  const isSoftTimeout =
    status === 'pending' && firstPendingAt !== null && now - firstPendingAt > SOFT_TIMEOUT_MS

  if (status === 'pending') {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-3">
        <div className="flex items-center gap-3">
          <div className="animate-spin h-5 w-5 border-2 border-teal-500 border-t-transparent rounded-full" />
          <p className="text-sm font-medium text-gray-700">Generando síntesis…</p>
        </div>
        {isSoftTimeout && (
          <p className="text-xs text-amber-600">
            Tomando más de lo esperado, podés reintentar manualmente.
          </p>
        )}
      </div>
    )
  }

  if (status === 'failed') {
    return (
      <div className="bg-white rounded-lg border border-red-200 p-6 space-y-3">
        <p className="text-sm font-semibold text-red-700">Falló generación de síntesis</p>
        <button
          onClick={() => synthesizeMutation.mutate()}
          disabled={synthesizeMutation.isPending}
          className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
            synthesizeMutation.isPending
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-red-600 text-white hover:bg-red-700'
          }`}
        >
          {synthesizeMutation.isPending ? 'Reintentando…' : 'Reintentar síntesis'}
        </button>
        {synthesizeMutation.isError && (
          <p className="text-xs text-red-500">
            Error al reintentar. Intentá de nuevo.
          </p>
        )}
      </div>
    )
  }

  if (status === 'ready' && data.session1_synthesis) {
    const s = data.session1_synthesis
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-5">
        <h3 className="text-sm font-semibold text-gray-700">Síntesis — Sesión 1</h3>

        <div>
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Resumen ejecutivo</p>
          <p className="text-sm text-gray-800">{s.summary}</p>
        </div>

        {(s.key_insights?.length ?? 0) > 0 && (
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Insights clave</p>
            <ul className="list-disc list-inside space-y-1">
              {s.key_insights!.map((insight: string, i: number) => (
                <li key={i} className="text-sm text-gray-700">{insight}</li>
              ))}
            </ul>
          </div>
        )}

        {(s.recommendations?.length ?? 0) > 0 && (
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Recomendaciones</p>
            <ul className="list-disc list-inside space-y-1">
              {s.recommendations!.map((rec: string, i: number) => (
                <li key={i} className="text-sm text-gray-700">{rec}</li>
              ))}
            </ul>
          </div>
        )}

        {s.hypothesis && (
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Hipótesis</p>
            <p className="text-sm text-gray-800">{s.hypothesis}</p>
          </div>
        )}

        <p className="text-xs text-gray-400">
          Generado {new Date(s.generated_at).toLocaleString('es-ES')} · {s.model}
        </p>
      </div>
    )
  }

  return null
}
