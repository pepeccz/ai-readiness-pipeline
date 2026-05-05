/**
 * TC.1 — REQ-5: useDraftAutosave
 *
 * Debounce 1.5s after last change. Flush on unmount. Flush on visibilitychange='hidden'.
 * On network failure → localStorage fallback.
 * Returns { savedAt, status: 'idle'|'saving'|'saved'|'error' }
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useDraftAutosave } from '../useDraftAutosave'

const mockFetchJson = vi.fn()
vi.mock('../../../admin/api/client', () => ({
  fetchJson: (...args: unknown[]) => mockFetchJson(...args),
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
      useDraftAutosave('lead-1', 'block-a', { q1: 'yes' }, false, true)
    )
    expect(result.current.status).toBe('idle')
    expect(result.current.savedAt).toBeNull()
  })

  it('does not save if isDirty is false', async () => {
    renderHook(() =>
      useDraftAutosave('lead-1', 'block-a', { q1: 'yes' }, false, true)
    )

    await act(async () => {
      vi.advanceTimersByTime(2000)
      await Promise.resolve()
    })

    expect(mockFetchJson).not.toHaveBeenCalled()
  })

  it('does not save when enabled=false', async () => {
    renderHook(() =>
      useDraftAutosave('lead-1', 'block-a', { q1: 'yes' }, true, false)
    )

    await act(async () => {
      vi.advanceTimersByTime(2000)
      await Promise.resolve()
    })

    expect(mockFetchJson).not.toHaveBeenCalled()
  })

  it('debounces: saves after 1.5s of inactivity when isDirty', async () => {
    const { result } = renderHook(() =>
      useDraftAutosave('lead-1', 'block-a', { q1: 'yes' }, true, true)
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

  it('resets debounce when values change before 1.5s: only one save after last change', async () => {
    const { rerender } = renderHook(
      ({ values }: { values: Record<string, unknown> }) =>
        useDraftAutosave('lead-1', 'block-a', values, true, true),
      { initialProps: { values: { q1: 'yes' } } }
    )

    // Immediately change values — resets any debounce started on mount
    await act(async () => {
      rerender({ values: { q1: 'no' } })
    })

    // 1.4s since last change — no call yet
    await act(async () => {
      vi.advanceTimersByTime(1400)
      await Promise.resolve()
    })
    expect(mockFetchJson).not.toHaveBeenCalled()

    // Past 1.5s — exactly one call
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
      useDraftAutosave('lead-1', 'block-a', { q1: 'fallback' }, true, true)
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
    mockFetchJson.mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() =>
      useDraftAutosave('lead-1', 'block-a', { q1: 'offline' }, true, true)
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
      useDraftAutosave('lead-1', 'block-a', { q1: 'unmount' }, true, true)
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
      useDraftAutosave('lead-1', 'block-a', { q1: 'vis' }, true, true)
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
