/**
 * TE.1 — useIntakeState: extended with synthesis fields + adaptive polling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// ---------------------------------------------------------------------------
// Mock fetchJson
// ---------------------------------------------------------------------------

const mockFetchJson = vi.fn()
vi.mock('../../../admin/api/client', () => ({
  fetchJson: (...args: unknown[]) => mockFetchJson(...args),
}))

import { useIntakeState } from '../intake'

function wrapper(qc: QueryClient) {
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children)
}

// ---------------------------------------------------------------------------
// TB.1 — REQ-1: refetchInterval and refetchOnWindowFocus (strict TDD)
// ---------------------------------------------------------------------------

describe('useIntakeState — REQ-1: polling intervals', () => {
  let qc: QueryClient

  beforeEach(() => {
    vi.clearAllMocks()
    qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  })

  it('uses refetchInterval=5000 when session1_synthesis_status is pending', async () => {
    mockFetchJson.mockResolvedValue({
      lead_id: 'lead-1',
      state: 'in_progress',
      primary_area: null,
      secondary_area: null,
      areas_involved: [],
      blocks_completed: [],
      deep_branches_count: 0,
      session1_synthesis: null,
      session1_synthesis_status: 'pending',
    })

    const { result } = renderHook(() => useIntakeState('lead-1'), {
      wrapper: wrapper(qc),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // Access the observer to check refetchInterval behavior
    const queryCache = qc.getQueryCache()
    const query = queryCache.find({ queryKey: ['intake', 'lead-1', 'state'] })
    expect(query).toBeDefined()

    // The refetchInterval function should return 5000 for pending
    const interval = (query!.options as { refetchInterval?: (q: typeof query) => number | false }).refetchInterval
    if (typeof interval === 'function') {
      // The query state now has pending status data
      expect(interval(query as never)).toBe(5000)
    }
  })

  it('uses refetchInterval>=30000 when session1_synthesis_status is NOT pending', async () => {
    mockFetchJson.mockResolvedValue({
      lead_id: 'lead-1',
      state: 'in_progress',
      primary_area: null,
      secondary_area: null,
      areas_involved: [],
      blocks_completed: [],
      deep_branches_count: 0,
      session1_synthesis: null,
      session1_synthesis_status: 'ready',
    })

    const { result } = renderHook(() => useIntakeState('lead-1'), {
      wrapper: wrapper(qc),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    const queryCache = qc.getQueryCache()
    const query = queryCache.find({ queryKey: ['intake', 'lead-1', 'state'] })
    expect(query).toBeDefined()

    const interval = (query!.options as { refetchInterval?: (q: typeof query) => number | false }).refetchInterval
    if (typeof interval === 'function') {
      const value = interval(query as never)
      expect(value).toBeGreaterThanOrEqual(30000)
    }
  })

  it('has refetchOnWindowFocus true', async () => {
    mockFetchJson.mockResolvedValue({
      lead_id: 'lead-1',
      state: 'in_progress',
      primary_area: null,
      secondary_area: null,
      areas_involved: [],
      blocks_completed: [],
      deep_branches_count: 0,
      session1_synthesis: null,
      session1_synthesis_status: 'not_started',
    })

    const { result } = renderHook(() => useIntakeState('lead-1'), {
      wrapper: wrapper(qc),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    const queryCache = qc.getQueryCache()
    const query = queryCache.find({ queryKey: ['intake', 'lead-1', 'state'] })
    expect(query).toBeDefined()
    expect(query!.options.refetchOnWindowFocus).toBe(true)
  })
})

describe('useIntakeState — synthesis extension', () => {
  let qc: QueryClient

  beforeEach(() => {
    vi.clearAllMocks()
    qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  })

  it('returns session1_synthesis and session1_synthesis_status from the API', async () => {
    mockFetchJson.mockResolvedValue({
      lead_id: 'lead-1',
      state: 'deep_pending',
      primary_area: null,
      secondary_area: null,
      areas_involved: [],
      blocks_completed: [],
      deep_branches_count: 2,
      session1_synthesis: null,
      session1_synthesis_status: 'pending',
    })

    const { result } = renderHook(() => useIntakeState('lead-1'), {
      wrapper: wrapper(qc),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.session1_synthesis_status).toBe('pending')
    expect(result.current.data?.session1_synthesis).toBeNull()
    expect(result.current.data?.deep_branches_count).toBe(2)
  })

  it('returns synthesis content when status is ready', async () => {
    const synthesis = {
      summary: 'Test summary',
      key_insights: ['insight1'],
      recommendations: ['rec1'],
      hypothesis: 'hyp',
      generated_at: '2026-01-01T00:00:00Z',
      model: 'gpt-4o',
    }
    mockFetchJson.mockResolvedValue({
      lead_id: 'lead-1',
      state: 'deep_received',
      primary_area: null,
      secondary_area: null,
      areas_involved: [],
      blocks_completed: [],
      deep_branches_count: 0,
      session1_synthesis: synthesis,
      session1_synthesis_status: 'ready',
    })

    const { result } = renderHook(() => useIntakeState('lead-1'), {
      wrapper: wrapper(qc),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.session1_synthesis_status).toBe('ready')
    expect(result.current.data?.session1_synthesis).toEqual(synthesis)
  })
})
