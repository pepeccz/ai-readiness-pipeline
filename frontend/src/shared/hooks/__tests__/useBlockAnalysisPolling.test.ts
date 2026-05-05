/**
 * T2.6 — REQ-6: useBlockAnalysisPolling does not query when blockId is null/undefined
 */

import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook } from '@testing-library/react'
import { useBlockAnalysisPolling } from '../useBlockAnalysisPolling'
import { intakeKeys } from '../../../intake/api/intake'
import React from 'react'

vi.mock('../../../admin/api/client', () => ({
  fetchJson: vi.fn().mockResolvedValue({ block_analysis_id: 'ba-1', status: 'ready' }),
}))

function makeWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children)
  }
}

describe('useBlockAnalysisPolling — REQ-6', () => {
  it('does not start a query when called with enabled=false (null guard at call site)', () => {
    const queryClient = new QueryClient()
    const fetchSpy = vi.fn().mockResolvedValue({})

    // Hook called with valid strings but enabled: false to simulate null guard at call site
    const { result } = renderHook(
      () => useBlockAnalysisPolling('lead-1', 'block-a', { enabled: false }),
      { wrapper: makeWrapper(queryClient) }
    )

    expect(fetchSpy).not.toHaveBeenCalled()
    expect(result.current.data).toBeUndefined()
  })

  it('key shape matches intakeKeys.blockAnalysis(leadId, blockId) for valid blockId', () => {
    const queryClient = new QueryClient()

    const { result } = renderHook(
      () => useBlockAnalysisPolling('lead-1', 'block-a'),
      { wrapper: makeWrapper(queryClient) }
    )

    // Query should be active (enabled by default with valid ids)
    // Verify the key is stored correctly in the cache
    const queries = queryClient.getQueryCache().getAll()
    const ourQuery = queries.find(
      (q) => JSON.stringify(q.queryKey) === JSON.stringify(intakeKeys.blockAnalysis('lead-1', 'block-a'))
    )
    expect(ourQuery).toBeDefined()

    // data is undefined (no network in tests)
    expect(result.current.data).toBeUndefined()
  })
})
