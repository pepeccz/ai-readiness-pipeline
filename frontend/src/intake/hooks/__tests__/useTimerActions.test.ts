/**
 * useTimerActions — TDD RED tests (REQ-10)
 *
 * Tests written BEFORE implementation. All should fail on first run.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

const mockFetchJson = vi.fn()
vi.mock('../../../admin/api/client', () => ({
  fetchJson: (...args: unknown[]) => mockFetchJson(...args),
  ApiError: class ApiError extends Error {},
}))

function makeWrapper(qc: QueryClient) {
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children)
}

const fakeTimerState = {
  started_at: null,
  paused_at: '2026-05-07T10:00:00Z',
  accumulated_seconds: 120,
  is_running: false,
  server_now: '2026-05-07T10:00:00Z',
}

describe('useTimerActions — REQ-10', () => {
  let qc: QueryClient
  let invalidateSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    vi.clearAllMocks()
    mockFetchJson.mockResolvedValue(fakeTimerState)
    qc = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    })
    invalidateSpy = vi.spyOn(qc, 'invalidateQueries')
  })

  it('pause mutation calls PATCH /intake/{leadId}/timer with action=pause', async () => {
    const { useTimerActions } = await import('../useTimerActions')
    const { result } = renderHook(() => useTimerActions('lead-1'), {
      wrapper: makeWrapper(qc),
    })

    await act(async () => {
      result.current.pause.mutate(undefined)
    })

    await waitFor(() => expect(result.current.pause.isSuccess).toBe(true))

    expect(mockFetchJson).toHaveBeenCalledWith(
      '/intake/lead-1/timer',
      expect.objectContaining({
        method: 'PATCH',
        body: expect.stringContaining('"action":"pause"'),
      }),
    )
  })

  it('resume mutation calls PATCH with action=resume', async () => {
    const { useTimerActions } = await import('../useTimerActions')
    const { result } = renderHook(() => useTimerActions('lead-1'), {
      wrapper: makeWrapper(qc),
    })

    await act(async () => {
      result.current.resume.mutate(undefined)
    })

    await waitFor(() => expect(result.current.resume.isSuccess).toBe(true))

    expect(mockFetchJson).toHaveBeenCalledWith(
      '/intake/lead-1/timer',
      expect.objectContaining({
        body: expect.stringContaining('"action":"resume"'),
      }),
    )
  })

  it('reset mutation calls PATCH with action=reset', async () => {
    const { useTimerActions } = await import('../useTimerActions')
    const { result } = renderHook(() => useTimerActions('lead-1'), {
      wrapper: makeWrapper(qc),
    })

    await act(async () => {
      result.current.reset.mutate(undefined)
    })

    await waitFor(() => expect(result.current.reset.isSuccess).toBe(true))

    expect(mockFetchJson).toHaveBeenCalledWith(
      '/intake/lead-1/timer',
      expect.objectContaining({
        body: expect.stringContaining('"action":"reset"'),
      }),
    )
  })

  it('adjust mutation calls PATCH with action=adjust and started_at', async () => {
    const { useTimerActions } = await import('../useTimerActions')
    const { result } = renderHook(() => useTimerActions('lead-1'), {
      wrapper: makeWrapper(qc),
    })

    const newStart = '2026-05-07T09:00:00Z'
    await act(async () => {
      result.current.adjust.mutate({ started_at: newStart })
    })

    await waitFor(() => expect(result.current.adjust.isSuccess).toBe(true))

    expect(mockFetchJson).toHaveBeenCalledWith(
      '/intake/lead-1/timer',
      expect.objectContaining({
        body: expect.stringContaining('"action":"adjust"'),
      }),
    )
    expect(mockFetchJson).toHaveBeenCalledWith(
      '/intake/lead-1/timer',
      expect.objectContaining({
        body: expect.stringContaining(newStart),
      }),
    )
  })

  it('onSuccess invalidates intake-state query key', async () => {
    const { useTimerActions } = await import('../useTimerActions')
    const { result } = renderHook(() => useTimerActions('lead-1'), {
      wrapper: makeWrapper(qc),
    })

    await act(async () => {
      result.current.pause.mutate(undefined)
    })

    await waitFor(() => expect(result.current.pause.isSuccess).toBe(true))

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: expect.arrayContaining(['intake', 'lead-1', 'state']),
      }),
    )
  })
})
