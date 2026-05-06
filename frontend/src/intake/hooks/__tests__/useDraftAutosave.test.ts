/**
 * TC.1 — REQ-5: useDraftAutosave
 * TA.7 — REQ-2/ADR-2, REQ-4/ADR-4: buildPayload callable + errorKind classification
 *
 * Debounce 1.5s after last change. Flush on unmount. Flush on visibilitychange='hidden'.
 * On network failure → localStorage fallback.
 * Returns { savedAt, status, errorKind, errorMessage }
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useDraftAutosave } from '../useDraftAutosave'
import { ApiError } from '../../../admin/api/client'

const mockFetchJson = vi.fn()
vi.mock('../../../admin/api/client', () => ({
  fetchJson: (...args: unknown[]) => mockFetchJson(...args),
  ApiError: class ApiError extends Error {
    status: number
    code: string
    body?: unknown
    constructor(status: number, code: string, message: string, body?: unknown) {
      super(message)
      this.name = 'ApiError'
      this.status = status
      this.code = code
      this.body = body
    }
  },
}))

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: false })
  mockFetchJson.mockReset()
  mockFetchJson.mockResolvedValue({ payload: {}, updated_at: '2026-05-06T10:00:00Z' })
  localStorage.clear()
  Object.defineProperty(document, 'hidden', { value: false, configurable: true })
})

afterEach(async () => {
  // Drain any pending timers + microtasks so async side-effects don't bleed
  await act(async () => {
    vi.runAllTimers()
    await Promise.resolve()
  })
  vi.clearAllTimers()
  vi.clearAllMocks()
  vi.useRealTimers()
})

describe('useDraftAutosave', () => {
  it('starts in idle status', () => {
    const { result } = renderHook(() =>
      useDraftAutosave('lead-1', 'block-a', () => ({ q1: 'yes' }), false, true)
    )
    expect(result.current.status).toBe('idle')
    expect(result.current.savedAt).toBeNull()
  })

  it('does not save if isDirty is false', async () => {
    renderHook(() =>
      useDraftAutosave('lead-1', 'block-a', () => ({ q1: 'yes' }), false, true)
    )

    await act(async () => {
      vi.advanceTimersByTime(2000)
      await Promise.resolve()
    })

    expect(mockFetchJson).not.toHaveBeenCalled()
  })

  it('does not save when enabled=false', async () => {
    renderHook(() =>
      useDraftAutosave('lead-1', 'block-a', () => ({ q1: 'yes' }), true, false)
    )

    await act(async () => {
      vi.advanceTimersByTime(2000)
      await Promise.resolve()
    })

    expect(mockFetchJson).not.toHaveBeenCalled()
  })

  it('debounces: saves after 1.5s of inactivity when isDirty', async () => {
    const { result } = renderHook(() =>
      useDraftAutosave('lead-1', 'block-a', () => ({ q1: 'yes' }), true, true)
    )

    // Before debounce fires — no call yet
    await act(async () => {
      vi.advanceTimersByTime(1000)
      await Promise.resolve()
    })
    expect(mockFetchJson).not.toHaveBeenCalled()

    // Advance past 1.5s total
    await act(async () => {
      vi.advanceTimersByTime(600)
      await Promise.resolve()
    })

    expect(mockFetchJson).toHaveBeenCalledOnce()
    expect(mockFetchJson).toHaveBeenCalledWith(
      '/intake/lead-1/blocks/block-a/draft',
      expect.objectContaining({ method: 'PUT' })
    )
    expect(result.current.status).toBe('saved')
    expect(result.current.savedAt).not.toBeNull()
  })

  it('resets debounce when buildPayload changes before 1.5s: only one save after last change', async () => {
    // buildPayload is a ref-stable fn that returns different values
    let currentPayload = { q1: 'yes' }
    const buildPayload = () => currentPayload

    const { rerender } = renderHook(
      ({ isDirty }: { isDirty: boolean }) =>
        useDraftAutosave('lead-1', 'block-a', buildPayload, isDirty, true),
      { initialProps: { isDirty: true } }
    )

    // Immediately change — resets debounce
    await act(async () => {
      currentPayload = { q1: 'no' }
      rerender({ isDirty: true })
    })

    // 1.4s since last change — no call yet
    await act(async () => {
      vi.advanceTimersByTime(1400)
      await Promise.resolve()
    })
    expect(mockFetchJson).not.toHaveBeenCalled()

    // Past 1.5s — exactly one call with latest payload
    await act(async () => {
      vi.advanceTimersByTime(200)
      await Promise.resolve()
    })
    expect(mockFetchJson).toHaveBeenCalledOnce()
    expect(mockFetchJson).toHaveBeenCalledWith(
      '/intake/lead-1/blocks/block-a/draft',
      expect.objectContaining({ body: JSON.stringify({ payload: { q1: 'no' } }) })
    )
  })

  it('writes to localStorage on save (offline fallback)', async () => {
    renderHook(() =>
      useDraftAutosave('lead-1', 'block-a', () => ({ q1: 'fallback' }), true, true)
    )

    await act(async () => {
      vi.advanceTimersByTime(1600)
      await Promise.resolve()
    })

    const stored = localStorage.getItem('draft_lead-1_block-a')
    expect(stored).not.toBeNull()
    expect(JSON.parse(stored!)).toEqual({ q1: 'fallback' })
  })

  it('sets status=error and falls back to localStorage on network failure', async () => {
    mockFetchJson.mockRejectedValueOnce(new TypeError('Failed to fetch'))

    const { result } = renderHook(() =>
      useDraftAutosave('lead-1', 'block-a', () => ({ q1: 'offline' }), true, true)
    )

    await act(async () => {
      vi.advanceTimersByTime(1600)
      await Promise.resolve()
    })

    expect(result.current.status).toBe('error')
    const stored = localStorage.getItem('draft_lead-1_block-a')
    expect(stored).not.toBeNull()
    expect(JSON.parse(stored!)).toEqual({ q1: 'offline' })
  })

  it('flushes immediately on unmount when dirty', async () => {
    const { unmount } = renderHook(() =>
      useDraftAutosave('lead-1', 'block-a', () => ({ q1: 'unmount' }), true, true)
    )

    // Debounce hasn't fired yet
    await act(async () => { vi.advanceTimersByTime(500) })
    expect(mockFetchJson).not.toHaveBeenCalled()

    // Unmount triggers flush
    await act(async () => {
      unmount()
      await Promise.resolve()
    })

    expect(mockFetchJson).toHaveBeenCalledOnce()
  })

  it('flushes on visibilitychange=hidden', async () => {
    renderHook(() =>
      useDraftAutosave('lead-1', 'block-a', () => ({ q1: 'vis' }), true, true)
    )

    // Not yet debounced
    await act(async () => { vi.advanceTimersByTime(500) })
    expect(mockFetchJson).not.toHaveBeenCalled()

    // Simulate visibility hidden
    await act(async () => {
      Object.defineProperty(document, 'hidden', { value: true, configurable: true })
      document.dispatchEvent(new Event('visibilitychange'))
      await Promise.resolve()
    })

    expect(mockFetchJson).toHaveBeenCalledOnce()
  })
})

// ---------------------------------------------------------------------------
// TA.7 — errorKind classification (REQ-4 / ADR-4)
// ---------------------------------------------------------------------------

describe('useDraftAutosave — TA.7: errorKind classification (REQ-4)', () => {
  it('errorKind is network for TypeError (fetch failure)', async () => {
    mockFetchJson.mockRejectedValueOnce(new TypeError('Failed to fetch'))

    const { result } = renderHook(() =>
      useDraftAutosave('lead-1', 'block-err', () => ({ q1: 'v' }), true, true)
    )

    await act(async () => {
      vi.advanceTimersByTime(1600)
      await Promise.resolve()
    })

    expect(result.current.status).toBe('error')
    expect(result.current.errorKind).toBe('network')
  })

  it('errorKind is http_client for ApiError 4xx', async () => {
    const { ApiError: MockApiError } = await import('../../../admin/api/client')
    mockFetchJson.mockRejectedValueOnce(new MockApiError(422, 'validation', 'Unprocessable'))

    const { result } = renderHook(() =>
      useDraftAutosave('lead-1', 'block-err', () => ({ q1: 'v' }), true, true)
    )

    await act(async () => {
      vi.advanceTimersByTime(1600)
      await Promise.resolve()
    })

    expect(result.current.status).toBe('error')
    expect(result.current.errorKind).toBe('http_client')
  })

  it('errorKind is http_server for ApiError 5xx', async () => {
    const { ApiError: MockApiError } = await import('../../../admin/api/client')
    mockFetchJson.mockRejectedValueOnce(new MockApiError(503, 'unavailable', 'Service unavailable'))

    const { result } = renderHook(() =>
      useDraftAutosave('lead-1', 'block-err', () => ({ q1: 'v' }), true, true)
    )

    await act(async () => {
      vi.advanceTimersByTime(1600)
      await Promise.resolve()
    })

    expect(result.current.status).toBe('error')
    expect(result.current.errorKind).toBe('http_server')
  })

  it('errorKind is unknown for unexpected non-fetch errors', async () => {
    mockFetchJson.mockRejectedValueOnce(new RangeError('Unexpected error'))

    const { result } = renderHook(() =>
      useDraftAutosave('lead-1', 'block-err', () => ({ q1: 'v' }), true, true)
    )

    await act(async () => {
      vi.advanceTimersByTime(1600)
      await Promise.resolve()
    })

    expect(result.current.status).toBe('error')
    expect(result.current.errorKind).toBe('unknown')
  })

  it('return type includes errorKind (SC-4)', () => {
    const { result } = renderHook(() =>
      useDraftAutosave('lead-1', 'block-a', () => ({}), false, true)
    )
    expect('errorKind' in result.current).toBe(true)
    expect('errorMessage' in result.current).toBe(true)
  })

  it('hook calls buildPayload() at flush time, not a stale ref', async () => {
    let call = 0
    const buildPayload = vi.fn(() => ({ call: ++call }))

    renderHook(() =>
      useDraftAutosave('lead-1', 'block-a', buildPayload, true, true)
    )

    await act(async () => {
      vi.advanceTimersByTime(1600)
      await Promise.resolve()
    })

    expect(buildPayload).toHaveBeenCalled()
    expect(mockFetchJson).toHaveBeenCalledWith(
      '/intake/lead-1/blocks/block-a/draft',
      expect.objectContaining({ body: JSON.stringify({ payload: { call: 1 } }) })
    )
  })
})
