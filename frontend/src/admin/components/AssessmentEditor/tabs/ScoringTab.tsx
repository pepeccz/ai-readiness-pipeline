/**
 * ScoringTab — maturity score, risk score, priority, and all 12 sub-scores.
 *
 * All fields are editable (consultant can manually correct scores).
 * Source badge shows [Editado] once a score is manually overridden.
 */

import { EditorField } from '../EditorField'

const MATURITY_LEVEL_OPTIONS = [
  { value: 'inicial', label: 'Inicial (0–25)' },
  { value: 'exploratorio', label: 'Exploratorio (26–50)' },
  { value: 'en_desarrollo', label: 'En desarrollo (51–70)' },
  { value: 'avanzado', label: 'Avanzado (71–85)' },
  { value: 'lider', label: 'Líder (86–100)' },
]

const RISK_LEVEL_OPTIONS = [
  { value: 'bajo', label: 'Bajo' },
  { value: 'medio', label: 'Medio' },
  { value: 'alto', label: 'Alto' },
  { value: 'critico', label: 'Crítico' },
]

interface Props {
  assessmentId: string
  fieldSources: Record<string, string>
}

export function ScoringTab({ assessmentId, fieldSources }: Props) {
  return (
    <div>
      <p className="text-xs text-gray-400 mb-4">
        Scores calculados por el motor de scoring. Podés corregirlos manualmente — se marcarán como{' '}
        <span className="bg-orange-100 text-orange-700 px-1 rounded text-xs">Editado</span>.
      </p>

      {/* Main scores */}
      <div className="mb-8">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Scores principales</h4>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6">
          <EditorField
            name="maturity_score"
            label="Score de madurez (0–100)"
            type="number"
            assessmentId={assessmentId}
            fieldSources={fieldSources}
            placeholder="0–100"
          />
          <EditorField
            name="maturity_level"
            label="Nivel de madurez"
            type="select"
            options={MATURITY_LEVEL_OPTIONS}
            assessmentId={assessmentId}
            fieldSources={fieldSources}
          />
          <EditorField
            name="risk_score"
            label="Score de riesgo (0–100)"
            type="number"
            assessmentId={assessmentId}
            fieldSources={fieldSources}
            placeholder="0–100"
          />
          <EditorField
            name="risk_level"
            label="Nivel de riesgo"
            type="select"
            options={RISK_LEVEL_OPTIONS}
            assessmentId={assessmentId}
            fieldSources={fieldSources}
          />
          <EditorField
            name="priority_score"
            label="Score de prioridad (0–100)"
            type="number"
            assessmentId={assessmentId}
            fieldSources={fieldSources}
            placeholder="0–100"
          />
          <EditorField
            name="priority_level"
            label="Nivel de prioridad"
            assessmentId={assessmentId}
            fieldSources={fieldSources}
            placeholder="Ej: alta"
          />
        </div>
      </div>

      {/* Sub-scores (12 pts_* fields) */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Sub-scores</h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-4">
          <EditorField name="pts_tools" label="Herramientas" type="number" assessmentId={assessmentId} fieldSources={fieldSources} />
          <EditorField name="pts_automation" label="Automatización" type="number" assessmentId={assessmentId} fieldSources={fieldSources} />
          <EditorField name="pts_area_usage" label="Uso por área" type="number" assessmentId={assessmentId} fieldSources={fieldSources} />
          <EditorField name="pts_governance" label="Gobernanza" type="number" assessmentId={assessmentId} fieldSources={fieldSources} />
          <EditorField name="pts_goal_clarity" label="Claridad de objetivos" type="number" assessmentId={assessmentId} fieldSources={fieldSources} />
          <EditorField name="pts_data_risk" label="Riesgo de datos" type="number" assessmentId={assessmentId} fieldSources={fieldSources} />
          <EditorField name="pts_ai_personal_data" label="IA + datos personales" type="number" assessmentId={assessmentId} fieldSources={fieldSources} />
          <EditorField name="pts_dpa" label="DPA" type="number" assessmentId={assessmentId} fieldSources={fieldSources} />
          <EditorField name="pts_dpia" label="DPIA" type="number" assessmentId={assessmentId} fieldSources={fieldSources} />
          <EditorField name="pts_automated_decisions" label="Decisiones automatizadas" type="number" assessmentId={assessmentId} fieldSources={fieldSources} />
          <EditorField name="pts_sector" label="Sector" type="number" assessmentId={assessmentId} fieldSources={fieldSources} />
          <EditorField name="pts_incident" label="Incidentes" type="number" assessmentId={assessmentId} fieldSources={fieldSources} />
        </div>
      </div>
    </div>
  )
}
