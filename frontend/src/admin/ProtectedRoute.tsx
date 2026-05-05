import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

/**
 * REQ-14 / ADR-11: Redirects unauthenticated users to /login with a
 * ?returnTo=<encoded current path> query parameter so LoginPage can
 * bounce them back after a successful authentication.
 *
 * The redirect target is always /login (not /admin/login) to keep it
 * consistent with the route topology.
 */
export function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-gray-500">Verificando sesión...</span>
        </div>
      </div>
    )
  }

  if (!user) {
    const returnTo = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/login?returnTo=${returnTo}`} replace />
  }

  return <Outlet />
}
