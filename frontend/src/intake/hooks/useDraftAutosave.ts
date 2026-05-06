/**
 * useDraftAutosave — REQ-5
 *
 * Debounces draft saves to the backend (1.5s after last change).
 * Flushes immediately on:
 *  - component unmount
 *  - document.visibilitychange === 'hidden'
 *
 * On network failure: writes to localStorage as offline fallback.
 *
 * TA.8 / ADR-2: accepts buildPayload() callable instead of raw values so the
 * wire shape is identical to the submit payload (nested composite).
 *
 * TA.8 / ADR-4: exposes errorKind discrimination per failure class.
 *
 * Returns { savedAt, status, errorKind, errorMessage }
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { fetchJson, ApiError } from '../../admin/api/client'
import type { FormValues } from '../types/schema'

export type DraftStatus = 'idle' | 'saving' | 'saved' | 'error'
export type ErrorKind = 'network' | 'http_client' | 'http_server' | 'unknown'

export interface DraftAutosaveResult {
  savedAt: Date | null
  status: DraftStatus
  errorKind: ErrorKind | null
  errorMessage: string | null
}

const LS_KEY = (leadId: string, blockId: string) => `draft_${leadId}_${blockId}`

/**
 * Classify a caught error per ADR-4.
 */
function classifyError(err: unknown): ErrorKind {
  if (err instanceof TypeError && /fetch|network|failed to fetch/i.test((err as TypeError).message)) {
    return 'network'
  }
  if (err instanceof ApiError) {
    if (err.status >= 400 && err.status < 500) return 'http_client'
    if (err.status >= 500) return 'http_server'
  }
  return 'unknown'
}

export function useDraftAutosave(
  leadId: string,
  blockId: string,
  buildPayload: () => FormValues,
  isDirty: boolean,
  enabled: boolean,
): DraftAutosaveResult {
  const [status, setStatus] = useState<DraftStatus>('idle')
  const [savedAt, setSavedAt] = useState<Date | null>(null)
  const [errorKind, setErrorKind] = useState<ErrorKind | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Keep refs to avoid stale closures in flush callbacks
  const buildPayloadRef = useRef(buildPayload)
  const isDirtyRef = useRef(isDirty)
  const enabledRef = useRef(enabled)
  buildPayloadRef.current = buildPayload
  isDirtyRef.current = isDirty
  enabledRef.current = enabled

  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const save = useCallback(async () => {
    if (!enabledRef.current || !isDirtyRef.current) return

    // Call buildPayload at flush time — wire shape = submit shape (ADR-2)
    const payload = buildPayloadRef.current()
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
      setErrorKind(null)
      setErrorMessage(null)
    } catch (err) {
      const kind = classifyError(err)
      setStatus('error')
      setErrorKind(kind)
      setErrorMessage(err instanceof Error ? err.message : String(err))
      // localStorage fallback already written above
    }
  }, [leadId, blockId])

  // Debounce: reset timer on every isDirty/enabled change
  useEffect(() => {
    if (!enabled || !isDirty) return

    if (debounceTimer.current) clearTimeout(debounceTimer.current)
    debounceTimer.current = setTimeout(() => {
      void save()
    }, 1500)

    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current)
    }
  }, [isDirty, enabled, save])

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

  return { savedAt, status, errorKind, errorMessage }
}
