/**
 * frontend/src/intake/hooks/useDeep.ts — T7.9
 *
 * Convenience hook combining DEEP list + patch + send mutations.
 * Abstracts the query layer from DeepReviewPanel.
 */

import { useState } from 'react'
import {
  useDeepBranches,
  useDeepPatch,
  useDeepSend,
  type DeepBranch,
  type DeepQuestion,
} from '../api/deep'

export interface UseDeepReturn {
  branches: DeepBranch[]
  isLoading: boolean
  error: Error | null
  editingBranchId: string | null
  editedQuestions: DeepQuestion[]
  startEditing: (branch: DeepBranch) => void
  cancelEditing: () => void
  updateQuestion: (index: number, text: string) => void
  saveEdits: (branchId: string) => Promise<void>
  sendToClient: (branchId: string) => Promise<void>
  isSaving: boolean
  isSending: boolean
}

export function useDeep(leadId: string): UseDeepReturn {
  const { data, isLoading, error } = useDeepBranches(leadId)
  const patchMutation = useDeepPatch(leadId)
  const sendMutation = useDeepSend(leadId)

  const [editingBranchId, setEditingBranchId] = useState<string | null>(null)
  const [editedQuestions, setEditedQuestions] = useState<DeepQuestion[]>([])

  const startEditing = (branch: DeepBranch) => {
    setEditingBranchId(branch.id)
    setEditedQuestions([...branch.generated_questions])
  }

  const cancelEditing = () => {
    setEditingBranchId(null)
    setEditedQuestions([])
  }

  const updateQuestion = (index: number, text: string) => {
    setEditedQuestions((prev) =>
      prev.map((q, i) => (i === index ? { ...q, text } : q))
    )
  }

  const saveEdits = async (branchId: string) => {
    await patchMutation.mutateAsync({ branchId, questions: editedQuestions })
    setEditingBranchId(null)
    setEditedQuestions([])
  }

  const sendToClient = async (branchId: string) => {
    await sendMutation.mutateAsync(branchId)
  }

  return {
    branches: data?.branches ?? [],
    isLoading,
    error: error as Error | null,
    editingBranchId,
    editedQuestions,
    startEditing,
    cancelEditing,
    updateQuestion,
    saveEdits,
    sendToClient,
    isSaving: patchMutation.isPending,
    isSending: sendMutation.isPending,
  }
}
