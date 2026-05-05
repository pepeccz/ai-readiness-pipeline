/**
 * useBlockAnalysisPolling — polls GET /api/intake/{leadId}/blocks/{blockId}/analysis
 * every 2s while status=pending_analysis, stops when ready or failed.
 *
 * Signature requires non-null blockId. Callers MUST guard with:
 *   {blockId && <AnalysisPanel blockId={blockId} ... />}
 * This ensures the query key always matches intakeKeys.blockAnalysis(leadId, blockId)
 * used in invalidations (ADR-4, REQ-6).
 */

import { useQuery } from '@tanstack/react-query'
import { fetchJson } from '../../admin/api/client'
import type { BlockAnalysis } from '../../intake/api/intake'
import { intakeKeys } from '../../intake/api/intake'

interface UseBlockAnalysisPollingOptions {
  enabled?: boolean
}

export function useBlockAnalysisPolling(
  leadId: string,
  blockId: string,
  options: UseBlockAnalysisPollingOptions = {}
) {
  const { enabled = true } = options
  return useQuery({
    queryKey: intakeKeys.blockAnalysis(leadId, blockId),
    queryFn: () =>
      fetchJson<BlockAnalysis>(`/intake/${leadId}/blocks/${blockId}/analysis`),
    enabled: enabled && Boolean(leadId) && Boolean(blockId),
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return false
      return data.status === 'pending_analysis' ? 2000 : false
    },
    retry: false,
  })
}
