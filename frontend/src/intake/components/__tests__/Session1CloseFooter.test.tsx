/**
 * TD.5 — Session1CloseFooter: visibility rules, modal flow, mutation call (REQ-1/D9)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import React from 'react'
import { Session1CloseFooter } from '../Session1CloseFooter'

// Mock the mutation hook
const mockMutate = vi.fn()
const mockIsLoading = { current: false }

vi.mock('../../api/intake', () => ({
  useSession1Close: vi.fn(() => ({
    mutate: mockMutate,
    isPending: mockIsLoading.current,
    isSuccess: false,
  })),
  intakeKeys: {
    state: (id: string) => ['intake', id, 'state'],
  },
}))

vi.mock('../../../admin/api/client', () => ({
  fetchJson: vi.fn(),
  ApiError: class ApiError extends Error {},
}))

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>()
  return { ...actual, useNavigate: () => mockNavigate }
})

function renderFooter(state: string, blocksCompleted: string[]) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <Session1CloseFooter
          leadId="lead-1"
          state={state}
          blocksCompleted={blocksCompleted}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Session1CloseFooter — REQ-1 D9', () => {
  beforeEach(() => {
    mockMutate.mockReset()
    mockNavigate.mockReset()
  })

  it('is hidden when state is deep_pending', () => {
    const { container } = renderFooter('deep_pending', ['block-1-strategic'])
    expect(container.firstChild).toBeNull()
  })

  it('is hidden when state is closed', () => {
    const { container } = renderFooter('closed', ['block-1-strategic'])
    expect(container.firstChild).toBeNull()
  })

  it('renders button when state=in_progress and block-1-strategic completed', () => {
    renderFooter('in_progress', ['block-1-strategic'])
    expect(screen.getByRole('button', { name: /cerrar sesión 1/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cerrar sesión 1/i })).not.toBeDisabled()
  })

  it('renders disabled button when state=in_progress but block-1-strategic NOT completed', () => {
    renderFooter('in_progress', [])
    const btn = screen.getByRole('button', { name: /cerrar sesión 1/i })
    expect(btn).toBeDisabled()
  })

  it('renders button when state=blocks_completed and block-1-strategic completed', () => {
    renderFooter('blocks_completed', ['block-1-strategic'])
    expect(screen.getByRole('button', { name: /cerrar sesión 1/i })).not.toBeDisabled()
  })

  it('opens confirm modal on button click', () => {
    renderFooter('in_progress', ['block-1-strategic'])
    fireEvent.click(screen.getByRole('button', { name: /cerrar sesión 1/i }))
    // Modal body text must appear
    expect(screen.getByText(/síntesis LLM/i)).toBeInTheDocument()
  })

  it('calls mutate on modal confirm', () => {
    renderFooter('in_progress', ['block-1-strategic'])
    fireEvent.click(screen.getByRole('button', { name: /cerrar sesión 1/i }))
    // Click Continuar in the modal
    fireEvent.click(screen.getByRole('button', { name: /continuar/i }))
    expect(mockMutate).toHaveBeenCalledOnce()
  })

  it('does NOT call mutate on modal cancel', () => {
    renderFooter('in_progress', ['block-1-strategic'])
    fireEvent.click(screen.getByRole('button', { name: /cerrar sesión 1/i }))
    fireEvent.click(screen.getByRole('button', { name: /cancelar/i }))
    expect(mockMutate).not.toHaveBeenCalled()
  })
})
