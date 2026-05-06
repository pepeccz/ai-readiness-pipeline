/**
 * C-3 — REQ-4: useUpdateSuggestionNote mutation hook
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

const mockFetchJson = vi.fn()
vi.mock('../../../admin/api/client', () => ({
  fetchJson: (...args: unknown[]) => mockFetchJson(...args),
}))

import { useUpdateSuggestionNote } from '../intake'

function wrapper(qc: QueryClient) {
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children)
}

describe('useUpdateSuggestionNote — C-3 (REQ-4)', () => {
  let qc: QueryClient

  beforeEach(() => {
    vi.clearAllMocks()
    qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  })

  it('C-3: calls PATCH /intake/{leadId}/suggestions/{suggestionId}/note with note', async () => {
    mockFetchJson.mockResolvedValue({
      id: 'sug-1',
      type: 'follow_up',
      text: 'Test',
      rationale: null,
      confidence: 0.9,
      priority: 'high',
      consultant_action: 'pending',
      consultant_note_text: 'Client noted X',
    })

    const { result } = renderHook(
      () => useUpdateSuggestionNote('lead-1', 'sug-1'),
      { wrapper: wrapper(qc) },
    )

    act(() => { result.current.mutate({ note: 'Client noted X' }) })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockFetchJson).toHaveBeenCalledWith(
      '/intake/lead-1/suggestions/sug-1/note',
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({ note: 'Client noted X' }),
      }),
    )
  })

  it('C-3: calls PATCH with null to clear the note', async () => {
    mockFetchJson.mockResolvedValue({
      id: 'sug-1',
      consultant_note_text: null,
    })

    const { result } = renderHook(
      () => useUpdateSuggestionNote('lead-1', 'sug-1'),
      { wrapper: wrapper(qc) },
    )

    act(() => { result.current.mutate({ note: null }) })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockFetchJson).toHaveBeenCalledWith(
      '/intake/lead-1/suggestions/sug-1/note',
      expect.objectContaining({ body: JSON.stringify({ note: null }) }),
    )
  })

  it('C-3: invalidates blockAnalysis cache on success', async () => {
    mockFetchJson.mockResolvedValue({ id: 'sug-1', consultant_note_text: 'ok' })
    const invalidateSpy = vi.spyOn(qc, 'invalidateQueries')

    const { result } = renderHook(
      () => useUpdateSuggestionNote('lead-1', 'sug-1', 'block-1-strategic'),
      { wrapper: wrapper(qc) },
    )

    act(() => { result.current.mutate({ note: 'ok' }) })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(invalidateSpy).toHaveBeenCalled()
  })
})
