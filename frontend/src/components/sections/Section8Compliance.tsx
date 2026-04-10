import type { FormState } from '../../types/form'
import { FormField } from '../ui/FormField'
import { RadioGroup } from '../ui/RadioGroup'
import { TextInput } from '../ui/TextInput'
import { TextArea } from '../ui/TextArea'

interface Props {
  state: FormState
  onChange: <K extends keyof FormState>(key: K, value: FormState[K]) => void
  errors?: Record<string, string>
}

const YES_NO_OPTIONS = [
  { value: 'si', label: 'Sí' },
  { value: 'no', label: 'No' },
]

const KNOWLEDGE_OPTIONS = [
  { value: 'si', label: 'Sí' },
  { value: 'no', label: 'No' },
  { value: 'no_seguro', label: 'No estoy seguro/a' },
]

const DPA_OPTIONS = [
  { value: 'si', label: 'Sí' },
  { value: 'no', label: 'No' },
  { value: 'no_se', label: 'No sé qué es' },
]

const AI_POLICY_OPTIONS = [
  { value: 'si', label: 'Sí, tenemos política' },
  { value: 'no', label: 'No tenemos' },
  { value: 'en_proceso', label: 'En proceso de elaborarla' },
]

export function Section8Compliance({ state, onChange, errors = {} }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <FormField label="¿Recogéis datos personales de clientes o empleados?" error={errors.collects_personal_data}>
        <RadioGroup
          name="collects_personal_data"
          options={YES_NO_OPTIONS}
          value={state.collects_personal_data}
          onChange={v => onChange('collects_personal_data', v)}
          columns={2}
        />
      </FormField>

      {state.collects_personal_data === 'si' && (
        <FormField label="¿Qué tipo de datos recogéis?" htmlFor="data_types">
          <TextInput
            id="data_types"
            value={state.data_types}
            onChange={v => onChange('data_types', v)}
            placeholder="Ej: nombre, email, teléfono, datos de salud..."
          />
        </FormField>
      )}

      <FormField
        label="¿Conocéis las implicaciones del RGPD respecto al uso de IA?"
        error={errors.knows_ai_gdpr}
      >
        <RadioGroup
          name="knows_ai_gdpr"
          options={KNOWLEDGE_OPTIONS}
          value={state.knows_ai_gdpr}
          onChange={v => onChange('knows_ai_gdpr', v)}
          columns={3}
        />
      </FormField>

      <FormField
        label="¿Tenéis acuerdo de tratamiento de datos (DPA) con vuestros proveedores tecnológicos?"
        error={errors.has_dpa}
      >
        <RadioGroup
          name="has_dpa"
          options={DPA_OPTIONS}
          value={state.has_dpa}
          onChange={v => onChange('has_dpa', v)}
          columns={3}
        />
      </FormField>

      {state.has_dpa === 'si' && (
        <FormField label="¿Con qué proveedores tenéis DPA firmado?" htmlFor="dpa_with_whom">
          <TextInput
            id="dpa_with_whom"
            value={state.dpa_with_whom}
            onChange={v => onChange('dpa_with_whom', v)}
            placeholder="Ej: Google, HubSpot, proveedor de email marketing..."
          />
        </FormField>
      )}

      <FormField
        label="¿Conocéis el AI Act europeo y sus obligaciones para empresas?"
        error={errors.knows_ai_act}
      >
        <RadioGroup
          name="knows_ai_act"
          options={KNOWLEDGE_OPTIONS}
          value={state.knows_ai_act}
          onChange={v => onChange('knows_ai_act', v)}
          columns={3}
        />
      </FormField>

      <FormField
        label="¿Tenéis o estáis desarrollando una política de uso de IA en la empresa?"
        error={errors.has_ai_policy}
      >
        <RadioGroup
          name="has_ai_policy"
          options={AI_POLICY_OPTIONS}
          value={state.has_ai_policy}
          onChange={v => onChange('has_ai_policy', v)}
          columns={3}
        />
      </FormField>

      <FormField label="¿Algo más que quieras contarnos sobre esta área? (opcional)">
        <TextArea
          value={state.compliance_context}
          onChange={v => onChange('compliance_context', v)}
          placeholder="Cualquier detalle adicional que nos ayude a entender mejor tu situación..."
          rows={3}
        />
      </FormField>
    </div>
  )
}
