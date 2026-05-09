/**
 * session2.ts — API wrappers for Sesión 2 prep endpoints.
 *
 * Backend endpoints will be implemented in PR7a. Tests mock these functions.
 * API shape defined in Session2PrepData type below.
 */

import { fetchJson } from '../../../admin/api/client'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type RiskProfile = 'low' | 'medium' | 'high' | 'critical'
export type BlockStatus = 'ready' | 'insufficient_data' | 'pending'
export type Severity = 'high' | 'med' | 'low'
export type Priority = 'high' | 'med' | 'low'

export interface Session2PrepData {
  session: {
    state: string
    composite_score: number | null
    composite_level: number | null
    composite_level_name: string | null
    risk_profile: RiskProfile | null
  }
  per_block: Array<{
    block_id: string
    block_title: string
    score: number | null
    level: number | null
    level_name: string | null
    status: BlockStatus
    missing_fields: string[]
  }>
  contradictions: Array<{
    finding_id: string
    block_id: string
    text: string
    severity: Severity
    dismissed: boolean
  }>
  follow_ups: Array<{
    finding_id: string
    block_id: string
    text: string
    priority: Priority
    confidence: number
    dismissed: boolean
  }>
}

export interface DismissResponse {
  ok: boolean
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * GET /intake/{leadId}/session2/prep
 * Returns aggregated scorecard, findings, and follow-ups for Sesión 2 prep.
 * Backend implemented in PR7a.
 */
export function getSession2Prep(leadId: string): Promise<Session2PrepData> {
  return fetchJson<Session2PrepData>(`/intake/${leadId}/session2/prep`)
}

/**
 * POST /intake/{leadId}/session2/dismissed-findings
 * Dismisses a finding (contradiction or follow-up) for a block.
 * Backend implemented in PR7a.
 */
export function dismissFinding(
  leadId: string,
  blockId: string,
  findingId: string,
): Promise<DismissResponse> {
  return fetchJson<DismissResponse>(`/intake/${leadId}/session2/dismissed-findings`, {
    method: 'POST',
    body: JSON.stringify({ block_id: blockId, finding_id: findingId }),
  })
}

/**
 * DELETE /intake/{leadId}/session2/dismissed-findings/{findingId}
 * Restores a previously dismissed finding.
 * Backend implemented in PR7a.
 */
export function restoreFinding(
  leadId: string,
  blockId: string,
  findingId: string,
): Promise<DismissResponse> {
  return fetchJson<DismissResponse>(
    `/intake/${leadId}/session2/dismissed-findings/${findingId}`,
    {
      method: 'DELETE',
      body: JSON.stringify({ block_id: blockId }),
    },
  )
}
