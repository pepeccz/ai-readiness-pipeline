import { Outlet } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { ErrorBoundary } from 'react-error-boundary'
import { queryClient } from './queryClient'
import { AuthProvider } from './AuthContext'
import { ErrorFallback } from '../shared/components/ErrorFallback'

/**
 * Root layout for all /admin/* and /intake/* routes.
 * Provides TanStack Query, AuthContext, and a top-level ErrorBoundary.
 *
 * REQ-7 / ADR-5: ErrorBoundary wraps the Outlet so any render error in the
 * authenticated tree shows the ErrorFallback instead of a blank screen.
 */
export function AdminLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <div className="min-h-screen bg-gray-50">
          <ErrorBoundary FallbackComponent={ErrorFallback}>
            <Outlet />
          </ErrorBoundary>
        </div>
      </AuthProvider>
    </QueryClientProvider>
  )
}
