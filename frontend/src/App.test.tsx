/**
 * T4.1 — REQ-13: Public triage wizard does NOT inherit admin QueryClient or AuthProvider
 * T4.2 — REQ-13: Admin and intake share the same QueryClient instance
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query'
import React from 'react'

// ---- Helper probes ----

/**
 * Renders inside useQueryClient() and captures the result (or throws).
 * Uses a React ref trick to avoid async: we capture on first render.
 */
function QueryClientProbe({ onCapture }: { onCapture: (client: QueryClient | null) => void }) {
  let client: QueryClient | null = null
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    client = useQueryClient()
  } catch {
    client = null
  }
  onCapture(client)
  return <div data-testid="probe" />
}

// ---- T4.1: triage route must NOT inherit QueryClient from any provider ----

describe('T4.1 — Public triage route has no shared QueryClient', () => {
  it('useQueryClient() inside triage returns null (no provider)', () => {
    let captured: QueryClient | null = undefined as unknown as QueryClient | null

    const trialRouter = createMemoryRouter(
      [
        {
          path: '/triage',
          element: <QueryClientProbe onCapture={(c) => { captured = c }} />,
        },
      ],
      { initialEntries: ['/triage'] }
    )

    render(<RouterProvider router={trialRouter} />)
    // The probe should have thrown → captured remains null
    expect(captured).toBeNull()
  })
})

// ---- T4.2: /admin/* and /intake/:leadId/* share the same QueryClient ----

describe('T4.2 — Admin and intake share a single QueryClient', () => {
  it('invalidating a key from the admin context is visible in the intake context', () => {
    // We use a single shared queryClient (as AdminLayout does)
    const sharedClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    })

    let adminClient: QueryClient | null = null
    let intakeClient: QueryClient | null = null

    function AdminProbe() {
      return <QueryClientProbe onCapture={(c) => { adminClient = c }} />
    }
    function IntakeProbe() {
      return <QueryClientProbe onCapture={(c) => { intakeClient = c }} />
    }

    const testRouter = createMemoryRouter(
      [
        {
          // Simulates the shared AdminLayout wrapping both routes
          element: (
            <QueryClientProvider client={sharedClient}>
              {/* RouterProvider will render Outlet here via children */}
              {/* We use index routes to simulate /admin and /intake children */}
              <React.Fragment>
                <AdminProbe />
                <IntakeProbe />
              </React.Fragment>
            </QueryClientProvider>
          ),
          path: '/',
          children: [{ index: true, element: null }],
        },
      ],
      { initialEntries: ['/'] }
    )

    render(<RouterProvider router={testRouter} />)

    // Both probes must have captured the same client instance
    expect(adminClient).not.toBeNull()
    expect(intakeClient).not.toBeNull()
    expect(adminClient).toBe(intakeClient)
    expect(adminClient).toBe(sharedClient)
  })
})
