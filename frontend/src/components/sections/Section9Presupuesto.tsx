import type { FormState } from '../../types/form'
import { FormField } from '../ui/FormField'
import { RadioGroup } from '../ui/RadioGroup'
import { TextArea } from '../ui/TextArea'
import { TextInput } from '../ui/TextInput'

interface Props {
  state: FormState
  onChange: <K extends keyof FormState>(key: K, value: FormState[K]) => void
  errors?: Record<string, string>
}

const BUDGET_OPTIONS = [
  { value: '<1000', label: 'Menos de 1.000€' },
  { value: '1000-3000', label: '1.000€ – 3.000€' },
  { value: '3000-10000', label: '3.000€ – 10.000€' },
  { value: '10000-30000', label: '10.000€ – 30.000€' },
  { value: '>30000', label: 'Más de 30.000€' },
  { value: 'no_claro', label: 'No lo tengo claro' },
]

const URGENCY_OPTIONS = [
  { value: 'sin_urgencia', label: 'No hay urgencia concreta' },
  { value: 'temporada_alta', label: 'Sí, antes de temporada alta' },
  { value: 'ahora_mismo', label: 'Sí, lo necesitamos ahora mismo' },
]

export function Section9Presupuesto({ state, onChange, errors = {} }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <FormField
        label="¿Qué presupuesto estáis dispuestos a invertir en IA este año?"
        required
        error={errors.investment_budget}
      >
        <RadioGroup
          name="investment_budget"
          options={BUDGET_OPTIONS}
          value={state.investment_budget}
          onChange={v => onChange('investment_budget', v)}
          columns={2}
        />
      </FormField>

      <FormField
        label="¿Hay alguna urgencia para implementar soluciones de IA?"
        required
        error={errors.urgency}
      >
        <RadioGroup
          name="urgency"
          options={URGENCY_OPTIONS}
          value={state.urgency}
          onChange={v => onChange('urgency', v)}
          columns={1}
        />
      </FormField>

      {state.urgency === 'temporada_alta' && (
        <FormField label="¿En qué fecha comienza esa temporada alta?" htmlFor="urgency_date">
          <TextInput
            id="urgency_date"
            type="date"
            value={state.urgency_date}
            onChange={v => onChange('urgency_date', v)}
          />
        </FormField>
      )}

      <FormField label="¿Hay algo más que quieras contarnos?" htmlFor="additional_notes">
        <TextArea
          id="additional_notes"
          value={state.additional_notes}
          onChange={v => onChange('additional_notes', v)}
          placeholder="Cualquier contexto adicional que creas relevante para el análisis..."
          rows={4}
          maxLength={1000}
        />
      </FormField>
    </div>
  )
}
