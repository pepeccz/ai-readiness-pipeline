/**
 * T2.1 — REQ-2: useBlockSubmit.onSuccess invalidates intakeKeys.blockAnalysis(leadId, blockId)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { QueryClient } from '@tanstack/react-query'
import { intakeKeys, useBlockSubmit } from '../../../intake/api/intake'
import { renderHook, act } from '@testing-library/react'
import { QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock fetchJson so the mutation succeeds without a real server
vi.mock('../../../admin/api/client', () => ({
  fetchJson: vi.fn().mockResolvedValue({ block_analysis_id: 'ba-1', status: 'pending_analysis' }),
}))

function makeWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children)
  }
}

describe('useBlockSubmit — REQ-2', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  })

  it('invalidates intakeKeys.blockAnalysis(leadId, blockId) on success', async () => {
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(() => useBlockSubmit('lead-1', 'block-a'), {
      wrapper: makeWrapper(queryClient),
    })

    await act(async () => {
      result.current.mutate({ answer: 'yes' })
      // Wait for the mutation to settle
      await new Promise((r) => setTimeout(r, 50))
    })

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: intakeKeys.blockAnalysis('lead-1', 'block-a'),
      })
    )
  })
})
