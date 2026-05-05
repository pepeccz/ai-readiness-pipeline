/**
 * LeadsListPage — Admin page showing paginated, filterable leads list.
 *
 * Route: /admin/leads
 *
 * Layout:
 *   - Sidebar filters (LeadFiltersPanel)
 *   - Main table with: empresa, email, sector, bucket badge, score, status, fecha, acciones
 *   - Pagination
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../AuthContext'
import { listLeads, patchLead } from '../api/leads'
import type { LeadFilters, LeadSummary } from '../api/leads'
import { LeadFiltersPanel } from '../components/LeadFilters/index'
import { BucketBadge } from '../components/LeadDetail/BucketBadge'

const DEFAULT_FILTERS: LeadFilters = {
  page: 1,
  page_size: 20,
}

const STATUS_LABELS: Record<string, string> = {
  pending_review: 'Pendiente',
  accepted: 'Aceptado',
  rejected: 'Rechazado',
  converted: 'Convertido',
}

export function LeadsListPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState<LeadFilters>(DEFAULT_FILTERS)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['leads', filters],
    queryFn: () => listLeads(filters),
    staleTime: 5_000,
  })

  const acceptMutation = useMutation({
    mutationFn: ({ id, consultantId }: { id: string; consultantId: string }) =>
      patchLead(id, { action: 'accept', consultant_id: consultantId }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['leads'] }),
  })

  const rejectMutation = useMutation({
    mutationFn: ({ id }: { id: string }) =>
      patchLead(id, { action: 'reject', reason: 'not_qualified_size' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['leads'] }),
  })

  const updateFilters = (partial: Partial<LeadFilters>) => {
    setFilters((prev) => ({ ...prev, ...partial }))
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <span className="text-base font-semibold text-gray-800">Zanovix Admin</span>
            <nav className="flex gap-1 ml-4">
              <button
                onClick={() => navigate('/admin/assessments')}
                className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 rounded-md hover:bg-gray-100 transition-colors"
              >
                Assessments
              </button>
              <button
                className="px-3 py-1.5 text-sm font-medium text-teal-700 bg-teal-50 rounded-md"
              >
                Leads
              </button>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">{user?.email}</span>
            <button
              onClick={logout}
              className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              Salir
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        <div className="mb-5">
          <h1 className="text-2xl font-bold text-gray-900">Leads</h1>
          {data && (
            <p className="text-sm text-gray-500 mt-0.5">
              {data.total} lead{data.total !== 1 ? 's' : ''} en total
            </p>
          )}
        </div>

        <div className="flex gap-6">
          {/* Filters sidebar */}
          <LeadFiltersPanel filters={filters} onFiltersChange={updateFilters} />

          {/* Content */}
          <div className="flex-1 min-w-0">
            {isLoading && (
              <div className="text-center py-12 text-gray-400">Cargando...</div>
            )}

            {isError && (
              <div className="text-center py-12 text-red-500">
                Error al cargar los leads. Intentá de nuevo.
              </div>
            )}

            {data && !isLoading && (
              <>
                {data.items.length === 0 ? (
                  <div className="text-center py-12 text-gray-400 bg-white rounded-lg border border-gray-200">
                    No hay leads con los filtros seleccionados.
                  </div>
                ) : (
                  <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Empresa / Email
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Sector
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Bucket
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Score
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Estado
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Fecha
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Acciones
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {data.items.map((lead) => (
                          <LeadRow
                            key={lead.id}
                            lead={lead}
                            onViewDetail={() => navigate(`/admin/leads/${lead.id}`)}
                          />
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Pagination */}
                {data.pages > 1 && (
                  <div className="mt-4 flex items-center justify-between">
                    <p className="text-sm text-gray-500">
                      Página {data.page} de {data.pages}
                    </p>
                    <div className="flex gap-2">
                      <button
                        disabled={data.page <= 1}
                        onClick={() => updateFilters({ page: data.page - 1 })}
                        className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-40 transition-colors"
                      >
                        Anterior
                      </button>
                      <button
                        disabled={data.page >= data.pages}
                        onClick={() => updateFilters({ page: data.page + 1 })}
                        className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-40 transition-colors"
                      >
                        Siguiente
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Row sub-component
// ---------------------------------------------------------------------------

function LeadRow({
  lead,
  onViewDetail,
}: {
  lead: LeadSummary
  onViewDetail: () => void
}) {
  const date = new Date(lead.created_at).toLocaleDateString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  })

  return (
    <tr className="hover:bg-gray-50 transition-colors">
      <td className="px-4 py-3">
        <p className="text-sm font-medium text-gray-900">{lead.company_name}</p>
        <p className="text-xs text-gray-500">{lead.email}</p>
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">{lead.sector}</td>
      <td className="px-4 py-3">
        <BucketBadge bucket={lead.triage_bucket} />
      </td>
      <td className="px-4 py-3 text-sm font-mono text-gray-700">{lead.triage_score}</td>
      <td className="px-4 py-3">
        <StatusBadge status={lead.status} />
      </td>
      <td className="px-4 py-3 text-xs text-gray-500">{date}</td>
      <td className="px-4 py-3">
        <button
          onClick={onViewDetail}
          className="text-xs text-teal-600 hover:text-teal-800 font-medium underline"
        >
          Ver detalle
        </button>
      </td>
    </tr>
  )
}

function StatusBadge({ status }: { status: string }) {
  const classes: Record<string, string> = {
    pending_review: 'bg-orange-100 text-orange-700',
    accepted: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
    converted: 'bg-purple-100 text-purple-700',
  }
  const cls = classes[status] ?? 'bg-gray-100 text-gray-600'
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {STATUS_LABELS[status] ?? status}
    </span>
  )
}
