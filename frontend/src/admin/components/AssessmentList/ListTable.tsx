/**
 * ListTable — sortable assessment table with status pills, score badges,
 * source badge ([IA]/[Editado]), and row actions (open, duplicate, archive).
 */

import { useNavigate } from 'react-router-dom'
import type { AssessmentListItem, ListFilters } from '../../api/assessments'
import { archiveAssessment, duplicateAssessment } from '../../api/assessments'
import { useQueryClient } from '@tanstack/react-query'

// ── Status pill ────────────────────────────────────────────────────────────────

const STATUS_LABELS: Record<string, string> = {
  draft: 'Borrador',
  pending_review: 'Pendiente revisión',
  approved: 'Aprobado',
  archived: 'Archivado',
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-600',
  pending_review: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-green-100 text-green-700',
  archived: 'bg-red-100 text-red-700',
}

const EMAIL_LABELS: Record<string, string> = {
  not_sent: 'No enviado',
  sent: 'Enviado',
  failed: 'Falló',
}

const EMAIL_COLORS: Record<string, string> = {
  not_sent: 'bg-gray-100 text-gray-500',
  sent: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
}

// ── Relative time ─────────────────────────────────────────────────────────────

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const secs = Math.floor(diff / 1000)
  if (secs < 60) return 'hace un momento'
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `hace ${mins}m`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `hace ${hours}h`
  const days = Math.floor(hours / 24)
  return `hace ${days}d`
}

// ── Sortable column header ────────────────────────────────────────────────────

const SORTABLE_COLUMNS: { key: string; label: string }[] = [
  { key: 'company_name', label: 'Empresa' },
  { key: 'created_at', label: 'Creado' },
  { key: 'updated_at', label: 'Modificado' },
  { key: 'maturity_score', label: 'Madurez' },
  { key: 'risk_score', label: 'Riesgo' },
]

interface SortHeaderProps {
  col: string
  label: string
  sortBy: string
  sortOrder: 'asc' | 'desc'
  onClick: (col: string) => void
}

function SortHeader({ col, label, sortBy, sortOrder, onClick }: SortHeaderProps) {
  const active = sortBy === col
  return (
    <th
      className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer select-none hover:text-gray-800 whitespace-nowrap"
      onClick={() => onClick(col)}
    >
      {label}
      {active && (
        <span className="ml-1 text-teal-500">{sortOrder === 'asc' ? '↑' : '↓'}</span>
      )}
    </th>
  )
}

// ── Main table ────────────────────────────────────────────────────────────────

interface Props {
  items: AssessmentListItem[]
  filters: ListFilters
  onSortChange: (col: string) => void
  onArchived: () => void
  onDuplicated: () => void
}

export function ListTable({ items, filters, onSortChange, onArchived, onDuplicated }: Props) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const handleDuplicate = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    try {
      await duplicateAssessment(id)
      queryClient.invalidateQueries({ queryKey: ['assessments'] })
      onDuplicated()
    } catch {
      alert('Error al duplicar el assessment.')
    }
  }

  const handleArchive = async (e: React.MouseEvent, id: string, name: string) => {
    e.stopPropagation()
    if (!confirm(`¿Archivar "${name}"? Esta acción se puede revertir desde el editor.`)) return
    try {
      await archiveAssessment(id)
      queryClient.invalidateQueries({ queryKey: ['assessments'] })
      onArchived()
    } catch {
      alert('Error al archivar el assessment.')
    }
  }

  const sortBy = filters.sort_by ?? 'created_at'
  const sortOrder = filters.sort_order ?? 'desc'

  if (items.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
        <p className="text-gray-400 text-sm">No se encontraron assessments con los filtros actuales.</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-28">
                ID
              </th>
              {SORTABLE_COLUMNS.map((col) => (
                <SortHeader
                  key={col.key}
                  col={col.key}
                  label={col.label}
                  sortBy={sortBy}
                  sortOrder={sortOrder}
                  onClick={onSortChange}
                />
              ))}
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Estado
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Email
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Fuente
              </th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {items.map((item) => {
              // [Editado] badge if any field is explicitly human-edited
              // We use last_edited_by_id as a proxy — if set, a human edited it
              const isHumanEdited = item.last_edited_by_id != null
              const shortId = item.id.slice(0, 8)

              return (
                <tr
                  key={item.id}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/admin/assessments/${item.id}`)}
                >
                  {/* ID */}
                  <td className="px-4 py-3 font-mono text-xs text-gray-400" title={item.id}>
                    {shortId}…
                  </td>

                  {/* Empresa */}
                  <td className="px-4 py-3 font-medium text-gray-900">
                    <div>{item.company_name || <span className="text-gray-400 italic">Sin nombre</span>}</div>
                    <div className="text-xs text-gray-400">{item.sector}</div>
                  </td>

                  {/* Creado */}
                  <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                    {relativeTime(item.created_at)}
                  </td>

                  {/* Modificado */}
                  <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                    {relativeTime(item.updated_at)}
                  </td>

                  {/* Madurez */}
                  <td className="px-4 py-3 text-gray-700">
                    {item.maturity_score != null ? (
                      <span className="font-semibold">{item.maturity_score.toFixed(1)}</span>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>

                  {/* Riesgo */}
                  <td className="px-4 py-3 text-gray-700">
                    {item.risk_score != null ? (
                      <span className="font-semibold">{item.risk_score.toFixed(1)}</span>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>

                  {/* Estado */}
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[item.status] ?? 'bg-gray-100 text-gray-600'}`}
                    >
                      {STATUS_LABELS[item.status] ?? item.status}
                    </span>
                  </td>

                  {/* Email */}
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${EMAIL_COLORS[item.email_status] ?? 'bg-gray-100 text-gray-500'}`}
                    >
                      {EMAIL_LABELS[item.email_status] ?? item.email_status}
                    </span>
                  </td>

                  {/* Fuente badge */}
                  <td className="px-4 py-3">
                    {isHumanEdited ? (
                      <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-700">
                        Editado
                      </span>
                    ) : (
                      <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
                        IA
                      </span>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={(e) => handleDuplicate(e, item.id)}
                        className="text-xs text-gray-500 hover:text-teal-600 transition-colors"
                        title="Duplicar"
                      >
                        Duplicar
                      </button>
                      <span className="text-gray-300">|</span>
                      <button
                        onClick={(e) => handleArchive(e, item.id, item.company_name)}
                        className="text-xs text-gray-500 hover:text-red-600 transition-colors"
                        title="Archivar"
                      >
                        Archivar
                      </button>
                    </div>
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
