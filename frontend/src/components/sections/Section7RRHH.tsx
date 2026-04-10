import type { FormState } from '../../types/form'
import { FormField } from '../ui/FormField'
import { SelectField } from '../ui/SelectField'
import { RadioGroup } from '../ui/RadioGroup'
import { TextInput } from '../ui/TextInput'

interface Props {
  state: FormState
  onChange: <K extends keyof FormState>(key: K, value: FormState[K]) => void
  errors?: Record<string, string>
}

const YES_NO_OPTIONS = [
  { value: 'si', label: 'Sí' },
  { value: 'no', label: 'No' },
]

const HR_MANAGEMENT_OPTIONS = [
  { value: 'software_rrhh', label: 'Software de RRHH' },
  { value: 'excel', label: 'Excel' },
  { value: 'gestoria', label: 'Gestoría' },
  { value: 'manual', label: 'Manual' },
]

const HOURS_PER_WEEK_OPTIONS = [
  { value: '<2h', label: 'Menos de 2 h' },
  { value: '2-5h', label: '2–5 h' },
  { value: '5-10h', label: '5–10 h' },
  { value: '>10h', label: 'Más de 10 h' },
]

export function Section7RRHH({ state, onChange, errors = {} }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <FormField label="¿Estáis en proceso de selección actualmente?" error={errors.is_hiring}>
        <RadioGroup
          name="is_hiring"
          options={YES_NO_OPTIONS}
          value={state.is_hiring}
          onChange={v => onChange('is_hiring', v)}
          columns={2}
        />
      </FormField>

      {state.is_hiring === 'si' && (
        <FormField label="¿Qué perfiles estáis buscando?" htmlFor="hiring_desc">
          <TextInput
            id="hiring_desc"
            value={state.hiring_desc}
            onChange={v => onChange('hiring_desc', v)}
            placeholder="Ej: 2 comerciales, 1 técnico de soporte..."
          />
        </FormField>
      )}

      <FormField label="¿Cómo gestionáis los RRHH (nóminas, vacaciones, ausencias)?" htmlFor="hr_management" error={errors.hr_management}>
        <SelectField
          id="hr_management"
          value={state.hr_management}
          onChange={v => onChange('hr_management', v)}
          options={HR_MANAGEMENT_OPTIONS}
          placeholder="Selecciona una opción..."
        />
      </FormField>

      <FormField label="Horas semanales dedicadas a gestión de RRHH" error={errors.hr_hours_per_week}>
        <RadioGroup
          name="hr_hours_per_week"
          options={HOURS_PER_WEEK_OPTIONS}
          value={state.hr_hours_per_week}
          onChange={v => onChange('hr_hours_per_week', v)}
          columns={2}
        />
      </FormField>
    </div>
  )
}
