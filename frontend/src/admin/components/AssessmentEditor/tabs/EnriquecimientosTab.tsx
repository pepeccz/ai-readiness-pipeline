/**
 * EnriquecimientosTab — LLM-enriched text fields with source badges.
 *
 * All fields here map to llm_enriched_data keys.
 * Source badge defaults to [IA] since all llm_* fields default to 'llm'.
 * When the consultant edits one, the PATCH marks it 'human' and badge turns [Editado].
 */

import { EditorField } from '../EditorField'

interface Props {
  assessmentId: string
  fieldSources: Record<string, string>
  hasEnrichments: boolean
}

export function EnriquecimientosTab({ assessmentId, fieldSources, hasEnrichments }: Props) {
  if (!hasEnrichments) {
    return (
      <div className="py-12 text-center">
        <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
          </svg>
        </div>
        <p className="text-gray-500 text-sm">
          Los enriquecimientos LLM no se han generado aún.
          <br />
          Usá el panel de la derecha para ejecutar <strong>Re-correr LLM</strong>.
        </p>
      </div>
    )
  }

  return (
    <div>
      <p className="text-xs text-gray-400 mb-4">
        Campos generados por IA. Los que editaste manualmente muestran la etiqueta{' '}
        <span className="bg-orange-100 text-orange-700 px-1 rounded text-xs">Editado</span>.
        Al re-correr LLM, solo se sobreescriben los campos con etiqueta{' '}
        <span className="bg-blue-100 text-blue-700 px-1 rounded text-xs">IA</span>.
      </p>

      <div className="space-y-2">
        <EditorField
          name="llm_executive_summary"
          label="Resumen ejecutivo"
          type="textarea"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Resumen ejecutivo generado por IA..."
        />
        <EditorField
          name="llm_current_state"
          label="Estado actual"
          type="textarea"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Diagnóstico del estado actual..."
        />
        <EditorField
          name="llm_opportunities"
          label="Oportunidades identificadas"
          type="textarea"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Principales oportunidades de IA..."
        />
        <EditorField
          name="llm_final_recommendation"
          label="Recomendación final"
          type="textarea"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Recomendación principal..."
        />
        <EditorField
          name="llm_final_narrative"
          label="Narrativa final"
          type="textarea"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Narrativa del cierre del reporte..."
        />
        <EditorField
          name="llm_next_step_proposal"
          label="Propuesta de próximos pasos"
          type="textarea"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Plan de acción inmediato..."
        />
        <EditorField
          name="llm_risk_findings"
          label="Hallazgos de riesgo"
          type="textarea"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Riesgos identificados en el análisis..."
        />
        <EditorField
          name="llm_roadmap_30_60_90"
          label="Roadmap 30–60–90 días"
          type="textarea"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Plan de implementación a 30, 60 y 90 días..."
        />
        <EditorField
          name="llm_tools_list"
          label="Lista de herramientas recomendadas"
          type="textarea"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Herramientas de IA recomendadas..."
        />
        <EditorField
          name="llm_ai_policy_draft"
          label="Borrador de política de IA"
          type="textarea"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Política de uso de IA sugerida..."
        />
        <EditorField
          name="llm_dpa_guidance"
          label="Guía DPA"
          type="textarea"
          assessmentId={assessmentId}
          fieldSources={fieldSources}
          placeholder="Guía de Data Processing Agreements..."
        />
      </div>
    </div>
  )
}
