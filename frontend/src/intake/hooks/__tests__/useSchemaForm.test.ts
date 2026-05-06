/**
 * T3.5 — useSchemaForm handles matrix type in validate() and buildPayload() (REQ-9)
 * + getAnsweredQuestions helper tests (REQ-1)
 */
import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSchemaForm, getAnsweredQuestions } from '../useSchemaForm'
import type { BlockSchema } from '../../types/schema'

// Matrix question schema — mirrors the YAML rows×columns structure (ADR-6)
function makeMatrixSchema(): BlockSchema {
  return {
    id: 'block-matrix',
    layer: 'core',
    order: 1,
    estimated_minutes: 3,
    title: 'Matrix block',
    questions: [
      {
        id: 'matrix_q1',
        type: 'matrix',
        label: 'Evaluación de áreas',
        required: true,
        rows: [
          { id: 'row_ops', label: 'Operaciones' },
          { id: 'row_tech', label: 'Tecnología' },
        ],
        columns: [
          { id: 'col_low', label: 'Bajo' },
          { id: 'col_med', label: 'Medio' },
          { id: 'col_high', label: 'Alto' },
        ],
      } as any, // typed below; schema.ts will get MatrixQuestion added
    ],
  }
}

// ---------------------------------------------------------------------------
// T1 — REQ-1: validateQuestion returns null for composite parent
// Strict TDD — RED before IMPL
// ---------------------------------------------------------------------------

describe('useSchemaForm — composite parent validation (REQ-1)', () => {
  function makeCompositeValidationSchema(): BlockSchema {
    return {
      id: 'block-composite-val',
      layer: 'core',
      order: 1,
      estimated_minutes: 5,
      title: 'Composite val block',
      questions: [
        {
          id: 'q1_1_objective',
          type: 'composite',
          label: 'Objetivo estratégico',
          required: true,
          sub_fields: [
            { id: 'q1_1_outcome', type: 'text', label: 'Resultado', required: true },
            { id: 'q1_1_metric', type: 'text', label: 'Métrica', required: true },
            { id: 'q1_1_horizon', type: 'text', label: 'Horizonte', required: true },
          ],
        } as any,
      ],
    }
  }

  it('validate() returns true when composite parent is required:true AND all sub-fields are filled', () => {
    const { result } = renderHook(() => useSchemaForm(makeCompositeValidationSchema()))

    act(() => {
      result.current.setValue('q1_1_outcome', 'Aumentar ingresos')
      result.current.setValue('q1_1_metric', 'Revenue ARR')
      result.current.setValue('q1_1_horizon', '12 meses')
    })

    let valid: boolean
    act(() => {
      valid = result.current.validate()
    })

    expect(valid!).toBe(true)
    expect(result.current.errors['q1_1_objective']).toBeFalsy()
  })

  it('validate() returns false when composite sub-fields are missing', () => {
    const { result } = renderHook(() => useSchemaForm(makeCompositeValidationSchema()))
    // Only one sub-field filled

    act(() => {
      result.current.setValue('q1_1_outcome', 'Aumentar ingresos')
    })

    let valid: boolean
    act(() => {
      valid = result.current.validate()
    })

    expect(valid!).toBe(false)
    expect(result.current.errors['q1_1_objective']).toBeFalsy() // parent key has no error
    expect(result.current.errors['q1_1_metric']).toBeTruthy()    // sub-field error
    expect(result.current.errors['q1_1_horizon']).toBeTruthy()   // sub-field error
  })
})

describe('useSchemaForm — matrix question type (REQ-9)', () => {
  it('validate() returns valid when all required rows have a selection', () => {
    const { result } = renderHook(() => useSchemaForm(makeMatrixSchema()))

    // Set a selection for every row
    act(() => {
      result.current.setValue('matrix_q1', { row_ops: 'col_low', row_tech: 'col_high' })
    })

    let valid: boolean
    act(() => {
      valid = result.current.validate()
    })

    expect(valid!).toBe(true)
    expect(result.current.errors['matrix_q1']).toBeFalsy()
  })

  it('validate() returns invalid when a required row is missing a selection', () => {
    const { result } = renderHook(() => useSchemaForm(makeMatrixSchema()))

    // Only one row answered — row_tech is missing
    act(() => {
      result.current.setValue('matrix_q1', { row_ops: 'col_low' })
    })

    let valid: boolean
    act(() => {
      valid = result.current.validate()
    })

    expect(valid!).toBe(false)
    expect(result.current.errors['matrix_q1']).toBeTruthy()
  })

  it('validate() returns invalid when matrix value is entirely missing (required)', () => {
    const { result } = renderHook(() => useSchemaForm(makeMatrixSchema()))
    // No setValue call — value is undefined

    let valid: boolean
    act(() => {
      valid = result.current.validate()
    })

    expect(valid!).toBe(false)
    expect(result.current.errors['matrix_q1']).toBeTruthy()
  })

  it('buildPayload() returns { [rowId]: columnId } dict directly', () => {
    const { result } = renderHook(() => useSchemaForm(makeMatrixSchema()))

    act(() => {
      result.current.setValue('matrix_q1', { row_ops: 'col_low', row_tech: 'col_high' })
    })

    let payload: Record<string, unknown>
    act(() => {
      payload = result.current.buildPayload()
    })

    expect(payload!['matrix_q1']).toEqual({ row_ops: 'col_low', row_tech: 'col_high' })
  })

  it('neither validate() nor buildPayload() throws on a matrix block', () => {
    const { result } = renderHook(() => useSchemaForm(makeMatrixSchema()))

    expect(() => {
      act(() => {
        result.current.validate()
        result.current.buildPayload()
      })
    }).not.toThrow()
  })
})

// ---------------------------------------------------------------------------
// REQ-1: getAnsweredQuestions helper — TA.1
// Tests written RED before implementation (Strict TDD)
// ---------------------------------------------------------------------------

const simpleBlock: BlockSchema = {
  id: 'b1',
  layer: 'core',
  order: 1,
  estimated_minutes: 5,
  title: 'Test',
  questions: [
    { id: 'q1', type: 'text', label: 'Q1' },
    { id: 'q2', type: 'text', label: 'Q2' },
  ],
}

const compositeBlock: BlockSchema = {
  id: 'b2',
  layer: 'core',
  order: 2,
  estimated_minutes: 5,
  title: 'Composite Test',
  questions: [
    {
      id: 'comp1',
      type: 'composite',
      label: 'Composite',
      sub_fields: [
        { id: 'comp1_a', type: 'text', label: 'A' },
        { id: 'comp1_b', type: 'text', label: 'B' },
        { id: 'comp1_c', type: 'text', label: 'C' },
      ],
    },
  ],
}

const mixedBlock: BlockSchema = {
  id: 'b3',
  layer: 'core',
  order: 3,
  estimated_minutes: 5,
  title: 'Mixed',
  questions: [
    { id: 's1', type: 'text', label: 'Simple 1' },
    { id: 's2', type: 'text', label: 'Simple 2' },
    {
      id: 'comp2',
      type: 'composite',
      label: 'Composite 2',
      sub_fields: [
        { id: 'comp2_a', type: 'text', label: 'A' },
        { id: 'comp2_b', type: 'text', label: 'B' },
      ],
    },
  ],
}

describe('getAnsweredQuestions (REQ-1)', () => {
  describe('simple questions', () => {
    it('returns 0 answered when no values', () => {
      expect(getAnsweredQuestions(simpleBlock, {}).length).toBe(0)
    })

    it('returns 1 answered when one simple question has value', () => {
      expect(getAnsweredQuestions(simpleBlock, { q1: 'hello' }).length).toBe(1)
    })

    it('returns 2 answered when both simple questions have values', () => {
      expect(getAnsweredQuestions(simpleBlock, { q1: 'hello', q2: 'world' }).length).toBe(2)
    })
  })

  describe('composite — "any" semantic (no required sub-fields declared)', () => {
    it('counts composite as 0 when no sub-fields filled', () => {
      expect(getAnsweredQuestions(compositeBlock, {}).length).toBe(0)
    })

    it('counts composite as 1 when ANY one sub-field is filled', () => {
      expect(getAnsweredQuestions(compositeBlock, { comp1_b: 'value' }).length).toBe(1)
    })

    it('counts composite as 1 when all sub-fields are filled', () => {
      expect(
        getAnsweredQuestions(compositeBlock, { comp1_a: 'a', comp1_b: 'b', comp1_c: 'c' }).length,
      ).toBe(1)
    })
  })

  describe('mixed block: 2 simple + 1 composite', () => {
    it('schema has 3 top-level questions (totalCount = 3)', () => {
      expect(mixedBlock.questions.length).toBe(3)
    })

    it('answered is 0 when nothing filled', () => {
      expect(getAnsweredQuestions(mixedBlock, {}).length).toBe(0)
    })

    it('answered is 2 when 2 simple filled, composite empty', () => {
      expect(getAnsweredQuestions(mixedBlock, { s1: 'x', s2: 'y' }).length).toBe(2)
    })

    it('answered is 3 when 2 simple + composite has any sub-field filled', () => {
      expect(
        getAnsweredQuestions(mixedBlock, { s1: 'x', s2: 'y', comp2_a: 'z' }).length,
      ).toBe(3)
    })
  })
})
