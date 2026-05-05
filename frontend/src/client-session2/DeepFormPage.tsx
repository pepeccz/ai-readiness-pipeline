/**
 * DeepFormPage — public client page for session 2 DEEP questionnaire.
 *
 * Accessed via signed URL: /client/deep/{token}
 * No login required.
 *
 * Flow:
 *  1. Load branches from GET /api/client/deep/{token}
 *  2. Wizard: show one branch at a time with ProgressIndicator
 *  3. On each submit: POST /api/client/deep/{token}/submit
 *  4. When all done: show "thank you" screen
 */

import { useEffect, useState } from 'react'
import { getDeepBranches } from './api/client'
import type { DeepBranchData, DeepFormData } from './api/client'
import { DeepBranchForm } from './components/DeepBranchForm'
import { ProgressIndicator } from './components/ProgressIndicator'
import { useDeepBranchSubmit } from './hooks/useDeepBranchSubmit'

interface Props {
  token: string
}

export function DeepFormPage({ token }: Props) {
  const [data, setData] = useState<DeepFormData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [submittedIds, setSubmittedIds] = useState<Set<string>>(new Set())
  const [allDone, setAllDone] = useState(false)

  const { submit, isSubmitting, error: submitError } = useDeepBranchSubmit(token)

  useEffect(() => {
    getDeepBranches(token)
      .then((d) => {
        setData(d)
        // Skip already-received branches
        const firstPending = d.deep_branches.findIndex((b) => b.status !== 'received')
        if (firstPending === -1) {
          setAllDone(true)
        } else {
          setCurrentIndex(firstPending)
          const alreadyDone = d.deep_branches
            .filter((b) => b.status === 'received')
            .map((b) => b.id)
          setSubmittedIds(new Set(alreadyDone))
        }
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Token inválido o expirado.')
      })
      .finally(() => setLoading(false))
  }, [token])

  async function handleBranchSubmit(
    branch: DeepBranchData,
    responses: Record<string, string>
  ) {
    const result = await submit(branch.id, responses)
    if (!result) return

    const newSubmitted = new Set(submittedIds).add(branch.id)
    setSubmittedIds(newSubmitted)

    if (!data) return
    const nextIndex = data.deep_branches.findIndex(
      (b, idx) => idx > currentIndex && b.status !== 'received' && !newSubmitted.has(b.id)
    )
    if (nextIndex === -1 || result.session_state === 'deep_received') {
      setAllDone(true)
    } else {
      setCurrentIndex(nextIndex)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-500 text-sm">Cargando cuestionario...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow p-6 text-center">
          <h1 className="text-xl font-semibold text-red-600 mb-2">Enlace inválido</h1>
          <p className="text-sm text-gray-600">
            Este enlace no es válido o ha expirado. Por favor, contactá a tu consultor de Zanovix.
          </p>
        </div>
      </div>
    )
  }

  if (allDone) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow p-8 text-center">
          <div className="text-4xl mb-4">✓</div>
          <h1 className="text-2xl font-semibold text-gray-800 mb-3">
            ¡Gracias por tus respuestas!
          </h1>
          <p className="text-sm text-gray-600">
            Hemos recibido toda la información. Recibirás una invitación para la sesión 2 de diagnóstico en los próximos días.
          </p>
        </div>
      </div>
    )
  }

  if (!data || data.deep_branches.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-500 text-sm">No hay secciones disponibles.</p>
      </div>
    )
  }

  const currentBranch = data.deep_branches[currentIndex]
  const totalBranches = data.deep_branches.length
  const completedCount = submittedIds.size

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Diagnóstico de IA Profundo</h1>
          <p className="text-sm text-gray-500 mt-1">
            Completá cada sección con honestidad. Podés tomarte el tiempo que necesitás.
          </p>
        </div>

        <ProgressIndicator total={totalBranches} completed={completedCount} />

        <div className="bg-white rounded-lg shadow p-6">
          {submitError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
              {submitError}
            </div>
          )}
          <DeepBranchForm
            branch={currentBranch}
            onSubmit={(responses) => handleBranchSubmit(currentBranch, responses)}
            isSubmitting={isSubmitting}
          />
        </div>
      </div>
    </div>
  )
}
