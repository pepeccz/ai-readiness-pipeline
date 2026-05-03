import { QueryClient } from '@tanstack/react-query'
import { ApiError } from './api/client'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        // Don't retry on 401 — it's a handled auth state transition, not a transient error
        if (error instanceof ApiError && error.status === 401) {
          return false
        }
        return failureCount < 2
      },
      staleTime: 30_000,
      // Don't refetch when user switches tabs — editors shouldn't surprise the consultant
      refetchOnWindowFocus: false,
    },
  },
})
