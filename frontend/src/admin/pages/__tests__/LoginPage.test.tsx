/**
 * T4.5 — REQ-14: LoginPage reads returnTo from URLSearchParams and navigates there on success
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock AuthContext — must be before LoginPage import
vi.mock('../../AuthContext', () => ({
  useAuth: vi.fn(),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// Mock ApiError
vi.mock('../../api/client', () => ({
  ApiError: class ApiError extends Error {
    status: number
    constructor(msg: string, status: number) {
      super(msg)
      this.status = status
    }
  },
}))

import { useAuth } from '../../AuthContext'
import { LoginPage } from '../LoginPage'

const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })

function makeLoginRouter(initialPath: string) {
  return createMemoryRouter(
    [
      {
        path: '/login',
        element: (
          <QueryClientProvider client={qc}>
            <LoginPage />
          </QueryClientProvider>
        ),
      },
      {
        path: '/admin/login',
        element: (
          <QueryClientProvider client={qc}>
            <LoginPage />
          </QueryClientProvider>
        ),
      },
      { path: '/intake/abc', element: <div data-testid="intake-page">Intake</div> },
      { path: '/admin/leads', element: <div data-testid="leads-page">Leads</div> },
    ],
    { initialEntries: [initialPath] }
  )
}

describe('T4.5 — LoginPage returnTo navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('navigates to returnTo path on successful login', async () => {
    const mockLogin = vi.fn().mockResolvedValue(undefined)
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      login: mockLogin,
      logout: vi.fn(),
      refresh: vi.fn(),
    })

    const router = makeLoginRouter('/login?returnTo=%2Fintake%2Fabc')
    render(<RouterProvider router={router} />)

    await act(async () => {
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'admin@test.com' },
      })
      fireEvent.change(screen.getByLabelText(/contraseña/i), {
        target: { value: 'password123' },
      })
      fireEvent.click(screen.getByRole('button', { name: /ingresar/i }))
    })

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/intake/abc')
    })
  })

  it('navigates to /admin/leads when no returnTo param present', async () => {
    const mockLogin = vi.fn().mockResolvedValue(undefined)
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      login: mockLogin,
      logout: vi.fn(),
      refresh: vi.fn(),
    })

    const router = makeLoginRouter('/admin/login')
    render(<RouterProvider router={router} />)

    await act(async () => {
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'admin@test.com' },
      })
      fireEvent.change(screen.getByLabelText(/contraseña/i), {
        target: { value: 'password123' },
      })
      fireEvent.click(screen.getByRole('button', { name: /ingresar/i }))
    })

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/admin/leads')
    })
  })

  it('ignores an external returnTo and falls back to /admin/leads', async () => {
    const mockLogin = vi.fn().mockResolvedValue(undefined)
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      login: mockLogin,
      logout: vi.fn(),
      refresh: vi.fn(),
    })

    // //evil.com is a protocol-relative URL → must be rejected by safeReturnTo
    const router = makeLoginRouter('/login?returnTo=%2F%2Fevil.com%2Fphish')
    render(<RouterProvider router={router} />)

    await act(async () => {
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'admin@test.com' },
      })
      fireEvent.change(screen.getByLabelText(/contraseña/i), {
        target: { value: 'password123' },
      })
      fireEvent.click(screen.getByRole('button', { name: /ingresar/i }))
    })

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/admin/leads')
    })
  })
})
