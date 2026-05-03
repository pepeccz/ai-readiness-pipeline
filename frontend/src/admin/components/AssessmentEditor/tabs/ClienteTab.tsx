/**
 * ClienteTab — atención al cliente (form_data section 3).
 *
 * 5 canonical form_data keys:
 *   contact_channels, daily_queries, support_team_desc,
 *   top_repetitive_queries, avg_resolution_time
 */

import { FormDataField } from '../FormDataField'

const CONTACT_CHANNEL_OPTIONS = [
  { value: 'web', label: 'Web' },
  { value: 'email', label: 'Email' },
  { value: 'telefono', label: 'Teléfono' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'redes_sociales', label: 'Redes sociales' },
  { value: 'presencial', label: 'Presencial' },
  { value: 'otro', label: 'Otro' },
]

const DAILY_QUERIES_OPTIONS = [
  { value: '<10', label: 'Menos de 10' },
  { value: '10-50', label: '10–50' },
  { value: '50-200', label: '50–200' },
  { value: '200-500', label: '200–500' },
  { value: '500+', label: 'Más de 500' },
]

const AVG_RESOLUTION_OPTIONS = [
  { value: '<1h', label: 'Menos de 1 hora' },
  { value: '1-4h', label: '1–4 horas' },
  { value: '4-24h', label: '4–24 horas' },
  { value: '1-3d', label: '1–3 días' },
  { value: '>3d', label: 'Más de 3 días' },
]

interface Props {
  assessmentId: string
  fieldSources: Record<string, string>
}

export function ClienteTab({ assessmentId, fieldSources }: Props) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
      <div className="sm:col-span-2">
        <FormDataField
          name="contact_channels"
          label="Canales de contacto con clientes"
          type="multiselect-options"
          options={CONTACT_CHANNEL_OPTIONS}
          assessmentId={assessmentId}
          fieldSources={fieldSources}
        />
      </div>

      <FormDataField
        name="daily_queries"
        label="Consultas diarias aproximadas"
        type="select"
        options={DAILY_QUERIES_OPTIONS}
        assessmentId={assessmentId}
        fieldSources={fieldSources}
      />

      <FormDataField
        name="avg_resolution_time"
        label="Tiempo medio de resolución"
        type="select"
        options={AVG_RESOLUTION_OPTIONS}
        assessmentId={assessmentId}
        fieldSources={fieldSources}
      />

      <div className="sm:col-span-2">
        <FormDataField
          name="support_team_desc"
          label="Descripción del equipo de soporte"
          type="textarea"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Cuántas personas, roles, turnos..."
        />
      </div>

      <div className="sm:col-span-2">
        <FormDataField
          name="top_repetitive_queries"
          label="Consultas más repetitivas"
          type="textarea"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="¿Cuáles son las preguntas que más se repiten?"
        />
      </div>
    </div>
  )
}
