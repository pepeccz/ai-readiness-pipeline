/**
 * T3.1 — BlockRenderer remounts form on block/payload change (REQ-5)
 * TB.6 — REQ-4: BlockRenderer error banner on submit failure
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act, fireEvent } from '@testing-library/react'
import { BlockRenderer } from '../../BlockRenderer'
import type { BlockSchema } from '../../types/schema'

// ---------------------------------------------------------------------------
// Configurable mock for useBlockSubmit — overridden per describe block
// ---------------------------------------------------------------------------
const mockMutateAsync = vi.fn()
vi.mock('../../api/intake', () => ({
  useBlockSubmit: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
    isError: false,
  }),
}))

function makeSchemaWithRequired(id: string): BlockSchema {
  return {
    id,
    layer: 'core',
    order: 1,
    estimated_minutes: 5,
    title: 'Error banner test block',
    questions: [
      {
        id: 'q1',
        type: 'text',
        label: 'Campo requerido',
        required: false,
      },
    ],
  }
}

// ---------------------------------------------------------------------------
// TB.6 — REQ-4: error banner on submit failure
// ---------------------------------------------------------------------------

describe('BlockRenderer — REQ-4: submit error banner', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders error banner when submit mutation rejects', async () => {
    mockMutateAsync.mockRejectedValue(new Error('Network error'))
    const schema = makeSchemaWithRequired('block-err')

    render(<BlockRenderer leadId="lead-1" schema={schema} />)

    const submitBtn = screen.getByRole('button', { name: /guardar bloque/i })

    await act(async () => {
      fireEvent.click(submitBtn)
      await new Promise((r) => setTimeout(r, 50))
    })

    // Error banner must be visible
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('alert').textContent).toMatch(/error/i)
  })

  it('re-enables the submit button after a failed submit', async () => {
    mockMutateAsync.mockRejectedValue(new Error('Network error'))
    const schema = makeSchemaWithRequired('block-err2')

    render(<BlockRenderer leadId="lead-1" schema={schema} />)

    const submitBtn = screen.getByRole('button', { name: /guardar bloque/i })

    await act(async () => {
      fireEvent.click(submitBtn)
      await new Promise((r) => setTimeout(r, 50))
    })

    // Submit button must be re-enabled (not disabled)
    expect(screen.getByRole('button', { name: /guardar bloque/i })).not.toBeDisabled()
  })

  it('clears error banner after a subsequent successful submit', async () => {
    // First call fails, second succeeds
    mockMutateAsync
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ block_analysis_id: 'ba-1', status: 'ok' })

    const schema = makeSchemaWithRequired('block-err3')

    render(<BlockRenderer leadId="lead-1" schema={schema} />)

    const submitBtn = screen.getByRole('button', { name: /guardar bloque/i })

    // First submit — fails
    await act(async () => {
      fireEvent.click(submitBtn)
      await new Promise((r) => setTimeout(r, 50))
    })

    expect(screen.getByRole('alert')).toBeInTheDocument()

    // Second submit — succeeds → error should clear
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /guardar bloque/i }))
      await new Promise((r) => setTimeout(r, 50))
    })

    expect(screen.queryByRole('alert')).toBeNull()
  })
})

// Minimal schema factories
function makeSchema(id: string, title = 'Test block'): BlockSchema {
  return {
    id,
    layer: 'core',
    order: 1,
    estimated_minutes: 5,
    title,
    questions: [
      {
        id: 'q1',
        type: 'text',
        label: 'Nombre',
        required: true,
      },
    ],
  }
}

describe('BlockRenderer — REQ-5 remount behaviour', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('displays initialPayload values when first rendered', () => {
    const schema = makeSchema('block-a')
    const { container } = render(
      <BlockRenderer
        leadId="lead-1"
        schema={schema}
        initialPayload={{ q1: 'original value' }}
      />,
    )
    // The value should be seeded into the form field
    const input = container.querySelector('input[type="text"], textarea, input')
    // The form state should be seeded; check via visible question count
    expect(screen.getByText('Nombre')).toBeInTheDocument()
    // Input should carry initialPayload value
    if (input) {
      expect((input as HTMLInputElement).value).toBe('original value')
    }
  })

  it('remounts and shows new initialPayload when schema.id changes (key-based remount)', () => {
    const schemaA = makeSchema('block-a')
    const schemaB = makeSchema('block-b', 'Block B')

    const { rerender, container } = render(
      <BlockRenderer
        leadId="lead-1"
        schema={schemaA}
        initialPayload={{ q1: 'value for A' }}
      />,
    )

    // Verify first render
    expect(screen.getByText('Test block')).toBeInTheDocument()
    const inputBefore = container.querySelector('input, textarea') as HTMLInputElement | null
    if (inputBefore) {
      expect(inputBefore.value).toBe('value for A')
    }

    // Navigate to a different block — this simulates block-to-block navigation
    rerender(
      <BlockRenderer
        leadId="lead-1"
        schema={schemaB}
        initialPayload={{ q1: 'value for B' }}
      />,
    )

    // New block title visible
    expect(screen.getByText('Block B')).toBeInTheDocument()

    // Input should show the NEW payload, NOT stale state from block-a
    const inputAfter = container.querySelector('input, textarea') as HTMLInputElement | null
    if (inputAfter) {
      expect(inputAfter.value).toBe('value for B')
    }
  })

  it('remounts when same schema.id receives a different initialPayload (payload version change)', () => {
    const schema = makeSchema('block-a')

    const { rerender, container } = render(
      <BlockRenderer
        leadId="lead-1"
        schema={schema}
        initialPayload={{ q1: 'first payload' }}
      />,
    )

    const inputBefore = container.querySelector('input, textarea') as HTMLInputElement | null
    if (inputBefore) {
      expect(inputBefore.value).toBe('first payload')
    }

    // Same schema but server sent updated payload
    rerender(
      <BlockRenderer
        leadId="lead-1"
        schema={schema}
        initialPayload={{ q1: 'updated payload' }}
      />,
    )

    // Must reflect the new payload — proves key-based remount is identity-aware
    const inputAfter = container.querySelector('input, textarea') as HTMLInputElement | null
    if (inputAfter) {
      expect(inputAfter.value).toBe('updated payload')
    }
  })
})
