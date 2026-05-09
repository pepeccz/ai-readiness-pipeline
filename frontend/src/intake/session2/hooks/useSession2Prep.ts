/**
 * useSession2Prep — React hook for Sesión 2 prep data.
 *
 * Wraps getSession2Prep with TanStack Query (project pattern from useIntakeState).
 * Polls every 30s; refetches on window focus.
 */

import { useQuery } from '@tanstack/react-query'
import { getSession2Prep } from '../api/session2'
import type { Session2PrepData } from '../api/session2'

export const session2Keys = {
  prep: (leadId: string) => ['session2', leadId, 'prep'] as const,
}

export function useSession2Prep(leadId: string) {
  return useQuery<Session2PrepData>({
    queryKey: session2Keys.prep(leadId),
    queryFn: () => getSession2Prep(leadId),
    enabled: Boolean(leadId),
    staleTime: 30 * 1000,
    refetchOnWindowFocus: true,
    retry: false,
  })
}
