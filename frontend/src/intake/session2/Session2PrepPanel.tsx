/**
 * Session2PrepPanel — composes ScorecardPreview + FindingsTable + FollowUpsTable.
 *
 * REQ-10: Consultor prep view for Sesión 2.
 * Layout: scorecard at top, then side-by-side findings / follow-ups (stacked on mobile).
 */

import { useSession2Prep } from './hooks/useSession2Prep'
import { ScorecardPreview } from './ScorecardPreview'
import { FindingsTable } from './FindingsTable'
import { FollowUpsTable } from './FollowUpsTable'

interface Props {
  leadId: string
}

export function Session2PrepPanel({ leadId }: Props) {
  const { data, isLoading, isError } = useSession2Prep(leadId)

  if (isLoading) {
    return (
      <div data-testid="session2-loading" className="flex items-center justify-center py-16">
        <p className="text-sm text-gray-400">Cargando datos de Sesión 2...</p>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div
        data-testid="session2-error"
        className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700"
      >
        No se pudo cargar la información de Sesión 2. Por favor, recarga la página.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Scorecard at top */}
      <ScorecardPreview data={data} />

      {/* Findings + follow-ups: side by side on md+, stacked on mobile */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FindingsTable leadId={leadId} findings={data.contradictions} />
        <FollowUpsTable leadId={leadId} followUps={data.follow_ups} />
      </div>
    </div>
  )
}
