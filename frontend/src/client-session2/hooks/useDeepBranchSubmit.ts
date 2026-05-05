/**
 * useDeepBranchSubmit — hook to submit a single DEEP branch's responses.
 *
 * Returns the mutation function + loading/error state.
 */

import { useState } from 'react'
import { submitDeepBranch } from '../api/client'
import type { DeepSubmitResponse } from '../api/client'

interface UseDeepBranchSubmitResult {
  submit: (branchId: string, responses: Record<string, string>) => Promise<DeepSubmitResponse | null>
  isSubmitting: boolean
  error: string | null
}

export function useDeepBranchSubmit(token: string): UseDeepBranchSubmitResult {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit(
    branchId: string,
    responses: Record<string, string>
  ): Promise<DeepSubmitResponse | null> {
    setIsSubmitting(true)
    setError(null)
    try {
      const result = await submitDeepBranch(token, { branch_id: branchId, responses })
      return result
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error al enviar las respuestas.'
      setError(msg)
      return null
    } finally {
      setIsSubmitting(false)
    }
  }

  return { submit, isSubmitting, error }
}
