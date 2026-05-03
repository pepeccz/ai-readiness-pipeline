/**
 * NewAssessmentPage — minimal create form for a new assessment.
 *
 * URL: /admin/assessments/new
 *
 * On submit: POST /api/admin/assessments → redirect to /admin/assessments/{id}
 * Consultant can fill remaining fields in the editor via debounced PATCH.
 *
 * Only company_name and sector are required for a useful initial record.
 * All other fields are optional at creation — the editor is the primary editing surface.
 */

import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { createAssessment } from '../api/assessments'
import { useAuth } from '../AuthContext'

const SECTOR_OPTIONS = [
  { value: '', label: '— Seleccionar sector —' },
  { value: 'retail', label: 'Retail' },
  { value: 'salud', label: 'Salud' },
  { value: 'finanzas', label: 'Finanzas' },
  { value: 'manufactura', label: 'Manufactura' },
  { value: 'educación', label: 'Educación' },
  { value: 'tecnología', label: 'Tecnología' },
  { value: 'logística', label: 'Logística' },
  { value: 'alimentación', label: 'Alimentación' },
  { value: 'construcción', label: 'Construcción' },
  { value: 'otro', label: 'Otro' },
]

const EMPLOYEE_OPTIONS = [
  { value: '', label: '— Rango de empleados —' },
  { value: '1-10', label: '1–10 empleados' },
  { value: '11-50', label: '11–50 empleados' },
  { value: '51-200', label: '51–200 empleados' },
  { value: '201-500', label: '201–500 empleados' },
  { value: '501-1000', label: '501–1.000 empleados' },
  { value: '1000+', label: 'Más de 1.000 empleados' },
]

const BUDGET_OPTIONS = [
  { value: '', label: '— Presupuesto —' },
  { value: '<10k', label: 'Menos de 10.000€' },
  { value: '10k-50k', label: '10.000–50.000€' },
  { value: '50k-200k', label: '50.000–200.000€' },
  { value: '200k-1M', label: '200.000€–1M€' },
  { value: '1M+', label: 'Más de 1M€' },
  { value: 'sin_definir', label: 'Sin definir aún' },
]

interface FormState {
  company_name: string
  sector: string
  employee_range: string
  revenue_range: string
  respondent_name_role: string
  respondent_email: string
  who_decides: string
  budget: string
  priority_text: string
  auto_publish: boolean
}

const INITIAL_FORM: FormState = {
  company_name: '',
  sector: '',
  employee_range: '',
  revenue_range: '',
  respondent_name_role: '',
  respondent_email: '',
  who_decides: '',
  budget: '',
  priority_text: '',
  auto_publish: false,
}

export function NewAssessmentPage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [form, setForm] = useState<FormState>(INITIAL_FORM)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const setField = (field: keyof FormState, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.company_name.trim()) {
      setError('El nombre de la empresa es obligatorio.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const assessment = await createAssessment({
        company_name: form.company_name,
        sector: form.sector,
        employee_range: form.employee_range,
        revenue_range: form.revenue_range,
        respondent_name_role: form.respondent_name_role,
        respondent_email: form.respondent_email || null,
        who_decides: form.who_decides,
        budget: form.budget,
        priority_text: form.priority_text,
        auto_publish: form.auto_publish,
        form_data: {},
      })
      navigate(`/admin/assessments/${assessment.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al crear el assessment.')
    } finally {
      setLoading(false)
    }
  }

  const inputClass =
    'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500'

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <span className="text-base font-semibold text-gray-800">Zanovix Admin</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">{user?.email}</span>
            <button onClick={logout} className="text-sm text-gray-600 hover:text-gray-900 hover:underline">
              Cerrar sesión
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        {/* Breadcrumb */}
        <div className="mb-6">
          <Link to="/admin/assessments" className="text-sm text-teal-600 hover:underline">
            ← Volver a la lista
          </Link>
        </div>

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Nuevo assessment</h1>
          <p className="text-sm text-gray-500 mt-1">
            Completá los datos básicos. Podés refinar todo en el editor.
          </p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Company name — required */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nombre de la empresa <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={form.company_name}
                onChange={(e) => setField('company_name', e.target.value)}
                placeholder="Ej: Acme S.A."
                className={inputClass}
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Sector */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Sector</label>
                <select
                  value={form.sector}
                  onChange={(e) => setField('sector', e.target.value)}
                  className={inputClass}
                >
                  {SECTOR_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>

              {/* Employee range */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rango de empleados</label>
                <select
                  value={form.employee_range}
                  onChange={(e) => setField('employee_range', e.target.value)}
                  className={inputClass}
                >
                  {EMPLOYEE_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>

              {/* Respondent name + role */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre y cargo del respondente
                </label>
                <input
                  type="text"
                  value={form.respondent_name_role}
                  onChange={(e) => setField('respondent_name_role', e.target.value)}
                  placeholder="Ej: María García, CTO"
                  className={inputClass}
                />
              </div>

              {/* Respondent email */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email del cliente
                </label>
                <input
                  type="email"
                  value={form.respondent_email}
                  onChange={(e) => setField('respondent_email', e.target.value)}
                  placeholder="cliente@empresa.com"
                  className={inputClass}
                />
              </div>

              {/* Who decides */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Quién decide sobre tecnología
                </label>
                <input
                  type="text"
                  value={form.who_decides}
                  onChange={(e) => setField('who_decides', e.target.value)}
                  placeholder="Ej: CTO, CEO"
                  className={inputClass}
                />
              </div>

              {/* Budget */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Presupuesto</label>
                <select
                  value={form.budget}
                  onChange={(e) => setField('budget', e.target.value)}
                  className={inputClass}
                >
                  {BUDGET_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Priority text */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Urgencia / prioridad
              </label>
              <textarea
                value={form.priority_text}
                onChange={(e) => setField('priority_text', e.target.value)}
                rows={3}
                placeholder="Descripción de la urgencia del cliente..."
                className={`${inputClass} resize-y`}
              />
            </div>

            {/* Auto publish */}
            <div className="flex items-center gap-3 py-2">
              <input
                type="checkbox"
                id="auto_publish"
                checked={form.auto_publish}
                onChange={(e) => setField('auto_publish', e.target.checked)}
                className="rounded border-gray-300 text-teal-500 focus:ring-teal-500"
              />
              <label htmlFor="auto_publish" className="text-sm text-gray-700">
                Auto publicar tras enriquecimiento (genera PDF y envía email automáticamente)
              </label>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-2 border-t border-gray-100">
              <Link
                to="/admin/assessments"
                className="px-4 py-2 rounded-lg border border-gray-300 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </Link>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 rounded-lg bg-teal-600 text-white text-sm font-medium hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {loading && (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                )}
                {loading ? 'Creando...' : 'Crear y abrir editor'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  )
}
