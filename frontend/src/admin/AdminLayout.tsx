import { Outlet } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './queryClient'
import { AuthProvider } from './AuthContext'

/**
 * Root layout for all /admin/* routes.
 * Provides TanStack Query and AuthContext exclusively to the admin tree —
 * the public wizard at "/" is untouched and doesn't pay for these deps.
 */
export function AdminLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <div className="min-h-screen bg-gray-50">
          <Outlet />
        </div>
      </AuthProvider>
    </QueryClientProvider>
  )
}
