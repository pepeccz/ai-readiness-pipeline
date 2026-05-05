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
import type { BlockSchema, Question, ShowIfRule, FormValues, FormErrors } from '../types/schema'

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

  // Build submit payload: only include visible fields
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
      } else if (values[q.id] !== undefined) {
        payload[q.id] = values[q.id]
      }
    }
    return payload
  }, [questions, values])

  return { values, errors, isDirty, setValue, getVisibleQuestions, validate, reset, buildPayload }
}
