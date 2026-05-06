/**
 * frontend/src/intake/hooks/useSession1Synthesize.ts — REQ-3
 *
 * TanStack mutation hook for triggering a session 1 synthesis retry.
 *
 * Endpoint: POST /api/intake/{leadId}/session1/synthesize
 * On success: invalidates ['intake-state', leadId] to trigger a re-fetch.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchJson } from '../../admin/api/client'

interface SynthesizeResponse {
  message: string
}

export function useSession1Synthesize(leadId: string) {
  const queryClient = useQueryClient()

  return useMutation<SynthesizeResponse, Error>({
    mutationFn: () =>
      fetchJson<SynthesizeResponse>(`/intake/${leadId}/session1/synthesize`, {
        method: 'POST',
      }),
    onSuccess: () => {
      // Invalidate intake state so the panel re-polls and shows updated status
      queryClient.invalidateQueries({ queryKey: ['intake-state', leadId] })
    },
  })
}
