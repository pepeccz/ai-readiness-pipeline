/**
 * admin/api/assessments.ts
 *
 * All admin assessment API calls.  Every function delegates to fetchJson()
 * which attaches credentials:'include' and the Content-Type header.
 *
 * Enum-like string unions (not TS enums — erasableSyntaxOnly is enabled).
 */

import { fetchJson } from './client'

// ── String union types (no enums — erasableSyntaxOnly) ────────────────────────

export type AssessmentStatus = 'draft' | 'pending_review' | 'approved' | 'archived'
export type EmailStatus = 'not_sent' | 'sent' | 'failed'
export type JobStatus = 'pending' | 'running' | 'done' | 'failed'
export type JobType =
  | 'enrich_llm'
  | 'enrich_recommendations'
  | 'score'
  | 'generate_pdf'
  | 'preview_pdf'
  | 'approve_and_send'
  | 'public_submission'
  | 'resend_email'

// ── Response shapes ───────────────────────────────────────────────────────────

export interface AssessmentListItem {
  id: string
  status: AssessmentStatus
  company_name: string
  sector: string
  employee_range: string
  created_at: string
  updated_at: string
  maturity_score: number | null
  maturity_level: string | null
  risk_score: number | null
  pdf_path: string | null
  email_status: EmailStatus
  last_edited_by_id: string | null
}

export interface AssessmentResponse {
  id: string
  status: AssessmentStatus
  auto_publish: boolean
  created_at: string
  updated_at: string
  created_by_id: string | null
  last_edited_by_id: string | null
  company_name: string
  sector: string
  employee_range: string
  revenue_range: string
  respondent_name_role: string
  respondent_email: string | null
  who_decides: string
  budget: string
  priority_text: string
  maturity_score: number | null
  maturity_level: string | null
  risk_score: number | null
  risk_level: string | null
  priority_score: number | null
  priority_level: string | null
  pts_tools: number | null
  pts_automation: number | null
  pts_area_usage: number | null
  pts_governance: number | null
  pts_goal_clarity: number | null
  pts_data_risk: number | null
  pts_ai_personal_data: number | null
  pts_dpa: number | null
  pts_dpia: number | null
  pts_automated_decisions: number | null
  pts_sector: number | null
  pts_incident: number | null
  pdf_path: string | null
  pdf_generated_at: string | null
  email_status: EmailStatus
  email_sent_at: string | null
  email_error: string | null
  task_id: string | null
  form_data: Record<string, unknown>
  llm_enriched_data: Record<string, unknown> | null
  recommendation_data: Record<string, unknown> | null
  field_sources: Record<string, string>
}

export interface AssessmentListResponse {
  items: AssessmentListItem[]
  total: number
  page: number
  page_size: number
}

export interface JobRecord {
  id: string
  type: JobType
  assessment_id: string
  status: JobStatus
  started_at: string | null
  finished_at: string | null
  error: string | null
}

export interface JobResponse {
  job_id: string
  status: string
}

// ── List filters ──────────────────────────────────────────────────────────────

export interface ListFilters {
  status?: AssessmentStatus[]
  sector?: string[]
  search?: string
  min_maturity_score?: number
  max_maturity_score?: number
  min_risk_score?: number
  max_risk_score?: number
  email_status?: EmailStatus
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

function buildQuery(filters: ListFilters): string {
  const params = new URLSearchParams()
  if (filters.status?.length) filters.status.forEach((s) => params.append('status', s))
  if (filters.sector?.length) filters.sector.forEach((s) => params.append('sector', s))
  if (filters.search) params.set('search', filters.search)
  if (filters.min_maturity_score != null)
    params.set('min_maturity_score', String(filters.min_maturity_score))
  if (filters.max_maturity_score != null)
    params.set('max_maturity_score', String(filters.max_maturity_score))
  if (filters.min_risk_score != null)
    params.set('min_risk_score', String(filters.min_risk_score))
  if (filters.max_risk_score != null)
    params.set('max_risk_score', String(filters.max_risk_score))
  if (filters.email_status) params.set('email_status', filters.email_status)
  if (filters.sort_by) params.set('sort_by', filters.sort_by)
  if (filters.sort_order) params.set('sort_order', filters.sort_order)
  if (filters.page != null) params.set('page', String(filters.page))
  if (filters.page_size != null) params.set('page_size', String(filters.page_size))
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

// ── CRUD ──────────────────────────────────────────────────────────────────────

export const listAssessments = (filters: ListFilters = {}) =>
  fetchJson<AssessmentListResponse>(`/admin/assessments${buildQuery(filters)}`)

export const getAssessment = (id: string) =>
  fetchJson<AssessmentResponse>(`/admin/assessments/${id}`)

export const createAssessment = (body: Record<string, unknown>) =>
  fetchJson<AssessmentResponse>('/admin/assessments', {
    method: 'POST',
    body: JSON.stringify(body),
  })

export const patchAssessment = (id: string, body: Record<string, unknown>) =>
  fetchJson<AssessmentResponse>(`/admin/assessments/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })

export const duplicateAssessment = (id: string) =>
  fetchJson<AssessmentResponse>(`/admin/assessments/${id}/duplicate`, { method: 'POST' })

export const archiveAssessment = (id: string) =>
  fetchJson<void>(`/admin/assessments/${id}/archive`, { method: 'POST' })

// ── Re-run actions ────────────────────────────────────────────────────────────

export const runLlmEnrichment = (id: string) =>
  fetchJson<JobResponse>(`/admin/assessments/${id}/run-llm-enrichment`, { method: 'POST' })

export const runRecommendations = (id: string) =>
  fetchJson<JobResponse>(`/admin/assessments/${id}/run-recommendations`, { method: 'POST' })

export const runScoring = (id: string) =>
  fetchJson<JobResponse>(`/admin/assessments/${id}/run-scoring`, { method: 'POST' })

export const generatePdf = (id: string) =>
  fetchJson<JobResponse>(`/admin/assessments/${id}/generate-pdf`, { method: 'POST' })

export const previewPdf = (id: string) =>
  fetchJson<JobResponse>(`/admin/assessments/${id}/preview-pdf`, { method: 'POST' })

export const approveAndSend = (id: string) =>
  fetchJson<JobResponse>(`/admin/assessments/${id}/approve-and-send`, { method: 'POST' })

export const resendEmail = (id: string) =>
  fetchJson<JobResponse>(`/admin/assessments/${id}/resend-email`, { method: 'POST' })

// ── Job polling ───────────────────────────────────────────────────────────────

export const getJobs = (id: string) =>
  fetchJson<JobRecord[]>(`/admin/assessments/${id}/jobs`)

// ── PDF URL builder (for iframe src — browser sends cookie automatically) ─────

export const pdfUrl = (id: string, draft = false) =>
  `/api/admin/assessments/${id}/pdf${draft ? '?draft=true' : ''}`
