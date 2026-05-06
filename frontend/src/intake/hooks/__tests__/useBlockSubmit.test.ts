/**
 * TB.3 — REQ-2: useBlockSubmit optimistic update, rollback, and invalidation
 * T2.1 — REQ-2: useBlockSubmit.onSuccess invalidates intakeKeys.blockAnalysis(leadId, blockId)
 * B-1  — REQ-2: useBlockSubmit skipAnalysis flag forwarded in POST body
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { QueryClient } from '@tanstack/react-query'
import { intakeKeys, useBlockSubmit } from '../../../intake/api/intake'
import type { IntakeState } from '../../../intake/api/intake'
import { renderHook, act } from '@testing-library/react'
import { QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// ---------------------------------------------------------------------------
// Shared mock — can be overridden per-test
// ---------------------------------------------------------------------------
const mockFetchJson = vi.fn()
vi.mock('../../../admin/api/client', () => ({
  fetchJson: (...args: unknown[]) => mockFetchJson(...args),
}))

function makeWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children)
  }
}

const baseState: IntakeState = {
  lead_id: 'lead-1',
  state: 'in_progress',
  primary_area: null,
  secondary_area: null,
  areas_involved: [],
  blocks_completed: ['block-existing'],
  deep_branches_count: 0,
  session1_synthesis: null,
  session1_synthesis_status: 'not_started',
}

describe('useBlockSubmit — REQ-2: optimistic update + rollback + invalidation', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    vi.clearAllMocks()
    mockFetchJson.mockResolvedValue({ block_analysis_id: 'ba-1', status: 'pending_analysis' })
    queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
    // Seed the state cache so onMutate has something to snapshot
    queryClient.setQueryData(intakeKeys.state('lead-1'), baseState)
  })

  it('onMutate optimistically appends blockId to blocks_completed (Set dedupe)', async () => {
    const { result } = renderHook(() => useBlockSubmit('lead-1', 'block-a'), {
      wrapper: makeWrapper(queryClient),
    })

    await act(async () => {
      result.current.mutate({ payload: { answer: 'yes' } })
      await new Promise((r) => setTimeout(r, 10))
    })

    // After onMutate fires (before settle), cache should have block-a appended
    const cached = queryClient.getQueryData<IntakeState>(intakeKeys.state('lead-1'))
    expect(cached?.blocks_completed).toContain('block-a')
    expect(cached?.blocks_completed).toContain('block-existing')
  })

  it('onMutate deduplicates if blockId already in blocks_completed', async () => {
    // Seed with block-a already completed
    queryClient.setQueryData(intakeKeys.state('lead-1'), {
      ...baseState,
      blocks_completed: ['block-a', 'block-existing'],
    })

    const { result } = renderHook(() => useBlockSubmit('lead-1', 'block-a'), {
      wrapper: makeWrapper(queryClient),
    })

    await act(async () => {
      result.current.mutate({ payload: { answer: 'yes' } })
      await new Promise((r) => setTimeout(r, 10))
    })

    const cached = queryClient.getQueryData<IntakeState>(intakeKeys.state('lead-1'))
    const count = cached?.blocks_completed.filter((b) => b === 'block-a').length ?? 0
    expect(count).toBe(1)
  })

  it('onError rolls back to snapshot when mutation fails', async () => {
    mockFetchJson.mockRejectedValue(new Error('Server error'))

    const { result } = renderHook(() => useBlockSubmit('lead-1', 'block-a'), {
      wrapper: makeWrapper(queryClient),
    })

    await act(async () => {
      result.current.mutate({ payload: { answer: 'yes' } })
      await new Promise((r) => setTimeout(r, 100))
    })

    // After error, cache should be rolled back to original snapshot
    const cached = queryClient.getQueryData<IntakeState>(intakeKeys.state('lead-1'))
    expect(cached?.blocks_completed).not.toContain('block-a')
    expect(cached?.blocks_completed).toEqual(['block-existing'])
  })

  it('onSuccess invalidates intakeKeys.state', async () => {
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(() => useBlockSubmit('lead-1', 'block-a'), {
      wrapper: makeWrapper(queryClient),
    })

    await act(async () => {
      result.current.mutate({ payload: { answer: 'yes' } })
      await new Promise((r) => setTimeout(r, 50))
    })

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: intakeKeys.state('lead-1'),
      })
    )
  })

  // B-1: skipAnalysis forwarded as skip_analysis in POST body
  it('B-1: mutate with skipAnalysis=true sends skip_analysis:true in POST body', async () => {
    const { result } = renderHook(() => useBlockSubmit('lead-1', 'block-a'), {
      wrapper: makeWrapper(queryClient),
    })

    await act(async () => {
      result.current.mutate({ payload: { answer: 'yes' }, skipAnalysis: true })
      await new Promise((r) => setTimeout(r, 50))
    })

    expect(mockFetchJson).toHaveBeenCalledWith(
      expect.stringContaining('/submit'),
      expect.objectContaining({
        body: expect.stringContaining('"skip_analysis":true'),
      }),
    )
  })

  it('B-1: mutate without skipAnalysis sends skip_analysis:false in POST body', async () => {
    const { result } = renderHook(() => useBlockSubmit('lead-1', 'block-a'), {
      wrapper: makeWrapper(queryClient),
    })

    await act(async () => {
      result.current.mutate({ payload: { answer: 'yes' } })
      await new Promise((r) => setTimeout(r, 50))
    })

    expect(mockFetchJson).toHaveBeenCalledWith(
      expect.stringContaining('/submit'),
      expect.objectContaining({
        body: expect.stringContaining('"skip_analysis":false'),
      }),
    )
  })

  it('onSuccess also invalidates intakeKeys.blockAnalysis(leadId, blockId)', async () => {
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(() => useBlockSubmit('lead-1', 'block-a'), {
      wrapper: makeWrapper(queryClient),
    })

    await act(async () => {
      result.current.mutate({ payload: { answer: 'yes' } })
      await new Promise((r) => setTimeout(r, 50))
    })

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: intakeKeys.blockAnalysis('lead-1', 'block-a'),
      })
    )
  })
})
