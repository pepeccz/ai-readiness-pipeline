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

const SOFTWARE_OPTIONS = [
  { value: 'google_workspace', label: 'Google Workspace' },
  { value: 'microsoft_365', label: 'Microsoft 365' },
  { value: 'erp', label: 'ERP (SAP, Odoo, etc.)' },
  { value: 'crm', label: 'CRM (HubSpot, Salesforce...)' },
  { value: 'ecommerce', label: 'E-commerce (Shopify, WooCommerce...)' },
  { value: 'contabilidad', label: 'Software de contabilidad' },
  { value: 'citas', label: 'Gestión de citas' },
  { value: 'ninguno', label: 'Ninguno' },
  { value: 'otro', label: 'Otro' },
]

const AI_TOOLS_OPTIONS = [
  { value: 'chatgpt', label: 'ChatGPT' },
  { value: 'copilot', label: 'Microsoft Copilot' },
  { value: 'gemini', label: 'Google Gemini' },
  { value: 'midjourney', label: 'Midjourney' },
  { value: 'claude', label: 'Claude' },
  { value: 'otra', label: 'Otra herramienta IA' },
  { value: 'ninguna', label: 'Ninguna' },
]

const YES_NO_OPTIONS = [
  { value: 'si', label: 'Sí' },
  { value: 'no', label: 'No' },
]

export function Section2Stack({ state, onChange, errors = {} }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <FormField label="Software que utilizáis actualmente" error={errors.software_used}>
        <MultiSelect
          options={SOFTWARE_OPTIONS}
          selected={state.software_used}
          onChange={v => onChange('software_used', v)}
          columns={2}
        />
      </FormField>

      <FormField label="Herramientas de IA que ya usáis" error={errors.ai_tools_used}>
        <MultiSelect
          options={AI_TOOLS_OPTIONS}
          selected={state.ai_tools_used}
          onChange={v => onChange('ai_tools_used', v)}
          columns={2}
        />
      </FormField>

      <FormField label="¿Tenéis algún chatbot implementado?" error={errors.has_chatbot}>
        <RadioGroup
          name="has_chatbot"
          options={YES_NO_OPTIONS}
          value={state.has_chatbot}
          onChange={v => onChange('has_chatbot', v)}
          columns={2}
        />
      </FormField>

      {state.has_chatbot === 'si' && (
        <FormField label="Describe brevemente el chatbot que tenéis" htmlFor="chatbot_desc">
          <TextInput
            id="chatbot_desc"
            value={state.chatbot_desc}
            onChange={v => onChange('chatbot_desc', v)}
            placeholder="Plataforma, propósito, dónde está integrado..."
          />
        </FormField>
      )}

      <FormField label="¿Tenéis automatizaciones de procesos?" error={errors.has_automations}>
        <RadioGroup
          name="has_automations"
          options={YES_NO_OPTIONS}
          value={state.has_automations}
          onChange={v => onChange('has_automations', v)}
          columns={2}
        />
      </FormField>

      {state.has_automations === 'si' && (
        <FormField label="¿Qué automatizaciones tenéis?" htmlFor="automations_desc">
          <TextInput
            id="automations_desc"
            value={state.automations_desc}
            onChange={v => onChange('automations_desc', v)}
            placeholder="Ej: Zapier para sincronizar emails con CRM..."
          />
        </FormField>
      )}
    </div>
  )
}
