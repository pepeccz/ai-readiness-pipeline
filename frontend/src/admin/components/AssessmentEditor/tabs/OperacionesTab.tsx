/**
 * OperacionesTab — operaciones (form_data section 5).
 *
 * 5 canonical form_data keys:
 *   most_time_consuming_process, process_people_count, process_hours_per_week,
 *   data_entry_channels, process_pain_points
 */

import { FormDataField } from '../FormDataField'

const PROCESS_PEOPLE_OPTIONS = [
  { value: '1', label: '1 persona' },
  { value: '2-5', label: '2–5 personas' },
  { value: '6-15', label: '6–15 personas' },
  { value: '16+', label: 'Más de 15 personas' },
]

const PROCESS_HOURS_OPTIONS = [
  { value: '<5', label: 'Menos de 5 horas/semana' },
  { value: '5-20', label: '5–20 horas/semana' },
  { value: '20-40', label: '20–40 horas/semana' },
  { value: '40+', label: 'Más de 40 horas/semana' },
]

const DATA_ENTRY_CHANNEL_OPTIONS = [
  { value: 'email', label: 'Email' },
  { value: 'formulario_web', label: 'Formulario web' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'excel', label: 'Excel / Hoja de cálculo' },
  { value: 'manual_papel', label: 'Manual / Papel' },
  { value: 'sistema_externo', label: 'Sistema externo / ERP' },
  { value: 'otro', label: 'Otro' },
]

const PAIN_POINT_OPTIONS = [
  { value: 'manual', label: 'Trabajo muy manual' },
  { value: 'errores', label: 'Errores frecuentes' },
  { value: 'lento', label: 'Proceso lento' },
  { value: 'retrabajo', label: 'Retrabajo / Duplicación' },
  { value: 'coordinacion', label: 'Problemas de coordinación' },
  { value: 'visibilidad', label: 'Falta de visibilidad' },
  { value: 'otro', label: 'Otro' },
]

interface Props {
  assessmentId: string
  fieldSources: Record<string, string>
}

export function OperacionesTab({ assessmentId, fieldSources }: Props) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
      <div className="sm:col-span-2">
        <FormDataField
          name="most_time_consuming_process"
          label="Proceso que más tiempo consume"
          type="textarea"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Describí el proceso que más tiempo (y personas) consume en el área..."
        />
      </div>

      <FormDataField
        name="process_people_count"
        label="¿Cuántas personas involucra?"
        type="select"
        options={PROCESS_PEOPLE_OPTIONS}
        assessmentId={assessmentId}
        fieldSources={fieldSources}
      />

      <FormDataField
        name="process_hours_per_week"
        label="¿Cuántas horas/semana consume?"
        type="select"
        options={PROCESS_HOURS_OPTIONS}
        assessmentId={assessmentId}
        fieldSources={fieldSources}
      />

      <div className="sm:col-span-2">
        <FormDataField
          name="data_entry_channels"
          label="Canales de entrada de datos"
          type="multiselect-options"
          options={DATA_ENTRY_CHANNEL_OPTIONS}
          assessmentId={assessmentId}
          fieldSources={fieldSources}
        />
      </div>

      <div className="sm:col-span-2">
        <FormDataField
          name="process_pain_points"
          label="Pain points del proceso"
          type="multiselect-options"
          options={PAIN_POINT_OPTIONS}
          assessmentId={assessmentId}
          fieldSources={fieldSources}
        />
      </div>
    </div>
  )
}
