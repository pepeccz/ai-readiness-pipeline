/**
 * MarketingTab — marketing y ventas (form_data section 4).
 *
 * 5 canonical form_data keys:
 *   content_generation, lead_acquisition, has_lead_tracking,
 *   lead_tracking_desc, monthly_marketing_budget
 */

import { useFormContext } from 'react-hook-form'
import { FormDataField } from '../FormDataField'

const CONTENT_GENERATION_OPTIONS = [
  { value: 'blog', label: 'Blog' },
  { value: 'redes_sociales', label: 'Redes sociales' },
  { value: 'email_marketing', label: 'Email marketing' },
  { value: 'video', label: 'Video' },
  { value: 'podcast', label: 'Podcast' },
  { value: 'otro', label: 'Otro' },
]

const LEAD_ACQUISITION_OPTIONS = [
  { value: 'seo', label: 'SEO' },
  { value: 'sem', label: 'SEM / Ads' },
  { value: 'redes_pagadas', label: 'Redes sociales pagadas' },
  { value: 'email', label: 'Email marketing' },
  { value: 'eventos', label: 'Eventos' },
  { value: 'referrals', label: 'Referrals / Boca a boca' },
  { value: 'outbound', label: 'Outbound / Prospección' },
  { value: 'otro', label: 'Otro' },
]

const MARKETING_BUDGET_OPTIONS = [
  { value: '<1k', label: 'Menos de 1.000€/mes' },
  { value: '1k-5k', label: '1.000–5.000€/mes' },
  { value: '5k-20k', label: '5.000–20.000€/mes' },
  { value: '20k-100k', label: '20.000–100.000€/mes' },
  { value: '100k+', label: 'Más de 100.000€/mes' },
]

interface Props {
  assessmentId: string
  fieldSources: Record<string, string>
}

export function MarketingTab({ assessmentId, fieldSources }: Props) {
  const { watch } = useFormContext()
  const formData = (watch('form_data') as Record<string, unknown>) ?? {}
  const hasLeadTracking = Boolean(formData['has_lead_tracking'])

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
      <div className="sm:col-span-2">
        <FormDataField
          name="content_generation"
          label="Generación de contenido"
          type="multiselect-options"
          options={CONTENT_GENERATION_OPTIONS}
          assessmentId={assessmentId}
          fieldSources={fieldSources}
        />
      </div>

      <div className="sm:col-span-2">
        <FormDataField
          name="lead_acquisition"
          label="Adquisición de leads"
          type="multiselect-options"
          options={LEAD_ACQUISITION_OPTIONS}
          assessmentId={assessmentId}
          fieldSources={fieldSources}
        />
      </div>

      <FormDataField
        name="has_lead_tracking"
        label="¿Trackea leads?"
        type="boolean"
        assessmentId={assessmentId}
        fieldSources={fieldSources}
        placeholder="Sí, hace seguimiento de leads"
      />

      <FormDataField
        name="monthly_marketing_budget"
        label="Presupuesto marketing mensual"
        type="select"
        options={MARKETING_BUDGET_OPTIONS}
        assessmentId={assessmentId}
        fieldSources={fieldSources}
      />

      {hasLeadTracking && (
        <div className="sm:col-span-2">
          <FormDataField
            name="lead_tracking_desc"
            label="Cómo trackea leads"
            type="textarea"
            assessmentId={assessmentId}
            fieldSources={fieldSources}
            placeholder="CRM, hojas de cálculo, herramientas específicas..."
          />
        </div>
      )}
    </div>
  )
}
