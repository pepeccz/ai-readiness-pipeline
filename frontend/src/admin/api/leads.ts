/**
 * admin/api/leads.ts — Admin lead management API hooks.
 *
 * All calls delegate to fetchJson() (credentials: 'include' + Content-Type).
 * String unions instead of TS enums (erasableSyntaxOnly is enabled).
 */

import { fetchJson } from './client'

// ── Types ─────────────────────────────────────────────────────────────────────

export type LeadBucket =
  | 'auto_accept'
  | 'review'
  | 'cold_warm'
  | 'cold_cool'
  | 'reject_soft'

export type LeadStatus = 'pending_review' | 'accepted' | 'rejected' | 'converted'

export type LeadAction =
  | 'accept'
  | 'reject'
  | 'request_extra_info'
  | 'assign_consultant'

export type RejectReason =
  | 'not_qualified_size'
  | 'out_of_sector'
  | 'no_decision_authority'
  | 'not_aligned_with_offering'
  | 'not_a_real_lead'
  | 'other'

// ── Response shapes ───────────────────────────────────────────────────────────

export interface LeadSummary {
  id: string
  full_name: string
  email: string
  company_name: string
  sector: string
  triage_bucket: LeadBucket
  triage_score: number
  status: LeadStatus
  created_at: string
  assigned_consultant_id: string | null
  /** Intake session lifecycle state — present only for accepted leads */
  intake_state?: string
}

export interface ConsentRecord {
  id: string
  type: string
  accepted: boolean
  timestamp: string
  policy_version: string
}

export interface LeadDetail extends LeadSummary {
  phone: string | null
  company_size: string
  respondent_role: string
  ai_maturity: string
  ai_goals: string[]
  urgency: string
  commitment: string
  triage_payload: Record<string, unknown>
  rejected_reason: string | null
  client_id: string | null
  accepted_at: string | null
  consents: ConsentRecord[]
}

export interface SideEffect {
  type: string
  description: string
}

export interface LeadActionResponse {
  lead: LeadDetail
  side_effects: SideEffect[]
}

export interface LeadListResponse {
  items: LeadSummary[]
  total: number
  page: number
  page_size: number
  pages: number
}

// ── Filter params ─────────────────────────────────────────────────────────────

export interface LeadFilters {
  bucket?: LeadBucket
  status?: LeadStatus
  sector?: string
  from_date?: string
  to_date?: string
  search?: string
  page?: number
  page_size?: number
}

// ── Request bodies ────────────────────────────────────────────────────────────

export interface LeadActionBody {
  action: LeadAction
  reason?: string
  consultant_id?: string
}

// ── API functions ─────────────────────────────────────────────────────────────

export function listLeads(filters: LeadFilters = {}): Promise<LeadListResponse> {
  const params = new URLSearchParams()
  if (filters.bucket) params.set('bucket', filters.bucket)
  if (filters.status) params.set('status', filters.status)
  if (filters.sector) params.set('sector', filters.sector)
  if (filters.from_date) params.set('from_date', filters.from_date)
  if (filters.to_date) params.set('to_date', filters.to_date)
  if (filters.search) params.set('search', filters.search)
  if (filters.page != null) params.set('page', String(filters.page))
  if (filters.page_size != null) params.set('page_size', String(filters.page_size))

  const qs = params.toString()
  return fetchJson<LeadListResponse>(`/admin/leads${qs ? `?${qs}` : ''}`)
}

export function getLead(id: string): Promise<LeadDetail> {
  return fetchJson<LeadDetail>(`/admin/leads/${id}`)
}

export function patchLead(id: string, body: LeadActionBody): Promise<LeadActionResponse> {
  return fetchJson<LeadActionResponse>(`/admin/leads/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}
