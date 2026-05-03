/**
 * FinanzasTab — finanzas (form_data section 6).
 *
 * 4 canonical form_data keys:
 *   invoicing_method, has_cash_flow_control, cash_flow_desc, admin_hours_per_week
 */

import { useFormContext } from 'react-hook-form'
import { FormDataField } from '../FormDataField'

const INVOICING_METHOD_OPTIONS = [
  { value: 'manual_excel', label: 'Manual / Excel' },
  { value: 'software_facturacion', label: 'Software de facturación' },
  { value: 'erp', label: 'ERP integrado' },
  { value: 'mixto', label: 'Mixto' },
]

const ADMIN_HOURS_OPTIONS = [
  { value: '<5', label: 'Menos de 5 horas/semana' },
  { value: '5-20', label: '5–20 horas/semana' },
  { value: '20-40', label: '20–40 horas/semana' },
  { value: '40+', label: 'Más de 40 horas/semana' },
]

interface Props {
  assessmentId: string
  fieldSources: Record<string, string>
}

export function FinanzasTab({ assessmentId, fieldSources }: Props) {
  const { watch } = useFormContext()
  const formData = (watch('form_data') as Record<string, unknown>) ?? {}
  const hasCashFlow = Boolean(formData['has_cash_flow_control'])

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
      <FormDataField
        name="invoicing_method"
        label="Método de facturación"
        type="select"
        options={INVOICING_METHOD_OPTIONS}
        assessmentId={assessmentId}
        fieldSources={fieldSources}
      />

      <FormDataField
        name="admin_hours_per_week"
        label="Horas de administración por semana"
        type="select"
        options={ADMIN_HOURS_OPTIONS}
        assessmentId={assessmentId}
        fieldSources={fieldSources}
      />

      <FormDataField
        name="has_cash_flow_control"
        label="¿Tiene control de cash flow?"
        type="boolean"
        assessmentId={assessmentId}
        fieldSources={fieldSources}
        placeholder="Sí, controla el cash flow"
      />

      {hasCashFlow && (
        <div className="sm:col-span-2">
          <FormDataField
            name="cash_flow_desc"
            label="Descripción del control de cash flow"
            type="textarea"
            assessmentId={assessmentId}
            fieldSources={fieldSources}
            placeholder="¿Con qué herramientas y con qué frecuencia se hace el seguimiento?"
          />
        </div>
      )}
    </div>
  )
}
