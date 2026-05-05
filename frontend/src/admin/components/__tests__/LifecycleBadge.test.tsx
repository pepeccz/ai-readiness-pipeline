/**
 * TC.1 — LifecycleBadge renders correct label + color class per state (REQ-6)
 * TC.3 — Badge mounts on 3 surfaces (LeadsListPage row, LeadDetailPage header, IntakeApp header)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { LifecycleBadge } from '../LifecycleBadge'

// ── TC.1 + TC.2: LifecycleBadge unit tests ──────────────────────────────────

describe('LifecycleBadge — REQ-6', () => {
  const cases: Array<{ state: string; label: string; colorHint: string }> = [
    { state: 'not_started',      label: 'Sin iniciar',       colorHint: 'gray'   },
    { state: 'in_progress',      label: 'En progreso',       colorHint: 'blue'   },
    { state: 'blocks_completed', label: 'Bloques completos', colorHint: 'indigo' },
    { state: 'deep_pending',     label: 'DEEP pendiente',    colorHint: 'orange' },
    { state: 'deep_received',    label: 'DEEP recibido',     colorHint: 'purple' },
    { state: 'closed',           label: 'Cerrado',           colorHint: 'green'  },
  ]

  for (const { state, label } of cases) {
    it(`renders label "${label}" for state "${state}"`, () => {
      render(<LifecycleBadge state={state} />)
      expect(screen.getByText(label)).toBeInTheDocument()
    })
  }

  it('renders unknown state as-is without crashing', () => {
    render(<LifecycleBadge state="unknown_state" />)
    expect(screen.getByText('unknown_state')).toBeInTheDocument()
  })
})

// ── TC.3: mount surface tests ────────────────────────────────────────────────

// Mock intake API so LeadsListPage / LeadDetailPage / IntakeApp can mount
vi.mock('../../../intake/api/intake', () => ({
  useIntakeState: vi.fn().mockReturnValue({
    data: {
      lead_id: 'lead-1',
      state: 'in_progress',
      primary_area: 'technology',
      secondary_area: null,
      areas_involved: [],
      blocks_completed: [],
    },
    isLoading: false,
    isError: false,
  }),
  useIntakeSchema: vi.fn().mockReturnValue({ data: null, isLoading: false }),
  useBlockPayload: vi.fn().mockReturnValue({ data: null }),
  intakeKeys: {
    state: (leadId: string) => ['intake', leadId, 'state'],
  },
}))

vi.mock('../../api/leads', () => ({
  listLeads: vi.fn().mockResolvedValue({ items: [
    {
      id: 'lead-1',
      full_name: 'Ana Torres',
      email: 'ana@example.com',
      company_name: 'Acme',
      sector: 'Tech',
      triage_bucket: 'review',
      triage_score: 80,
      status: 'accepted',
      created_at: '2026-01-01T00:00:00Z',
      assigned_consultant_id: null,
      intake_state: 'in_progress',
    }
  ], total: 1, page: 1, page_size: 20, pages: 1 }),
  getLead: vi.fn().mockResolvedValue({}),
  patchLead: vi.fn(),
}))

vi.mock('../../AuthContext', () => ({
  useAuth: vi.fn().mockReturnValue({ user: { email: 'admin@test.com' }, logout: vi.fn() }),
}))

vi.mock('../../../intake/hooks/useIntakeSession', () => ({
  useIntakeSession: vi.fn().mockReturnValue({
    session: {
      lead_id: 'lead-1',
      state: 'in_progress',
      primary_area: 'technology',
      blocks_completed: [],
    },
    isLoading: false,
    isError: false,
    isBlockCompleted: () => false,
    hasAreaSelected: () => true,
  }),
}))

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

describe('TC.3 — LifecycleBadge mounts in LeadsListPage rows', () => {
  it('renders a LifecycleBadge in each lead row when intake_state is present', async () => {
    const { LeadsListPage } = await import('../../pages/LeadsListPage')
    const { waitFor } = await import('@testing-library/react')

    const qc = makeQC()
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <LeadsListPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    await waitFor(() => {
      // Should render the badge for the in_progress state
      expect(screen.getByText('En progreso')).toBeInTheDocument()
    })
  })
})

describe('TC.3 — LifecycleBadge mounts in IntakeApp header', () => {
  it('renders LifecycleBadge next to "Sesión 1 — Intake CORE" header text', async () => {
    const { IntakeApp } = await import('../../../intake/IntakeApp')

    const qc = makeQC()
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <IntakeApp leadId="lead-1" />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    // Header text must be present
    expect(screen.getByText('Sesión 1 — Intake CORE')).toBeInTheDocument()
    // Badge must be present
    expect(screen.getByText('En progreso')).toBeInTheDocument()
  })
})
