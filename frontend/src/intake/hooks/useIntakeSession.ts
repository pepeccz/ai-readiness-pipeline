/**
 * useIntakeSession — loads and tracks the intake session state.
 *
 * Wraps useIntakeState from the API layer and provides derived helpers.
 */

import { useIntakeState } from '../api/intake'

export function useIntakeSession(leadId: string) {
  const query = useIntakeState(leadId)

  const isBlockCompleted = (blockId: string): boolean => {
    return query.data?.blocks_completed?.includes(blockId) ?? false
  }

  const hasAreaSelected = (): boolean => {
    return Boolean(query.data?.primary_area && query.data.primary_area !== 'not_set')
  }

  return {
    session: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    isBlockCompleted,
    hasAreaSelected,
    refetch: query.refetch,
  }
}
