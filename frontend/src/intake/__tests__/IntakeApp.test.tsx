/**
 * TA.13 — REQ-5 / ADR-6: IntakeApp passes undefined (not '') to useBlockPayload
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// ---------------------------------------------------------------------------
// Mock useBlockPayload — capture arguments
// ---------------------------------------------------------------------------
const mockUseBlockPayload = vi.fn().mockReturnValue({ data: undefined })

vi.mock('../api/intake', () => ({
  useIntakeSchema: () => ({ data: undefined, isLoading: true }),
  useBlockPayload: (...args: unknown[]) => mockUseBlockPayload(...args),
  intakeKeys: {
    state: (id: string) => ['intake', id, 'state'],
    schema: (id: string, area?: string) => ['intake', id, 'schema', area],
  },
}))

vi.mock('../hooks/useIntakeSession', () => ({
  useIntakeSession: () => ({
    session: null,
    isLoading: true,
    hasAreaSelected: () => false,
  }),
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

describe('IntakeApp — TA.13: passes undefined not empty string to useBlockPayload (REQ-5)', () => {
  beforeEach(() => {
    mockUseBlockPayload.mockClear()
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
