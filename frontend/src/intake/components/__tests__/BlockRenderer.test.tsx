/**
 * T3.1 — BlockRenderer remounts form on block/payload change (REQ-5)
 * TB.6 — REQ-4: BlockRenderer error banner on submit failure
 * TA.5 — REQ-1: BlockRenderer rehydration with composite expansion
 * TA.9 — REQ-4: BlockRenderer error copy mapping by errorKind
 * TA.11 — REQ-3: BlockRenderer formKey remount — no form.reset()
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act, fireEvent, waitFor } from '@testing-library/react'
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

// ---------------------------------------------------------------------------
// Mock useDraftAutosave — controlled per test via mockAutosaveReturn
// ---------------------------------------------------------------------------
type ErrorKind = 'network' | 'http_client' | 'http_server' | 'unknown'
let mockAutosaveReturn: {
  savedAt: Date | null
  status: string
  errorKind?: ErrorKind
  errorMessage?: string
} = { savedAt: null, status: 'idle' }

vi.mock('../../hooks/useDraftAutosave', () => ({
  useDraftAutosave: () => mockAutosaveReturn,
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

    const submitBtn = screen.getByRole('button', { name: /cerrar bloque/i })

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

    const submitBtn = screen.getByRole('button', { name: /cerrar bloque/i })

    await act(async () => {
      fireEvent.click(submitBtn)
      await new Promise((r) => setTimeout(r, 50))
    })

    // Submit button must be re-enabled (not disabled)
    expect(screen.getByRole('button', { name: /cerrar bloque/i })).not.toBeDisabled()
  })

  it('clears error banner after a subsequent successful submit', async () => {
    // First call fails, second succeeds
    mockMutateAsync
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ block_analysis_id: 'ba-1', status: 'ok' })

    const schema = makeSchemaWithRequired('block-err3')

    render(<BlockRenderer leadId="lead-1" schema={schema} />)

    const submitBtn = screen.getByRole('button', { name: /cerrar bloque/i })

    // First submit — fails
    await act(async () => {
      fireEvent.click(submitBtn)
      await new Promise((r) => setTimeout(r, 50))
    })

    expect(screen.getByRole('alert')).toBeInTheDocument()

    // Second submit — succeeds → error should clear
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /cerrar bloque/i }))
      await new Promise((r) => setTimeout(r, 50))
    })

    expect(screen.queryByRole('alert')).toBeNull()
  })
})

// ---------------------------------------------------------------------------
// T3 — REQ-2: global validation error banner on submit with invalid fields
// T4 — REQ-2: data-error attribute present + scrollIntoView called
// T6 — REQ-3: button label is "Cerrar bloque" + helper text
// ---------------------------------------------------------------------------

function makeSchemaWithRequiredField(id: string): BlockSchema {
  return {
    id,
    layer: 'core',
    order: 1,
    estimated_minutes: 5,
    title: 'Validation banner test',
    questions: [
      {
        id: 'req_field',
        type: 'text',
        label: 'Campo obligatorio',
        required: true,
      },
    ],
  }
}

describe('BlockRenderer — T3/T4: validation error banner + data-error (REQ-2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    // Mock scrollIntoView — not available in jsdom
    window.HTMLElement.prototype.scrollIntoView = vi.fn()
  })

  it('T3: shows global error banner with field count after submit when required field is empty', async () => {
    const schema = makeSchemaWithRequiredField('block-val-banner')
    render(<BlockRenderer leadId="lead-1" schema={schema} />)

    const submitBtn = screen.getByRole('button', { name: /cerrar bloque/i })
    await act(async () => {
      fireEvent.click(submitBtn)
    })

    expect(screen.getByRole('alert', { name: /campos requeridos/i })).toBeInTheDocument()
    expect(screen.getByText(/1 campo/i)).toBeInTheDocument()
  })

  it('T4: [data-error="true"] wrapper present after failed submit', async () => {
    const schema = makeSchemaWithRequiredField('block-data-error')
    const { container } = render(<BlockRenderer leadId="lead-1" schema={schema} />)

    const submitBtn = screen.getByRole('button', { name: /cerrar bloque/i })
    await act(async () => {
      fireEvent.click(submitBtn)
    })

    expect(container.querySelector('[data-error="true"]')).toBeTruthy()
  })

  it('T4: scrollIntoView is called after failed submit', async () => {
    const schema = makeSchemaWithRequiredField('block-scroll')
    render(<BlockRenderer leadId="lead-1" schema={schema} />)

    const submitBtn = screen.getByRole('button', { name: /cerrar bloque/i })
    await act(async () => {
      fireEvent.click(submitBtn)
    })

    expect(window.HTMLElement.prototype.scrollIntoView).toHaveBeenCalled()
  })
})

describe('BlockRenderer — T6: submit button label (REQ-3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('T6: button label is "Cerrar bloque" (not "Guardar bloque")', () => {
    const schema = makeSchemaWithRequiredField('block-label')
    render(<BlockRenderer leadId="lead-1" schema={schema} />)

    expect(screen.getByRole('button', { name: /cerrar bloque/i })).toBeInTheDocument()
    expect(screen.queryByText(/guardar bloque/i)).toBeNull()
  })

  it('T6: helper text "Genera análisis IA y habilita cierre de sesión" is visible', () => {
    const schema = makeSchemaWithRequiredField('block-helper')
    render(<BlockRenderer leadId="lead-1" schema={schema} />)

    expect(screen.getByText(/Genera análisis IA y habilita cierre de sesión/i)).toBeInTheDocument()
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

// ---------------------------------------------------------------------------
// TA.5 — REQ-1: BlockRenderer rehydration effect with composite expansion
// ---------------------------------------------------------------------------

function makeCompositeSchema(id: string): BlockSchema {
  return {
    id,
    layer: 'core',
    order: 1,
    estimated_minutes: 5,
    title: 'Composite block',
    questions: [
      {
        id: 'comp1',
        type: 'composite',
        label: 'Composite question',
        sub_fields: [
          { id: 'comp1_objective', type: 'text', label: 'Objective' },
          { id: 'comp1_effort', type: 'text', label: 'Effort' },
        ],
      } as BlockSchema['questions'][0],
    ],
  }
}

describe('BlockRenderer — TA.5: rehydration with composite expansion (REQ-1)', () => {
  beforeEach(() => {
    mockAutosaveReturn = { savedAt: null, status: 'idle' }
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('applies flat sub-field values when initialPayload is nested composite', () => {
    const schema = makeCompositeSchema('block-composite')
    // Nested composite payload: comp1 is an object with sub-keys
    render(
      <BlockRenderer
        leadId="lead-1"
        schema={schema}
        initialPayload={{ comp1: { comp1_objective: 'A', comp1_effort: 'B' } }}
      />
    )
    // Both sub-fields should be rendered and have their values
    const inputs = document.querySelectorAll('input, textarea')
    const values = Array.from(inputs).map((i) => (i as HTMLInputElement).value)
    expect(values).toContain('A')
    expect(values).toContain('B')
  })

  it('is idempotent: already-flat payload passes through unchanged', () => {
    const schema = makeCompositeSchema('block-composite-flat')
    render(
      <BlockRenderer
        leadId="lead-1"
        schema={schema}
        initialPayload={{ comp1_objective: 'X', comp1_effort: 'Y' }}
      />
    )
    const inputs = document.querySelectorAll('input, textarea')
    const values = Array.from(inputs).map((i) => (i as HTMLInputElement).value)
    expect(values).toContain('X')
    expect(values).toContain('Y')
  })
})

// ---------------------------------------------------------------------------
// TA.9 — REQ-4: BlockRenderer error copy mapping by errorKind
// ---------------------------------------------------------------------------

function makeSimpleSchema(id: string): BlockSchema {
  return {
    id,
    layer: 'core',
    order: 1,
    estimated_minutes: 5,
    title: 'Simple block',
    questions: [{ id: 'q1', type: 'text', label: 'Q1', required: false }],
  }
}

describe('BlockRenderer — TA.9: error copy mapping by errorKind (REQ-4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders "Sin conexión — borrador en local" for errorKind=network', () => {
    mockAutosaveReturn = { savedAt: null, status: 'error', errorKind: 'network' }
    render(<BlockRenderer leadId="lead-1" schema={makeSimpleSchema('block-ek-net')} />)
    expect(screen.getByText(/Sin conexión — borrador en local/i)).toBeInTheDocument()
  })

  it('renders "Error al guardar (verificá datos)" for errorKind=http_client', () => {
    mockAutosaveReturn = { savedAt: null, status: 'error', errorKind: 'http_client' }
    render(<BlockRenderer leadId="lead-1" schema={makeSimpleSchema('block-ek-4xx')} />)
    expect(screen.getByText(/Error al guardar \(verificá datos\)/i)).toBeInTheDocument()
  })

  it('renders "Error del servidor — reintentando" for errorKind=http_server', () => {
    mockAutosaveReturn = { savedAt: null, status: 'error', errorKind: 'http_server' }
    render(<BlockRenderer leadId="lead-1" schema={makeSimpleSchema('block-ek-5xx')} />)
    expect(screen.getByText(/Error del servidor — reintentando/i)).toBeInTheDocument()
  })

  it('renders "Error al guardar borrador" for errorKind=unknown', () => {
    mockAutosaveReturn = { savedAt: null, status: 'error', errorKind: 'unknown' }
    render(<BlockRenderer leadId="lead-1" schema={makeSimpleSchema('block-ek-unk')} />)
    expect(screen.getByText(/Error al guardar borrador/i)).toBeInTheDocument()
  })

  it('does not render network copy for http_client kind', () => {
    mockAutosaveReturn = { savedAt: null, status: 'error', errorKind: 'http_client' }
    render(<BlockRenderer leadId="lead-1" schema={makeSimpleSchema('block-ek-no-bleed')} />)
    expect(screen.queryByText(/Sin conexión/i)).toBeNull()
  })
})

// ---------------------------------------------------------------------------
// TA.11 — REQ-3: BlockRenderer formKey remount — no form.reset()
// ---------------------------------------------------------------------------

describe('BlockRenderer — TA.11: formKey remount, no form.reset() (REQ-3)', () => {
  beforeEach(() => {
    mockAutosaveReturn = { savedAt: null, status: 'idle' }
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('formKey flips when initialPayload changes (monotonic advance)', () => {
    const schema = makeSimpleSchema('block-fk')
    const { rerender } = render(
      <BlockRenderer leadId="lead-1" schema={schema} initialPayload={{ q1: 'v1' }} />
    )
    const inputBefore = document.querySelector('input, textarea') as HTMLInputElement | null
    const valueBefore = inputBefore?.value

    rerender(
      <BlockRenderer leadId="lead-1" schema={schema} initialPayload={{ q1: 'v2' }} />
    )
    const inputAfter = document.querySelector('input, textarea') as HTMLInputElement | null
    expect(inputAfter?.value).toBe('v2')
    expect(inputAfter?.value).not.toBe(valueBefore)
  })

  it('submit success does not crash (form.reset() removed)', async () => {
    mockMutateAsync.mockResolvedValue({ block_analysis_id: 'ba-1' })
    const schema = makeSimpleSchema('block-noreset')
    render(<BlockRenderer leadId="lead-1" schema={schema} />)

    const submitBtn = screen.getByRole('button', { name: /cerrar bloque/i })
    await act(async () => {
      fireEvent.click(submitBtn)
      await new Promise((r) => setTimeout(r, 50))
    })
    // Should not throw; no form.reset() is called
    expect(screen.queryByRole('alert')).toBeNull()
  })
})
