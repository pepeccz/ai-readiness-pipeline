/**
 * TimerAdjustModal — datetime-local input to adjust timer_started_at (REQ-10).
 *
 * Pre-filled with the current timer_started_at in local time.
 * Submits the new value as an ISO UTC string via the adjust mutation.
 * Surfaces 422 errors inline (e.g. "La hora ajustada produciría tiempo negativo").
 */

import { useState } from 'react'
import type { TimerState } from '../api/intake'
import type { UseTimerActionsResult } from '../hooks/useTimerActions'

interface TimerAdjustModalProps {
  open: boolean
  timer: TimerState
  adjust: UseTimerActionsResult['adjust']
  onClose: () => void
}

/** Format a UTC ISO string as a datetime-local value (local TZ). */
function toDatetimeLocal(isoUtc: string): string {
  const d = new Date(isoUtc)
  // Shift to local TZ offset for datetime-local input
  const pad = (n: number) => String(n).padStart(2, '0')
  const Y = d.getFullYear()
  const M = pad(d.getMonth() + 1)
  const D = pad(d.getDate())
  const h = pad(d.getHours())
  const m = pad(d.getMinutes())
  return `${Y}-${M}-${D}T${h}:${m}`
}

export function TimerAdjustModal({ open, timer, adjust, onClose }: TimerAdjustModalProps) {
  const defaultValue = timer.started_at ? toDatetimeLocal(timer.started_at) : ''
  const [value, setValue] = useState(defaultValue)
  const [error, setError] = useState<string | null>(null)

  if (!open) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!value) return
    setError(null)
    // Convert local datetime-local string to ISO UTC
    const localDate = new Date(value)
    const isoUtc = localDate.toISOString()

    adjust.mutate(
      { started_at: isoUtc },
      {
        onSuccess: () => {
          onClose()
        },
        onError: (err) => {
          // Surface 422 inline
          const msg = err?.message ?? String(err)
          setError(
            msg.includes('422') || msg.includes('negativo')
              ? 'La hora ajustada produciría tiempo negativo'
              : msg,
          )
        },
      },
    )
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      role="dialog"
      aria-modal="true"
      aria-labelledby="timer-adjust-modal-title"
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
        <h2
          id="timer-adjust-modal-title"
          className="text-base font-semibold text-gray-900 mb-4"
        >
          Ajustar inicio del temporizador
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="timer-adjust-input"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Nueva hora de inicio
            </label>
            <input
              id="timer-adjust-input"
              type="datetime-local"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm
                focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              required
            />
          </div>

          {error && (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border
                border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={adjust.isPending}
              className="px-4 py-2 text-sm font-medium rounded-md transition-colors
                bg-teal-600 text-white hover:bg-teal-700
                disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {adjust.isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
