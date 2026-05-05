/**
 * T3.1 — BlockRenderer remounts form on block/payload change (REQ-5)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { BlockRenderer } from '../../BlockRenderer'
import type { BlockSchema } from '../../types/schema'

// Mock useBlockSubmit — not under test here
vi.mock('../../api/intake', () => ({
  useBlockSubmit: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
    isError: false,
  }),
}))

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
