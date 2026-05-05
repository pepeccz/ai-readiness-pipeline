/**
 * LeadDetailPage — Full lead detail view.
 *
 * Route: /admin/leads/:id
 *
 * Shows:
 *   - Contact info (name, email, company, phone, sector, role)
 *   - TRIAGE payload (expandable JSON)
 *   - Score breakdown + bucket badge
 *   - Active consents audit trail
 *   - Accept / Reject / Request extra info action panel (only when pending_review)
 */

import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getLead } from '../api/leads'
import { BucketBadge } from '../components/LeadDetail/BucketBadge'
import { LeadActionPanel } from '../components/LeadDetail/LeadActionPanel'

const STATUS_LABELS: Record<string, string> = {
  pending_review: 'Pendiente revisión',
  accepted: 'Aceptado',
  rejected: 'Rechazado',
  converted: 'Convertido',
}

export function LeadDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [showPayload, setShowPayload] = useState(false)

  const { data: lead, isLoading, isError, refetch } = useQuery({
    queryKey: ['lead', id],
    queryFn: () => getLead(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-400">Cargando lead...</p>
      </div>
    )
  }

  if (isError || !lead) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center gap-4">
        <p className="text-red-500">No se pudo cargar el lead.</p>
        <button
          onClick={() => navigate('/admin/leads')}
          className="text-sm text-teal-600 underline"
        >
          Volver a la lista
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-4">
          <button
            onClick={() => navigate('/admin/leads')}
            className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Leads
          </button>
          <span className="text-gray-300">/</span>
          <h1 className="text-sm font-semibold text-gray-800 truncate">
            {lead.company_name}
          </h1>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Top info card */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900">{lead.company_name}</h2>
              <p className="text-gray-500 text-sm mt-0.5">{lead.full_name}</p>
            </div>
            <div className="flex items-center gap-2">
              <BucketBadge bucket={lead.triage_bucket} />
              <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                lead.status === 'accepted' ? 'bg-green-100 text-green-700' :
                lead.status === 'rejected' ? 'bg-red-100 text-red-700' :
                lead.status === 'converted' ? 'bg-purple-100 text-purple-700' :
                'bg-orange-100 text-orange-700'
              }`}>
                {STATUS_LABELS[lead.status] ?? lead.status}
              </span>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
            <InfoField label="Email" value={lead.email} />
            <InfoField label="Teléfono" value={lead.phone ?? '—'} />
            <InfoField label="Sector" value={lead.sector} />
            <InfoField label="Tamaño empresa" value={lead.company_size} />
            <InfoField label="Rol" value={lead.respondent_role} />
            <InfoField label="Madurez IA" value={lead.ai_maturity} />
            <InfoField label="Urgencia" value={lead.urgency} />
            <InfoField label="Compromiso" value={lead.commitment} />
            <InfoField
              label="Creado"
              value={new Date(lead.created_at).toLocaleString('es-ES')}
            />
          </div>

          {lead.rejected_reason && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-md px-4 py-3 text-sm text-red-700">
              <span className="font-medium">Motivo de rechazo:</span> {lead.rejected_reason}
            </div>
          )}
        </div>

        {/* Score card */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Scoring TRIAGE</h3>
          <div className="flex items-center gap-4">
            <div className="text-4xl font-bold text-gray-900">{lead.triage_score}</div>
            <div>
              <p className="text-sm text-gray-500">Score total (máx. 136)</p>
              <div className="mt-1 w-48 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-teal-500 h-2 rounded-full"
                  style={{ width: `${Math.min(100, (lead.triage_score / 136) * 100)}%` }}
                />
              </div>
            </div>
            <div className="ml-4">
              <BucketBadge bucket={lead.triage_bucket} />
            </div>
          </div>

          {lead.ai_goals?.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                Objetivos IA
              </p>
              <div className="flex gap-2 flex-wrap">
                {lead.ai_goals.map((goal, i) => (
                  <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                    {goal}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* TRIAGE payload — expandable */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <button
            onClick={() => setShowPayload((v) => !v)}
            className="flex items-center gap-2 text-sm font-semibold text-gray-700 w-full text-left"
          >
            <svg
              className={`w-4 h-4 transition-transform ${showPayload ? 'rotate-90' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
            Payload TRIAGE completo
          </button>
          {showPayload && (
            <pre className="mt-3 bg-gray-50 rounded p-4 text-xs overflow-auto max-h-96 text-gray-700">
              {JSON.stringify(lead.triage_payload, null, 2)}
            </pre>
          )}
        </div>

        {/* Consents */}
        {lead.consents?.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Consentimientos</h3>
            <table className="min-w-full divide-y divide-gray-100 text-sm">
              <thead>
                <tr>
                  <th className="text-left text-xs text-gray-500 font-medium py-2 pr-4">Tipo</th>
                  <th className="text-left text-xs text-gray-500 font-medium py-2 pr-4">Aceptado</th>
                  <th className="text-left text-xs text-gray-500 font-medium py-2 pr-4">Versión política</th>
                  <th className="text-left text-xs text-gray-500 font-medium py-2">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {lead.consents.map((c) => (
                  <tr key={c.id}>
                    <td className="py-2 pr-4 font-medium text-gray-700">{c.type}</td>
                    <td className="py-2 pr-4">
                      <span className={c.accepted ? 'text-green-600' : 'text-red-500'}>
                        {c.accepted ? 'Sí' : 'No'}
                      </span>
                    </td>
                    <td className="py-2 pr-4 text-gray-500">{c.policy_version}</td>
                    <td className="py-2 text-gray-400 text-xs">
                      {new Date(c.timestamp).toLocaleString('es-ES')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Action panel */}
        <LeadActionPanel lead={lead} onActionComplete={() => refetch()} />
      </main>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Info field helper
// ---------------------------------------------------------------------------

function InfoField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-400 uppercase tracking-wide font-medium">{label}</p>
      <p className="text-sm text-gray-800 mt-0.5">{value}</p>
    </div>
  )
}
