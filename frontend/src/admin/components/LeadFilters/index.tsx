/**
 * LeadFilters — Sidebar filter panel for the leads list.
 *
 * Exposes: bucket multi-select, status, sector, date range, search.
 * Calls onFiltersChange with updated filter values on every change.
 */

import type { LeadFilters, LeadBucket, LeadStatus } from '../../api/leads'

const BUCKETS: { value: LeadBucket; label: string; color: string }[] = [
  { value: 'auto_accept', label: 'Auto-aceptado', color: 'bg-green-100 text-green-700' },
  { value: 'review', label: 'Revisión', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'cold_warm', label: 'Frío-cálido', color: 'bg-blue-100 text-blue-700' },
  { value: 'cold_cool', label: 'Frío-frío', color: 'bg-gray-100 text-gray-700' },
  { value: 'reject_soft', label: 'Rechazado', color: 'bg-red-100 text-red-700' },
]

const STATUSES: { value: LeadStatus; label: string }[] = [
  { value: 'pending_review', label: 'Pendiente revisión' },
  { value: 'accepted', label: 'Aceptado' },
  { value: 'rejected', label: 'Rechazado' },
  { value: 'converted', label: 'Convertido' },
]

interface LeadFiltersProps {
  filters: LeadFilters
  onFiltersChange: (partial: Partial<LeadFilters>) => void
}

export function LeadFiltersPanel({ filters, onFiltersChange }: LeadFiltersProps) {
  return (
    <aside className="w-64 shrink-0 space-y-6">
      {/* Search */}
      <div>
        <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
          Búsqueda
        </label>
        <input
          type="text"
          value={filters.search ?? ''}
          onChange={(e) => onFiltersChange({ search: e.target.value || undefined, page: 1 })}
          placeholder="Email o empresa..."
          className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-400"
        />
      </div>

      {/* Bucket filter */}
      <div>
        <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
          Bucket
        </label>
        <div className="space-y-1">
          {BUCKETS.map((b) => (
            <button
              key={b.value}
              onClick={() =>
                onFiltersChange({ bucket: filters.bucket === b.value ? undefined : b.value, page: 1 })
              }
              className={`w-full text-left px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                filters.bucket === b.value
                  ? b.color + ' ring-1 ring-current'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              {b.label}
            </button>
          ))}
        </div>
      </div>

      {/* Status filter */}
      <div>
        <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
          Estado
        </label>
        <select
          value={filters.status ?? ''}
          onChange={(e) =>
            onFiltersChange({ status: (e.target.value as LeadStatus) || undefined, page: 1 })
          }
          className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-400"
        >
          <option value="">Todos</option>
          {STATUSES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      {/* Sector filter */}
      <div>
        <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
          Sector
        </label>
        <input
          type="text"
          value={filters.sector ?? ''}
          onChange={(e) => onFiltersChange({ sector: e.target.value || undefined, page: 1 })}
          placeholder="tecnologia, salud..."
          className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-400"
        />
      </div>

      {/* Date range */}
      <div>
        <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
          Rango de fechas
        </label>
        <div className="space-y-2">
          <div>
            <span className="text-xs text-gray-400">Desde</span>
            <input
              type="date"
              value={filters.from_date ?? ''}
              onChange={(e) => onFiltersChange({ from_date: e.target.value || undefined, page: 1 })}
              className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm mt-0.5 focus:outline-none focus:ring-2 focus:ring-teal-400"
            />
          </div>
          <div>
            <span className="text-xs text-gray-400">Hasta</span>
            <input
              type="date"
              value={filters.to_date ?? ''}
              onChange={(e) => onFiltersChange({ to_date: e.target.value || undefined, page: 1 })}
              className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm mt-0.5 focus:outline-none focus:ring-2 focus:ring-teal-400"
            />
          </div>
        </div>
      </div>

      {/* Clear all */}
      <button
        onClick={() => onFiltersChange({ bucket: undefined, status: undefined, sector: undefined, from_date: undefined, to_date: undefined, search: undefined, page: 1 })}
        className="w-full text-sm text-gray-500 hover:text-gray-700 underline"
      >
        Limpiar filtros
      </button>
    </aside>
  )
}
