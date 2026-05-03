/**
 * RRHHTab — recursos humanos (form_data section 7).
 *
 * 4 canonical form_data keys:
 *   is_hiring, hiring_desc, hr_management_method, hr_hours_per_week
 */

import { useFormContext } from 'react-hook-form'
import { FormDataField } from '../FormDataField'

const HR_MANAGEMENT_OPTIONS = [
  { value: 'manual', label: 'Manual / Sin software específico' },
  { value: 'software_hr', label: 'Software de RRHH' },
  { value: 'mixto', label: 'Mixto' },
  { value: 'tercerizado', label: 'Tercerizado / Gestoría' },
]

const HR_HOURS_OPTIONS = [
  { value: '<5', label: 'Menos de 5 horas/semana' },
  { value: '5-20', label: '5–20 horas/semana' },
  { value: '20-40', label: '20–40 horas/semana' },
  { value: '40+', label: 'Más de 40 horas/semana' },
]

interface Props {
  assessmentId: string
  fieldSources: Record<string, string>
}

export function RRHHTab({ assessmentId, fieldSources }: Props) {
  const { watch } = useFormContext()
  const formData = (watch('form_data') as Record<string, unknown>) ?? {}
  const isHiring = Boolean(formData['is_hiring'])

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
      <FormDataField
        name="is_hiring"
        label="¿Está contratando actualmente?"
        type="boolean"
        assessmentId={assessmentId}
        fieldSources={fieldSources}
        placeholder="Sí, está en proceso de contratación"
      />

      {isHiring && (
        <div className="sm:col-span-2">
          <FormDataField
            name="hiring_desc"
            label="Descripción del proceso de contratación"
            type="textarea"
            assessmentId={assessmentId}
            fieldSources={fieldSources}
            placeholder="¿Qué perfiles busca, cómo es el proceso, cuánto tarda...?"
          />
        </div>
      )}

      <FormDataField
        name="hr_management_method"
        label="Método de gestión de RRHH"
        type="select"
        options={HR_MANAGEMENT_OPTIONS}
        assessmentId={assessmentId}
        fieldSources={fieldSources}
      />

      <FormDataField
        name="hr_hours_per_week"
        label="Horas de RRHH por semana"
        type="select"
        options={HR_HOURS_OPTIONS}
        assessmentId={assessmentId}
        fieldSources={fieldSources}
      />
    </div>
  )
}
