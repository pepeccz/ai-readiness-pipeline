/**
 * SessionTimer — live HH:MM:SS timer display + control buttons (REQ-10).
 *
 * Receives timer state from useIntakeState (server source of truth).
 * Client ticks visually via setInterval — no server traffic on each tick.
 *
 * Tick logic (ADR-1, ADR-2):
 *   if is_running: display = accumulated_seconds + floor((Date.now() - started_at) / 1000)
 *   else:          display = accumulated_seconds
 *
 * Server writes happen ONLY on user action (pause/resume/reset/adjust).
 */

import { useState, useEffect } from 'react'
import { useTimerActions } from '../hooks/useTimerActions'
import { ConfirmModal } from '../../shared/components/ConfirmModal'
import { TimerAdjustModal } from './TimerAdjustModal'
import type { TimerState } from '../api/intake'

interface SessionTimerProps {
  leadId: string
  timer: TimerState
  sessionState: string
}

/** Format total seconds as HH:MM:SS (hours unbounded). */
function formatTime(totalSeconds: number): string {
  const s = Math.max(0, totalSeconds)
  const hours = Math.floor(s / 3600)
  const minutes = Math.floor((s % 3600) / 60)
  const seconds = s % 60
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`
}

export function SessionTimer({ leadId, timer, sessionState }: SessionTimerProps) {
  const [display, setDisplay] = useState<number>(timer.accumulated_seconds)
  const [confirmResetOpen, setConfirmResetOpen] = useState(false)
  const [adjustModalOpen, setAdjustModalOpen] = useState(false)

  const actions = useTimerActions(leadId)
  const disabled = sessionState === 'closed'

  // Tick effect: compute display from server-provided timer fields (Design §Tick)
  useEffect(() => {
    const compute = () => {
      if (timer.is_running && timer.started_at) {
        const startMs = new Date(timer.started_at).getTime()
        const nowMs = Date.now()
        setDisplay(timer.accumulated_seconds + Math.max(0, Math.floor((nowMs - startMs) / 1000)))
      } else {
        setDisplay(timer.accumulated_seconds)
      }
    }

    compute()
    if (!timer.is_running) return

    const id = setInterval(compute, 1000)
    return () => clearInterval(id)
  }, [timer.is_running, timer.started_at, timer.accumulated_seconds])

  const handleResetConfirm = () => {
    setConfirmResetOpen(false)
    actions.reset.mutate(undefined)
  }

  return (
    <div className="mt-4 p-4 rounded-lg border border-neutral-200 bg-white space-y-3">
      {/* Status + display */}
      <div className="flex items-center gap-2">
        <span
          data-testid="timer-status-dot"
          className={`inline-block w-2 h-2 rounded-full flex-shrink-0 ${
            timer.is_running ? 'bg-green-500' : 'bg-gray-400'
          }`}
          aria-hidden="true"
        />
        <span className="font-mono text-xl font-semibold text-neutral-800 tabular-nums">
          {formatTime(display)}
        </span>
      </div>

      {/* Control buttons */}
      <div className="flex flex-col gap-2">
        {/* Pause / Resume toggle */}
        {timer.is_running ? (
          <button
            type="button"
            disabled={disabled || actions.pause.isPending}
            onClick={() => actions.pause.mutate(undefined)}
            className="w-full px-3 py-1.5 text-sm font-medium rounded-md transition-colors
              bg-amber-100 text-amber-800 hover:bg-amber-200
              disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Pausar
          </button>
        ) : (
          <button
            type="button"
            disabled={disabled || actions.resume.isPending}
            onClick={() => actions.resume.mutate(undefined)}
            className="w-full px-3 py-1.5 text-sm font-medium rounded-md transition-colors
              bg-teal-100 text-teal-800 hover:bg-teal-200
              disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Reanudar
          </button>
        )}

        {/* Reset */}
        <button
          type="button"
          disabled={disabled || actions.reset.isPending}
          onClick={() => setConfirmResetOpen(true)}
          className="w-full px-3 py-1.5 text-sm font-medium rounded-md transition-colors
            bg-neutral-100 text-neutral-700 hover:bg-neutral-200
            disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Reiniciar
        </button>

        {/* Adjust */}
        <button
          type="button"
          disabled={disabled || actions.adjust.isPending}
          onClick={() => setAdjustModalOpen(true)}
          className="w-full px-3 py-1.5 text-sm font-medium rounded-md transition-colors
            bg-neutral-100 text-neutral-700 hover:bg-neutral-200
            disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Ajustar inicio
        </button>
      </div>

      {/* Reset confirm modal */}
      <ConfirmModal
        open={confirmResetOpen}
        title="¿Reiniciar temporizador?"
        body="Esto restablecerá el tiempo acumulado a cero y reiniciará el conteo. ¿Continuar?"
        confirmLabel="Confirmar"
        cancelLabel="Cancelar"
        variant="danger"
        onConfirm={handleResetConfirm}
        onCancel={() => setConfirmResetOpen(false)}
      />

      {/* Adjust modal */}
      <TimerAdjustModal
        open={adjustModalOpen}
        timer={timer}
        adjust={actions.adjust}
        onClose={() => setAdjustModalOpen(false)}
      />
    </div>
  )
}
