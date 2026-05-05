/**
 * T2.3 — REQ-3: LeadActionPanel invalidates ['leads'] with exact: false after accept
 * T2.4 — REQ-4: LeadActionPanel invalidates intakeKeys.state(leadId) after accept
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react'
import { LeadActionPanel } from '../LeadDetail/LeadActionPanel'
import { intakeKeys } from '../../../intake/api/intake'
import type { LeadDetail } from '../../api/leads'
import React from 'react'

// Mock API calls
vi.mock('../../api/leads', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../api/leads')>()
  return {
    ...actual,
    patchLead: vi.fn().mockResolvedValue({ id: 'lead-1', status: 'accepted' }),
  }
})

vi.mock('../../../admin/api/client', () => ({
  fetchJson: vi.fn().mockResolvedValue([
    { id: 'consultant-1', email: 'c@test.com', display_name: 'Consultor Test' },
  ]),
  ApiError: class ApiError extends Error {},
}))

const PENDING_LEAD: LeadDetail = {
  id: 'lead-1',
  status: 'pending_review',
  company_name: 'Acme',
  contact_name: 'John',
  contact_email: 'john@acme.com',
  created_at: '2026-01-01T00:00:00Z',
} as LeadDetail

function renderWithQueryClient(queryClient: QueryClient) {
  return render(
    React.createElement(
      QueryClientProvider,
      { client: queryClient },
      React.createElement(LeadActionPanel, {
        lead: PENDING_LEAD,
        onActionComplete: vi.fn(),
      })
    )
  )
}

describe('LeadActionPanel cache invalidation — REQ-3 + REQ-4', () => {
  let queryClient: QueryClient
  let invalidateSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')
  })

  async function triggerAccept() {
    // Click "Aceptar" to reveal the accept form
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /aceptar/i }))
    })
    // Wait for consultants to load (consultantId must be set before button is enabled)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /confirmar aceptaci/i })).not.toBeDisabled()
    })
    // Click "Confirmar aceptación"
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /confirmar aceptaci/i }))
      await new Promise((r) => setTimeout(r, 100))
    })
  }

  it('invalidates ["leads"] with exact: false after accept', async () => {
    renderWithQueryClient(queryClient)
    await triggerAccept()

    await waitFor(() => {
      expect(invalidateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ queryKey: ['leads'], exact: false })
      )
    })
  })

  it('invalidates intakeKeys.state(leadId) after accept', async () => {
    renderWithQueryClient(queryClient)
    await triggerAccept()

    await waitFor(() => {
      expect(invalidateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ queryKey: intakeKeys.state('lead-1') })
      )
    })
  })
})
