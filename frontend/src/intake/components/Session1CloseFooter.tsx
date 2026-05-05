/**
 * Session1CloseFooter — "Cerrar sesión 1" button + confirm modal (D9/REQ-1).
 *
 * Visibility rules:
 *   - Shown only when state in {in_progress, blocks_completed}
 *   - Hidden when state >= deep_pending
 *   - Button enabled only when block-1-strategic is in blocksCompleted
 *   - On confirm: calls POST /intake/{leadId}/session1/close
 *   - On success: navigates to /admin/leads/{leadId}
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ConfirmModal } from '../../shared/components/ConfirmModal'
import { useSession1Close } from '../api/intake'

const VISIBLE_STATES = new Set(['in_progress', 'blocks_completed'])
const BLOCK1_ID = 'block-1-strategic'

const MODAL_BODY =
  'Esto disparará síntesis LLM y generará follow-ups DEEP automáticamente. ' +
  'Bloques sin enviar quedan sin contribuir a la síntesis. ¿Continuar?'

interface Session1CloseFooterProps {
  leadId: string
  state: string
  blocksCompleted: string[]
}

export function Session1CloseFooter({
  leadId,
  state,
  blocksCompleted,
}: Session1CloseFooterProps) {
  const navigate = useNavigate()
  const [modalOpen, setModalOpen] = useState(false)

  const { mutate, isPending } = useSession1Close(leadId)

  if (!VISIBLE_STATES.has(state)) return null

  const block1Done = blocksCompleted.includes(BLOCK1_ID)

  const handleConfirm = () => {
    setModalOpen(false)
    mutate(undefined, {
      onSuccess: () => {
        navigate(`/admin/leads/${leadId}`)
      },
    })
  }

  return (
    <>
      <div className="mt-8 pt-6 border-t border-neutral-200 flex justify-end">
        <div className="flex flex-col items-end gap-1">
          {!block1Done && (
            <p className="text-xs text-neutral-500">
              Necesitás enviar el bloque 1 antes de cerrar
            </p>
          )}
          <button
            type="button"
            disabled={!block1Done || isPending}
            onClick={() => setModalOpen(true)}
            className="px-5 py-2 text-sm font-medium rounded-md transition-colors
              bg-teal-600 text-white hover:bg-teal-700
              disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isPending ? 'Cerrando...' : 'Cerrar sesión 1'}
          </button>
        </div>
      </div>

      <ConfirmModal
        open={modalOpen}
        title="¿Cerrar sesión 1?"
        body={MODAL_BODY}
        confirmLabel="Continuar"
        cancelLabel="Cancelar"
        onConfirm={handleConfirm}
        onCancel={() => setModalOpen(false)}
      />
    </>
  )
}
