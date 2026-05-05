/**
 * T2.8 — REQ-8: useSuggestionAction invalidates only intakeKeys.blockAnalysis(leadId, blockId)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, act } from '@testing-library/react'
import { useSuggestionAction, intakeKeys } from '../../../intake/api/intake'
import React from 'react'

vi.mock('../../../admin/api/client', () => ({
  fetchJson: vi.fn().mockResolvedValue({ id: 'sug-1', type: 'apply', text: 'Do X' }),
}))

function makeWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children)
  }
}

describe('useSuggestionAction — REQ-8', () => {
  let queryClient: QueryClient
  let invalidateSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')
  })

  it('invalidates only intakeKeys.blockAnalysis(leadId, blockId)', async () => {
    const { result } = renderHook(
      () => useSuggestionAction('lead-1', 'block-a'),
      { wrapper: makeWrapper(queryClient) }
    )

    await act(async () => {
      result.current.mutate({ suggestionId: 'sug-1', action: 'apply' })
      await new Promise((r) => setTimeout(r, 50))
    })

    expect(invalidateSpy).toHaveBeenCalledTimes(1)
    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: intakeKeys.blockAnalysis('lead-1', 'block-a'),
      })
    )
  })

  it('does NOT call invalidateQueries with a broad key like ["intake"]', async () => {
    const { result } = renderHook(
      () => useSuggestionAction('lead-1', 'block-a'),
      { wrapper: makeWrapper(queryClient) }
    )

    await act(async () => {
      result.current.mutate({ suggestionId: 'sug-1', action: 'apply' })
      await new Promise((r) => setTimeout(r, 50))
    })

    const broadCall = invalidateSpy.mock.calls.find(
      (args) =>
        args[0] &&
        typeof args[0] === 'object' &&
        'queryKey' in args[0] &&
        Array.isArray((args[0] as { queryKey: unknown[] }).queryKey) &&
        (args[0] as { queryKey: unknown[] }).queryKey.length <= 2
    )
    expect(broadCall).toBeUndefined()
  })
})
