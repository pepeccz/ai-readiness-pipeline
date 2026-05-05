/**
 * TF.3 — "Marcar como cerrado" button in LeadActionPanel
 * Visible: state=deep_received OR (state=deep_pending AND deep_branches_count=0)
 * Hidden: other states
 * Uses ConfirmModal. force=true only when deep_pending+0.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('../../api/leads', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../api/leads')>()
  return {
    ...actual,
    patchLead: vi.fn().mockResolvedValue({ id: 'lead-1', status: 'accepted' }),
  }
})

vi.mock('../../../admin/api/client', () => ({
  fetchJson: vi.fn().mockResolvedValue([]),
  ApiError: class ApiError extends Error {},
}))

const mockMutate = vi.fn()
let mockIntakeData: Record<string, unknown> | null = null

vi.mock('../../../intake/api/intake', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../../intake/api/intake')>()
  return {
    ...actual,
    useIntakeState: () => ({ data: mockIntakeData, isLoading: false }),
    useFinalClose: () => ({
      mutate: mockMutate,
      isPending: false,
    }),
  }
})

import { LeadActionPanel } from '../LeadDetail/LeadActionPanel'
import type { LeadDetail } from '../../api/leads'

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children)
}

function makeLead(overrides: Partial<LeadDetail> = {}): LeadDetail {
  return {
    id: 'lead-1',
    status: 'accepted',
    company_name: 'Acme',
    contact_name: 'John',
    contact_email: 'john@acme.com',
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  } as LeadDetail
}

describe('LeadActionPanel — Marcar como cerrado', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockIntakeData = null
  })

  it('shows button when intake_state is deep_received', () => {
    mockIntakeData = { state: 'deep_received', deep_branches_count: 1, session1_synthesis_status: 'ready', session1_synthesis: null }
    render(
      React.createElement(LeadActionPanel, { lead: makeLead(), onActionComplete: vi.fn() }),
      { wrapper: makeWrapper() }
    )
    expect(screen.getByRole('button', { name: /marcar como cerrado/i })).toBeInTheDocument()
  })

  it('shows button when intake_state is deep_pending with 0 branches', () => {
    mockIntakeData = { state: 'deep_pending', deep_branches_count: 0, session1_synthesis_status: 'pending', session1_synthesis: null }
    render(
      React.createElement(LeadActionPanel, { lead: makeLead(), onActionComplete: vi.fn() }),
      { wrapper: makeWrapper() }
    )
    expect(screen.getByRole('button', { name: /marcar como cerrado/i })).toBeInTheDocument()
  })

  it('does NOT show close button when intake_state is in_progress', () => {
    mockIntakeData = { state: 'in_progress', deep_branches_count: 0, session1_synthesis_status: 'not_started', session1_synthesis: null }
    render(
      React.createElement(LeadActionPanel, { lead: makeLead(), onActionComplete: vi.fn() }),
      { wrapper: makeWrapper() }
    )
    expect(screen.queryByRole('button', { name: /marcar como cerrado/i })).not.toBeInTheDocument()
  })

  it('opens confirm modal when button is clicked', () => {
    mockIntakeData = { state: 'deep_received', deep_branches_count: 1, session1_synthesis_status: 'ready', session1_synthesis: null }
    render(
      React.createElement(LeadActionPanel, { lead: makeLead(), onActionComplete: vi.fn() }),
      { wrapper: makeWrapper() }
    )
    fireEvent.click(screen.getByRole('button', { name: /marcar como cerrado/i }))
    expect(screen.getByText(/esto cierra la sesión definitivamente/i)).toBeInTheDocument()
  })

  it('calls mutate without force when state is deep_received', () => {
    mockIntakeData = { state: 'deep_received', deep_branches_count: 1, session1_synthesis_status: 'ready', session1_synthesis: null }
    render(
      React.createElement(LeadActionPanel, { lead: makeLead(), onActionComplete: vi.fn() }),
      { wrapper: makeWrapper() }
    )
    fireEvent.click(screen.getByRole('button', { name: /marcar como cerrado/i }))
    fireEvent.click(screen.getByRole('button', { name: /confirmar/i }))
    expect(mockMutate).toHaveBeenCalledWith({ force: false })
  })

  it('calls mutate with force=true when state is deep_pending+0 branches', () => {
    mockIntakeData = { state: 'deep_pending', deep_branches_count: 0, session1_synthesis_status: 'pending', session1_synthesis: null }
    render(
      React.createElement(LeadActionPanel, { lead: makeLead(), onActionComplete: vi.fn() }),
      { wrapper: makeWrapper() }
    )
    fireEvent.click(screen.getByRole('button', { name: /marcar como cerrado/i }))
    fireEvent.click(screen.getByRole('button', { name: /confirmar/i }))
    expect(mockMutate).toHaveBeenCalledWith({ force: true })
  })
})
