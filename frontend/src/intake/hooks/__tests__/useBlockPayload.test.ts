/**
 * TC.3 — REQ-6: useBlockPayload extended return shape
 *
 * API now returns { payload, source: 'submitted'|'draft'|'none', updated_at }
 * Hook must expose these fields.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useBlockPayload } from '../../api/intake'

const mockFetchJson = vi.fn()
vi.mock('../../../admin/api/client', () => ({
  fetchJson: (...args: unknown[]) => mockFetchJson(...args),
}))

function makeWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children)
  }
}

beforeEach(() => {
  mockFetchJson.mockReset()
})

describe('useBlockPayload — REQ-6 extended shape', () => {
  it('exposes source=submitted when block has been submitted', async () => {
    mockFetchJson.mockResolvedValue({
      block_id: 'block-a',
      payload: { q1: 'yes' },
      source: 'submitted',
      updated_at: '2026-05-06T10:00:00Z',
    })

    const { result } = renderHook(
      () => useBlockPayload('lead-1', 'block-a'),
      { wrapper: makeWrapper() }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.source).toBe('submitted')
    expect(result.current.data?.payload).toEqual({ q1: 'yes' })
    expect(result.current.data?.updated_at).toBe('2026-05-06T10:00:00Z')
  })

  it('exposes source=draft when only draft exists', async () => {
    mockFetchJson.mockResolvedValue({
      block_id: 'block-a',
      payload: { q1: 'draft-val' },
      source: 'draft',
      updated_at: '2026-05-06T09:00:00Z',
    })

    const { result } = renderHook(
      () => useBlockPayload('lead-1', 'block-a'),
      { wrapper: makeWrapper() }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.source).toBe('draft')
    expect(result.current.data?.payload).toEqual({ q1: 'draft-val' })
  })

  it('returns isError for 404 (source=none case)', async () => {
    mockFetchJson.mockRejectedValue(Object.assign(new Error('No payload'), { status: 404 }))

    const { result } = renderHook(
      () => useBlockPayload('lead-1', 'block-a'),
      { wrapper: makeWrapper() }
    )

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
