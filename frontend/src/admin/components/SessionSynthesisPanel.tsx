/**
 * SessionSynthesisPanel — Dual-mode synthesis editor/viewer for Session 1.
 *
 * Mode resolution:
 *   mode='edit' when intakeState in {deep_received, closed}
 *   mode='view' when intakeState === 'deep_pending'
 *   hidden when intakeState in {not_started, in_progress, blocks_completed}
 *
 * Features:
 *   - F.1: mode='view' | 'edit' derived from intakeState
 *   - F.2: useFieldArray for recommendations, key_insights, next_steps, roadmap
 *   - F.3: Explicit "Guardar" button — no auto-save; disabled when !isDirty
 *   - F.4: Per-block "Restaurar original" button (frontend-only, no immediate PATCH)
 *   - F.5: hypothesis shown read-only; excluded from PATCH body
 *
 * UI copy: Castellano, tú/usted-neutral, no voseo.
 */

import { useEffect } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import type { Session1Synthesis, RecommendationItem } from '../../types/api'
import { useServiceCatalog } from '../hooks/useCatalog'

// ── State constants ──────────────────────────────────────────────────────────

const EDIT_STATES = new Set(['deep_received', 'closed'])
const VIEW_STATES = new Set(['deep_pending'])

// ── Types ────────────────────────────────────────────────────────────────────

interface FormValues {
  summary: string
  key_insights: Array<{ value: string }>
  recommendations: Array<{
    text: string
    impact: string
    effort: string
    related_service: string
    custom_service_label: string
  }>
  roadmap_d30: Array<{ value: string }>
  roadmap_d60: Array<{ value: string }>
  roadmap_d90: Array<{ value: string }>
  next_steps: Array<{ value: string }>
}

interface Props {
  leadId: string
  intakeState: string
  synthesisEffective: Session1Synthesis | null
  synthesisRaw: Session1Synthesis | null
  onSaveSuccess?: () => void
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function toFieldArray(items: string[] | undefined) {
  return (items ?? []).map((value) => ({ value }))
}

function fromFieldArray(items: Array<{ value: string }>) {
  return items.map((i) => i.value)
}

function toRecsForm(recs: RecommendationItem[] | undefined) {
  return (recs ?? []).map((r) => ({
    text: r.text ?? '',
    impact: r.impact ?? '',
    effort: r.effort ?? '',
    related_service: r.related_service ?? '',
    custom_service_label: r.custom_service_label ?? '',
  }))
}

function synthesisToForm(s: Session1Synthesis | null): FormValues {
  if (!s) {
    return {
      summary: '',
      key_insights: [],
      recommendations: [],
      roadmap_d30: [],
      roadmap_d60: [],
      roadmap_d90: [],
      next_steps: [],
    }
  }
  return {
    summary: s.summary ?? '',
    key_insights: toFieldArray(s.key_insights),
    recommendations: toRecsForm(s.recommendations),
    roadmap_d30: toFieldArray(s.roadmap?.d30),
    roadmap_d60: toFieldArray(s.roadmap?.d60),
    roadmap_d90: toFieldArray(s.roadmap?.d90),
    next_steps: toFieldArray(s.next_steps),
  }
}

// ── Component ────────────────────────────────────────────────────────────────

export function SessionSynthesisPanel({
  leadId,
  intakeState,
  synthesisEffective,
  synthesisRaw,
  onSaveSuccess,
}: Props) {
  const { data: catalog = [] } = useServiceCatalog()

  const mode: 'edit' | 'view' | 'hidden' = EDIT_STATES.has(intakeState)
    ? 'edit'
    : VIEW_STATES.has(intakeState)
    ? 'view'
    : 'hidden'

  const {
    register,
    control,
    handleSubmit,
    reset,
    setValue,
    formState: { isDirty, isSubmitting },
    watch,
  } = useForm<FormValues>({
    defaultValues: synthesisToForm(synthesisEffective),
  })

  // Reset form when effective synthesis changes (e.g. after successful save)
  useEffect(() => {
    reset(synthesisToForm(synthesisEffective))
  }, [synthesisEffective, reset])

  const { fields: insightFields } = useFieldArray({ control, name: 'key_insights' })
  const { fields: recFields } = useFieldArray({ control, name: 'recommendations' })
  const { fields: d30Fields } = useFieldArray({ control, name: 'roadmap_d30' })
  const { fields: d60Fields } = useFieldArray({ control, name: 'roadmap_d60' })
  const { fields: d90Fields } = useFieldArray({ control, name: 'roadmap_d90' })
  const { fields: nextStepFields } = useFieldArray({ control, name: 'next_steps' })

  if (mode === 'hidden') return null

  const isReadOnly = mode === 'view'

  const onSubmit = async (data: FormValues) => {
    // hypothesis is deliberately EXCLUDED from the PATCH body
    const body = {
      summary: data.summary || null,
      key_insights: fromFieldArray(data.key_insights),
      recommendations: data.recommendations.map((r) => ({
        text: r.text,
        impact: r.impact || null,
        effort: r.effort || null,
        related_service: r.related_service || null,
        custom_service_label:
          r.related_service === 'otro' && r.custom_service_label.trim()
            ? r.custom_service_label.trim()
            : null,
      })),
      roadmap: {
        d30: fromFieldArray(data.roadmap_d30),
        d60: fromFieldArray(data.roadmap_d60),
        d90: fromFieldArray(data.roadmap_d90),
      },
      next_steps: fromFieldArray(data.next_steps),
    }

    const resp = await fetch(`/api/intake/${leadId}/session1/synthesis`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(body),
    })

    if (resp.ok) {
      reset(data)
      onSaveSuccess?.()
    }
  }

  const restoreField = (
    fieldName: keyof FormValues,
    rawValue: Session1Synthesis | null
  ) => {
    if (!rawValue) return
    const rawForm = synthesisToForm(rawValue)
    setValue(fieldName, rawForm[fieldName] as never, { shouldDirty: true })
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
      <h3 className="text-sm font-semibold text-gray-700">Síntesis — Sesión 1</h3>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

        {/* ── Hipótesis interna (read-only, excluded from form body) ─────────── */}
        {synthesisEffective?.hypothesis && (
          <div className="bg-amber-50 border border-amber-200 rounded p-3 space-y-1">
            <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide">
              Hipótesis interna — Solo visible para el equipo Zanovix
            </p>
            <p className="text-sm text-amber-800">{synthesisEffective.hypothesis}</p>
          </div>
        )}

        {/* ── Resumen ejecutivo ─────────────────────────────────────────────── */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Resumen ejecutivo
            </label>
            {!isReadOnly && synthesisRaw?.summary !== watch('summary') && (
              <button
                type="button"
                onClick={() => restoreField('summary', synthesisRaw)}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Restaurar original
              </button>
            )}
          </div>
          <textarea
            {...register('summary')}
            readOnly={isReadOnly}
            rows={4}
            className="w-full text-sm border border-gray-200 rounded px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-teal-400 disabled:bg-gray-50"
          />
        </div>

        {/* ── Insights clave ────────────────────────────────────────────────── */}
        {insightFields.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Hallazgos clave
            </p>
            <div className="space-y-2">
              {insightFields.map((field, i) => (
                <textarea
                  key={field.id}
                  {...register(`key_insights.${i}.value`)}
                  readOnly={isReadOnly}
                  rows={2}
                  className="w-full text-sm border border-gray-200 rounded px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-teal-400"
                />
              ))}
            </div>
          </div>
        )}

        {/* ── Recomendaciones ───────────────────────────────────────────────── */}
        {recFields.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Recomendaciones
            </p>
            {recFields.map((field, i) => (
              <div key={field.id} className="border border-gray-200 rounded p-3 space-y-2">
                <textarea
                  {...register(`recommendations.${i}.text`)}
                  readOnly={isReadOnly}
                  rows={2}
                  className="w-full text-sm border border-gray-100 rounded px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-teal-400"
                />
                {!isReadOnly && (
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="text-xs text-gray-500">Impacto</label>
                      <select
                        {...register(`recommendations.${i}.impact`)}
                        className="w-full text-sm border border-gray-200 rounded px-2 py-1"
                      >
                        <option value="">—</option>
                        <option value="alto">Alto</option>
                        <option value="medio">Medio</option>
                        <option value="bajo">Bajo</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Esfuerzo</label>
                      <select
                        {...register(`recommendations.${i}.effort`)}
                        className="w-full text-sm border border-gray-200 rounded px-2 py-1"
                      >
                        <option value="">—</option>
                        <option value="alto">Alto</option>
                        <option value="medio">Medio</option>
                        <option value="bajo">Bajo</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Servicio Zanovix relacionado</label>
                      <select
                        {...register(`recommendations.${i}.related_service`)}
                        className="w-full text-sm border border-gray-200 rounded px-2 py-1"
                      >
                        <option value="">Ninguno</option>
                        {catalog.map((svc) => (
                          <option key={svc.key} value={svc.key}>
                            {svc.nombre}
                          </option>
                        ))}
                        <option value="otro">Otro / Externo</option>
                      </select>
                    </div>
                  </div>
                )}
                {!isReadOnly &&
                  watch(`recommendations.${i}.related_service`) === 'otro' && (
                    <div className="mt-2">
                      <label className="text-xs text-gray-500">
                        Etiqueta personalizada (ej: Derivar a partner X)
                      </label>
                      <input
                        type="text"
                        maxLength={80}
                        placeholder="Acción externa o partner derivado"
                        {...register(`recommendations.${i}.custom_service_label`)}
                        className="w-full text-sm border border-gray-200 rounded px-2 py-1"
                      />
                    </div>
                  )}
              </div>
            ))}
          </div>
        )}

        {/* ── Roadmap 30/60/90 ─────────────────────────────────────────────── */}
        {(d30Fields.length > 0 || d60Fields.length > 0 || d90Fields.length > 0) && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Hoja de ruta
            </p>
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: '30 días', fields: d30Fields, name: 'roadmap_d30' as const },
                { label: '60 días', fields: d60Fields, name: 'roadmap_d60' as const },
                { label: '90 días', fields: d90Fields, name: 'roadmap_d90' as const },
              ].map(({ label, fields, name }) => (
                <div key={name} className="space-y-1">
                  <p className="text-xs font-medium text-gray-600">{label}</p>
                  {fields.map((field, i) => (
                    <textarea
                      key={field.id}
                      {...register(`${name}.${i}.value`)}
                      readOnly={isReadOnly}
                      rows={2}
                      className="w-full text-sm border border-gray-200 rounded px-2 py-1 resize-none"
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Próximos pasos ────────────────────────────────────────────────── */}
        {nextStepFields.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Próximos pasos
            </p>
            <div className="space-y-2">
              {nextStepFields.map((field, i) => (
                <textarea
                  key={field.id}
                  {...register(`next_steps.${i}.value`)}
                  readOnly={isReadOnly}
                  rows={2}
                  className="w-full text-sm border border-gray-200 rounded px-3 py-2 resize-none"
                />
              ))}
            </div>
          </div>
        )}

        {/* ── Guardar button ────────────────────────────────────────────────── */}
        {!isReadOnly && (
          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={!isDirty || isSubmitting}
              className="px-4 py-2 text-sm font-medium bg-teal-600 text-white rounded hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Guardando…' : 'Guardar'}
            </button>
          </div>
        )}
      </form>
    </div>
  )
}
