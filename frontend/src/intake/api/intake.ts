/**
 * TanStack Query hooks and API functions for intake endpoints.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchJson } from '../../admin/api/client'
import type { CoreSchema, FormValues } from '../types/schema'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type SynthesisStatus = 'not_started' | 'pending' | 'ready' | 'failed'

// Timer types (REQ-8 / REQ-10)
export interface TimerState {
  started_at: string | null
  paused_at: string | null
  accumulated_seconds: number
  is_running: boolean
  server_now: string
}

export type TimerAction = 'pause' | 'resume' | 'reset' | 'adjust'

export interface TimerPatchPayload {
  action: TimerAction
  started_at?: string | null
}

export interface Session1Synthesis {
  summary: string
  key_insights: string[]
  recommendations: string[]
  hypothesis: string
  generated_at: string
  model: string
}

export interface IntakeState {
  lead_id: string
  state: string
  primary_area: string | null
  secondary_area: string | null
  areas_involved: string[]
  blocks_completed: string[]
  deep_branches_count: number
  session1_synthesis: Session1Synthesis | null
  session1_synthesis_status: SynthesisStatus
  synthesis_edited_json: Session1Synthesis | null
  synthesis_edited_at: string | null
  synthesis_last_exported_at: string | null
  synthesis_export_count: number
  /** Timer state — always present in the response (REQ-8) */
  timer: TimerState
}

export interface FinalClosePayload {
  force?: boolean
}

export interface AreaSelectionPayload {
  primary_area: string
  secondary_area?: string
  areas_involved?: string[]
}

export interface BlockSubmitPayload {
  payload: FormValues
  skipAnalysis?: boolean
}

export interface BlockSubmitResponse {
  block_analysis_id: string
  status: string
}

export interface BlockPayloadResponse {
  block_id: string
  payload: FormValues
  status: string
  /** 'submitted' | 'draft' | 'none' — returned by backend since REQ-6 */
  source: 'submitted' | 'draft' | 'none'
  updated_at: string | null
}

export interface Suggestion {
  id: string
  type: string
  text: string
  rationale: string | null
  confidence: number
  priority: string
  consultant_action: string
  consultant_note_text?: string | null
}

export interface BlockAnalysis {
  block_analysis_id: string
  status: string
  llm_output: {
    synthesis: string
    contradictions: Array<{ text: string; severity: string }>
    follow_ups: Array<{ text: string; rationale: string; priority: string; confidence: number }>
    preliminary_hypothesis: string | null
  } | null
  suggestions: Suggestion[]
  generated_at: string | null
}

// ---------------------------------------------------------------------------
// Query keys
//
// Cache invalidation convention (ADR-2):
//   - Each mutation that touches multiple surfaces issues multiple explicit
//     invalidateQueries calls — one per surface (NOT a single broad predicate).
//   - Use exact: false for hierarchical prefix invalidation (e.g. ['leads']).
//   - Narrow to the most specific key possible (e.g. blockAnalysis per block).
// ---------------------------------------------------------------------------

export const intakeKeys = {
  schema: (leadId: string, area?: string) => ['intake', leadId, 'schema', area] as const,
  state: (leadId: string) => ['intake', leadId, 'state'] as const,
  blockPayload: (leadId: string, blockId: string) =>
    ['intake', leadId, 'blocks', blockId, 'payload'] as const,
  blockAnalysis: (leadId: string, blockId: string) =>
    ['intake', leadId, 'blocks', blockId, 'analysis'] as const,
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export function useIntakeSchema(leadId: string, area?: string) {
  const params = area ? `?area=${area}` : ''
  return useQuery({
    queryKey: intakeKeys.schema(leadId, area),
    queryFn: () => fetchJson<CoreSchema>(`/intake/${leadId}/schema${params}`),
    enabled: Boolean(leadId),
    staleTime: 5 * 60 * 1000,
  })
}

export function useIntakeState(leadId: string) {
  return useQuery({
    queryKey: intakeKeys.state(leadId),
    queryFn: () => fetchJson<IntakeState>(`/intake/${leadId}/state`),
    enabled: Boolean(leadId),
    refetchInterval: (query) => {
      const status = query.state.data?.session1_synthesis_status
      return status === 'pending' ? 5000 : 30000
    },
    refetchOnWindowFocus: true,
  })
}

export function useFinalClose(leadId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: FinalClosePayload) =>
      fetchJson<IntakeState>(`/intake/${leadId}/close`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lead', leadId] })
      queryClient.invalidateQueries({ queryKey: intakeKeys.state(leadId) })
    },
  })
}

export function useBlockPayload(leadId: string, blockId: string | undefined) {
  return useQuery({
    queryKey: intakeKeys.blockPayload(leadId, blockId ?? ''),
    queryFn: () => fetchJson<BlockPayloadResponse>(`/intake/${leadId}/blocks/${blockId}/payload`),
    enabled: Boolean(leadId) && Boolean(blockId),
    retry: false,
  })
}

export function useAreaSelection(leadId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: AreaSelectionPayload) =>
      fetchJson<IntakeState>(`/intake/${leadId}/area-selection`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: intakeKeys.state(leadId) })
      queryClient.invalidateQueries({ queryKey: ['intake', leadId, 'schema'] })
    },
  })
}

export function useBlockAnalysis(leadId: string, blockId: string) {
  return useQuery({
    queryKey: intakeKeys.blockAnalysis(leadId, blockId),
    queryFn: () => fetchJson<BlockAnalysis>(`/intake/${leadId}/blocks/${blockId}/analysis`),
    enabled: Boolean(leadId) && Boolean(blockId),
    refetchInterval: (query) => {
      const data = query.state.data
      return data?.status === 'pending_analysis' ? 2000 : false
    },
  })
}

export function useSuggestionAction(leadId: string, blockId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ suggestionId, action }: { suggestionId: string; action: string }) =>
      fetchJson<Suggestion>(`/intake/${leadId}/suggestions/${suggestionId}/action`, {
        method: 'POST',
        body: JSON.stringify({ action }),
      }),
    onSuccess: () => {
      // Narrow invalidation to the specific block (ADR-2: explicit per-surface invalidation)
      queryClient.invalidateQueries({ queryKey: intakeKeys.blockAnalysis(leadId, blockId) })
    },
  })
}

export function useSession1Close(leadId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () =>
      fetchJson<IntakeState>(`/intake/${leadId}/session1/close`, {
        method: 'POST',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: intakeKeys.state(leadId) })
    },
  })
}

// ---------------------------------------------------------------------------
// C-3 — REQ-4: useUpdateSuggestionNote
// ---------------------------------------------------------------------------

export function useUpdateSuggestionNote(leadId: string, suggestionId: string, blockId?: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ note }: { note: string | null }) =>
      fetchJson<Suggestion>(`/intake/${leadId}/suggestions/${suggestionId}/note`, {
        method: 'PATCH',
        body: JSON.stringify({ note }),
      }),
    onSuccess: () => {
      if (blockId) {
        queryClient.invalidateQueries({ queryKey: intakeKeys.blockAnalysis(leadId, blockId) })
      }
    },
  })
}

// ---------------------------------------------------------------------------
// Timer API — REQ-10
// ---------------------------------------------------------------------------

export function patchTimer(leadId: string, payload: TimerPatchPayload): Promise<TimerState> {
  return fetchJson<TimerState>(`/intake/${leadId}/timer`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function useBlockSubmit(leadId: string, blockId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ payload, skipAnalysis }: BlockSubmitPayload) =>
      fetchJson<BlockSubmitResponse>(`/intake/${leadId}/blocks/${blockId}/submit`, {
        method: 'POST',
        body: JSON.stringify({ payload, skip_analysis: skipAnalysis ?? false }),
      }),
    onMutate: async () => {
      // Cancel in-flight queries to avoid overwriting optimistic update
      await queryClient.cancelQueries({ queryKey: intakeKeys.state(leadId) })
      // Snapshot for rollback
      const snapshot = queryClient.getQueryData<IntakeState>(intakeKeys.state(leadId))
      // Optimistic append with Set dedupe
      if (snapshot) {
        queryClient.setQueryData<IntakeState>(intakeKeys.state(leadId), {
          ...snapshot,
          blocks_completed: Array.from(new Set([...snapshot.blocks_completed, blockId])),
        })
      }
      return { snapshot }
    },
    onError: (_err, _vars, context) => {
      // Roll back to snapshot
      if (context?.snapshot !== undefined) {
        queryClient.setQueryData<IntakeState>(intakeKeys.state(leadId), context.snapshot)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: intakeKeys.state(leadId) })
      queryClient.invalidateQueries({ queryKey: intakeKeys.blockPayload(leadId, blockId) })
      queryClient.invalidateQueries({ queryKey: intakeKeys.blockAnalysis(leadId, blockId) })
    },
  })
}
