/**
 * TE.5 — SessionSynthesisPanel mounts in LeadDetailPage when state >= deep_pending
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import React from 'react'

// Mock getLead
vi.mock('../../api/leads', () => ({
  getLead: vi.fn().mockResolvedValue({
    id: 'lead-1',
    status: 'accepted',
    company_name: 'Acme',
    full_name: 'John Doe',
    email: 'john@acme.com',
    phone: null,
    sector: 'tech',
    company_size: '10-50',
    respondent_role: 'CTO',
    ai_maturity: 'beginner',
    urgency: 'medium',
    commitment: 'high',
    created_at: '2026-01-01T00:00:00Z',
    triage_score: 80,
    triage_bucket: 'A',
    triage_payload: {},
    ai_goals: [],
    consents: [],
    rejected_reason: null,
  }),
}))

// Mock useIntakeState to return deep_pending state
const mockUseIntakeState = vi.fn()
vi.mock('../../../intake/api/intake', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../../intake/api/intake')>()
  return {
    ...actual,
    useIntakeState: (...args: unknown[]) => mockUseIntakeState(...args),
    useFinalClose: vi.fn().mockReturnValue({ mutate: vi.fn(), isPending: false }),
  }
})

// Mock useCatalog hook for SessionSynthesisPanel
vi.mock('../../hooks/useCatalog', () => ({
  useServiceCatalog: () => ({ data: [], isLoading: false, isError: false }),
}))

// Mock BucketBadge to avoid complex rendering
vi.mock('../../components/LeadDetail/BucketBadge', () => ({
  BucketBadge: () => null,
}))

// Use real SessionSynthesisPanel — its internal visibility logic depends on useIntakeState (mocked above)

// Also mock LifecycleBadge (added by Batch C)
vi.mock('../../components/LifecycleBadge', () => ({
  LifecycleBadge: ({ state }: { state: string }) =>
    React.createElement('span', { 'data-testid': 'lifecycle-badge' }, state),
}))

// Mock LeadActionPanel (avoid complex rendering)
vi.mock('../../components/LeadDetail/LeadActionPanel', () => ({
  LeadActionPanel: () => null,
}))

import { LeadDetailPage } from '../LeadDetailPage'

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(
      QueryClientProvider,
      { client: qc },
      React.createElement(
        MemoryRouter,
        { initialEntries: ['/admin/leads/lead-1'] },
        React.createElement(
          Routes,
          null,
          React.createElement(Route, { path: '/admin/leads/:id', element: children })
        )
      )
    )
}

describe('LeadDetailPage — SessionSynthesisPanel mount', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('mounts SessionSynthesisPanel when intake state is deep_pending (H.1 updated)', async () => {
    // New component: deep_pending with synthesis ready shows read-only panel
    mockUseIntakeState.mockReturnValue({
      data: {
        state: 'deep_pending',
        session1_synthesis_status: 'ready',
        session1_synthesis: {
          summary: 'Resumen del lead.',
          key_insights: ['Insight clave'],
          recommendations: [{ text: 'Rec 1', impact: null, effort: null, related_service: null }],
          hypothesis: 'Hipótesis interna.',
          generated_at: '2026-01-01T00:00:00Z',
          model: 'claude-sonnet-4-6',
        },
        synthesis_edited_json: null,
        synthesis_edited_at: null,
        synthesis_last_exported_at: null,
        synthesis_export_count: 0,
        deep_branches_count: 2,
      },
      isLoading: false,
      refetch: vi.fn(),
    })

    render(React.createElement(LeadDetailPage), { wrapper: makeWrapper() })

    // Wait for the lead to load (async query)
    await screen.findAllByText('Acme')
    // New component: synthesis content is shown read-only for deep_pending
    expect(screen.getByDisplayValue('Resumen del lead.')).toBeInTheDocument()
    // No Guardar button in view mode
    expect(screen.queryByRole('button', { name: /guardar/i })).not.toBeInTheDocument()
  })

  it('does NOT show synthesis panel content when intake state is in_progress', async () => {
    mockUseIntakeState.mockReturnValue({
      data: { state: 'in_progress', session1_synthesis_status: 'not_started', session1_synthesis: null, deep_branches_count: 0 },
      isLoading: false,
    })

    render(React.createElement(LeadDetailPage), { wrapper: makeWrapper() })

    await screen.findAllByText('Acme')
    // Panel is mounted but renders null — so its content is absent
    expect(screen.queryByText(/generando síntesis/i)).not.toBeInTheDocument()
  })
})
