/**
 * TF.1 — useFinalClose: mutation hook calling POST /intake/{lead_id}/close
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

const mockFetchJson = vi.fn()
vi.mock('../../../admin/api/client', () => ({
  fetchJson: (...args: unknown[]) => mockFetchJson(...args),
}))

import { useFinalClose } from '../intake'

function wrapper(qc: QueryClient) {
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children)
}

describe('useFinalClose', () => {
  let qc: QueryClient

  beforeEach(() => {
    vi.clearAllMocks()
    qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  })

  it('calls POST /intake/{lead_id}/close without force', async () => {
    mockFetchJson.mockResolvedValue({ state: 'closed', lead_id: 'lead-1' })
    const { result } = renderHook(() => useFinalClose('lead-1'), { wrapper: wrapper(qc) })

    act(() => { result.current.mutate({}) })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockFetchJson).toHaveBeenCalledWith(
      '/intake/lead-1/close',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({}) })
    )
  })

  it('calls POST /intake/{lead_id}/close with force=true', async () => {
    mockFetchJson.mockResolvedValue({ state: 'closed', lead_id: 'lead-1' })
    const { result } = renderHook(() => useFinalClose('lead-1'), { wrapper: wrapper(qc) })

    act(() => { result.current.mutate({ force: true }) })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockFetchJson).toHaveBeenCalledWith(
      '/intake/lead-1/close',
      expect.objectContaining({ body: JSON.stringify({ force: true }) })
    )
  })

  it('invalidates lead and state queries on success', async () => {
    mockFetchJson.mockResolvedValue({ state: 'closed', lead_id: 'lead-1' })
    const invalidateSpy = vi.spyOn(qc, 'invalidateQueries')
    const { result } = renderHook(() => useFinalClose('lead-1'), { wrapper: wrapper(qc) })

    act(() => { result.current.mutate({}) })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ['lead', 'lead-1'] })
    )
    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ['intake', 'lead-1', 'state'] })
    )
  })
})
