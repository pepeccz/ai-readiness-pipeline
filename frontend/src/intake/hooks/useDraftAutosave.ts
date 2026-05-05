/**
 * useDraftAutosave — REQ-5
 *
 * Debounces draft saves to the backend (1.5s after last change).
 * Flushes immediately on:
 *  - component unmount
 *  - document.visibilitychange === 'hidden'
 *
 * On network failure: writes to localStorage as offline fallback.
 * Returns { savedAt, status }
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { fetchJson } from '../../admin/api/client'

export type DraftStatus = 'idle' | 'saving' | 'saved' | 'error'

export interface DraftAutosaveResult {
  savedAt: Date | null
  status: DraftStatus
}

const LS_KEY = (leadId: string, blockId: string) => `draft_${leadId}_${blockId}`

export function useDraftAutosave(
  leadId: string,
  blockId: string,
  values: Record<string, unknown>,
  isDirty: boolean,
  enabled: boolean,
): DraftAutosaveResult {
  const [status, setStatus] = useState<DraftStatus>('idle')
  const [savedAt, setSavedAt] = useState<Date | null>(null)

  // Keep a ref to latest values/isDirty for flush calls (avoids stale closures)
  const valuesRef = useRef(values)
  const isDirtyRef = useRef(isDirty)
  const enabledRef = useRef(enabled)
  valuesRef.current = values
  isDirtyRef.current = isDirty
  enabledRef.current = enabled

  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const save = useCallback(async () => {
    if (!enabledRef.current || !isDirtyRef.current) return

    const payload = valuesRef.current
    // Write localStorage fallback unconditionally
    localStorage.setItem(LS_KEY(leadId, blockId), JSON.stringify(payload))

    setStatus('saving')
    try {
      await fetchJson(`/intake/${leadId}/blocks/${blockId}/draft`, {
        method: 'PUT',
        body: JSON.stringify({ payload }),
      })
      setStatus('saved')
      setSavedAt(new Date())
    } catch {
      setStatus('error')
      // localStorage fallback already written above
    }
  }, [leadId, blockId])

  // Debounce: reset timer on every values/isDirty change
  useEffect(() => {
    if (!enabled || !isDirty) return

    if (debounceTimer.current) clearTimeout(debounceTimer.current)
    debounceTimer.current = setTimeout(() => {
      void save()
    }, 1500)

    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current)
    }
  }, [values, isDirty, enabled, save])

  // Flush on unmount — only if dirty and enabled
  useEffect(() => {
    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current)
      if (enabledRef.current && isDirtyRef.current) {
        void save()
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Flush on visibilitychange=hidden
  useEffect(() => {
    function handleVisibility() {
      if (document.hidden) {
        if (debounceTimer.current) clearTimeout(debounceTimer.current)
        void save()
      }
    }
    document.addEventListener('visibilitychange', handleVisibility)
    return () => document.removeEventListener('visibilitychange', handleVisibility)
  }, [save])

  return { savedAt, status }
}
