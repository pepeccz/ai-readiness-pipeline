/**
 * B-3 — REQ-2: AnalysisPanel handles status='skipped' gracefully
 * A-3 — REQ-2: AnalysisPanel root ref + scrollIntoView after submit
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act, fireEvent, waitFor } from '@testing-library/react'
import { AnalysisPanel } from '../AnalysisPanel'

// ---------------------------------------------------------------------------
// Mock useBlockAnalysisPolling — controlled per test
// ---------------------------------------------------------------------------
const mockUseBlockAnalysisPolling = vi.fn()
vi.mock('../../shared/hooks/useBlockAnalysisPolling', () => ({
  useBlockAnalysisPolling: (...args: unknown[]) => mockUseBlockAnalysisPolling(...args),
}))

// Mock useSuggestionAction + useUpdateSuggestionNote (added in C-3)
const mockNoteMutate = vi.fn()
vi.mock('../api/intake', () => ({
  useSuggestionAction: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateSuggestionNote: () => ({ mutate: mockNoteMutate, isPending: false, isError: false }),
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

// ---------------------------------------------------------------------------
// A-3 — REQ-2: AnalysisPanel scrollIntoView on mount when status=ready
// ---------------------------------------------------------------------------

describe('AnalysisPanel — A-3: scrollIntoView called on mount when ready (REQ-2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    window.HTMLElement.prototype.scrollIntoView = vi.fn()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('A-3: scrollIntoView is called with smooth+start after 100ms when status becomes ready', async () => {
    mockUseBlockAnalysisPolling.mockReturnValue({
      data: {
        block_analysis_id: 'ba-scroll',
        status: 'ready',
        llm_output: { synthesis: 'Síntesis', contradictions: [], follow_ups: [], preliminary_hypothesis: null },
        suggestions: [],
        generated_at: '2026-01-01',
      },
      isLoading: false,
      isError: false,
    })

    render(<AnalysisPanel leadId="lead-1" blockId="block-scroll" />)

    // Before timer fires — scrollIntoView not yet called
    expect(window.HTMLElement.prototype.scrollIntoView).not.toHaveBeenCalled()

    // Advance timer by 100ms
    await act(async () => {
      vi.advanceTimersByTime(100)
    })

    expect(window.HTMLElement.prototype.scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'start',
    })
  })

  it('A-3: scrollIntoView is NOT called when status is pending_analysis', async () => {
    mockUseBlockAnalysisPolling.mockReturnValue({
      data: { block_analysis_id: 'ba-pending', status: 'pending_analysis', llm_output: null, suggestions: [], generated_at: null },
      isLoading: false,
      isError: false,
    })

    render(<AnalysisPanel leadId="lead-1" blockId="block-pending-scroll" />)

    await act(async () => {
      vi.advanceTimersByTime(200)
    })

    expect(window.HTMLElement.prototype.scrollIntoView).not.toHaveBeenCalled()
  })
})

// ---------------------------------------------------------------------------
// C-4 — REQ-4: consultant note textarea per suggestion
// ---------------------------------------------------------------------------

function makeReadyAnalysis(suggestions: unknown[]) {
  return {
    data: {
      block_analysis_id: 'ba-c4',
      status: 'ready',
      llm_output: { synthesis: 'Síntesis', contradictions: [], follow_ups: [], preliminary_hypothesis: null },
      suggestions,
      generated_at: '2026-01-01',
    },
    isLoading: false,
    isError: false,
  }
}

describe('AnalysisPanel — C-4: consultant note textarea per suggestion (REQ-4)', () => {
  beforeEach(() => {
    mockNoteMutate.mockReset()
    vi.useFakeTimers()
    window.HTMLElement.prototype.scrollIntoView = vi.fn()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('C-4: renders "Anotar respuesta del cliente" textarea per suggestion', () => {
    mockUseBlockAnalysisPolling.mockReturnValue(makeReadyAnalysis([
      { id: 'sug-1', type: 'follow_up', text: 'Q1', rationale: null, confidence: 0.9, priority: 'high', consultant_action: 'pending', consultant_note_text: null },
    ]))

    render(<AnalysisPanel leadId="lead-1" blockId="block-c4" />)

    expect(screen.getByPlaceholderText(/anotar respuesta/i)).toBeInTheDocument()
  })

  it('C-4: pre-fills textarea with existing consultant_note_text', () => {
    mockUseBlockAnalysisPolling.mockReturnValue(makeReadyAnalysis([
      { id: 'sug-1', type: 'follow_up', text: 'Q1', rationale: null, confidence: 0.9, priority: 'high', consultant_action: 'pending', consultant_note_text: 'Previous note' },
    ]))

    render(<AnalysisPanel leadId="lead-1" blockId="block-c4-prefill" />)

    expect(screen.getByDisplayValue('Previous note')).toBeInTheDocument()
  })

  it('C-4: PATCH fires on blur (save triggered when user leaves field)', async () => {
    mockUseBlockAnalysisPolling.mockReturnValue(makeReadyAnalysis([
      { id: 'sug-1', type: 'follow_up', text: 'Q1', rationale: null, confidence: 0.9, priority: 'high', consultant_action: 'pending', consultant_note_text: null },
    ]))

    render(<AnalysisPanel leadId="lead-1" blockId="block-c4-debounce" />)

    const textarea = screen.getByPlaceholderText(/anotar respuesta/i)

    fireEvent.change(textarea, { target: { value: 'typed note' } })

    // Verify the value updated (proves fireEvent works)
    expect((textarea as HTMLTextAreaElement).value).toBe('typed note')

    // Trigger blur to force immediate save (bypasses debounce)
    fireEvent.blur(textarea)

    expect(mockNoteMutate).toHaveBeenCalledWith({ note: 'typed note' }, expect.any(Object))
  })

  it('C-4: textarea retains value while in-flight (optimistic local state)', async () => {
    mockUseBlockAnalysisPolling.mockReturnValue(makeReadyAnalysis([
      { id: 'sug-1', type: 'follow_up', text: 'Q1', rationale: null, confidence: 0.9, priority: 'high', consultant_action: 'pending', consultant_note_text: null },
    ]))

    render(<AnalysisPanel leadId="lead-1" blockId="block-c4-optimistic" />)

    const textarea = screen.getByPlaceholderText(/anotar respuesta/i) as HTMLTextAreaElement
    fireEvent.change(textarea, { target: { value: 'in-flight value' } })

    // Value must persist without waiting for PATCH response
    expect(textarea.value).toBe('in-flight value')
  })
})
