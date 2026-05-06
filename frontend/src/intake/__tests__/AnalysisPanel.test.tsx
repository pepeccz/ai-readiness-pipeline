/**
 * B-3 — REQ-2: AnalysisPanel handles status='skipped' gracefully
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AnalysisPanel } from '../AnalysisPanel'

// ---------------------------------------------------------------------------
// Mock useBlockAnalysisPolling — controlled per test
// ---------------------------------------------------------------------------
const mockUseBlockAnalysisPolling = vi.fn()
vi.mock('../../shared/hooks/useBlockAnalysisPolling', () => ({
  useBlockAnalysisPolling: (...args: unknown[]) => mockUseBlockAnalysisPolling(...args),
}))

// Mock useSuggestionAction
vi.mock('../api/intake', () => ({
  useSuggestionAction: () => ({ mutate: vi.fn(), isPending: false }),
}))

describe('AnalysisPanel — B-3: skipped status', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('B-3: renders neutral "Análisis IA omitido" message when status=skipped', () => {
    mockUseBlockAnalysisPolling.mockReturnValue({
      data: { block_analysis_id: 'ba-1', status: 'skipped', llm_output: null, suggestions: [], generated_at: null },
      isLoading: false,
      isError: false,
    })

    render(<AnalysisPanel leadId="lead-1" blockId="block-a" />)
    expect(screen.getByText(/análisis ia omitido/i)).toBeInTheDocument()
  })

  it('B-3: skipped status does NOT render error state or error testid', () => {
    mockUseBlockAnalysisPolling.mockReturnValue({
      data: { block_analysis_id: 'ba-1', status: 'skipped', llm_output: null, suggestions: [], generated_at: null },
      isLoading: false,
      isError: false,
    })

    render(<AnalysisPanel leadId="lead-1" blockId="block-a" />)
    expect(screen.queryByTestId('analysis-error')).toBeNull()
  })

  it('B-3: skipped status does NOT render the skeleton loader', () => {
    mockUseBlockAnalysisPolling.mockReturnValue({
      data: { block_analysis_id: 'ba-1', status: 'skipped', llm_output: null, suggestions: [], generated_at: null },
      isLoading: false,
      isError: false,
    })

    render(<AnalysisPanel leadId="lead-1" blockId="block-a" />)
    expect(screen.queryByTestId('analysis-skeleton')).toBeNull()
  })

  it('B-3: failed status still renders error message (regression guard)', () => {
    mockUseBlockAnalysisPolling.mockReturnValue({
      data: { block_analysis_id: 'ba-2', status: 'failed', llm_output: null, suggestions: [], generated_at: null },
      isLoading: false,
      isError: false,
    })

    render(<AnalysisPanel leadId="lead-1" blockId="block-b" />)
    expect(screen.getByTestId('analysis-error')).toBeInTheDocument()
  })

  it('B-3: ready status still renders analysis panel (regression guard)', () => {
    mockUseBlockAnalysisPolling.mockReturnValue({
      data: {
        block_analysis_id: 'ba-3',
        status: 'ready',
        llm_output: { synthesis: 'Síntesis ok', contradictions: [], follow_ups: [], preliminary_hypothesis: null },
        suggestions: [],
        generated_at: '2026-01-01',
      },
      isLoading: false,
      isError: false,
    })

    render(<AnalysisPanel leadId="lead-1" blockId="block-c" />)
    expect(screen.getByTestId('analysis-panel')).toBeInTheDocument()
  })
})
