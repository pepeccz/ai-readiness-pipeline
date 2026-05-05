/**
 * useSchemaForm — generic block form state with show_if + client-side validation.
 *
 * Responsibilities:
 * - Tracks form values keyed by question id
 * - Evaluates show_if conditions reactively
 * - Validates on submit attempt
 * - Exposes helpers: setValue, getVisible, submit
 */

import { useState, useCallback } from 'react'
import type { BlockSchema, Question, ShowIfRule, FormValues, FormErrors, MatrixQuestion } from '../types/schema'

// ---------------------------------------------------------------------------
// show_if evaluation
// ---------------------------------------------------------------------------

function evaluateShowIf(rule: ShowIfRule, values: FormValues): boolean {
  const fieldValue = values[rule.field]

  switch (rule.op) {
    case 'eq':
      return fieldValue === rule.value
    case 'neq':
      return fieldValue !== rule.value
    case 'in': {
      const arr = Array.isArray(rule.value) ? rule.value : [rule.value]
      return arr.includes(fieldValue as string)
    }
    case 'not_in': {
      const arr = Array.isArray(rule.value) ? rule.value : [rule.value]
      return !arr.includes(fieldValue as string)
    }
    case 'gt':
      return (fieldValue as number) > (rule.value as number)
    case 'lt':
      return (fieldValue as number) < (rule.value as number)
    case 'any_of': {
      const selected = fieldValue as string[]
      const arr = rule.value as string[]
      return Array.isArray(selected) && selected.some((s) => arr.includes(s))
    }
    case 'all_of': {
      const selected = fieldValue as string[]
      const arr = rule.value as string[]
      return Array.isArray(selected) && arr.every((a) => selected.includes(a))
    }
    default:
      return true
  }
}

function isVisible(question: Question, values: FormValues): boolean {
  if (!question.show_if) return true
  return evaluateShowIf(question.show_if, values)
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

function validateQuestion(q: Question, value: unknown): string | null {
  // Matrix: validate that every required row has a selected column (ADR-6)
  if (q.type === 'matrix') {
    const matrixQ = q as MatrixQuestion
    if (!matrixQ.required) return null
    const answers = value as Record<string, string> | undefined
    if (!answers || typeof answers !== 'object') {
      return 'Este campo es obligatorio'
    }
    const missingRow = matrixQ.rows.find((row) => !answers[row.id])
    if (missingRow) {
      return `Seleccioná una opción para "${missingRow.label}"`
    }
    return null
  }

  if (q.required && (value === undefined || value === null || value === '')) {
    return 'Este campo es obligatorio'
  }
  if (q.type === 'multi_choice' && 'min_selections' in q && q.min_selections) {
    const arr = value as string[]
    if (!Array.isArray(arr) || arr.length < q.min_selections) {
      return `Seleccioná al menos ${q.min_selections} opciones`
    }
  }
  if (q.type === 'multi_choice' && 'max_selections' in q && q.max_selections) {
    const arr = value as string[]
    if (Array.isArray(arr) && arr.length > q.max_selections) {
      return `Máximo ${q.max_selections} opciones`
    }
  }
  for (const rule of q.validations ?? []) {
    if (rule.type === 'max_length' && typeof value === 'string') {
      if (value.length > (rule.value as number)) {
        return rule.message ?? `Máximo ${rule.value} caracteres`
      }
    }
    if (rule.type === 'min_length' && typeof value === 'string') {
      if (value.length < (rule.value as number)) {
        return rule.message ?? `Mínimo ${rule.value} caracteres`
      }
    }
  }
  return null
}

// ---------------------------------------------------------------------------
// getAnsweredQuestions — REQ-1
// ---------------------------------------------------------------------------
//
// Counts how many top-level questions are "answered" in the given values map.
// Rules (Decision 1 — hybrid composite semantic):
//   - Simple question: answered if value is non-empty (not undefined/null/''/[]).
//   - Composite question with NO required sub-fields: answered if ANY visible
//     sub-field has a non-empty value ("any" semantic).
//   - Composite question WITH required sub-fields: answered if ALL required
//     visible sub-fields have non-empty values ("all-required" semantic).
//
// NOTE: `_other_text` sibling keys are flat values at root level — they are
// NOT included in this count (they are companions to a question, not questions).
//
// Returns the subset of questions that are considered answered so that callers
// can use both `.length` (answeredCount) and the question list itself.
//
export function getAnsweredQuestions(schema: BlockSchema, values: FormValues): Question[] {
  return schema.questions.filter((q) => isQuestionAnswered(q, values))
}

function hasValue(v: unknown): boolean {
  if (v === undefined || v === null || v === '') return false
  if (Array.isArray(v)) return v.length > 0
  return true
}

function isQuestionAnswered(q: Question, values: FormValues): boolean {
  if (q.type === 'composite') {
    const requiredSubs = q.sub_fields.filter((s) => s.required)
    if (requiredSubs.length > 0) {
      // All-required semantic: every required visible sub-field must have a value
      return requiredSubs.every((s) => isVisible(s, values) && hasValue(values[s.id]))
    }
    // Any semantic: at least one visible sub-field has a value
    return q.sub_fields.some((s) => isVisible(s, values) && hasValue(values[s.id]))
  }
  return hasValue(values[q.id])
}

// ---------------------------------------------------------------------------
// Dev-mode schema contract validation (TD.2, REQ-7)
// ---------------------------------------------------------------------------

function validateSchemaContract(schema: BlockSchema | null): void {
  if (import.meta.env.DEV && schema) {
    // Assert: no question id ends in reserved suffix '_other_text'
    const violations: string[] = []

    function checkQuestionIds(questions: Question[]): void {
      for (const q of questions) {
        if (q.id.endsWith('_other_text')) {
          violations.push(q.id)
        }
        // Check sub-fields in composite questions
        if (q.type === 'composite') {
          for (const sub of q.sub_fields) {
            if (sub.id.endsWith('_other_text')) {
              violations.push(sub.id)
            }
          }
        }
      }
    }

    checkQuestionIds(schema.questions)

    if (violations.length > 0) {
      console.error(
        `[Schema Contract Violation] The following question IDs end in the reserved suffix '_other_text', ` +
          `which would collide with companion free-text keys. Please rename them:\n  ${violations.join(', ')}`
      )
    }
  }
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export interface UseSchemaFormResult {
  values: FormValues
  errors: FormErrors
  isDirty: boolean
  setValue: (id: string, value: unknown) => void
  getVisibleQuestions: () => Question[]
  validate: () => boolean
  reset: () => void
  buildPayload: () => FormValues
}

export function useSchemaForm(schema: BlockSchema | null): UseSchemaFormResult {
  const [values, setValues] = useState<FormValues>({})
  const [errors, setErrors] = useState<FormErrors>({})
  const [isDirty, setIsDirty] = useState(false)

  // Validate schema contract on mount
  validateSchemaContract(schema)

  const setValue = useCallback((id: string, value: unknown) => {
    setValues((prev) => ({ ...prev, [id]: value }))
    setErrors((prev) => ({ ...prev, [id]: '' }))
    setIsDirty(true)
  }, [])

  const questions = schema?.questions ?? []

  const getVisibleQuestions = useCallback((): Question[] => {
    return questions.filter((q) => isVisible(q, values))
  }, [questions, values])

  const validate = useCallback((): boolean => {
    const visible = questions.filter((q) => isVisible(q, values))
    const newErrors: FormErrors = {}
    let valid = true

    for (const q of visible) {
      const err = validateQuestion(q, values[q.id])
      if (err) {
        newErrors[q.id] = err
        valid = false
      }
      // Validate sub_fields in composite
      if (q.type === 'composite') {
        for (const sub of q.sub_fields) {
          if (isVisible(sub, values)) {
            const subErr = validateQuestion(sub, values[sub.id])
            if (subErr) {
              newErrors[sub.id] = subErr
              valid = false
            }
          }
        }
      }
    }

    setErrors(newErrors)
    return valid
  }, [questions, values])

  const reset = useCallback(() => {
    setValues({})
    setErrors({})
    setIsDirty(false)
  }, [])

  // Build submit payload: only include visible fields.
  //
  // _other_text keys (e.g. "q4_3_other_text") are stored as flat root-level keys
  // in `values` by FieldRenderer. They are NOT question ids themselves, so they
  // are NOT processed in the per-question loop. Instead, we copy all _other_text
  // keys that are present in values directly into the payload AFTER the loop.
  // This ensures sibling companion values survive the payload build without being
  // nested inside composite sub-payloads. (Decision 2, REQ-2 / REQ-3)
  const buildPayload = useCallback((): FormValues => {
    const visible = questions.filter((q) => isVisible(q, values))
    const payload: FormValues = {}
    for (const q of visible) {
      if (q.type === 'composite') {
        const subPayload: FormValues = {}
        for (const sub of q.sub_fields) {
          if (isVisible(sub, values) && values[sub.id] !== undefined) {
            subPayload[sub.id] = values[sub.id]
          }
        }
        payload[q.id] = subPayload
      } else if (q.type === 'matrix') {
        // Matrix payload: { [rowId]: columnId } dict — passed through directly (ADR-6)
        if (values[q.id] !== undefined) {
          payload[q.id] = values[q.id]
        }
      } else if (values[q.id] !== undefined) {
        payload[q.id] = values[q.id]
      }
    }
    // Include _other_text companion keys at root level (flat, not inside composite)
    for (const [key, val] of Object.entries(values)) {
      if (key.endsWith('_other_text') && val !== undefined && val !== '') {
        payload[key] = val
      }
    }
    return payload
  }, [questions, values])

  return { values, errors, isDirty, setValue, getVisibleQuestions, validate, reset, buildPayload }
}
