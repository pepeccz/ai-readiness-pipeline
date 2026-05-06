/**
 * LeadActionPanel — Accept / Reject / Request extra info action buttons.
 * Shown on LeadDetailPage for leads in pending_review status.
 */

import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { patchLead } from '../../api/leads'
import type { LeadDetail, RejectReason } from '../../api/leads'
import { ApiError, fetchJson } from '../../../admin/api/client'
import { intakeKeys, useIntakeState, useFinalClose } from '../../../intake/api/intake'
import { ConfirmModal } from '../../../shared/components/ConfirmModal'

interface ConsultantOption {
  id: string
  email: string
  display_name: string
}

const REJECT_REASONS: { value: RejectReason; label: string }[] = [
  { value: 'not_qualified_size', label: 'Empresa demasiado pequeña/grande' },
  { value: 'out_of_sector', label: 'Fuera de sectores objetivo' },
  { value: 'no_decision_authority', label: 'Sin autoridad de decisión' },
  { value: 'not_aligned_with_offering', label: 'No encaja con el producto' },
  { value: 'not_a_real_lead', label: 'Sospecha de competencia/test' },
  { value: 'other', label: 'Otro' },
]

interface LeadActionPanelProps {
  lead: LeadDetail
  onActionComplete: () => void
}

export function LeadActionPanel({ lead, onActionComplete }: LeadActionPanelProps) {
  const queryClient = useQueryClient()
  const [showRejectForm, setShowRejectForm] = useState(false)
  const [rejectReason, setRejectReason] = useState<RejectReason>('not_qualified_size')
  const [consultantId, setConsultantId] = useState('')
  const [showCloseConfirm, setShowCloseConfirm] = useState(false)

  const { data: intakeState } = useIntakeState(lead.id)
  const finalClose = useFinalClose(lead.id)

  const isDeepReceived = intakeState?.state === 'deep_received'
  const isDeepPendingZero =
    intakeState?.state === 'deep_pending' && (intakeState?.deep_branches_count ?? 1) === 0
  const showCloseButton = isDeepReceived || isDeepPendingZero
  const useForce = isDeepPendingZero && !isDeepReceived

  const { data: consultants = [] } = useQuery<ConsultantOption[]>({
    queryKey: ['admin-users'],
    queryFn: () => fetchJson<ConsultantOption[]>('/admin/users'),
    staleTime: 5 * 60_000,
  })

  useEffect(() => {
    if (!consultantId && consultants.length > 0) {
      setConsultantId(consultants[0].id)
    }
  }, [consultants, consultantId])
  const [showAcceptForm, setShowAcceptForm] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: (body: Parameters<typeof patchLead>[1]) => patchLead(lead.id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lead', lead.id] })
      queryClient.invalidateQueries({ queryKey: ['leads'], exact: false })
      queryClient.invalidateQueries({ queryKey: intakeKeys.state(lead.id) })
      setShowRejectForm(false)
      setShowAcceptForm(false)
      setError(null)
      onActionComplete()
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Error inesperado. Intentá de nuevo.')
      }
    },
  })

  if (lead.status !== 'pending_review' && !showCloseButton) {
    return null
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
      <h3 className="text-sm font-semibold text-gray-700">Acciones</h3>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {lead.status === 'pending_review' && !showAcceptForm && !showRejectForm && (
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setShowAcceptForm(true)}
            className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition-colors"
          >
            Aceptar
          </button>
          <button
            onClick={() => setShowRejectForm(true)}
            className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 transition-colors"
          >
            Rechazar
          </button>
          <button
            onClick={() => mutation.mutate({ action: 'request_extra_info' })}
            disabled={mutation.isPending}
            className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            Pedir más info
          </button>
        </div>
      )}

      {showAcceptForm && (
        <div className="space-y-3">
          <label className="block">
            <span className="text-sm font-medium text-gray-700">Consultor asignado</span>
            {consultants.length === 0 ? (
              <p className="mt-1 text-sm text-gray-500">Cargando consultores...</p>
            ) : (
              <select
                value={consultantId}
                onChange={(e) => setConsultantId(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-400"
              >
                {consultants.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.display_name} ({c.email})
                  </option>
                ))}
              </select>
            )}
          </label>
          <div className="flex gap-2">
            <button
              onClick={() =>
                mutation.mutate({ action: 'accept', consultant_id: consultantId })
              }
              disabled={mutation.isPending || !consultantId.trim()}
              className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {mutation.isPending ? 'Guardando...' : 'Confirmar aceptación'}
            </button>
            <button
              onClick={() => setShowAcceptForm(false)}
              className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-200 transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {showCloseButton && (
        <div className="pt-2 border-t border-gray-100">
          <button
            onClick={() => setShowCloseConfirm(true)}
            disabled={finalClose.isPending}
            className="px-4 py-2 bg-gray-700 text-white text-sm font-medium rounded-md hover:bg-gray-800 disabled:opacity-50 transition-colors"
          >
            {finalClose.isPending ? 'Cerrando...' : 'Marcar como cerrado'}
          </button>
        </div>
      )}

      <ConfirmModal
        open={showCloseConfirm}
        title="Cerrar sesión definitivamente"
        body="Esto cierra la sesión definitivamente. No podrás reabrirla. ¿Continuar?"
        confirmLabel="Confirmar"
        cancelLabel="Cancelar"
        variant="danger"
        onCancel={() => setShowCloseConfirm(false)}
        onConfirm={() => {
          setShowCloseConfirm(false)
          finalClose.mutate({ force: useForce })
        }}
      />

      {showRejectForm && (
        <div className="space-y-3">
          <label className="block">
            <span className="text-sm font-medium text-gray-700">Motivo del rechazo</span>
            <select
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value as RejectReason)}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-400"
            >
              {REJECT_REASONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </label>
          <div className="flex gap-2">
            <button
              onClick={() =>
                mutation.mutate({ action: 'reject', reason: rejectReason })
              }
              disabled={mutation.isPending}
              className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              {mutation.isPending ? 'Guardando...' : 'Confirmar rechazo'}
            </button>
            <button
              onClick={() => setShowRejectForm(false)}
              className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-200 transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
