/**
 * AssessmentEditorPage — full assessment editor with tabs, enrichment panel,
 * approve-and-send, email retry, and PDF preview.
 *
 * URL: /admin/assessments/:id
 *
 * Architecture:
 *   - useQuery to load assessment (staleTime: 1000, refetchOnWindowFocus: false)
 *   - react-hook-form FormProvider wraps all tabs (ONE form for all 40+ fields)
 *   - Each EditorField fires useDebouncedPatch(500ms) on blur/change
 *   - useJobPolling polls GET /jobs and invalidates ["assessment", id] on completion
 *   - EnrichmentPanel renders the 5 action buttons
 *   - ApproveAndSendDialog handles the approve flow
 *   - EmailRetryBanner handles the email retry flow
 *   - PreviewPanel embeds the draft PDF in an iframe
 *
 * erasableSyntaxOnly compliance:
 *   - No TS enums (TabKey is a string union type)
 *   - No constructor parameter properties
 *   - No namespaces
 */

import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useForm, FormProvider } from 'react-hook-form'
import { useAuth } from '../AuthContext'
import { getAssessment } from '../api/assessments'
import { EditorTabs } from '../components/AssessmentEditor/EditorTabs'
import type { TabKey } from '../components/AssessmentEditor/EditorTabs'
import { EnrichmentPanel } from '../components/AssessmentEditor/EnrichmentPanel'
import { ApproveAndSendDialog } from '../components/AssessmentEditor/ApproveAndSendDialog'
import { EmailRetryBanner } from '../components/AssessmentEditor/EmailRetryBanner'
import { PreviewPanel } from '../components/AssessmentEditor/PreviewPanel'
import { EmpresaTab } from '../components/AssessmentEditor/tabs/EmpresaTab'
import { StackTab } from '../components/AssessmentEditor/tabs/StackTab'
import { ClienteTab } from '../components/AssessmentEditor/tabs/ClienteTab'
import { MarketingTab } from '../components/AssessmentEditor/tabs/MarketingTab'
import { OperacionesTab } from '../components/AssessmentEditor/tabs/OperacionesTab'
import { FinanzasTab } from '../components/AssessmentEditor/tabs/FinanzasTab'
import { RRHHTab } from '../components/AssessmentEditor/tabs/RRHHTab'
import { ComplianceTab } from '../components/AssessmentEditor/tabs/ComplianceTab'
import { PresupuestoTab } from '../components/AssessmentEditor/tabs/PresupuestoTab'
import { EnriquecimientosTab } from '../components/AssessmentEditor/tabs/EnriquecimientosTab'
import { ScoringTab } from '../components/AssessmentEditor/tabs/ScoringTab'

export function AssessmentEditorPage() {
  const { id } = useParams<{ id: string }>()
  const { user, logout } = useAuth()
  const [activeTab, setActiveTab] = useState<TabKey>('empresa')
  const [showPreview, setShowPreview] = useState(false)

  // ── Load assessment ─────────────────────────────────────────────────────────

  const {
    data: assessment,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['assessment', id],
    queryFn: () => getAssessment(id!),
    enabled: Boolean(id),
    staleTime: 1000,
  })

  // ── Form setup ──────────────────────────────────────────────────────────────

  const methods = useForm({
    defaultValues: {},
  })

  // Sync form when assessment data loads or refreshes (after mutation/polling)
  useEffect(() => {
    if (!assessment) return
    methods.reset({
      // Flat identity fields
      company_name: assessment.company_name,
      sector: assessment.sector,
      employee_range: assessment.employee_range,
      revenue_range: assessment.revenue_range,
      respondent_name_role: assessment.respondent_name_role,
      respondent_email: assessment.respondent_email ?? '',
      who_decides: assessment.who_decides,
      budget: assessment.budget,
      priority_text: assessment.priority_text,
      status: assessment.status,
      auto_publish: assessment.auto_publish,
      // Scoring
      maturity_score: assessment.maturity_score ?? '',
      maturity_level: assessment.maturity_level ?? '',
      risk_score: assessment.risk_score ?? '',
      risk_level: assessment.risk_level ?? '',
      priority_score: assessment.priority_score ?? '',
      priority_level: assessment.priority_level ?? '',
      pts_tools: assessment.pts_tools ?? '',
      pts_automation: assessment.pts_automation ?? '',
      pts_area_usage: assessment.pts_area_usage ?? '',
      pts_governance: assessment.pts_governance ?? '',
      pts_goal_clarity: assessment.pts_goal_clarity ?? '',
      pts_data_risk: assessment.pts_data_risk ?? '',
      pts_ai_personal_data: assessment.pts_ai_personal_data ?? '',
      pts_dpa: assessment.pts_dpa ?? '',
      pts_dpia: assessment.pts_dpia ?? '',
      pts_automated_decisions: assessment.pts_automated_decisions ?? '',
      pts_sector: assessment.pts_sector ?? '',
      pts_incident: assessment.pts_incident ?? '',
      // LLM fields (from llm_enriched_data blob, surfaced as top-level for form)
      llm_executive_summary: assessment.llm_enriched_data?.llm_executive_summary ?? '',
      llm_current_state: assessment.llm_enriched_data?.llm_current_state ?? '',
      llm_opportunities: assessment.llm_enriched_data?.llm_opportunities ?? '',
      llm_final_recommendation: assessment.llm_enriched_data?.llm_final_recommendation ?? '',
      llm_final_narrative: assessment.llm_enriched_data?.llm_final_narrative ?? '',
      llm_next_step_proposal: assessment.llm_enriched_data?.llm_next_step_proposal ?? '',
      llm_risk_findings: assessment.llm_enriched_data?.llm_risk_findings ?? '',
      llm_roadmap_30_60_90: assessment.llm_enriched_data?.llm_roadmap_30_60_90 ?? '',
      llm_tools_list: assessment.llm_enriched_data?.llm_tools_list ?? '',
      llm_ai_policy_draft: assessment.llm_enriched_data?.llm_ai_policy_draft ?? '',
      llm_dpa_guidance: assessment.llm_enriched_data?.llm_dpa_guidance ?? '',
      // JSON blobs (for read-display in form_data tabs)
      form_data: assessment.form_data ?? {},
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assessment])

  // ── Handlers ────────────────────────────────────────────────────────────────

  const handlePreviewReady = () => {
    setShowPreview(true)
  }

  // ── Loading / error states ──────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-gray-500">Cargando assessment...</span>
        </div>
      </div>
    )
  }

  if (isError || !assessment) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-sm mb-3">
            No se pudo cargar el assessment. Puede que no exista o esté archivado.
          </p>
          <Link to="/admin/assessments" className="text-teal-600 text-sm hover:underline">
            ← Volver a la lista
          </Link>
        </div>
      </div>
    )
  }

  const fieldSources = assessment.field_sources ?? {}

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Admin header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <span className="text-base font-semibold text-gray-800">Zanovix Admin</span>
            <span className="text-gray-300">/</span>
            <Link to="/admin/assessments" className="text-sm text-gray-500 hover:text-gray-700">
              Assessments
            </Link>
            <span className="text-gray-300">/</span>
            <span className="text-sm text-gray-800 font-medium truncate max-w-48">
              {assessment.company_name || 'Sin nombre'}
            </span>
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

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {/* Email retry banner (shown when email_status='failed') */}
        <EmailRetryBanner assessment={assessment} />

        {/* Page header with action buttons */}
        <div className="mb-6 flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {assessment.company_name || 'Sin nombre'}
            </h1>
            <div className="flex items-center gap-3 mt-1 flex-wrap">
              <span className="text-sm text-gray-500">{assessment.sector}</span>
              <span
                className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                  assessment.status === 'approved'
                    ? 'bg-green-100 text-green-700'
                    : assessment.status === 'pending_review'
                    ? 'bg-yellow-100 text-yellow-700'
                    : assessment.status === 'archived'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {assessment.status === 'approved'
                  ? 'Aprobado'
                  : assessment.status === 'pending_review'
                  ? 'Pendiente revisión'
                  : assessment.status === 'archived'
                  ? 'Archivado'
                  : 'Borrador'}
              </span>
              {assessment.maturity_score != null && (
                <span className="text-xs text-gray-400">
                  Madurez: <strong className="text-gray-700">{assessment.maturity_score.toFixed(1)}</strong>
                </span>
              )}
            </div>
          </div>

          {/* Approve and send */}
          <ApproveAndSendDialog assessment={assessment} />
        </div>

        {/* Two-column layout: editor (left) + enrichment panel (right) */}
        <div className="flex gap-6">
          {/* Editor column */}
          <div className="flex-1 min-w-0">
            {/* Tabs */}
            <EditorTabs activeTab={activeTab} onTabChange={setActiveTab} />

            {/* Tab content */}
            <FormProvider {...methods}>
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                {activeTab === 'empresa' && (
                  <EmpresaTab assessmentId={assessment.id} fieldSources={fieldSources} />
                )}
                {activeTab === 'stack' && (
                  <StackTab assessmentId={assessment.id} fieldSources={fieldSources} />
                )}
                {activeTab === 'cliente' && (
                  <ClienteTab assessmentId={assessment.id} fieldSources={fieldSources} />
                )}
                {activeTab === 'marketing' && (
                  <MarketingTab assessmentId={assessment.id} fieldSources={fieldSources} />
                )}
                {activeTab === 'operaciones' && (
                  <OperacionesTab assessmentId={assessment.id} fieldSources={fieldSources} />
                )}
                {activeTab === 'finanzas' && (
                  <FinanzasTab assessmentId={assessment.id} fieldSources={fieldSources} />
                )}
                {activeTab === 'rrhh' && (
                  <RRHHTab assessmentId={assessment.id} fieldSources={fieldSources} />
                )}
                {activeTab === 'compliance' && (
                  <ComplianceTab assessmentId={assessment.id} fieldSources={fieldSources} />
                )}
                {activeTab === 'presupuesto' && (
                  <PresupuestoTab assessmentId={assessment.id} fieldSources={fieldSources} />
                )}
                {activeTab === 'enriquecimientos' && (
                  <EnriquecimientosTab
                    assessmentId={assessment.id}
                    fieldSources={fieldSources}
                    hasEnrichments={assessment.llm_enriched_data != null}
                  />
                )}
                {activeTab === 'scoring' && (
                  <ScoringTab assessmentId={assessment.id} fieldSources={fieldSources} />
                )}
              </div>
            </FormProvider>
          </div>

          {/* Right sidebar */}
          <div className="w-72 flex-shrink-0 space-y-4">
            {/* Enrichment actions */}
            <EnrichmentPanel
              assessmentId={assessment.id}
              assessment={assessment}
              onPreviewReady={handlePreviewReady}
            />

            {/* Assessment metadata */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <h3 className="text-sm font-semibold text-gray-800 mb-3">Información</h3>
              <dl className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <dt className="text-gray-500">ID</dt>
                  <dd className="font-mono text-gray-700 truncate max-w-32" title={assessment.id}>
                    {assessment.id.slice(0, 8)}…
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Creado</dt>
                  <dd className="text-gray-700">
                    {new Date(assessment.created_at).toLocaleDateString('es-ES')}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Modificado</dt>
                  <dd className="text-gray-700">
                    {new Date(assessment.updated_at).toLocaleDateString('es-ES')}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Email</dt>
                  <dd
                    className={`font-medium ${
                      assessment.email_status === 'sent'
                        ? 'text-green-600'
                        : assessment.email_status === 'failed'
                        ? 'text-red-600'
                        : 'text-gray-400'
                    }`}
                  >
                    {assessment.email_status === 'sent'
                      ? 'Enviado'
                      : assessment.email_status === 'failed'
                      ? 'Falló'
                      : 'No enviado'}
                  </dd>
                </div>
                {assessment.pdf_path && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">PDF</dt>
                    <dd className="text-green-600 font-medium">Generado</dd>
                  </div>
                )}
              </dl>
            </div>
          </div>
        </div>
      </main>

      {/* PDF Preview modal */}
      <PreviewPanel
        assessmentId={assessment.id}
        visible={showPreview}
        onClose={() => setShowPreview(false)}
      />
    </div>
  )
}
