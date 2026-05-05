/**
 * useBlockAnalysisPolling — polls GET /api/intake/{leadId}/blocks/{blockId}/analysis
 * every 2s while status=pending_analysis, stops when ready or failed.
 */

import { useQuery } from '@tanstack/react-query'
import { fetchJson } from '../../admin/api/client'
import type { BlockAnalysis } from '../../intake/api/intake'

export function useBlockAnalysisPolling(leadId: string, blockId: string | null) {
  return useQuery({
    queryKey: ['intake', leadId, 'blocks', blockId, 'analysis'],
    queryFn: () =>
      fetchJson<BlockAnalysis>(`/intake/${leadId}/blocks/${blockId}/analysis`),
    enabled: Boolean(leadId) && Boolean(blockId),
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return false
      return data.status === 'pending_analysis' ? 2000 : false
    },
    retry: false,
  })
}
