/**
 * FollowUpsTable — renders follow-ups list with dismiss/restore UX.
 *
 * REQ-11: Optimistic dismiss with rollback on API error.
 * Each follow-up has its own local dismissed state for independent toggling.
 */

import { useState } from 'react'
import { dismissFinding, restoreFinding } from './api/session2'
import type { Session2PrepData } from './api/session2'

type FollowUp = Session2PrepData['follow_ups'][number]

const PRIORITY_COLORS = {
  high: 'bg-red-100 text-red-700',
  med: 'bg-orange-100 text-orange-700',
  low: 'bg-gray-100 text-gray-600',
}

const PRIORITY_LABELS = {
  high: 'Alta',
  med: 'Media',
  low: 'Baja',
}

interface Props {
  leadId: string
  followUps: FollowUp[]
}

export function FollowUpsTable({ leadId, followUps }: Props) {
  // Local optimistic state: map from finding_id → dismissed
  const [dismissedMap, setDismissedMap] = useState<Record<string, boolean>>(() => {
    const map: Record<string, boolean> = {}
    for (const f of followUps) {
      map[f.finding_id] = f.dismissed
    }
    return map
  })
  const [pendingMap, setPendingMap] = useState<Record<string, boolean>>({})

  async function handleDismiss(followUp: FollowUp) {
    const prev = dismissedMap[followUp.finding_id]
    setDismissedMap((m) => ({ ...m, [followUp.finding_id]: true }))
    setPendingMap((m) => ({ ...m, [followUp.finding_id]: true }))
    try {
      await dismissFinding(leadId, followUp.block_id, followUp.finding_id)
    } catch {
      setDismissedMap((m) => ({ ...m, [followUp.finding_id]: prev }))
    } finally {
      setPendingMap((m) => ({ ...m, [followUp.finding_id]: false }))
    }
  }

  async function handleRestore(followUp: FollowUp) {
    const prev = dismissedMap[followUp.finding_id]
    setDismissedMap((m) => ({ ...m, [followUp.finding_id]: false }))
    setPendingMap((m) => ({ ...m, [followUp.finding_id]: true }))
    try {
      await restoreFinding(leadId, followUp.block_id, followUp.finding_id)
    } catch {
      setDismissedMap((m) => ({ ...m, [followUp.finding_id]: prev }))
    } finally {
      setPendingMap((m) => ({ ...m, [followUp.finding_id]: false }))
    }
  }

  if (followUps.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <p className="text-sm text-gray-400 italic">Sin preguntas de seguimiento.</p>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100">
        <h4 className="text-sm font-semibold text-gray-700">
          Preguntas de seguimiento ({followUps.length})
        </h4>
      </div>
      <ul className="divide-y divide-gray-50">
        {followUps.map((followUp) => {
          const isDismissed = dismissedMap[followUp.finding_id] ?? followUp.dismissed
          const isPending = pendingMap[followUp.finding_id] ?? false
          return (
            <li
              key={followUp.finding_id}
              className={`px-4 py-3 flex items-start gap-3 ${isDismissed ? 'opacity-50' : ''}`}
            >
              <div className="flex-1 min-w-0">
                <p className={`text-sm text-gray-800 ${isDismissed ? 'line-through' : ''}`}>
                  {followUp.text}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-400">{followUp.block_id}</span>
                  <span
                    className={`inline-flex px-1.5 py-0.5 rounded text-xs font-medium ${PRIORITY_COLORS[followUp.priority]}`}
                  >
                    {PRIORITY_LABELS[followUp.priority]}
                  </span>
                  <span className="text-xs text-gray-400">
                    Confianza: {Math.round(followUp.confidence * 100)}%
                  </span>
                </div>
              </div>
              <div className="shrink-0">
                {isDismissed ? (
                  <button
                    onClick={() => handleRestore(followUp)}
                    disabled={isPending}
                    className="text-xs text-teal-600 hover:text-teal-800 disabled:opacity-50 transition-colors"
                    aria-label="Restaurar"
                  >
                    Restaurar
                  </button>
                ) : (
                  <button
                    onClick={() => handleDismiss(followUp)}
                    disabled={isPending}
                    className="text-xs text-gray-500 hover:text-red-600 disabled:opacity-50 transition-colors"
                    aria-label="Descartar"
                  >
                    Descartar
                  </button>
                )}
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
