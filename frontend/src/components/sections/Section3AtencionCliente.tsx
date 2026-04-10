import type { FormState } from '../../types/form'
import { FormField } from '../ui/FormField'
import { MultiSelect } from '../ui/MultiSelect'
import { RadioGroup } from '../ui/RadioGroup'
import { TextInput } from '../ui/TextInput'
import { TextArea } from '../ui/TextArea'

interface Props {
  state: FormState
  onChange: <K extends keyof FormState>(key: K, value: FormState[K]) => void
  errors?: Record<string, string>
}

const CHANNEL_OPTIONS = [
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'email', label: 'Email' },
  { value: 'telefono', label: 'Teléfono' },
  { value: 'web_chat', label: 'Web / Chat' },
  { value: 'redes_sociales', label: 'Redes sociales' },
  { value: 'presencial', label: 'Presencial' },
]

const DAILY_QUERIES_OPTIONS = [
  { value: '<10', label: 'Menos de 10' },
  { value: '10-30', label: '10 – 30' },
  { value: '30-100', label: '30 – 100' },
  { value: '100+', label: 'Más de 100' },
]

const RESOLUTION_TIME_OPTIONS = [
  { value: '<5min', label: 'Menos de 5 min' },
  { value: '5-30min', label: '5 – 30 min' },
  { value: '30min-2h', label: '30 min – 2 h' },
  { value: '>2h', label: 'Más de 2 h' },
]

export function Section3AtencionCliente({ state, onChange, errors = {} }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <FormField label="Canales de contacto con clientes" error={errors.contact_channels}>
        <MultiSelect
          options={CHANNEL_OPTIONS}
          selected={state.contact_channels}
          onChange={v => onChange('contact_channels', v)}
          columns={2}
        />
      </FormField>

      <FormField label="Consultas diarias recibidas (aprox.)" error={errors.daily_queries}>
        <RadioGroup
          name="daily_queries"
          options={DAILY_QUERIES_OPTIONS}
          value={state.daily_queries}
          onChange={v => onChange('daily_queries', v)}
          columns={2}
        />
      </FormField>

      <FormField label="Descripción del equipo de soporte" htmlFor="support_team_desc">
        <TextInput
          id="support_team_desc"
          value={state.support_team_desc}
          onChange={v => onChange('support_team_desc', v)}
          placeholder="Ej: 2 personas a tiempo completo, horario 9-18h..."
        />
      </FormField>

      <FormField label="Top 3 consultas repetitivas más frecuentes" htmlFor="top_repetitive_queries">
        <TextArea
          id="top_repetitive_queries"
          value={state.top_repetitive_queries}
          onChange={v => onChange('top_repetitive_queries', v)}
          placeholder="Describe las 3 preguntas o solicitudes que se repiten más..."
          rows={4}
          maxLength={500}
        />
      </FormField>

      <FormField label="Tiempo medio de resolución por consulta" error={errors.avg_resolution_time}>
        <RadioGroup
          name="avg_resolution_time"
          options={RESOLUTION_TIME_OPTIONS}
          value={state.avg_resolution_time}
          onChange={v => onChange('avg_resolution_time', v)}
          columns={2}
        />
      </FormField>
    </div>
  )
}
