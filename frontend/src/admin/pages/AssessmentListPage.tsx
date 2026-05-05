/**
 * AssessmentListPage — REAL assessment list with filters, sort, pagination.
 *
 * Replaces the Phase A placeholder.
 *
 * State: all filter/sort/page state lives in React state (not URL params —
 * Phase D can add URL sync if needed).
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../AuthContext'
import { createAssessment, listAssessments } from '../api/assessments'
import type { ListFilters } from '../api/assessments'
import { ListFilters as ListFiltersComponent } from '../components/AssessmentList/ListFilters'
import { ListTable } from '../components/AssessmentList/ListTable'
import { Pagination } from '../components/AssessmentList/Pagination'

const DEFAULT_FILTERS: ListFilters = {
  sort_by: 'created_at',
  sort_order: 'desc',
  page: 1,
  page_size: 25,
}

export function AssessmentListPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState<ListFilters>(DEFAULT_FILTERS)
  const [creating, setCreating] = useState(false)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['assessments', filters],
    queryFn: () => listAssessments(filters),
    staleTime: 1000,
  })

  const updateFilters = (partial: Partial<ListFilters>) => {
    setFilters((prev) => ({ ...prev, ...partial }))
  }

  const handleSortChange = (col: string) => {
    setFilters((prev) => {
      if (prev.sort_by === col) {
        return { ...prev, sort_order: prev.sort_order === 'asc' ? 'desc' : 'asc', page: 1 }
      }
      return { ...prev, sort_by: col, sort_order: 'desc', page: 1 }
    })
  }

  const handleNewAssessment = async () => {
    setCreating(true)
    try {
      const assessment = await createAssessment({ company_name: 'Nuevo assessment', sector: '' })
      navigate(`/admin/assessments/${assessment.id}`)
    } catch {
      alert('Error al crear el assessment.')
    } finally {
      setCreating(false)
    }
  }

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['assessments'] })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Admin header */}
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
                className="px-3 py-1.5 text-sm font-medium text-teal-700 bg-teal-50 rounded-md"
              >
                Assessments
              </button>
              <button
                onClick={() => navigate('/admin/leads')}
                className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 rounded-md hover:bg-gray-100 transition-colors"
              >
                Leads
              </button>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">{user?.email}</span>
            <button
              onClick={logout}
              className="text-sm text-gray-600 hover:text-gray-900 hover:underline transition-colors"
            >
              Cerrar sesión
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Page header */}
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Assessments</h1>
            <p className="text-sm text-gray-500 mt-1">
              Gestión de assessments de AI Readiness
              {data && (
                <span className="ml-2 text-gray-400">· {data.total} total</span>
              )}
            </p>
          </div>
          <button
            onClick={handleNewAssessment}
            disabled={creating}
            className="flex-shrink-0 flex items-center gap-2 px-4 py-2 rounded-lg bg-teal-600 text-white text-sm font-medium hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {creating ? (
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
            )}
            Nuevo assessment
          </button>
        </div>

        {/* Filters */}
        <ListFiltersComponent filters={filters} onChange={updateFilters} />

        {/* Table */}
        {isLoading ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-gray-400">Cargando assessments...</span>
            </div>
          </div>
        ) : isError ? (
          <div className="bg-white rounded-xl border border-red-200 p-8 text-center">
            <p className="text-red-600 text-sm">Error al cargar los assessments.</p>
            <button
              onClick={handleRefresh}
              className="mt-2 text-sm text-teal-600 hover:underline"
            >
              Reintentar
            </button>
          </div>
        ) : (
          <>
            <ListTable
              items={data?.items ?? []}
              filters={filters}
              onSortChange={handleSortChange}
              onArchived={handleRefresh}
              onDuplicated={handleRefresh}
            />
            <Pagination
              page={filters.page ?? 1}
              pageSize={filters.page_size ?? 25}
              total={data?.total ?? 0}
              onPageChange={(p) => updateFilters({ page: p })}
              onPageSizeChange={(s) => updateFilters({ page_size: s, page: 1 })}
            />
          </>
        )}
      </main>
    </div>
  )
}
