/**
 * PresupuestoTab — presupuesto y prioridad (form_data section 9).
 *
 * Flat editable (admin overrides): budget, priority_text  → via EditorField
 * form_data canonical keys (3): investment_budget, urgency, additional_notes
 *
 * R5 sync: editing investment_budget (form_data) → backend syncs flat budget.
 * Editing urgency (form_data) → backend syncs flat priority_text.
 * Both columns shown here so the consultant sees both; flat fields are for
 * direct admin override when needed.
 */

import { EditorField } from '../EditorField'
import { FormDataField } from '../FormDataField'

const INVESTMENT_BUDGET_OPTIONS = [
  { value: '<5k', label: 'Menos de 5.000€' },
  { value: '5k-15k', label: '5.000–15.000€' },
  { value: '15k-50k', label: '15.000–50.000€' },
  { value: '50k-150k', label: '50.000–150.000€' },
  { value: '150k+', label: 'Más de 150.000€' },
  { value: 'no_definido', label: 'No definido aún' },
]

const URGENCY_OPTIONS = [
  { value: 'inmediata', label: 'Inmediata (ya)' },
  { value: 'corto_plazo_3m', label: 'Corto plazo (3 meses)' },
  { value: 'medio_plazo_6m', label: 'Medio plazo (6 meses)' },
  { value: 'largo_plazo_12m', label: 'Largo plazo (12 meses)' },
  { value: 'exploratorio', label: 'Exploratorio / Sin prisa' },
]

const BUDGET_OPTIONS = [
  { value: '<10k', label: 'Menos de 10.000€' },
  { value: '10k-50k', label: '10.000–50.000€' },
  { value: '50k-200k', label: '50.000–200.000€' },
  { value: '200k-1M', label: '200.000€–1M€' },
  { value: '1M+', label: 'Más de 1M€' },
  { value: 'sin_definir', label: 'Sin definir aún' },
]

interface Props {
  assessmentId: string
  fieldSources: Record<string, string>
}

export function PresupuestoTab({ assessmentId, fieldSources }: Props) {
  return (
    <div>
      {/* form_data wizard fields — canonical source */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Datos del formulario (wizard)</h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
          <FormDataField
            name="investment_budget"
            label="Presupuesto de inversión en IA (formulario)"
            type="select"
            options={INVESTMENT_BUDGET_OPTIONS}
            assessmentId={assessmentId}
            fieldSources={fieldSources}
          />
          <FormDataField
            name="urgency"
            label="Urgencia declarada (formulario)"
            type="select"
            options={URGENCY_OPTIONS}
            assessmentId={assessmentId}
            fieldSources={fieldSources}
          />
          <div className="sm:col-span-2">
            <FormDataField
              name="additional_notes"
              label="¿Algo más que quieras contarnos?"
              type="textarea"
              assessmentId={assessmentId}
              fieldSources={fieldSources}
              placeholder="Notas adicionales del cliente..."
            />
          </div>
        </div>
      </div>

      {/* Flat columns — admin override. Synced FROM form_data by backend (R5). */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-700 mb-1">Override de admin</h4>
        <p className="text-xs text-gray-400 mb-3">
          Estos campos se sincronizan automáticamente desde el formulario. Podés editarlos
          directamente aquí para hacer un override puntual (no afecta los datos del wizard).
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
          <EditorField
            name="budget"
            label="Presupuesto (override admin)"
            type="select"
            options={BUDGET_OPTIONS}
            assessmentId={assessmentId}
            fieldSources={fieldSources}
          />
          <EditorField
            name="priority_text"
            label="Urgencia / prioridad (override admin)"
            type="textarea"
            assessmentId={assessmentId}
            fieldSources={fieldSources}
            placeholder="Descripción de la urgencia del cliente..."
          />
        </div>
      </div>
    </div>
  )
}
