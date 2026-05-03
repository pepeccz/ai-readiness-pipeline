import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from './api/client'
import * as authApi from './api/auth'
import type { AdminUser } from './api/auth'

interface AuthContextValue {
  user: AdminUser | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AdminUser | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const refresh = async () => {
    try {
      const data = await authApi.me()
      setUser(data)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setUser(null)
      } else {
        // Network errors etc. — don't clear user optimistically
        throw err
      }
    }
  }

  // Seed auth state on mount
  useEffect(() => {
    refresh()
      .catch(() => {
        // Already handled inside refresh(); this catch prevents unhandled rejection
        // on non-401 errors during mount (e.g. network down)
        setUser(null)
      })
      .finally(() => {
        setLoading(false)
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = async (email: string, password: string) => {
    // Throws ApiError up to LoginPage on failure
    await authApi.login(email, password)
    // Re-fetch canonical user from /me to hydrate context
    const data = await authApi.me()
    setUser(data)
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch {
      // Best-effort: even if the server-side revocation fails, clear local state
    }
    setUser(null)
    navigate('/admin/login', { replace: true })
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>')
  }
  return ctx
}
