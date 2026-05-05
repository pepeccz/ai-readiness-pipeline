/**
 * TD.3 — useSession1Close mutation hook calls POST /session1/close + invalidates state (REQ-1)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useSession1Close } from '../../api/intake'
import { intakeKeys } from '../../api/intake'

vi.mock('../../../admin/api/client', () => ({
  fetchJson: vi.fn().mockResolvedValue({ state: 'deep_pending' }),
  ApiError: class ApiError extends Error {},
}))

function wrapper(queryClient: QueryClient) {
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
}

describe('useSession1Close — REQ-1', () => {
  let qc: QueryClient
  let invalidateSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
    invalidateSpy = vi.spyOn(qc, 'invalidateQueries')
  })

  it('calls POST /intake/{leadId}/session1/close', async () => {
    const { fetchJson } = await import('../../../admin/api/client')
    const { result } = renderHook(() => useSession1Close('lead-1'), {
      wrapper: wrapper(qc),
    })

    await act(async () => {
      result.current.mutate()
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(fetchJson).toHaveBeenCalledWith(
      '/intake/lead-1/session1/close',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('invalidates intake state on success', async () => {
    const { result } = renderHook(() => useSession1Close('lead-1'), {
      wrapper: wrapper(qc),
    })

    await act(async () => {
      result.current.mutate()
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: intakeKeys.state('lead-1') }),
    )
  })
})
