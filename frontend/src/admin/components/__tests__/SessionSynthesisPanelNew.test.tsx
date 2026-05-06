/**
 * SessionSynthesisPanelNew.test.tsx — Tests for F.1-F.5
 *
 * Tests the new dual-mode SessionSynthesisPanel with mode prop.
 * These tests replace the old interface (leadId-based) with props-based.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import type { Session1Synthesis, ServiceCatalogEntry } from '../../../types/api'

// Mock useCatalog hook
vi.mock('../../hooks/useCatalog', () => ({
  useServiceCatalog: () => ({
    data: [
      {
        key: 'diagnostico_profundo',
        nombre: 'Diagnóstico Profundo de Procesos',
        descripcion: '...',
        cuando_recomendar: [],
        nota_priorizacion: null,
      },
      {
        key: 'desarrollo_acompanamiento',
        nombre: 'Desarrollo y Acompañamiento de Implementación',
        descripcion: '...',
        cuando_recomendar: [],
        nota_priorizacion: null,
      },
      {
        key: 'formacion_personalizada',
        nombre: 'Formación Personalizada en IA',
        descripcion: '...',
        cuando_recomendar: [],
        nota_priorizacion: 'Preferir',
      },
    ] as ServiceCatalogEntry[],
    isLoading: false,
    isError: false,
  }),
}))

import { SessionSynthesisPanel } from '../SessionSynthesisPanel'

const mockSynthesis: Session1Synthesis = {
  summary: 'Resumen ejecutivo de prueba.',
  key_insights: ['Insight 1', 'Insight 2'],
  recommendations: [
    {
      text: 'Implementar RPA',
      impact: 'alto',
      effort: 'medio',
      related_service: 'desarrollo_acompanamiento',
    },
  ],
  roadmap: { d30: ['Paso 1'], d60: [], d90: [] },
  next_steps: ['Próximo paso'],
  hypothesis: 'Hipótesis interna — Solo visible para el equipo Zanovix.',
  generated_at: '2026-05-06T12:00:00Z',
  model: 'claude-sonnet-4-6',
}

function wrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children)
}

describe('SessionSynthesisPanel — new dual-mode', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── F.1 ──────────────────────────────────────────────────────────────────

  it('F.1 — read-only when deep_pending (no inputs, no Guardar)', () => {
    render(
      React.createElement(SessionSynthesisPanel, {
        leadId: 'lead-1',
        intakeState: 'deep_pending',
        synthesisEffective: mockSynthesis,
        synthesisRaw: mockSynthesis,
      }),
      { wrapper: wrapper() }
    )

    expect(screen.queryByRole('button', { name: /guardar/i })).not.toBeInTheDocument()
    // Should not have editable textareas
    const textareas = screen.queryAllByRole('textbox')
    textareas.forEach((ta) => {
      expect(ta).toHaveAttribute('readonly')
    })
  })

  it('F.1 — hidden when in_progress', () => {
    const { container } = render(
      React.createElement(SessionSynthesisPanel, {
        leadId: 'lead-1',
        intakeState: 'in_progress',
        synthesisEffective: null,
        synthesisRaw: null,
      }),
      { wrapper: wrapper() }
    )

    expect(container.firstChild).toBeNull()
  })

  it('F.1 — editable when deep_received (Guardar present)', () => {
    render(
      React.createElement(SessionSynthesisPanel, {
        leadId: 'lead-1',
        intakeState: 'deep_received',
        synthesisEffective: mockSynthesis,
        synthesisRaw: mockSynthesis,
      }),
      { wrapper: wrapper() }
    )

    expect(screen.getByRole('button', { name: /guardar/i })).toBeInTheDocument()
  })

  // ── F.2 ──────────────────────────────────────────────────────────────────

  it('F.2 — recommendations render as cards with service label', () => {
    render(
      React.createElement(SessionSynthesisPanel, {
        leadId: 'lead-1',
        intakeState: 'deep_received',
        synthesisEffective: mockSynthesis,
        synthesisRaw: mockSynthesis,
      }),
      { wrapper: wrapper() }
    )

    expect(screen.getByDisplayValue('Implementar RPA')).toBeInTheDocument()
  })

  it('F.2 — related_service select has 4 options (3 services + ninguno)', () => {
    render(
      React.createElement(SessionSynthesisPanel, {
        leadId: 'lead-1',
        intakeState: 'deep_received',
        synthesisEffective: mockSynthesis,
        synthesisRaw: mockSynthesis,
      }),
      { wrapper: wrapper() }
    )

    const selects = screen.getAllByRole('combobox')
    // Find a related_service select — should have 4 options
    const serviceSelect = selects.find((s) => {
      const options = s.querySelectorAll('option')
      return options.length === 4
    })
    expect(serviceSelect).toBeDefined()
  })

  // ── F.3 ──────────────────────────────────────────────────────────────────

  it('F.3 — Guardar button disabled when form not dirty', () => {
    render(
      React.createElement(SessionSynthesisPanel, {
        leadId: 'lead-1',
        intakeState: 'deep_received',
        synthesisEffective: mockSynthesis,
        synthesisRaw: mockSynthesis,
      }),
      { wrapper: wrapper() }
    )

    const guardarBtn = screen.getByRole('button', { name: /guardar/i })
    expect(guardarBtn).toBeDisabled()
  })

  // ── F.5 ──────────────────────────────────────────────────────────────────

  it('F.5 — hypothesis visible in edit mode with internal label', () => {
    render(
      React.createElement(SessionSynthesisPanel, {
        leadId: 'lead-1',
        intakeState: 'deep_received',
        synthesisEffective: mockSynthesis,
        synthesisRaw: mockSynthesis,
      }),
      { wrapper: wrapper() }
    )

    // Label appears somewhere in the DOM (may be multiple matches with getAllByText)
    const hipotesisElements = screen.getAllByText(/hipótesis interna/i)
    expect(hipotesisElements.length).toBeGreaterThanOrEqual(1)
    // The hypothesis value itself must be visible
    expect(screen.getByText('Hipótesis interna — Solo visible para el equipo Zanovix.')).toBeInTheDocument()
  })

  it('F.5 — hypothesis NOT in form submit body', async () => {
    let capturedBody: Record<string, unknown> | undefined

    vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, init) => {
      if (typeof url === 'string' && url.includes('synthesis')) {
        capturedBody = JSON.parse((init?.body as string) ?? '{}')
        return new Response(JSON.stringify(mockSynthesis), { status: 200 })
      }
      return new Response('{}', { status: 200 })
    })

    render(
      React.createElement(SessionSynthesisPanel, {
        leadId: 'lead-1',
        intakeState: 'deep_received',
        synthesisEffective: mockSynthesis,
        synthesisRaw: mockSynthesis,
      }),
      { wrapper: wrapper() }
    )

    // Edit the summary to make form dirty
    const summaryInput = screen.getByDisplayValue('Resumen ejecutivo de prueba.')
    fireEvent.change(summaryInput, { target: { value: 'Resumen modificado.' } })

    const guardarBtn = screen.getByRole('button', { name: /guardar/i })
    expect(guardarBtn).not.toBeDisabled()
    fireEvent.click(guardarBtn)

    await waitFor(() => expect(capturedBody).toBeDefined())
    // hypothesis must not be in the submitted body
    expect(capturedBody).not.toHaveProperty('hypothesis')
  })
})
