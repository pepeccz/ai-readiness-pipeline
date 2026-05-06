/**
 * TA.3 — expandCompositePayload helper (REQ-1 / ADR-1)
 * Strict TDD — RED written before implementation.
 */

import { describe, it, expect } from 'vitest'
import { expandCompositePayload } from '../useSchemaForm'
import type { Question } from '../../types/schema'

const compositeQuestions: Question[] = [
  {
    id: 'q1_1',
    type: 'composite',
    label: 'Composite Q',
    sub_fields: [
      { id: 'q1_1_objective', type: 'text', label: 'Objective' },
      { id: 'q1_1_effort', type: 'text', label: 'Effort' },
    ],
  } as Question,
  {
    id: 'q2',
    type: 'text',
    label: 'Simple Q',
  } as Question,
]

describe('expandCompositePayload', () => {
  it('expands nested composite object into flat sub-field keys', () => {
    const payload = { q1_1: { q1_1_objective: 'A', q1_1_effort: 'B' } }
    const result = expandCompositePayload(payload, compositeQuestions)
    expect(result).toEqual({
      q1_1_objective: 'A',
      q1_1_effort: 'B',
    })
    expect(result['q1_1']).toBeUndefined()
  })

  it('is idempotent — already-flat payload passes through unchanged', () => {
    const payload = { q1_1_objective: 'A', q1_1_effort: 'B', q2: 'hello' }
    const result = expandCompositePayload(payload, compositeQuestions)
    expect(result).toEqual(payload)
  })

  it('preserves root _other_text sibling keys (they win over nested duplicates)', () => {
    const payload = {
      q1_1: { q1_1_objective: 'other' },
      'q1_1_objective_other_text': 'Custom',
    }
    const result = expandCompositePayload(payload, compositeQuestions)
    expect(result['q1_1_objective']).toBe('other')
    expect(result['q1_1_objective_other_text']).toBe('Custom')
  })

  it('passes through null payload[K] as-is (no expansion)', () => {
    const payload = { q1_1: null as unknown as Record<string, unknown> }
    const result = expandCompositePayload(payload, compositeQuestions)
    expect(result['q1_1']).toBeNull()
  })

  it('no-op for a question whose parent key is absent from payload', () => {
    const payload = { q2: 'hello' }
    const result = expandCompositePayload(payload, compositeQuestions)
    expect(result).toEqual({ q2: 'hello' })
    expect(result['q1_1']).toBeUndefined()
  })

  it('keeps non-composite questions untouched', () => {
    const payload = { q2: 'simple value' }
    const result = expandCompositePayload(payload, compositeQuestions)
    expect(result['q2']).toBe('simple value')
  })
})
