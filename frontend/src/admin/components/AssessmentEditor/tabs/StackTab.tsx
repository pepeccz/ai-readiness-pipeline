/**
 * StackTab — stack tecnológico (form_data section 2).
 *
 * 6 canonical form_data keys:
 *   software_used, ai_tools_used, has_chatbot, chatbot_desc,
 *   has_automations, automations_desc
 */

import { useFormContext } from 'react-hook-form'
import { FormDataField } from '../FormDataField'

interface Props {
  assessmentId: string
  fieldSources: Record<string, string>
}

export function StackTab({ assessmentId, fieldSources }: Props) {
  const { watch } = useFormContext()
  const formData = (watch('form_data') as Record<string, unknown>) ?? {}
  const hasChatbot = Boolean(formData['has_chatbot'])
  const hasAutomations = Boolean(formData['has_automations'])

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
      <div className="sm:col-span-2">
        <FormDataField
          name="software_used"
          label="Software actual"
          type="multiselect-free"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Ej: Notion, Slack, Excel..."
        />
      </div>

      <div className="sm:col-span-2">
        <FormDataField
          name="ai_tools_used"
          label="Herramientas de IA actuales"
          type="multiselect-free"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Ej: ChatGPT, Copilot, Midjourney..."
        />
      </div>

      <FormDataField
        name="has_chatbot"
        label="¿Tiene chatbot?"
        type="boolean"
        assessmentId={assessmentId}
        fieldSources={fieldSources}
        placeholder="Sí, tiene chatbot"
      />

      {hasChatbot && (
        <div className="sm:col-span-2">
          <FormDataField
            name="chatbot_desc"
            label="Descripción del chatbot"
            type="textarea"
            assessmentId={assessmentId}
            fieldSources={fieldSources}
            placeholder="Tecnología, proveedor, canales donde se usa..."
          />
        </div>
      )}

      <FormDataField
        name="has_automations"
        label="¿Tiene automatizaciones?"
        type="boolean"
        assessmentId={assessmentId}
        fieldSources={fieldSources}
        placeholder="Sí, tiene automatizaciones"
      />

      {hasAutomations && (
        <div className="sm:col-span-2">
          <FormDataField
            name="automations_desc"
            label="Descripción de automatizaciones"
            type="textarea"
            assessmentId={assessmentId}
            fieldSources={fieldSources}
            placeholder="Qué procesos están automatizados, con qué herramientas..."
          />
        </div>
      )}
    </div>
  )
}
