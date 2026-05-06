/**
 * TA.13 — REQ-5 / ADR-6: IntakeApp passes undefined (not '') to useBlockPayload
 * A-2  — REQ-2: always-rendered min-h-[300px] placeholder div below BlockRenderer
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// ---------------------------------------------------------------------------
// Configurable mocks — adjusted per describe block via beforeEach
// ---------------------------------------------------------------------------
const mockUseBlockPayload = vi.fn().mockReturnValue({ data: undefined })
const mockUseIntakeSchema = vi.fn().mockReturnValue({ data: undefined, isLoading: true })
const mockUseIntakeSession = vi.fn().mockReturnValue({
  session: null,
  isLoading: true,
  hasAreaSelected: () => false,
})

vi.mock('../api/intake', () => ({
  useIntakeSchema: (...args: unknown[]) => mockUseIntakeSchema(...args),
  useBlockPayload: (...args: unknown[]) => mockUseBlockPayload(...args),
  intakeKeys: {
    state: (id: string) => ['intake', id, 'state'],
    schema: (id: string, area?: string) => ['intake', id, 'schema', area],
  },
}))

vi.mock('../hooks/useIntakeSession', () => ({
  useIntakeSession: (...args: unknown[]) => mockUseIntakeSession(...args),
}))

vi.mock('../components/Session1CloseFooter', () => ({
  Session1CloseFooter: () => null,
}))

vi.mock('../AreaSelector', () => ({
  AreaSelector: () => null,
}))

vi.mock('../BlockRenderer', () => ({
  BlockRenderer: () => null,
}))

vi.mock('../components/BlockNav', () => ({
  BlockNav: () => null,
}))

vi.mock('../AnalysisPanel', () => ({
  AnalysisPanel: () => null,
}))

vi.mock('../../admin/components/LifecycleBadge', () => ({
  LifecycleBadge: () => null,
}))

function makeWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </MemoryRouter>
  )
}

// ---------------------------------------------------------------------------
// TA.13 — REQ-5: passes undefined not empty string to useBlockPayload
// ---------------------------------------------------------------------------

describe('IntakeApp — TA.13: passes undefined not empty string to useBlockPayload (REQ-5)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseBlockPayload.mockReturnValue({ data: undefined })
    mockUseIntakeSchema.mockReturnValue({ data: undefined, isLoading: true })
    mockUseIntakeSession.mockReturnValue({
      session: null,
      isLoading: true,
      hasAreaSelected: () => false,
    })
  })

  it('passes undefined as blockId when currentBlockId is null', async () => {
    const { default: React } = await import('react')
    const { IntakeApp } = await import('../IntakeApp')
    const Wrapper = makeWrapper()

    render(
      <Wrapper>
        <IntakeApp leadId="lead-123" />
      </Wrapper>
    )

    // useBlockPayload should be called with leadId and undefined, NOT ''
    expect(mockUseBlockPayload).toHaveBeenCalled()
    const [calledLeadId, calledBlockId] = mockUseBlockPayload.mock.calls[0]
    expect(calledLeadId).toBe('lead-123')
    expect(calledBlockId).toBeUndefined()
    expect(calledBlockId).not.toBe('')
  })
})

// ---------------------------------------------------------------------------
// A-2 — REQ-2: always-rendered placeholder div below BlockRenderer
// ---------------------------------------------------------------------------

describe('IntakeApp — A-2: placeholder div min-h-[300px] always rendered (REQ-2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseBlockPayload.mockReturnValue({ data: undefined })
  })

  it('A-2: renders placeholder div with min-h-[300px] when block is selected and no analysis yet', async () => {
    const { default: React } = await import('react')
    const { IntakeApp } = await import('../IntakeApp')

    mockUseIntakeSession.mockReturnValue({
      session: { state: 'in_progress', primary_area: 'tech', blocks_completed: [] },
      isLoading: false,
      hasAreaSelected: () => true,
    })

    mockUseIntakeSchema.mockReturnValue({
      data: {
        blocks_order: ['block-1-strategic'],
        blocks: [{ id: 'block-1-strategic', title: 'Strategic', questions: [], estimated_minutes: 10, layer: 'core', order: 1 }],
        area_selector: {},
        area: 'tech',
      },
      isLoading: false,
    })

    const Wrapper = makeWrapper()
    const { container } = render(
      <Wrapper><IntakeApp leadId="lead-123" /></Wrapper>
    )

    // Placeholder with min-h-[300px] must exist regardless of lastSubmittedBlock
    const placeholder = container.querySelector('.min-h-\\[300px\\]')
    expect(placeholder).not.toBeNull()
  })
})
