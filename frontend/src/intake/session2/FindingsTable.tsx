/**
 * FindingsTable — renders contradictions list with dismiss/restore UX.
 *
 * REQ-11: Optimistic dismiss with rollback on API error.
 * Each finding has its own local dismissed state to allow independent toggling.
 */

import { useState } from 'react'
import { dismissFinding, restoreFinding } from './api/session2'
import type { Session2PrepData } from './api/session2'

type Contradiction = Session2PrepData['contradictions'][number]

const SEVERITY_COLORS = {
  high: 'bg-red-100 text-red-700',
  med: 'bg-orange-100 text-orange-700',
  low: 'bg-gray-100 text-gray-600',
}

const SEVERITY_LABELS = {
  high: 'Alta',
  med: 'Media',
  low: 'Baja',
}

interface Props {
  leadId: string
  findings: Contradiction[]
}

export function FindingsTable({ leadId, findings }: Props) {
  // Local optimistic state: map from finding_id → dismissed
  const [dismissedMap, setDismissedMap] = useState<Record<string, boolean>>(() => {
    const map: Record<string, boolean> = {}
    for (const f of findings) {
      map[f.finding_id] = f.dismissed
    }
    return map
  })
  const [pendingMap, setPendingMap] = useState<Record<string, boolean>>({})

  async function handleDismiss(finding: Contradiction) {
    const prev = dismissedMap[finding.finding_id]
    // Optimistic update
    setDismissedMap((m) => ({ ...m, [finding.finding_id]: true }))
    setPendingMap((m) => ({ ...m, [finding.finding_id]: true }))
    try {
      await dismissFinding(leadId, finding.block_id, finding.finding_id)
    } catch {
      // Rollback
      setDismissedMap((m) => ({ ...m, [finding.finding_id]: prev }))
    } finally {
      setPendingMap((m) => ({ ...m, [finding.finding_id]: false }))
    }
  }

  async function handleRestore(finding: Contradiction) {
    const prev = dismissedMap[finding.finding_id]
    // Optimistic update
    setDismissedMap((m) => ({ ...m, [finding.finding_id]: false }))
    setPendingMap((m) => ({ ...m, [finding.finding_id]: true }))
    try {
      await restoreFinding(leadId, finding.block_id, finding.finding_id)
    } catch {
      // Rollback
      setDismissedMap((m) => ({ ...m, [finding.finding_id]: prev }))
    } finally {
      setPendingMap((m) => ({ ...m, [finding.finding_id]: false }))
    }
  }

  if (findings.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <p className="text-sm text-gray-400 italic">Sin contradicciones detectadas.</p>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100">
        <h4 className="text-sm font-semibold text-gray-700">
          Contradicciones ({findings.length})
        </h4>
      </div>
      <ul className="divide-y divide-gray-50">
        {findings.map((finding) => {
          const isDismissed = dismissedMap[finding.finding_id] ?? finding.dismissed
          const isPending = pendingMap[finding.finding_id] ?? false
          return (
            <li
              key={finding.finding_id}
              className={`px-4 py-3 flex items-start gap-3 ${isDismissed ? 'opacity-50' : ''}`}
            >
              <div className="flex-1 min-w-0">
                <p className={`text-sm text-gray-800 ${isDismissed ? 'line-through' : ''}`}>
                  {finding.text}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-400">{finding.block_id}</span>
                  <span
                    className={`inline-flex px-1.5 py-0.5 rounded text-xs font-medium ${SEVERITY_COLORS[finding.severity]}`}
                  >
                    {SEVERITY_LABELS[finding.severity]}
                  </span>
                </div>
              </div>
              <div className="shrink-0">
                {isDismissed ? (
                  <button
                    onClick={() => handleRestore(finding)}
                    disabled={isPending}
                    className="text-xs text-teal-600 hover:text-teal-800 disabled:opacity-50 transition-colors"
                    aria-label="Restaurar"
                  >
                    Restaurar
                  </button>
                ) : (
                  <button
                    onClick={() => handleDismiss(finding)}
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
