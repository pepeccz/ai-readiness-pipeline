/**
 * useJobPolling — TanStack Query v5 hook for polling background jobs.
 *
 * Polls GET /api/admin/assessments/{id}/jobs every 2 seconds while any job
 * is in 'pending' or 'running' state.  Stops automatically once all jobs
 * are in terminal state ('done' or 'failed').
 *
 * On job completion, invalidates ["assessment", id] so the editor re-renders
 * with updated llm_enriched_data / scores.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import type { JobRecord } from '../api/assessments'
import { getJobs } from '../api/assessments'

function hasActiveJobs(jobs: JobRecord[] | undefined): boolean {
  if (!jobs || jobs.length === 0) return false
  return jobs.some((j) => j.status === 'pending' || j.status === 'running')
}

export function useJobPolling(assessmentId: string) {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: ['jobs', assessmentId],
    queryFn: () => getJobs(assessmentId),
    staleTime: 1000,
    refetchInterval: (q) => {
      return hasActiveJobs(q.state.data) ? 2000 : false
    },
  })

  // When jobs finish (transition from active to all-terminal), invalidate the
  // assessment query so the editor picks up new enrichment data.
  useEffect(() => {
    const jobs = query.data
    if (!jobs || jobs.length === 0) return
    // Any job just completed (finished_at set, status done/failed)?
    const anyJustFinished = jobs.some(
      (j) => (j.status === 'done' || j.status === 'failed') && j.finished_at != null,
    )
    if (anyJustFinished && !hasActiveJobs(jobs)) {
      queryClient.invalidateQueries({ queryKey: ['assessment', assessmentId] })
    }
  }, [query.data, assessmentId, queryClient])

  return {
    jobs: query.data ?? [],
    isPolling: hasActiveJobs(query.data),
    refetch: query.refetch,
  }
}

/** Returns the most recent job of a given type, or undefined. */
export function useLatestJobOfType(
  assessmentId: string,
  type: string,
): JobRecord | undefined {
  const { jobs } = useJobPolling(assessmentId)
  return jobs.filter((j) => j.type === type)[0]
}
