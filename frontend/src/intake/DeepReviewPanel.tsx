/**
 * frontend/src/intake/DeepReviewPanel.tsx — T7.9
 *
 * Consultant panel for reviewing AI-generated DEEP branch questions.
 *
 * Features:
 * - Lists all DeepBranch rows for the current lead
 * - Shows status badge per branch (pending_review, sent_to_client, received)
 * - Inline editing of individual questions
 * - Save edits (PATCH) + Send to client (POST send)
 * - Loading skeleton while branches are in pending_generation
 */

import { useDeep } from './hooks/useDeep'
import type { DeepBranch } from './api/deep'

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------

const STATUS_LABELS: Record<string, string> = {
  pending_generation: 'Generando…',
  pending_review: 'Pendiente revisión',
  sent_to_client: 'Enviado al cliente',
  received: 'Recibido',
  generation_failed: 'Error generación',
}

const STATUS_COLORS: Record<string, string> = {
  pending_generation: 'bg-gray-100 text-gray-600',
  pending_review: 'bg-yellow-100 text-yellow-800',
  sent_to_client: 'bg-teal-100 text-teal-800',
  received: 'bg-green-100 text-green-800',
  generation_failed: 'bg-red-100 text-red-800',
}

function StatusBadge({ status }: { status: string }) {
  const label = STATUS_LABELS[status] ?? status
  const color = STATUS_COLORS[status] ?? 'bg-gray-100 text-gray-600'
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {label}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Branch card
// ---------------------------------------------------------------------------

interface BranchCardProps {
  branch: DeepBranch
  isEditing: boolean
  editedQuestions: { id: string; text: string }[]
  isSaving: boolean
  isSending: boolean
  onStartEdit: () => void
  onCancelEdit: () => void
  onUpdateQuestion: (index: number, text: string) => void
  onSave: () => void
  onSend: () => void
}

function BranchCard({
  branch,
  isEditing,
  editedQuestions,
  isSaving,
  isSending,
  onStartEdit,
  onCancelEdit,
  onUpdateQuestion,
  onSave,
  onSend,
}: BranchCardProps) {
  const isPendingGeneration = branch.status === 'pending_generation'
  const isSent = branch.status === 'sent_to_client' || branch.status === 'received'

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold text-gray-900">{branch.branch_id}</h3>
          <StatusBadge status={branch.status} />
        </div>
        {!isSent && !isPendingGeneration && (
          <div className="flex gap-2">
            {isEditing ? (
              <>
                <button
                  onClick={onCancelEdit}
                  className="px-3 py-1 text-xs text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={onSave}
                  disabled={isSaving}
                  className="px-3 py-1 text-xs text-white bg-teal-600 rounded hover:bg-teal-700 disabled:opacity-50"
                >
                  {isSaving ? 'Guardando…' : 'Guardar'}
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={onStartEdit}
                  className="px-3 py-1 text-xs text-gray-700 border border-gray-300 rounded hover:bg-gray-50"
                >
                  Editar
                </button>
                <button
                  onClick={onSend}
                  disabled={isSending}
                  className="px-3 py-1 text-xs text-white bg-green-600 rounded hover:bg-green-700 disabled:opacity-50"
                >
                  {isSending ? 'Enviando…' : 'Enviar al cliente'}
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {/* Questions */}
      <div className="p-4 space-y-3">
        {isPendingGeneration ? (
          // Skeleton loader
          <div className="space-y-2 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-4 bg-gray-200 rounded w-full" />
            ))}
          </div>
        ) : branch.generated_questions.length === 0 ? (
          <p className="text-sm text-gray-400 italic">Sin preguntas generadas.</p>
        ) : isEditing ? (
          editedQuestions.map((q, idx) => (
            <div key={q.id} className="flex flex-col gap-1">
              <label className="text-xs text-gray-500 font-medium">{q.id}</label>
              <textarea
                value={q.text}
                onChange={(e) => onUpdateQuestion(idx, e.target.value)}
                className="w-full text-sm border border-gray-300 rounded p-2 focus:outline-none focus:ring-2 focus:ring-teal-300 resize-none"
                rows={2}
              />
            </div>
          ))
        ) : (
          branch.generated_questions.map((q, idx) => (
            <div key={q.id || idx} className="flex gap-2">
              <span className="text-xs text-gray-400 font-mono mt-0.5 shrink-0">{idx + 1}.</span>
              <p className="text-sm text-gray-700">{q.text}</p>
            </div>
          ))
        )}
      </div>

      {/* Sent info */}
      {branch.sent_to_client_at && (
        <div className="px-4 pb-3">
          <p className="text-xs text-gray-400">
            Enviado: {new Date(branch.sent_to_client_at).toLocaleDateString('es-AR')}
          </p>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// DeepReviewPanel
// ---------------------------------------------------------------------------

interface DeepReviewPanelProps {
  leadId: string
}

export function DeepReviewPanel({ leadId }: DeepReviewPanelProps) {
  const {
    branches,
    isLoading,
    error,
    editingBranchId,
    editedQuestions,
    startEditing,
    cancelEditing,
    updateQuestion,
    saveEdits,
    sendToClient,
    isSaving,
    isSending,
  } = useDeep(leadId)

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/3" />
          <div className="h-24 bg-gray-200 rounded" />
          <div className="h-24 bg-gray-200 rounded" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <p className="text-sm text-red-600">Error al cargar las ramas DEEP: {error.message}</p>
      </div>
    )
  }

  if (branches.length === 0) {
    return (
      <div className="p-6 text-center">
        <p className="text-sm text-gray-500">
          No se activaron ramas DEEP (ningún trigger detectado en el diagnóstico). Si la sesión 1 aún no fue cerrada, las ramas se generarán al cerrarla.
        </p>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-base font-semibold text-gray-900">
          Revisión DEEP — {branches.length} rama{branches.length !== 1 ? 's' : ''}
        </h2>
      </div>
      {branches.map((branch) => (
        <BranchCard
          key={branch.id}
          branch={branch}
          isEditing={editingBranchId === branch.id}
          editedQuestions={editingBranchId === branch.id ? editedQuestions : []}
          isSaving={isSaving}
          isSending={isSending}
          onStartEdit={() => startEditing(branch)}
          onCancelEdit={cancelEditing}
          onUpdateQuestion={updateQuestion}
          onSave={() => saveEdits(branch.id)}
          onSend={() => sendToClient(branch.id)}
        />
      ))}
    </div>
  )
}

export default DeepReviewPanel
