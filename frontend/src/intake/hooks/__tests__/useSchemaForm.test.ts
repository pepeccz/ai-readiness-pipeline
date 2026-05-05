/**
 * T3.5 — useSchemaForm handles matrix type in validate() and buildPayload() (REQ-9)
 */
import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSchemaForm } from '../useSchemaForm'
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
