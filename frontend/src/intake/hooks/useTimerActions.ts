/**
 * useTimerActions — wraps PATCH /intake/{leadId}/timer mutations (REQ-10).
 *
 * Each action (pause/resume/reset/adjust) is a separate useMutation.
 * On success, invalidates the intake-state query so the timer display reconciles.
 *
 * Design ADR-4: single PATCH endpoint with action discriminator.
 * Design ADR-8: server is single source of truth — no localStorage.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { patchTimer } from '../api/intake'
import { intakeKeys } from '../api/intake'
import type { TimerState } from '../api/intake'

export interface UseTimerActionsResult {
  pause: ReturnType<typeof useMutation<TimerState, Error, undefined>>
  resume: ReturnType<typeof useMutation<TimerState, Error, undefined>>
  reset: ReturnType<typeof useMutation<TimerState, Error, undefined>>
  adjust: ReturnType<typeof useMutation<TimerState, Error, { started_at: string }>>
  isPending: boolean
}

export function useTimerActions(leadId: string): UseTimerActionsResult {
  const queryClient = useQueryClient()

  const invalidateState = () => {
    queryClient.invalidateQueries({ queryKey: intakeKeys.state(leadId) })
  }

  const pause = useMutation<TimerState, Error, undefined>({
    mutationFn: () => patchTimer(leadId, { action: 'pause' }),
    onSuccess: invalidateState,
  })

  const resume = useMutation<TimerState, Error, undefined>({
    mutationFn: () => patchTimer(leadId, { action: 'resume' }),
    onSuccess: invalidateState,
  })

  const reset = useMutation<TimerState, Error, undefined>({
    mutationFn: () => patchTimer(leadId, { action: 'reset' }),
    onSuccess: invalidateState,
  })

  const adjust = useMutation<TimerState, Error, { started_at: string }>({
    mutationFn: ({ started_at }) => patchTimer(leadId, { action: 'adjust', started_at }),
    onSuccess: invalidateState,
  })

  const isPending =
    pause.isPending || resume.isPending || reset.isPending || adjust.isPending

  return { pause, resume, reset, adjust, isPending }
}
