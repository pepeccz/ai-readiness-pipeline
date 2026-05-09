/**
 * ScorecardPreview — renders composite score + all 7 blocks with CMMI level badges.
 *
 * REQ-08: blocks in insufficient_data render "Datos pendientes — completar en Sesión 2"
 * REQ-19: all 7 dimensions shown with score, CMMI level, and color badge
 */

import type { Session2PrepData } from './api/session2'

// ---------------------------------------------------------------------------
// CMMI level metadata
// ---------------------------------------------------------------------------

const CMMI_LEVELS: Record<number, { label: string; color: string }> = {
  0: { label: 'Inicial', color: 'bg-red-100 text-red-700' },
  1: { label: 'Emergente', color: 'bg-orange-100 text-orange-700' },
  2: { label: 'Establecido', color: 'bg-yellow-100 text-yellow-700' },
  3: { label: 'Avanzado', color: 'bg-green-100 text-green-700' },
  4: { label: 'Optimizado', color: 'bg-blue-100 text-blue-700' },
}

const RISK_COLORS: Record<string, string> = {
  low: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
}

const RISK_LABELS: Record<string, string> = {
  low: 'Riesgo bajo',
  medium: 'Riesgo medio',
  high: 'Riesgo alto',
  critical: 'Riesgo crítico',
}

interface Props {
  data: Session2PrepData
}

export function ScorecardPreview({ data }: Props) {
  const { session, per_block } = data
  const compositeLevel = session.composite_level
  const compositeLevelMeta = compositeLevel !== null ? CMMI_LEVELS[compositeLevel] : null
  const riskProfile = session.risk_profile
  const riskColor = riskProfile ? RISK_COLORS[riskProfile] : 'bg-gray-100 text-gray-600'
  const riskLabel = riskProfile ? RISK_LABELS[riskProfile] : 'Riesgo desconocido'

  return (
    <div className="space-y-4">
      {/* Composite score header */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Scorecard — Resumen
        </h3>
        <div className="flex flex-wrap items-center gap-4">
          {session.composite_score !== null ? (
            <div className="flex flex-col items-center">
              <span className="text-3xl font-bold text-gray-900">
                {Math.round(session.composite_score * 100)}%
              </span>
              <span className="text-xs text-gray-400 mt-0.5">Score compuesto</span>
            </div>
          ) : (
            <div className="text-sm text-gray-400 italic">Score aún no disponible</div>
          )}

          {compositeLevelMeta && (
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${compositeLevelMeta.color}`}
            >
              CMMI {compositeLevel} — {compositeLevelMeta.label}
            </span>
          )}

          {riskProfile && (
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${riskColor}`}
            >
              {riskLabel}
            </span>
          )}
        </div>
      </div>

      {/* Per-block rows */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-100 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                Dimensión
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                Score
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                Nivel CMMI
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                Estado
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {per_block.map((block) => {
              const levelMeta =
                block.level !== null ? CMMI_LEVELS[block.level] : null
              const isInsufficient = block.status === 'insufficient_data'

              return (
                <tr key={block.block_id} className={isInsufficient ? 'bg-gray-50' : ''}>
                  <td className="px-4 py-3 font-medium text-gray-800">
                    {block.block_title}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {block.score !== null ? `${Math.round(block.score * 100)}%` : '—'}
                  </td>
                  <td className="px-4 py-3">
                    {levelMeta ? (
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${levelMeta.color}`}
                      >
                        {block.level} — {levelMeta.label}
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {isInsufficient ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-200 text-gray-600">
                        Datos pendientes — completar en Sesión 2
                      </span>
                    ) : (
                      <span className="text-gray-400 text-xs capitalize">{block.status}</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
