/**
 * TanStack Query hooks and API functions for intake endpoints.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchJson } from '../../admin/api/client'
import type { CoreSchema, FormValues } from '../types/schema'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface IntakeState {
  lead_id: string
  state: string
  primary_area: string | null
  secondary_area: string | null
  areas_involved: string[]
  blocks_completed: string[]
}

export interface AreaSelectionPayload {
  primary_area: string
  secondary_area?: string
  areas_involved?: string[]
}

export interface BlockSubmitPayload {
  payload: FormValues
}

export interface BlockSubmitResponse {
  block_analysis_id: string
  status: string
}

export interface BlockPayloadResponse {
  block_id: string
  payload: FormValues
  status: string
}

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const intakeKeys = {
  schema: (leadId: string, area?: string) => ['intake', leadId, 'schema', area] as const,
  state: (leadId: string) => ['intake', leadId, 'state'] as const,
  blockPayload: (leadId: string, blockId: string) =>
    ['intake', leadId, 'blocks', blockId, 'payload'] as const,
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
  })
}

export function useBlockPayload(leadId: string, blockId: string) {
  return useQuery({
    queryKey: intakeKeys.blockPayload(leadId, blockId),
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

export function useBlockSubmit(leadId: string, blockId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: FormValues) =>
      fetchJson<BlockSubmitResponse>(`/intake/${leadId}/blocks/${blockId}/submit`, {
        method: 'POST',
        body: JSON.stringify({ payload }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: intakeKeys.state(leadId) })
      queryClient.invalidateQueries({ queryKey: intakeKeys.blockPayload(leadId, blockId) })
    },
  })
}
