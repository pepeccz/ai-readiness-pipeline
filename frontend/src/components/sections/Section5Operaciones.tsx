import type { FormState } from '../../types/form'
import { FormField } from '../ui/FormField'
import { MultiSelect } from '../ui/MultiSelect'
import { RadioGroup } from '../ui/RadioGroup'
import { TextArea } from '../ui/TextArea'

interface Props {
  state: FormState
  onChange: <K extends keyof FormState>(key: K, value: FormState[K]) => void
  errors?: Record<string, string>
}

const PEOPLE_COUNT_OPTIONS = [
  { value: 'solo_yo', label: 'Solo yo' },
  { value: '2-3', label: '2–3 personas' },
  { value: '4-6', label: '4–6 personas' },
  { value: 'mas_de_6', label: 'Más de 6' },
]

const HOURS_PER_WEEK_OPTIONS = [
  { value: '<2h', label: 'Menos de 2 h' },
  { value: '2-5h', label: '2–5 h' },
  { value: '5-10h', label: '5–10 h' },
  { value: '>10h', label: 'Más de 10 h' },
]

const DATA_ENTRY_OPTIONS = [
  { value: 'email', label: 'Email' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'formulario_web', label: 'Formulario web' },
  { value: 'papel', label: 'Papel / físico' },
  { value: 'sistema_erp', label: 'Sistema / ERP' },
  { value: 'excel', label: 'Excel' },
  { value: 'verbal', label: 'Verbal / telefónico' },
]

const PAIN_POINTS_OPTIONS = [
  { value: 'clasificar_info', label: 'Clasificar información manualmente' },
  { value: 'buscar_info', label: 'Buscar info en distintos sitios' },
  { value: 'responder_repetitivas', label: 'Responder preguntas repetitivas' },
  { value: 'pasar_datos', label: 'Pasar datos entre sistemas' },
  { value: 'revisar_errores', label: 'Revisar / corregir errores' },
  { value: 'esperas', label: 'Esperas / cuellos de botella' },
  { value: 'generar_docs', label: 'Generar documentos manualmente' },
  { value: 'otro', label: 'Otro' },
]

export function Section5Operaciones({ state, onChange, errors = {} }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <FormField
        label="¿Cuál es el proceso que más tiempo os consume?"
        htmlFor="most_time_consuming_process"
        required
        error={errors.most_time_consuming_process}
      >
        <TextArea
          id="most_time_consuming_process"
          value={state.most_time_consuming_process}
          onChange={v => onChange('most_time_consuming_process', v)}
          placeholder="Describe el proceso paso a paso: quién lo hace, cuándo, qué herramientas usa..."
          rows={5}
          maxLength={800}
        />
      </FormField>

      <FormField label="¿Cuántas personas participan en ese proceso?" error={errors.process_people_count}>
        <RadioGroup
          name="process_people_count"
          options={PEOPLE_COUNT_OPTIONS}
          value={state.process_people_count}
          onChange={v => onChange('process_people_count', v)}
          columns={2}
        />
      </FormField>

      <FormField label="¿Cuántas horas semanales consume ese proceso?" error={errors.hours_per_week}>
        <RadioGroup
          name="hours_per_week"
          options={HOURS_PER_WEEK_OPTIONS}
          value={state.hours_per_week}
          onChange={v => onChange('hours_per_week', v)}
          columns={2}
        />
      </FormField>

      <FormField label="¿Cómo os llega la información que procesáis?" error={errors.data_entry_channels}>
        <MultiSelect
          options={DATA_ENTRY_OPTIONS}
          selected={state.data_entry_channels}
          onChange={v => onChange('data_entry_channels', v)}
          columns={2}
        />
      </FormField>

      <FormField label="Principales problemas en vuestros procesos" error={errors.process_pain_points}>
        <MultiSelect
          options={PAIN_POINTS_OPTIONS}
          selected={state.process_pain_points}
          onChange={v => onChange('process_pain_points', v)}
          columns={2}
        />
      </FormField>
    </div>
  )
}
