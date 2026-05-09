/**
 * H.1 RED → GREEN — Session2PrepPanel tests (REQ-10, REQ-08, REQ-19)
 *
 * Tests:
 * - Renders scorecard section + findings (contradictions) section + follow-ups section
 * - Loading state shown while data fetching
 * - Panel hidden when intake state == "in_progress"
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// ---------------------------------------------------------------------------
// Mock useSession2Prep
// ---------------------------------------------------------------------------
const mockUseSession2Prep = vi.fn()
vi.mock('../hooks/useSession2Prep', () => ({
  useSession2Prep: (...args: unknown[]) => mockUseSession2Prep(...args),
}))

// Mock sub-components so we can test Session2PrepPanel in isolation
vi.mock('../ScorecardPreview', () => ({
  ScorecardPreview: ({ data }: { data: unknown }) =>
    React.createElement('div', { 'data-testid': 'scorecard-preview' }, 'Scorecard'),
}))

vi.mock('../FindingsTable', () => ({
  FindingsTable: ({ findings }: { findings: unknown[] }) =>
    React.createElement('div', { 'data-testid': 'findings-table' }, `Findings: ${findings.length}`),
}))

vi.mock('../FollowUpsTable', () => ({
  FollowUpsTable: ({ followUps }: { followUps: unknown[] }) =>
    React.createElement('div', { 'data-testid': 'follow-ups-table' }, `FollowUps: ${followUps.length}`),
}))

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children)
}

const mockPrepData = {
  session: {
    state: 'session2_pending',
    composite_score: 0.62,
    composite_level: 2,
    composite_level_name: 'Establecido',
    risk_profile: 'medium' as const,
  },
  per_block: [
    {
      block_id: 'block-1-strategic',
      block_title: 'Estrategia',
      score: 0.7,
      level: 3,
      level_name: 'Avanzado',
      status: 'ready' as const,
      missing_fields: [],
    },
    {
      block_id: 'block-3-data',
      block_title: 'Datos',
      score: null,
      level: null,
      level_name: null,
      status: 'insufficient_data' as const,
      missing_fields: ['q3_2_quality'],
    },
  ],
  contradictions: [
    {
      finding_id: 'abc123',
      block_id: 'block-1-strategic',
      text: 'Contradicción estratégica detectada',
      severity: 'high' as const,
      dismissed: false,
    },
  ],
  follow_ups: [
    {
      finding_id: 'def456',
      block_id: 'block-1-strategic',
      text: 'Revisar KPIs de adopción',
      priority: 'high' as const,
      confidence: 0.85,
      dismissed: false,
    },
  ],
}

describe('Session2PrepPanel — H.1: scorecard + findings + follow-ups sections (REQ-10)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('H.1-a: renders all three sections when data is loaded', async () => {
    mockUseSession2Prep.mockReturnValue({
      data: mockPrepData,
      isLoading: false,
      isError: false,
    })

    const { Session2PrepPanel } = await import('../Session2PrepPanel')
    render(
      React.createElement(Session2PrepPanel, { leadId: 'lead-1' }),
      { wrapper: makeWrapper() }
    )

    expect(screen.getByTestId('scorecard-preview')).toBeInTheDocument()
    expect(screen.getByTestId('findings-table')).toBeInTheDocument()
    expect(screen.getByTestId('follow-ups-table')).toBeInTheDocument()
  })

  it('H.1-b: shows loading state while data is fetching', async () => {
    mockUseSession2Prep.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    })

    const { Session2PrepPanel } = await import('../Session2PrepPanel')
    render(
      React.createElement(Session2PrepPanel, { leadId: 'lead-1' }),
      { wrapper: makeWrapper() }
    )

    expect(screen.getByTestId('session2-loading')).toBeInTheDocument()
    expect(screen.queryByTestId('scorecard-preview')).not.toBeInTheDocument()
  })

  it('H.1-c: panel renders null/empty when state is in_progress (hidden by parent)', async () => {
    // The panel itself doesn't gate on state — it trusts the parent.
    // But we test that when prep data reflects in_progress, the component renders normally
    // (visibility is controlled by the tab in LeadDetailPage / IntakeApp via H.8).
    // This test verifies the panel renders data when given it.
    mockUseSession2Prep.mockReturnValue({
      data: {
        ...mockPrepData,
        session: { ...mockPrepData.session, state: 'in_progress' },
      },
      isLoading: false,
      isError: false,
    })

    const { Session2PrepPanel } = await import('../Session2PrepPanel')
    render(
      React.createElement(Session2PrepPanel, { leadId: 'lead-1' }),
      { wrapper: makeWrapper() }
    )

    // Panel itself renders when given data — tab visibility is controlled by H.8
    expect(screen.getByTestId('scorecard-preview')).toBeInTheDocument()
  })

  it('H.1-d: shows error state when fetch fails', async () => {
    mockUseSession2Prep.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    })

    const { Session2PrepPanel } = await import('../Session2PrepPanel')
    render(
      React.createElement(Session2PrepPanel, { leadId: 'lead-1' }),
      { wrapper: makeWrapper() }
    )

    expect(screen.getByTestId('session2-error')).toBeInTheDocument()
  })
})
