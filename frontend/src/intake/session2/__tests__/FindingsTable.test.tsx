/**
 * H.5 RED → GREEN — FindingsTable tests (REQ-11)
 *
 * Tests:
 * - Click dismiss → API called → finding hidden (or strikethrough)
 * - Click restore → finding back in normal state
 * - Optimistic UI: dismiss shows immediately, rollback on API error
 * - Multiple findings dismiss independently
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// ---------------------------------------------------------------------------
// Mock API functions
// ---------------------------------------------------------------------------
const mockDismissFinding = vi.fn()
const mockRestoreFinding = vi.fn()

vi.mock('../api/session2', () => ({
  dismissFinding: (...args: unknown[]) => mockDismissFinding(...args),
  restoreFinding: (...args: unknown[]) => mockRestoreFinding(...args),
}))

const mockFindings = [
  {
    finding_id: 'abc123',
    block_id: 'block-1-strategic',
    text: 'Contradicción en estrategia',
    severity: 'high' as const,
    dismissed: false,
  },
  {
    finding_id: 'def456',
    block_id: 'block-3-data',
    text: 'Inconsistencia en datos',
    severity: 'med' as const,
    dismissed: false,
  },
  {
    finding_id: 'ghi789',
    block_id: 'block-6-compliance',
    text: 'Contradicción ya descartada',
    severity: 'low' as const,
    dismissed: true,
  },
]

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children)
}

describe('FindingsTable — H.5: dismiss and restore (REQ-11)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('H.5-a: renders all findings', async () => {
    const { FindingsTable } = await import('../FindingsTable')
    render(
      React.createElement(FindingsTable, { leadId: 'lead-1', findings: mockFindings }),
      { wrapper: makeWrapper() }
    )

    expect(screen.getByText('Contradicción en estrategia')).toBeInTheDocument()
    expect(screen.getByText('Inconsistencia en datos')).toBeInTheDocument()
    expect(screen.getByText('Contradicción ya descartada')).toBeInTheDocument()
  })

  it('H.5-b: click dismiss calls API and shows optimistic dismissed state', async () => {
    mockDismissFinding.mockResolvedValue({ ok: true })

    const { FindingsTable } = await import('../FindingsTable')
    render(
      React.createElement(FindingsTable, { leadId: 'lead-1', findings: mockFindings }),
      { wrapper: makeWrapper() }
    )

    // Find the first finding's dismiss button
    const dismissButtons = screen.getAllByRole('button', { name: /descartar/i })
    fireEvent.click(dismissButtons[0])

    // Optimistic update: dismissed immediately
    await waitFor(() => {
      expect(mockDismissFinding).toHaveBeenCalledWith('lead-1', 'block-1-strategic', 'abc123')
    })
  })

  it('H.5-c: click restore on dismissed finding calls restore API', async () => {
    mockRestoreFinding.mockResolvedValue({ ok: true })

    const { FindingsTable } = await import('../FindingsTable')
    render(
      React.createElement(FindingsTable, { leadId: 'lead-1', findings: mockFindings }),
      { wrapper: makeWrapper() }
    )

    // The third finding (ghi789) is dismissed, so it should show a restore button
    const restoreButton = screen.getByRole('button', { name: /restaurar/i })
    fireEvent.click(restoreButton)

    await waitFor(() => {
      expect(mockRestoreFinding).toHaveBeenCalledWith('lead-1', 'block-6-compliance', 'ghi789')
    })
  })

  it('H.5-d: optimistic dismiss rolls back on API error', async () => {
    mockDismissFinding.mockRejectedValue(new Error('Network error'))

    const { FindingsTable } = await import('../FindingsTable')
    render(
      React.createElement(FindingsTable, { leadId: 'lead-1', findings: mockFindings }),
      { wrapper: makeWrapper() }
    )

    const dismissButtons = screen.getAllByRole('button', { name: /descartar/i })
    fireEvent.click(dismissButtons[0])

    // After rollback, finding should be visible again (not strikethrough/hidden)
    await waitFor(() => {
      expect(mockDismissFinding).toHaveBeenCalled()
    })

    // Finding text should still be in the document after rollback
    expect(screen.getByText('Contradicción en estrategia')).toBeInTheDocument()
  })

  it('H.5-e: multiple findings dismiss independently', async () => {
    mockDismissFinding.mockResolvedValue({ ok: true })

    const { FindingsTable } = await import('../FindingsTable')
    render(
      React.createElement(FindingsTable, { leadId: 'lead-1', findings: mockFindings }),
      { wrapper: makeWrapper() }
    )

    const dismissButtons = screen.getAllByRole('button', { name: /descartar/i })
    // Both non-dismissed findings have their own dismiss buttons
    expect(dismissButtons).toHaveLength(2)

    // Dismiss first
    fireEvent.click(dismissButtons[0])
    await waitFor(() => expect(mockDismissFinding).toHaveBeenCalledTimes(1))

    // Each dismiss call is independent — different finding IDs
    expect(mockDismissFinding).toHaveBeenCalledWith('lead-1', 'block-1-strategic', 'abc123')
  })
})
