import type { FormState } from '../../types/form'
import { FormField } from '../ui/FormField'
import { MultiSelect } from '../ui/MultiSelect'
import { RadioGroup } from '../ui/RadioGroup'
import { TextInput } from '../ui/TextInput'

interface Props {
  state: FormState
  onChange: <K extends keyof FormState>(key: K, value: FormState[K]) => void
  errors?: Record<string, string>
}

const CONTENT_GENERATION_OPTIONS = [
  { value: 'equipo_interno', label: 'Equipo interno' },
  { value: 'agencia', label: 'Agencia' },
  { value: 'freelance', label: 'Freelance' },
  { value: 'duenio', label: 'El dueño/a' },
  { value: 'no_generamos', label: 'No generamos contenido' },
]

const LEAD_ACQUISITION_OPTIONS = [
  { value: 'web_seo', label: 'Web / SEO' },
  { value: 'redes_sociales', label: 'Redes sociales' },
  { value: 'boca_a_boca', label: 'Boca a boca' },
  { value: 'publicidad', label: 'Publicidad (Google Ads, Meta...)' },
  { value: 'ferias_eventos', label: 'Ferias / Eventos' },
  { value: 'comerciales', label: 'Equipo comercial' },
  { value: 'otros', label: 'Otros' },
]

const YES_NO_OPTIONS = [
  { value: 'si', label: 'Sí' },
  { value: 'no', label: 'No' },
]

const MARKETING_BUDGET_OPTIONS = [
  { value: '<500', label: 'Menos de 500€/mes' },
  { value: '500-2000', label: '500€ – 2.000€/mes' },
  { value: '2000-5000', label: '2.000€ – 5.000€/mes' },
  { value: '>5000', label: 'Más de 5.000€/mes' },
  { value: 'no_invertimos', label: 'No invertimos en marketing' },
]

export function Section4Marketing({ state, onChange, errors = {} }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <FormField label="¿Quién genera el contenido de marketing?" error={errors.content_generation}>
        <MultiSelect
          options={CONTENT_GENERATION_OPTIONS}
          selected={state.content_generation}
          onChange={v => onChange('content_generation', v)}
          columns={2}
        />
      </FormField>

      <FormField label="¿Cómo conseguís nuevos clientes / leads?" error={errors.lead_acquisition}>
        <MultiSelect
          options={LEAD_ACQUISITION_OPTIONS}
          selected={state.lead_acquisition}
          onChange={v => onChange('lead_acquisition', v)}
          columns={2}
        />
      </FormField>

      <FormField label="¿Hacéis seguimiento estructurado de leads?" error={errors.lead_tracking}>
        <RadioGroup
          name="lead_tracking"
          options={YES_NO_OPTIONS}
          value={state.lead_tracking}
          onChange={v => onChange('lead_tracking', v)}
          columns={2}
        />
      </FormField>

      {state.lead_tracking === 'si' && (
        <FormField label="¿Cómo gestionáis el seguimiento de leads?" htmlFor="lead_tracking_desc">
          <TextInput
            id="lead_tracking_desc"
            value={state.lead_tracking_desc}
            onChange={v => onChange('lead_tracking_desc', v)}
            placeholder="Ej: CRM, hoja de Excel, Notion..."
          />
        </FormField>
      )}

      <FormField label="Presupuesto mensual en marketing / publicidad" error={errors.marketing_budget}>
        <RadioGroup
          name="marketing_budget"
          options={MARKETING_BUDGET_OPTIONS}
          value={state.marketing_budget}
          onChange={v => onChange('marketing_budget', v)}
          columns={2}
        />
      </FormField>
    </div>
  )
}
