/**
 * LeadDetailPagePdf.test.tsx — G.1 + G.2 tests.
 *
 * G.1: PDF export button visibility and click behavior.
 * G.2: Staleness banner logic.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import React from 'react'

// Mock catalog hook
vi.mock('../../hooks/useCatalog', () => ({
  useServiceCatalog: () => ({ data: [], isLoading: false, isError: false }),
}))

// Mock useIntakeState
const mockUseIntakeState = vi.fn()
vi.mock('../../../intake/api/intake', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../../intake/api/intake')>()
  return { ...actual, useIntakeState: (...args: unknown[]) => mockUseIntakeState(...args) }
})

// Mock getLead
const mockGetLead = vi.fn()
vi.mock('../../api/leads', () => ({ getLead: (...args: unknown[]) => mockGetLead(...args) }))

import { LeadDetailPage } from '../LeadDetailPage'

const baseLead = {
  id: 'lead-1',
  full_name: 'Test User',
  email: 'test@test.com',
  company_name: 'Test Corp',
  phone: null,
  status: 'accepted',
  bucket: 'alto',
  triage_payload: {},
  consents: [],
  score: 80,
  score_breakdown: {},
  created_at: '2026-01-01T00:00:00Z',
}

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(
      QueryClientProvider,
      { client: qc },
      React.createElement(
        MemoryRouter,
        { initialEntries: ['/admin/leads/lead-1'] },
        React.createElement(Routes, null,
          React.createElement(Route, { path: '/admin/leads/:id', element: children })
        )
      )
    )
}

describe('LeadDetailPage — PDF export button (G.1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetLead.mockResolvedValue(baseLead)
  })

  it('PDF button hidden when in_progress (no synthesis)', async () => {
    mockUseIntakeState.mockReturnValue({
      data: {
        state: 'in_progress',
        session1_synthesis_status: 'pending',
        session1_synthesis: null,
        synthesis_edited_json: null,
        synthesis_edited_at: null,
        synthesis_last_exported_at: null,
        synthesis_export_count: 0,
      },
    })

    render(React.createElement(LeadDetailPage), { wrapper: makeWrapper() })

    await waitFor(() => expect(mockGetLead).toHaveBeenCalled())
    expect(screen.queryByRole('button', { name: /exportar pdf/i })).not.toBeInTheDocument()
  })

  it('PDF button visible when session2_pending with synthesis', async () => {
    mockUseIntakeState.mockReturnValue({
      data: {
        state: 'session2_pending',
        session1_synthesis_status: 'ready',
        session1_synthesis: { summary: 'Test', key_insights: [], recommendations: [], hypothesis: null },
        synthesis_edited_json: null,
        synthesis_edited_at: null,
        synthesis_last_exported_at: null,
        synthesis_export_count: 0,
      },
    })

    render(React.createElement(LeadDetailPage), { wrapper: makeWrapper() })

    await waitFor(() => screen.getByRole('button', { name: /exportar pdf/i }))
    expect(screen.getByRole('button', { name: /exportar pdf/i })).toBeInTheDocument()
  })

  it('PDF button visible when closed with synthesis', async () => {
    mockUseIntakeState.mockReturnValue({
      data: {
        state: 'closed',
        session1_synthesis_status: 'ready',
        session1_synthesis: { summary: 'Test', key_insights: [], recommendations: [], hypothesis: null },
        synthesis_edited_json: null,
        synthesis_edited_at: null,
        synthesis_last_exported_at: null,
        synthesis_export_count: 0,
      },
    })

    render(React.createElement(LeadDetailPage), { wrapper: makeWrapper() })

    await waitFor(() => screen.getByRole('button', { name: /exportar pdf/i }))
    expect(screen.getByRole('button', { name: /exportar pdf/i })).toBeInTheDocument()
  })

  it('PDF click triggers POST request to export-pdf endpoint', async () => {
    mockUseIntakeState.mockReturnValue({
      data: {
        state: 'session2_pending',
        session1_synthesis_status: 'ready',
        session1_synthesis: { summary: 'Test', key_insights: [], recommendations: [], hypothesis: null },
        synthesis_edited_json: null,
        synthesis_edited_at: null,
        synthesis_last_exported_at: null,
        synthesis_export_count: 0,
      },
    })

    const mockBlob = new Blob(['%PDF-fake'], { type: 'application/pdf' })
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      headers: { get: (_h: string) => null },
      blob: () => Promise.resolve(mockBlob),
    } as unknown as Response)

    // Stub URL.createObjectURL to avoid happy-dom issues
    vi.stubGlobal('URL', {
      createObjectURL: vi.fn().mockReturnValue('blob:fake'),
      revokeObjectURL: vi.fn(),
    })

    render(React.createElement(LeadDetailPage), { wrapper: makeWrapper() })

    const btn = await waitFor(() => screen.getByRole('button', { name: /exportar pdf/i }))
    fireEvent.click(btn)

    await waitFor(() =>
      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining('export-pdf'),
        expect.objectContaining({ method: 'POST' })
      )
    )
  })
})

describe('LeadDetailPage — Staleness banner (G.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetLead.mockResolvedValue(baseLead)
  })

  it('staleness banner visible when edited_at > last_exported_at', async () => {
    mockUseIntakeState.mockReturnValue({
      data: {
        state: 'closed',
        session1_synthesis_status: 'ready',
        session1_synthesis: { summary: 'Test', key_insights: [], recommendations: [] },
        synthesis_edited_json: { summary: 'Edited' },
        synthesis_edited_at: '2026-05-06T16:00:00Z',  // after export
        synthesis_last_exported_at: '2026-05-06T14:00:00Z',
        synthesis_export_count: 1,
      },
    })

    render(React.createElement(LeadDetailPage), { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText(/desactualizado/i))
    expect(screen.getByText(/pdf exportado el/i)).toBeInTheDocument()
  })

  it('no banner when never exported (synthesis_last_exported_at is null)', async () => {
    mockUseIntakeState.mockReturnValue({
      data: {
        state: 'closed',
        session1_synthesis_status: 'ready',
        session1_synthesis: { summary: 'Test', key_insights: [], recommendations: [] },
        synthesis_edited_json: null,
        synthesis_edited_at: '2026-05-06T16:00:00Z',
        synthesis_last_exported_at: null,
        synthesis_export_count: 0,
      },
    })

    render(React.createElement(LeadDetailPage), { wrapper: makeWrapper() })

    // Wait for lead to load (check for email which is unique)
    await waitFor(() => screen.getByText('test@test.com'))
    expect(screen.queryByText(/pdf exportado el/i)).not.toBeInTheDocument()
  })

  it('no banner when export is newer than edit', async () => {
    mockUseIntakeState.mockReturnValue({
      data: {
        state: 'closed',
        session1_synthesis_status: 'ready',
        session1_synthesis: { summary: 'Test', key_insights: [], recommendations: [] },
        synthesis_edited_json: { summary: 'Edited' },
        synthesis_edited_at: '2026-05-06T12:00:00Z',  // BEFORE export
        synthesis_last_exported_at: '2026-05-06T14:00:00Z',
        synthesis_export_count: 1,
      },
    })

    render(React.createElement(LeadDetailPage), { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('test@test.com'))
    expect(screen.queryByText(/pdf exportado el/i)).not.toBeInTheDocument()
  })
})
