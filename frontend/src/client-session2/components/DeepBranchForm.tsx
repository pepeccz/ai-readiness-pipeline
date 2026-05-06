/**
 * DeepBranchForm — renders one DEEP branch's questions with text inputs.
 *
 * One branch at a time. On submit, calls onSubmit with the responses map.
 */

import { useState } from 'react'
import type { DeepBranchData } from '../api/client'

interface Props {
  branch: DeepBranchData
  onSubmit: (responses: Record<string, string>) => Promise<void>
  isSubmitting: boolean
}

export function DeepBranchForm({ branch, onSubmit, isSubmitting }: Props) {
  const [responses, setResponses] = useState<Record<string, string>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})

  function handleChange(questionId: string, value: string) {
    setResponses((prev) => ({ ...prev, [questionId]: value }))
    if (errors[questionId]) {
      setErrors((prev) => {
        const next = { ...prev }
        delete next[questionId]
        return next
      })
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    // Validate all questions answered
    const newErrors: Record<string, string> = {}
    for (const q of branch.generated_questions) {
      if (!responses[q.id]?.trim()) {
        newErrors[q.id] = 'Este campo es obligatorio.'
      }
    }
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }
    await onSubmit(responses)
  }

  const branchLabels: Record<string, string> = {
    strategic: 'Estratégico',
    data: 'Datos',
    talent: 'Talento',
    infrastructure: 'Infraestructura',
    compliance: 'Cumplimiento',
    governance: 'Gobernanza',
    process: 'Procesos',
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-gray-800">
          Sección: {branchLabels[branch.branch_id] ?? branch.branch_id}
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          Respondé las siguientes preguntas con la mayor honestidad posible.
        </p>
      </div>

      {branch.generated_questions.map((q, idx) => (
        <div key={q.id} className="space-y-1">
          <label
            htmlFor={q.id}
            className="block text-sm font-medium text-gray-700"
          >
            {idx + 1}. {q.text}
          </label>
          {q.rationale && (
            <p className="text-xs text-gray-400 italic">{q.rationale}</p>
          )}
          <textarea
            id={q.id}
            rows={3}
            value={responses[q.id] ?? ''}
            onChange={(e) => handleChange(q.id, e.target.value)}
            className={`w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500 ${
              errors[q.id]
                ? 'border-red-400 focus:ring-red-400'
                : 'border-gray-300'
            }`}
            placeholder="Escribí tu respuesta acá..."
          />
          {errors[q.id] && (
            <p className="text-xs text-red-600">{errors[q.id]}</p>
          )}
        </div>
      ))}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full rounded-md bg-teal-600 px-4 py-2 text-white font-medium hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isSubmitting ? 'Enviando...' : 'Enviar esta sección'}
      </button>
    </form>
  )
}
