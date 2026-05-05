/**
 * T4.4 — REQ-14: ProtectedRoute redirects to /login?returnTo=<encoded path>
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock AuthContext — must be before the ProtectedRoute import
vi.mock('../../AuthContext', () => ({
  useAuth: vi.fn(),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

import { useAuth } from '../../AuthContext'
import { ProtectedRoute } from '../../ProtectedRoute'

const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })

function makeRouter(initialPath: string) {
  return createMemoryRouter(
    [
      {
        path: '/login',
        element: <div data-testid="login-page">Login</div>,
      },
      {
        path: '/intake/:leadId',
        element: (
          <QueryClientProvider client={qc}>
            <ProtectedRoute />
          </QueryClientProvider>
        ),
        children: [{ index: true, element: <div>Intake Content</div> }],
      },
      {
        path: '/admin',
        element: (
          <QueryClientProvider client={qc}>
            <ProtectedRoute />
          </QueryClientProvider>
        ),
        children: [
          { path: 'leads', element: <div>Admin Leads</div> },
        ],
      },
    ],
    { initialEntries: [initialPath] }
  )
}

describe('T4.4 — ProtectedRoute returnTo redirect', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('redirects unauthenticated user to /login?returnTo=%2Fintake%2Fabc', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    })

    const router = makeRouter('/intake/abc')
    render(<RouterProvider router={router} />)

    expect(router.state.location.pathname).toBe('/login')
    const params = new URLSearchParams(router.state.location.search)
    expect(params.get('returnTo')).toBe('/intake/abc')
  })

  it('redirects unauthenticated /admin/leads to /login?returnTo=%2Fadmin%2Fleads', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    })

    const router = makeRouter('/admin/leads')
    render(<RouterProvider router={router} />)

    expect(router.state.location.pathname).toBe('/login')
    const params = new URLSearchParams(router.state.location.search)
    expect(params.get('returnTo')).toBe('/admin/leads')
  })

  it('renders children when authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: '1', email: 'a@b.com', display_name: 'A' } as any,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    })

    const router = makeRouter('/admin/leads')
    render(<RouterProvider router={router} />)

    expect(screen.getByText('Admin Leads')).toBeTruthy()
  })
})
