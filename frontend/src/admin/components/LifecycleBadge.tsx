/**
 * LifecycleBadge — Color-coded badge for IntakeSession.state values.
 *
 * Single source of truth for lifecycle state label + color mapping (D8).
 * Used in: LeadsListPage rows, LeadDetailPage header, IntakeApp header.
 */

const STATE_CONFIG: Record<string, { label: string; cls: string }> = {
  not_started: {
    label: 'Sin iniciar',
    cls: 'bg-gray-100 text-gray-600 border-gray-200',
  },
  in_progress: {
    label: 'En progreso',
    cls: 'bg-blue-100 text-blue-700 border-blue-200',
  },
  blocks_completed: {
    label: 'Bloques completos',
    cls: 'bg-indigo-100 text-indigo-700 border-indigo-200',
  },
  deep_pending: {
    label: 'DEEP pendiente',
    cls: 'bg-orange-100 text-orange-700 border-orange-200',
  },
  deep_received: {
    label: 'DEEP recibido',
    cls: 'bg-purple-100 text-purple-700 border-purple-200',
  },
  closed: {
    label: 'Cerrado',
    cls: 'bg-green-100 text-green-700 border-green-200',
  },
}

interface LifecycleBadgeProps {
  state: string
}

export function LifecycleBadge({ state }: LifecycleBadgeProps) {
  const config = STATE_CONFIG[state]
  const label = config?.label ?? state
  const cls = config?.cls ?? 'bg-gray-100 text-gray-600 border-gray-200'

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}
    >
      {label}
    </span>
  )
}
