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

const SECTOR_OPTIONS = [
  { value: 'retail', label: 'Retail / Comercio' },
  { value: 'hosteleria', label: 'Hostelería / Restauración' },
  { value: 'salud', label: 'Salud / Bienestar' },
  { value: 'educacion', label: 'Educación / Formación' },
  { value: 'legal', label: 'Legal / Asesoría' },
  { value: 'construccion', label: 'Construcción / Inmobiliaria' },
  { value: 'tecnologia', label: 'Tecnología / Software' },
  { value: 'logistica', label: 'Logística / Transporte' },
  { value: 'marketing', label: 'Marketing / Comunicación' },
  { value: 'consultoria', label: 'Consultoría / Servicios profesionales' },
  { value: 'manufactura', label: 'Manufactura / Industria' },
  { value: 'finanzas', label: 'Finanzas / Contabilidad' },
  { value: 'otro', label: 'Otro' },
]

const EMPLOYEE_OPTIONS = [
  { value: '1-5', label: '1–5 personas' },
  { value: '6-10', label: '6–10 personas' },
  { value: '11-25', label: '11–25 personas' },
  { value: '26-50', label: '26–50 personas' },
  { value: '51-100', label: '51–100 personas' },
  { value: '100+', label: 'Más de 100' },
]

const REVENUE_OPTIONS = [
  { value: '<100k', label: 'Menos de 100.000€' },
  { value: '100k-500k', label: '100.000€ – 500.000€' },
  { value: '500k-1m', label: '500.000€ – 1.000.000€' },
  { value: '1m-5m', label: '1M€ – 5M€' },
  { value: '5m+', label: 'Más de 5M€' },
  { value: 'no_indica', label: 'Prefiero no indicarlo' },
]

export function Section1Empresa({ state, onChange, errors = {} }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <FormField label="Sector de actividad" htmlFor="sector" required error={errors.sector}>
        <SelectField
          id="sector"
          value={state.sector}
          onChange={v => onChange('sector', v)}
          options={SECTOR_OPTIONS}
          placeholder="Selecciona tu sector..."
        />
      </FormField>

      <FormField label="Número de empleados" required error={errors.employee_range}>
        <RadioGroup
          name="employee_range"
          options={EMPLOYEE_OPTIONS}
          value={state.employee_range}
          onChange={v => onChange('employee_range', v)}
          columns={2}
        />
      </FormField>

      <FormField label="Facturación anual aproximada" htmlFor="revenue_range">
        <SelectField
          id="revenue_range"
          value={state.revenue_range}
          onChange={v => onChange('revenue_range', v)}
          options={REVENUE_OPTIONS}
          placeholder="Selecciona un rango..."
        />
      </FormField>

      <FormField label="Nombre de contacto" htmlFor="contact_name" required error={errors.contact_name}>
        <TextInput
          id="contact_name"
          value={state.contact_name}
          onChange={v => onChange('contact_name', v)}
          placeholder="Tu nombre completo"
        />
      </FormField>

      <FormField label="Cargo / Rol en la empresa" htmlFor="contact_role">
        <TextInput
          id="contact_role"
          value={state.contact_role}
          onChange={v => onChange('contact_role', v)}
          placeholder="Ej: CEO, Director de Operaciones..."
        />
      </FormField>

      <FormField label="¿Quién toma las decisiones tecnológicas?" htmlFor="tech_decision_maker">
        <TextInput
          id="tech_decision_maker"
          value={state.tech_decision_maker}
          onChange={v => onChange('tech_decision_maker', v)}
          placeholder="Nombre o cargo de la persona responsable"
        />
      </FormField>
    </div>
  )
}
