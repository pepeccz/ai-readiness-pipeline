/**
 * EmpresaTab — datos de la empresa (section 1).
 *
 * Flat editable fields (via EditorField):
 *   company_name, sector, employee_range, revenue_range,
 *   respondent_name_role, respondent_email, status, auto_publish
 *
 * form_data fields (via FormDataField, 3 keys):
 *   contact_name, contact_role, tech_decision_maker
 */

import { EditorField } from '../EditorField'
import { FormDataField } from '../FormDataField'

const STATUS_OPTIONS = [
  { value: 'draft', label: 'Borrador' },
  { value: 'pending_review', label: 'Pendiente revisión' },
  { value: 'approved', label: 'Aprobado' },
  { value: 'archived', label: 'Archivado' },
]

const SECTOR_OPTIONS = [
  { value: 'retail', label: 'Retail' },
  { value: 'salud', label: 'Salud' },
  { value: 'finanzas', label: 'Finanzas' },
  { value: 'manufactura', label: 'Manufactura' },
  { value: 'educación', label: 'Educación' },
  { value: 'tecnología', label: 'Tecnología' },
  { value: 'logística', label: 'Logística' },
  { value: 'alimentación', label: 'Alimentación' },
  { value: 'construcción', label: 'Construcción' },
  { value: 'otro', label: 'Otro' },
]

const EMPLOYEE_OPTIONS = [
  { value: '1-10', label: '1–10 empleados' },
  { value: '11-50', label: '11–50 empleados' },
  { value: '51-200', label: '51–200 empleados' },
  { value: '201-500', label: '201–500 empleados' },
  { value: '501-1000', label: '501–1.000 empleados' },
  { value: '1000+', label: 'Más de 1.000 empleados' },
]

const REVENUE_OPTIONS = [
  { value: '<1M', label: 'Menos de 1M€' },
  { value: '1M-5M', label: '1M–5M€' },
  { value: '5M-20M', label: '5M–20M€' },
  { value: '20M-100M', label: '20M–100M€' },
  { value: '100M+', label: 'Más de 100M€' },
]

interface Props {
  assessmentId: string
  fieldSources: Record<string, string>
}

export function EmpresaTab({ assessmentId, fieldSources }: Props) {
  return (
    <div>
      {/* Flat fields — sourced from ORM columns */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
        <EditorField
          name="company_name"
          label="Nombre de la empresa"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Ej: Acme S.A."
        />
        <EditorField
          name="sector"
          label="Sector"
          type="select"
          options={SECTOR_OPTIONS}
          assessmentId={assessmentId}
          fieldSources={fieldSources}
        />
        <EditorField
          name="employee_range"
          label="Rango de empleados"
          type="select"
          options={EMPLOYEE_OPTIONS}
          assessmentId={assessmentId}
          fieldSources={fieldSources}
        />
        <EditorField
          name="revenue_range"
          label="Rango de facturación"
          type="select"
          options={REVENUE_OPTIONS}
          assessmentId={assessmentId}
          fieldSources={fieldSources}
        />
        <EditorField
          name="respondent_name_role"
          label="Nombre y cargo del respondente"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Ej: María García, CTO"
        />
        <EditorField
          name="respondent_email"
          label="Email de contacto (cliente)"
          type="email"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="cliente@empresa.com"
        />
        <EditorField
          name="status"
          label="Estado del assessment"
          type="select"
          options={STATUS_OPTIONS}
          assessmentId={assessmentId}
          fieldSources={fieldSources}
        />
        <EditorField
          name="auto_publish"
          label="Auto publicar"
          type="checkbox"
          placeholder="Publicar automáticamente tras enriquecimiento"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
        />
      </div>

      {/* form_data fields — sourced from wizard answers */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Datos del contacto (formulario)</h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
          <FormDataField
            name="contact_name"
            label="Nombre del contacto principal"
            type="text"
            assessmentId={assessmentId}
            fieldSources={fieldSources}
            placeholder="Ej: María García"
          />
          <FormDataField
            name="contact_role"
            label="Rol del contacto"
            type="text"
            assessmentId={assessmentId}
            fieldSources={fieldSources}
            placeholder="Ej: CTO, CEO, Director de Operaciones"
          />
          <div className="sm:col-span-2">
            <FormDataField
              name="tech_decision_maker"
              label="¿Quién decide sobre tecnología?"
              type="text"
              assessmentId={assessmentId}
              fieldSources={fieldSources}
              placeholder="Nombre y cargo de quien toma decisiones tecnológicas"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
