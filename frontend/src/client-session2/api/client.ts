/**
 * client-session2/api/client.ts — Token-based API calls (no auth header).
 *
 * All requests use the signed URL token embedded in the URL path.
 * No session cookies, no Bearer headers.
 */

const API_BASE = '/api'

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`API error ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DeepQuestion {
  id: string
  text: string
  rationale?: string
}

export interface DeepBranchData {
  id: string
  branch_id: string
  generated_questions: DeepQuestion[]
  status: string
}

export interface DeepFormData {
  lead_id: string
  status: string
  deep_branches: DeepBranchData[]
}

export interface DeepSubmitPayload {
  branch_id: string
  responses: Record<string, string>
}

export interface DeepSubmitResponse {
  received: boolean
  branch_id: string
  status: string
  session_state: string
}

export interface ReportStatusResponse {
  status: 'pending' | 'ready'
  content?: string
  lead_id?: string
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function getDeepBranches(token: string): Promise<DeepFormData> {
  return fetchJson<DeepFormData>(`/client/deep/${token}`)
}

export async function submitDeepBranch(
  token: string,
  payload: DeepSubmitPayload
): Promise<DeepSubmitResponse> {
  return fetchJson<DeepSubmitResponse>(`/client/deep/${token}/submit`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getReportStatus(token: string): Promise<ReportStatusResponse> {
  const res = await fetch(`${API_BASE}/client/report/${token}`, {
    headers: { 'Content-Type': 'application/json' },
  })
  // 202 is also valid (pending)
  if (res.status === 202 || res.ok) {
    return res.json() as Promise<ReportStatusResponse>
  }
  const text = await res.text().catch(() => '')
  throw new Error(`API error ${res.status}: ${text}`)
}

export async function downloadReport(token: string): Promise<ReportStatusResponse> {
  const res = await fetch(`${API_BASE}/client/report/${token}/download`, {
    headers: { 'Content-Type': 'application/json' },
  })
  if (res.status === 202 || res.ok) {
    return res.json() as Promise<ReportStatusResponse>
  }
  const text = await res.text().catch(() => '')
  throw new Error(`API error ${res.status}: ${text}`)
}
