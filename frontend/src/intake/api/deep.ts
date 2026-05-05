/**
 * frontend/src/intake/api/deep.ts — T7.9
 *
 * TanStack Query hooks and API functions for DEEP branch endpoints.
 *
 * Endpoints:
 *   GET   /api/intake/{leadId}/deep
 *   PATCH /api/intake/{leadId}/deep/{branchId}
 *   POST  /api/intake/{leadId}/deep/{branchId}/send
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchJson } from '../../admin/api/client'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DeepQuestion {
  id: string
  text: string
  rationale: string
  type: 'textarea' | 'single_choice' | 'multi_choice'
  options: { value: string; label: string }[] | null
  required: boolean
}

export interface DeepBranch {
  id: string
  branch_id: string
  status: string
  generated_questions: DeepQuestion[]
  consultant_edits: DeepQuestion[] | null
  consultant_reviewed_at: string | null
  sent_to_client_at: string | null
}

export interface DeepListResponse {
  lead_id: string
  branches: DeepBranch[]
}

export interface DeepSendResponse {
  signed_url: string
  sent_to: string
  expires_at: string
}

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const deepKeys = {
  list: (leadId: string) => ['intake', leadId, 'deep'] as const,
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export function useDeepBranches(leadId: string) {
  return useQuery({
    queryKey: deepKeys.list(leadId),
    queryFn: () => fetchJson<DeepListResponse>(`/intake/${leadId}/deep`),
    enabled: Boolean(leadId),
  })
}

export function useDeepPatch(leadId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ branchId, questions }: { branchId: string; questions: DeepQuestion[] }) =>
      fetchJson<DeepBranch>(`/intake/${leadId}/deep/${branchId}`, {
        method: 'PATCH',
        body: JSON.stringify({ questions }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: deepKeys.list(leadId) })
    },
  })
}

export function useDeepSend(leadId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (branchId: string) =>
      fetchJson<DeepSendResponse>(`/intake/${leadId}/deep/${branchId}/send`, {
        method: 'POST',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: deepKeys.list(leadId) })
    },
  })
}
