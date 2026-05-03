/**
 * SparseConfirmDialog — warns the user before running LLM enrichment, generating
 * the PDF, or approving-and-sending when the assessment form_data is sparse.
 *
 * The dialog is ONLY rendered when `open === true`; the caller decides when to
 * show it (isSparse check lives in the parent, not here).
 *
 * Default focus: "Cancelar" button — pressing Enter or Esc does NOT confirm.
 * Users must actively click "Sí, continuar" to proceed.
 *
 * Styling follows ApproveAndSendDialog.tsx conventions.
 * TypeScript strict + erasableSyntaxOnly — no enums, no constructor param props.
 */

import type { CompletenessResult } from '../../hooks/useAssessmentCompleteness'

interface Props {
  open: boolean
  completeness: CompletenessResult
  /** Label for the risky action, e.g. "re-correr LLM", "generar PDF", "aprobar y enviar" */
  actionLabel: string
  onConfirm: () => void
  onCancel: () => void
}

export function SparseConfirmDialog({ open, completeness, actionLabel, onConfirm, onCancel }: Props) {
  if (!open) return null

  const { filledKeys, totalKeys, percentage, missingCritical } = completeness
  const percentDisplay = Math.round(percentage * 100)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6">
        {/* Header */}
        <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
          <span className="text-amber-500">⚠</span>
          Datos incompletos
        </h3>

        {/* Main warning */}
        <p className="text-sm text-gray-600 mb-3">
          El assessment tiene{' '}
          <strong>
            {filledKeys} de {totalKeys} campos completos ({percentDisplay}%)
          </strong>
          . El reporte va a salir limitado.
        </p>

        {/* Critical fields list (conditional) */}
        {missingCritical.length > 0 && (
          <div className="mb-4 p-3 rounded-lg bg-amber-50 border border-amber-200">
            <p className="text-xs font-medium text-amber-800 mb-1">Faltan datos críticos:</p>
            <p className="text-xs text-amber-700">{missingCritical.join(', ')}</p>
          </div>
        )}

        {/* Confirm question */}
        <p className="text-sm text-gray-700 mb-5">
          ¿Querés <strong>{actionLabel}</strong> de todas formas?
        </p>

        {/* Actions — Cancel is default-focused */}
        <div className="flex justify-end gap-3">
          <button
            // eslint-disable-next-line jsx-a11y/no-autofocus
            autoFocus
            onClick={onCancel}
            className="px-4 py-2 rounded-lg border border-gray-300 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 rounded-lg bg-amber-500 text-white text-sm font-medium hover:bg-amber-600 transition-colors"
          >
            Sí, continuar
          </button>
        </div>
      </div>
    </div>
  )
}
