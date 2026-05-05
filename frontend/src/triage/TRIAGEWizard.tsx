/**
 * TRIAGEWizard — public TRIAGE form (session 0).
 *
 * Flow:
 *  1. GET /api/public/triage/schema → schema with questions + consents
 *  2. Render all questions via FieldRenderer (reused from intake/)
 *  3. POST /api/public/triage/submit → show bucket message on success
 *
 * No login required. No admin navbar.
 */

import { useEffect, useState, useCallback } from 'react'
import { FieldRenderer } from '../intake/FieldRenderer'
import type { Question, FormValues, FormErrors } from '../intake/types/schema'

// ---------------------------------------------------------------------------
// API types
// ---------------------------------------------------------------------------

interface TriageSchemaResponse {
  schema_version: string
  schema: {
    questions: Question[]
    consents: Question[]
  }
}

interface TriageSubmitResponse {
  lead_id: number
  bucket: string
  message: string
}

// ---------------------------------------------------------------------------
// Bucket messages
// ---------------------------------------------------------------------------

const BUCKET_MESSAGES: Record<string, { title: string; body: string }> = {
  auto_accept: {
    title: 'Tu diagnóstico IA está confirmado',
    body: 'Nuestro equipo se pondrá en contacto contigo en las próximas 24 horas para coordinar la sesión inicial.',
  },
  review: {
    title: 'Estamos revisando tu caso',
    body: 'Recibirás una respuesta en un plazo de 48 horas con los próximos pasos.',
  },
  cold_warm: {
    title: 'No es el momento perfecto, pero esto te ayudará',
    body: 'Te enviamos recursos para prepararte. Podrás solicitar una re-evaluación en unos meses.',
  },
  cold_cool: {
    title: 'Te mandamos recursos para prepararte',
    body: 'Recibirás un checklist y materiales de preparación para cuando estés listo.',
  },
  reject_soft: {
    title: 'En este momento no podemos ayudarte',
    body: 'Gracias por tu interés. Te hemos enviado información que puede resultarte útil.',
  },
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function evaluateShowIf(
  rule: NonNullable<Question['show_if']>,
  values: FormValues,
): boolean {
  const fieldValue = values[rule.field]
  switch (rule.op) {
    case 'eq': return fieldValue === rule.value
    case 'neq': return fieldValue !== rule.value
    case 'in': {
      const arr = Array.isArray(rule.value) ? rule.value : [rule.value]
      return arr.includes(fieldValue as string)
    }
    case 'not_in': {
      const arr = Array.isArray(rule.value) ? rule.value : [rule.value]
      return !arr.includes(fieldValue as string)
    }
    case 'any_of': {
      const selected = fieldValue as string[]
      return Array.isArray(selected) && (rule.value as string[]).some((s) => selected.includes(s))
    }
    case 'all_of': {
      const selected = fieldValue as string[]
      return Array.isArray(selected) && (rule.value as string[]).every((a) => selected.includes(a))
    }
    default: return true
  }
}

function isVisible(q: Question, values: FormValues): boolean {
  if (!q.show_if) return true
  return evaluateShowIf(q.show_if, values)
}

function validateQuestion(q: Question, value: unknown): string | null {
  if (q.required && (value === undefined || value === null || value === '')) {
    return 'Este campo es obligatorio'
  }
  if (q.type === 'consent' && q.required && !value) {
    return 'Debés aceptar esta política para continuar'
  }
  if (q.type === 'multi_choice' && 'max_selections' in q && q.max_selections) {
    const arr = value as string[]
    if (Array.isArray(arr) && arr.length > q.max_selections) {
      return `Máximo ${q.max_selections} opciones`
    }
  }
  return null
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function TRIAGEWizard() {
  const [loading, setLoading] = useState(true)
  const [schema, setSchema] = useState<TriageSchemaResponse | null>(null)
  const [fetchError, setFetchError] = useState<string | null>(null)

  const [values, setValues] = useState<FormValues>({})
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [result, setResult] = useState<TriageSubmitResponse | null>(null)

  // Fetch schema on mount
  useEffect(() => {
    fetch('/api/public/triage/schema')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<TriageSchemaResponse>
      })
      .then(setSchema)
      .catch((err) => setFetchError(err instanceof Error ? err.message : 'Error cargando el formulario'))
      .finally(() => setLoading(false))
  }, [])

  const setValue = useCallback((id: string, value: unknown) => {
    setValues((prev) => ({ ...prev, [id]: value }))
    setErrors((prev) => ({ ...prev, [id]: '' }))
  }, [])

  const allQuestions: Question[] = [
    ...(schema?.schema.questions ?? []),
    ...(schema?.schema.consents ?? []),
  ]

  const visibleQuestions = allQuestions.filter((q) => isVisible(q, values))

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    // Validate all visible questions
    const newErrors: FormErrors = {}
    let valid = true
    for (const q of visibleQuestions) {
      const err = validateQuestion(q, values[q.id])
      if (err) {
        newErrors[q.id] = err
        valid = false
      }
    }
    setErrors(newErrors)
    if (!valid) return

    // Build payload: answers + consents
    const answers: FormValues = {}
    const consentIds = new Set((schema?.schema.consents ?? []).map((c) => c.id))
    const consents: Array<{ type: string; accepted: boolean; policy_version: string }> = []

    for (const q of visibleQuestions) {
      if (consentIds.has(q.id)) {
        if (q.type === 'consent') {
          consents.push({
            type: q.id, // convention: question id is the consent type (e.g. "privacy")
            accepted: Boolean(values[q.id]),
            policy_version: (q as { policy_version?: string }).policy_version ?? 'v1.0-2025-05',
          })
        }
      } else {
        answers[q.id] = values[q.id]
      }
    }

    setSubmitting(true)
    setSubmitError(null)

    try {
      const res = await fetch('/api/public/triage/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers, consents }),
      })

      if (res.status === 429) {
        setSubmitError('Has alcanzado el límite de envíos por hora. Intentá de nuevo más tarde.')
        return
      }

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        const detail = (body as { detail?: string }).detail ?? `Error ${res.status}`
        setSubmitError(detail)
        return
      }

      const data = await res.json() as TriageSubmitResponse
      setResult(data)
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Error enviando el formulario')
    } finally {
      setSubmitting(false)
    }
  }

  // ── Loading ──────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-500 text-sm">Cargando formulario...</p>
      </div>
    )
  }

  if (fetchError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow p-6 text-center">
          <h1 className="text-xl font-semibold text-red-600 mb-2">Error al cargar</h1>
          <p className="text-sm text-gray-600">{fetchError}</p>
        </div>
      </div>
    )
  }

  // ── Success screen ───────────────────────────────────────────────────────

  if (result) {
    const msg = BUCKET_MESSAGES[result.bucket] ?? {
      title: 'Formulario enviado',
      body: result.message,
    }
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow p-8 text-center">
          <div className="w-12 h-12 rounded-full bg-teal-100 flex items-center justify-center mx-auto mb-6">
            <svg className="w-6 h-6 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-3">{msg.title}</h1>
          <p className="text-sm text-gray-600 leading-relaxed">{msg.body}</p>
        </div>
      </div>
    )
  }

  // ── Form ─────────────────────────────────────────────────────────────────

  const consentQuestions = schema?.schema.consents ?? []
  const regularQuestions = schema?.schema.questions ?? []
  const visibleRegular = regularQuestions.filter((q) => isVisible(q, values))
  const visibleConsents = consentQuestions.filter((q) => isVisible(q, values))

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900">Diagnóstico de IA para tu empresa</h1>
          <p className="text-gray-500 text-sm mt-2 leading-relaxed">
            Completá este formulario y nuestro equipo analizará el potencial de la inteligencia
            artificial en tu negocio.
          </p>
        </div>

        <form onSubmit={handleSubmit} noValidate className="bg-white rounded-lg shadow p-8 space-y-6">
          {/* Regular questions */}
          {visibleRegular.map((q) => (
            <FieldRenderer
              key={q.id}
              question={q}
              values={values}
              errors={errors}
              onChange={setValue}
            />
          ))}

          {/* Divider before consents */}
          {visibleConsents.length > 0 && (
            <div className="border-t pt-4">
              <p className="text-xs text-gray-500 mb-4">
                Para continuar, revisá y aceptá las siguientes políticas:
              </p>
              {visibleConsents.map((q) => (
                <FieldRenderer
                  key={q.id}
                  question={q}
                  values={values}
                  errors={errors}
                  onChange={setValue}
                />
              ))}
            </div>
          )}

          {/* Submit error */}
          {submitError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
              {submitError}
            </div>
          )}

          {/* Submit button */}
          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="px-8 py-3 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? 'Enviando...' : 'Enviar diagnóstico'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
