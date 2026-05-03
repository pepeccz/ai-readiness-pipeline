/**
 * ComplianceTab — compliance y regulación (form_data section 8).
 *
 * Realigned to canonical form_data keys (7):
 *   collects_personal_data, personal_data_types, knows_ai_gdpr, has_dpa,
 *   dpa_with_whom, knows_ai_act, has_ai_policy
 *
 * Plus flat editable field: who_decides (via EditorField — admin-only, not in form_data).
 *
 * Previous phantom keys (gdpr_compliance, dpa_signed, data_retention_policy,
 * ai_usage_policy, automated_decision_systems, incident_response_plan,
 * sector_specific_regulations) are removed — they were not canonical.
 */

import { useFormContext } from 'react-hook-form'
import { EditorField } from '../EditorField'
import { FormDataField } from '../FormDataField'

const KNOWS_AI_GDPR_OPTIONS = [
  { value: 'si_total', label: 'Sí, lo conocemos bien' },
  { value: 'parcial', label: 'Parcialmente' },
  { value: 'no', label: 'No' },
]

const HAS_DPA_OPTIONS = [
  { value: 'si', label: 'Sí, con todos los proveedores relevantes' },
  { value: 'parcial', label: 'Con algunos proveedores' },
  { value: 'no', label: 'No' },
  { value: 'no_aplica', label: 'No aplica' },
]

const KNOWS_AI_ACT_OPTIONS = [
  { value: 'si_total', label: 'Sí, lo conocemos bien' },
  { value: 'parcial', label: 'Parcialmente' },
  { value: 'no', label: 'No' },
]

const HAS_AI_POLICY_OPTIONS = [
  { value: 'si', label: 'Sí, está implementada' },
  { value: 'borrador', label: 'En borrador' },
  { value: 'no', label: 'No' },
]

interface Props {
  assessmentId: string
  fieldSources: Record<string, string>
}

export function ComplianceTab({ assessmentId, fieldSources }: Props) {
  const { watch } = useFormContext()
  const formData = (watch('form_data') as Record<string, unknown>) ?? {}
  const collectsPersonalData = Boolean(formData['collects_personal_data'])
  const hasDpa = (formData['has_dpa'] as string | undefined)
  const showDpaWithWhom = hasDpa === 'si' || hasDpa === 'parcial'

  return (
    <div>
      {/* Flat editable field — admin-only, not from wizard */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Decisiones tecnológicas</h4>
        <EditorField
          name="who_decides"
          label="Quién decide sobre tecnología"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Ej: CTO, CEO, comité de dirección"
        />
      </div>

      {/* form_data compliance fields */}
      <h4 className="text-sm font-semibold text-gray-700 mb-3">Compliance y regulación</h4>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
        <FormDataField
          name="collects_personal_data"
          label="¿Recolecta datos personales?"
          type="boolean"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Sí, recolecta datos personales"
        />

        {collectsPersonalData && (
          <div className="sm:col-span-2">
            <FormDataField
              name="personal_data_types"
              label="Tipos de datos personales que recolecta"
              type="textarea"
              assessmentId={assessmentId}
              fieldSources={fieldSources}
              placeholder="Ej: nombre, email, datos financieros, datos de salud..."
            />
          </div>
        )}

        <FormDataField
          name="knows_ai_gdpr"
          label="¿Conoce las implicaciones de IA + RGPD?"
          type="select"
          options={KNOWS_AI_GDPR_OPTIONS}
          assessmentId={assessmentId}
          fieldSources={fieldSources}
        />

        <FormDataField
          name="has_dpa"
          label="¿Tiene DPA firmados con proveedores?"
          type="select"
          options={HAS_DPA_OPTIONS}
          assessmentId={assessmentId}
          fieldSources={fieldSources}
        />

        {showDpaWithWhom && (
          <div className="sm:col-span-2">
            <FormDataField
              name="dpa_with_whom"
              label="DPA firmados con quién"
              type="textarea"
              assessmentId={assessmentId}
              fieldSources={fieldSources}
              placeholder="Proveedores o categorías de proveedores con DPA firmado..."
            />
          </div>
        )}

        <FormDataField
          name="knows_ai_act"
          label="¿Conoce el AI Act?"
          type="select"
          options={KNOWS_AI_ACT_OPTIONS}
          assessmentId={assessmentId}
          fieldSources={fieldSources}
        />

        <FormDataField
          name="has_ai_policy"
          label="¿Tiene política de uso de IA?"
          type="select"
          options={HAS_AI_POLICY_OPTIONS}
          assessmentId={assessmentId}
          fieldSources={fieldSources}
        />
      </div>
    </div>
  )
}
