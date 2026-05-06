/**
 * SessionSynthesisPanel.test.tsx — H.2 Updated fixtures for new dual-mode component.
 *
 * Tests the new props-based SessionSynthesisPanel interface.
 * Replaces old useIntakeState-based tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import type { Session1Synthesis } from '../../../types/api'

// Mock useCatalog hook (no network calls in tests)
vi.mock('../../hooks/useCatalog', () => ({
  useServiceCatalog: () => ({
    data: [],
    isLoading: false,
    isError: false,
  }),
}))

import { SessionSynthesisPanel } from '../SessionSynthesisPanel'

// ── Fixtures (H.2 — updated to new schema) ─────────────────────────────────

const legacySynthesis: Session1Synthesis = {
  summary: 'Executive summary text',
  key_insights: ['Insight A', 'Insight B'],
  // Legacy: recommendations as string array — coerced to RecommendationItem by backend
  // Frontend receives them as objects after coercion
  recommendations: [{ text: 'Rec 1', impact: null, effort: null, related_service: null }],
  hypothesis: 'Hypothesis text',
  generated_at: '2026-01-01T00:00:00Z',
  model: 'claude-sonnet-4-6',
}

const newSchemaSynthesis: Session1Synthesis = {
  summary: 'Executive summary text',
  key_insights: ['Insight A', 'Insight B'],
  recommendations: [
    {
      text: 'Rec 1',
      impact: 'alto',
      effort: 'medio',
      related_service: 'desarrollo_acompanamiento',
    },
  ],
  roadmap: { d30: ['Step 1'], d60: ['Step 2'], d90: [] },
  next_steps: ['Next step 1'],
  hypothesis: 'Hypothesis text',
  synthesis_edited_at: '2026-05-06T15:00:00Z',
  synthesis_last_exported_at: '2026-05-06T14:00:00Z',
  synthesis_export_count: 1,
  generated_at: '2026-01-01T00:00:00Z',
  model: 'claude-sonnet-4-6',
}

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
    const { container } = render(
      React.createElement(SessionSynthesisPanel, {
        leadId: 'lead-1',
        intakeState: 'not_started',
        synthesisEffective: null,
        synthesisRaw: null,
      }),
      { wrapper: wrapper() }
    )
    expect(container.firstChild).toBeNull()
  })

  it('returns null when state is in_progress', () => {
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

  it('renders read-only view when deep_pending with synthesis', () => {
    render(
      React.createElement(SessionSynthesisPanel, {
        leadId: 'lead-1',
        intakeState: 'deep_pending',
        synthesisEffective: legacySynthesis,
        synthesisRaw: legacySynthesis,
      }),
      { wrapper: wrapper() }
    )
    expect(screen.getByDisplayValue('Executive summary text')).toBeInTheDocument()
    // No Guardar button in view mode
    expect(screen.queryByRole('button', { name: /guardar/i })).not.toBeInTheDocument()
  })

  it('renders synthesis content when status is ready (new schema)', () => {
    render(
      React.createElement(SessionSynthesisPanel, {
        leadId: 'lead-1',
        intakeState: 'deep_received',
        synthesisEffective: newSchemaSynthesis,
        synthesisRaw: newSchemaSynthesis,
      }),
      { wrapper: wrapper() }
    )
    expect(screen.getByDisplayValue('Executive summary text')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Insight A')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Rec 1')).toBeInTheDocument()
    // Hypothesis is visible
    expect(screen.getByText('Hypothesis text')).toBeInTheDocument()
  })

  it('shows editable form with Guardar when deep_received', () => {
    render(
      React.createElement(SessionSynthesisPanel, {
        leadId: 'lead-1',
        intakeState: 'deep_received',
        synthesisEffective: newSchemaSynthesis,
        synthesisRaw: newSchemaSynthesis,
      }),
      { wrapper: wrapper() }
    )
    expect(screen.getByRole('button', { name: /guardar/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /guardar/i })).toBeDisabled()
  })

  it('renders legacy synthesis (string recs as objects) without crash', () => {
    render(
      React.createElement(SessionSynthesisPanel, {
        leadId: 'lead-1',
        intakeState: 'deep_received',
        synthesisEffective: legacySynthesis,
        synthesisRaw: legacySynthesis,
      }),
      { wrapper: wrapper() }
    )
    // Should render without error and show the recommendation text
    expect(screen.getByDisplayValue('Rec 1')).toBeInTheDocument()
  })
})
