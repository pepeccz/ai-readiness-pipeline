/**
 * ListFilters — filter bar for the assessment list page.
 *
 * Controls: search (text), status (multi-select checkboxes), sector (select),
 * maturity score range (min/max), risk score range (min/max), email_status.
 */

import type { AssessmentStatus, EmailStatus, ListFilters } from '../../api/assessments'

const STATUS_OPTIONS: { value: AssessmentStatus; label: string }[] = [
  { value: 'draft', label: 'Borrador' },
  { value: 'pending_review', label: 'Pendiente revisión' },
  { value: 'approved', label: 'Aprobado' },
  { value: 'archived', label: 'Archivado' },
]

const EMAIL_STATUS_OPTIONS: { value: EmailStatus | ''; label: string }[] = [
  { value: '', label: 'Todos' },
  { value: 'not_sent', label: 'No enviado' },
  { value: 'sent', label: 'Enviado' },
  { value: 'failed', label: 'Falló' },
]

const SECTOR_OPTIONS = [
  'retail',
  'salud',
  'finanzas',
  'manufactura',
  'educación',
  'tecnología',
  'logística',
  'alimentación',
  'construcción',
  'otro',
]

interface Props {
  filters: ListFilters
  onChange: (f: Partial<ListFilters>) => void
}

export function ListFilters({ filters, onChange }: Props) {
  const toggleStatus = (s: AssessmentStatus) => {
    const current = filters.status ?? []
    const next = current.includes(s) ? current.filter((x) => x !== s) : [...current, s]
    onChange({ status: next.length ? next : undefined, page: 1 })
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4 space-y-4">
      {/* Search */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Buscar empresa</label>
        <input
          type="text"
          placeholder="Nombre de empresa..."
          value={filters.search ?? ''}
          onChange={(e) => onChange({ search: e.target.value || undefined, page: 1 })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {/* Status */}
        <div>
          <p className="text-xs font-medium text-gray-600 mb-1">Estado</p>
          <div className="space-y-1">
            {STATUS_OPTIONS.map((opt) => (
              <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={(filters.status ?? []).includes(opt.value)}
                  onChange={() => toggleStatus(opt.value)}
                  className="rounded border-gray-300 text-teal-500 focus:ring-teal-500"
                />
                <span className="text-xs text-gray-700">{opt.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Sector */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Sector</label>
          <select
            value={filters.sector?.[0] ?? ''}
            onChange={(e) =>
              onChange({ sector: e.target.value ? [e.target.value] : undefined, page: 1 })
            }
            className="w-full rounded-lg border border-gray-300 px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">Todos</option>
            {SECTOR_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Maturity score range */}
        <div>
          <p className="text-xs font-medium text-gray-600 mb-1">Madurez (0–100)</p>
          <div className="flex gap-1">
            <input
              type="number"
              min={0}
              max={100}
              placeholder="Mín"
              value={filters.min_maturity_score ?? ''}
              onChange={(e) =>
                onChange({
                  min_maturity_score: e.target.value ? Number(e.target.value) : undefined,
                  page: 1,
                })
              }
              className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
            />
            <input
              type="number"
              min={0}
              max={100}
              placeholder="Máx"
              value={filters.max_maturity_score ?? ''}
              onChange={(e) =>
                onChange({
                  max_maturity_score: e.target.value ? Number(e.target.value) : undefined,
                  page: 1,
                })
              }
              className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
            />
          </div>
        </div>

        {/* Email status */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
          <select
            value={filters.email_status ?? ''}
            onChange={(e) =>
              onChange({
                email_status: e.target.value ? (e.target.value as EmailStatus) : undefined,
                page: 1,
              })
            }
            className="w-full rounded-lg border border-gray-300 px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            {EMAIL_STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Clear filters */}
      {(filters.search ||
        filters.status?.length ||
        filters.sector?.length ||
        filters.email_status ||
        filters.min_maturity_score != null ||
        filters.max_maturity_score != null) && (
        <button
          onClick={() =>
            onChange({
              search: undefined,
              status: undefined,
              sector: undefined,
              email_status: undefined,
              min_maturity_score: undefined,
              max_maturity_score: undefined,
              page: 1,
            })
          }
          className="text-xs text-teal-600 hover:underline"
        >
          Limpiar filtros
        </button>
      )}
    </div>
  )
}
