/**
 * TE.3 — SessionSynthesisPanel renders correct state per synthesis_status
 * TE.5 — SessionSynthesisPanel mounts in LeadDetailPage when state >= deep_pending
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// ---------------------------------------------------------------------------
// Mock useIntakeState
// ---------------------------------------------------------------------------

const mockUseIntakeState = vi.fn()
vi.mock('../../../intake/api/intake', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../../intake/api/intake')>()
  return {
    ...actual,
    useIntakeState: (...args: unknown[]) => mockUseIntakeState(...args),
  }
})

import { SessionSynthesisPanel } from '../SessionSynthesisPanel'

function wrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children)
}

describe('SessionSynthesisPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns null when state is not_started', () => {
    mockUseIntakeState.mockReturnValue({
      data: { state: 'not_started', session1_synthesis_status: 'not_started', session1_synthesis: null },
      isLoading: false,
    })
    const { container } = render(
      React.createElement(SessionSynthesisPanel, { leadId: 'lead-1' }),
      { wrapper: wrapper() }
    )
    expect(container.firstChild).toBeNull()
  })

  it('returns null when state is in_progress', () => {
    mockUseIntakeState.mockReturnValue({
      data: { state: 'in_progress', session1_synthesis_status: 'not_started', session1_synthesis: null },
      isLoading: false,
    })
    const { container } = render(
      React.createElement(SessionSynthesisPanel, { leadId: 'lead-1' }),
      { wrapper: wrapper() }
    )
    expect(container.firstChild).toBeNull()
  })

  it('shows loading spinner when synthesis_status is pending', () => {
    mockUseIntakeState.mockReturnValue({
      data: { state: 'deep_pending', session1_synthesis_status: 'pending', session1_synthesis: null },
      isLoading: false,
    })
    render(
      React.createElement(SessionSynthesisPanel, { leadId: 'lead-1' }),
      { wrapper: wrapper() }
    )
    expect(screen.getByText(/generando síntesis/i)).toBeInTheDocument()
  })

  it('renders synthesis content when status is ready', () => {
    mockUseIntakeState.mockReturnValue({
      data: {
        state: 'deep_pending',
        session1_synthesis_status: 'ready',
        session1_synthesis: {
          summary: 'Executive summary text',
          key_insights: ['Insight A', 'Insight B'],
          recommendations: ['Rec 1'],
          hypothesis: 'Hypothesis text',
          generated_at: '2026-01-01T00:00:00Z',
          model: 'gpt-4o',
        },
      },
      isLoading: false,
    })
    render(
      React.createElement(SessionSynthesisPanel, { leadId: 'lead-1' }),
      { wrapper: wrapper() }
    )
    expect(screen.getByText('Executive summary text')).toBeInTheDocument()
    expect(screen.getByText('Insight A')).toBeInTheDocument()
    expect(screen.getByText('Rec 1')).toBeInTheDocument()
    expect(screen.getByText('Hypothesis text')).toBeInTheDocument()
  })

  it('shows error card with disabled retry when status is failed', () => {
    mockUseIntakeState.mockReturnValue({
      data: { state: 'deep_pending', session1_synthesis_status: 'failed', session1_synthesis: null },
      isLoading: false,
    })
    render(
      React.createElement(SessionSynthesisPanel, { leadId: 'lead-1' }),
      { wrapper: wrapper() }
    )
    expect(screen.getByText(/falló generación/i)).toBeInTheDocument()
    const retryBtn = screen.getByRole('button', { name: /reintentar/i })
    expect(retryBtn).toBeDisabled()
  })

  it('shows soft-timeout warning after 3 minutes (mocked timer)', () => {
    vi.useFakeTimers()
    mockUseIntakeState.mockReturnValue({
      data: { state: 'deep_pending', session1_synthesis_status: 'pending', session1_synthesis: null },
      isLoading: false,
    })

    render(
      React.createElement(SessionSynthesisPanel, { leadId: 'lead-1' }),
      { wrapper: wrapper() }
    )

    // Before timeout — no warning
    expect(screen.queryByText(/tomando más de lo esperado/i)).not.toBeInTheDocument()

    // Advance 3 minutes + 1s
    act(() => {
      vi.advanceTimersByTime(181_000)
    })

    expect(screen.getByText(/tomando más de lo esperado/i)).toBeInTheDocument()
    vi.useRealTimers()
  })
})
