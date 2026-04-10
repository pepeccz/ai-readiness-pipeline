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

const INVOICING_OPTIONS = [
  { value: 'software', label: 'Software específico de facturación' },
  { value: 'excel', label: 'Excel / hojas de cálculo' },
  { value: 'gestoria', label: 'Gestoría externa' },
  { value: 'manual', label: 'Manual / papel' },
]

const YES_NO_OPTIONS = [
  { value: 'si', label: 'Sí' },
  { value: 'no', label: 'No' },
]

const HOURS_PER_WEEK_OPTIONS = [
  { value: '<2h', label: 'Menos de 2 h' },
  { value: '2-5h', label: '2–5 h' },
  { value: '5-10h', label: '5–10 h' },
  { value: '>10h', label: 'Más de 10 h' },
]

export function Section6GestionFinanzas({ state, onChange, errors = {} }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <FormField label="¿Cómo gestionáis la facturación?" htmlFor="invoicing_method" error={errors.invoicing_method}>
        <SelectField
          id="invoicing_method"
          value={state.invoicing_method}
          onChange={v => onChange('invoicing_method', v)}
          options={INVOICING_OPTIONS}
          placeholder="Selecciona una opción..."
        />
      </FormField>

      <FormField label="¿Tenéis control de flujo de caja actualizado?" error={errors.cash_flow_control}>
        <RadioGroup
          name="cash_flow_control"
          options={YES_NO_OPTIONS}
          value={state.cash_flow_control}
          onChange={v => onChange('cash_flow_control', v)}
          columns={2}
        />
      </FormField>

      {state.cash_flow_control === 'si' && (
        <FormField label="¿Cómo lo gestionáis?" htmlFor="cash_flow_desc">
          <TextInput
            id="cash_flow_desc"
            value={state.cash_flow_desc}
            onChange={v => onChange('cash_flow_desc', v)}
            placeholder="Ej: Hoja de cálculo, software contable, gestoría..."
          />
        </FormField>
      )}

      <FormField label="Horas semanales dedicadas a gestión administrativa" error={errors.admin_hours_per_week}>
        <RadioGroup
          name="admin_hours_per_week"
          options={HOURS_PER_WEEK_OPTIONS}
          value={state.admin_hours_per_week}
          onChange={v => onChange('admin_hours_per_week', v)}
          columns={2}
        />
      </FormField>
    </div>
  )
}
