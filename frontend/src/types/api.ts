/**
 * Response from POST /api/assessment (Phase C — fire-and-forget flow).
 * The assessment is processed in the background; the report is delivered
 * by email when the consultant approves it. No polling needed.
 */
export interface SubmissionResponse {
  assessment_id: string
  status: 'pending_review'
  message: string
}

export interface AssessmentFormPayload {
  // Section 1
  company_name: string
  sector: string
  employee_range: string
  revenue_range: string
  contact_name: string
  contact_role: string
  tech_decision_maker: string

  // Section 2
  software_used: string[]
  ai_tools_used: string[]
  has_chatbot: boolean
  chatbot_desc?: string
  has_automations: boolean
  automations_desc?: string

  // Section 3
  contact_channels: string[]
  daily_queries: string
  support_team_desc: string
  top_repetitive_queries: string
  avg_resolution_time: string

  // Section 4
  content_generation: string[]
  lead_acquisition: string[]
  has_lead_tracking: boolean
  lead_tracking_desc?: string
  monthly_marketing_budget: string

  // Section 5
  most_time_consuming_process: string
  process_people_count: string
  process_hours_per_week: string
  data_entry_channels: string[]
  process_pain_points: string[]

  // Section 6
  invoicing_method: string
  has_cash_flow_control: boolean
  cash_flow_desc?: string
  admin_hours_per_week: string

  // Section 7
  is_hiring: boolean
  hiring_desc?: string
  hr_management_method: string
  hr_hours_per_week: string

  // Section 8
  collects_personal_data: boolean
  personal_data_types?: string
  knows_ai_gdpr: string
  has_dpa: string
  dpa_with_whom?: string
  knows_ai_act: string
  has_ai_policy: string

  // Section 9
  investment_budget: string
  urgency: string
  urgency_date?: string
  additional_notes?: string

  // Auth (not sent in body, used for header)
  _token?: string
}

// ── Session 1 Synthesis types (pdf-export-and-editor) ──────────────────────

export type ImpactLevel = 'alto' | 'medio' | 'bajo'
export type EffortLevel = 'alto' | 'medio' | 'bajo'
export type RelatedServiceKey =
  | 'diagnostico_profundo'
  | 'desarrollo_acompanamiento'
  | 'formacion_personalizada'
  | 'otro'

export interface RecommendationItem {
  text: string
  impact: ImpactLevel | null
  effort: EffortLevel | null
  related_service: RelatedServiceKey | null
  custom_service_label?: string | null
}

export interface RoadmapBuckets {
  d30: string[]
  d60: string[]
  d90: string[]
}

export interface Session1Synthesis {
  summary?: string
  key_insights?: string[]
  recommendations?: RecommendationItem[]
  roadmap?: RoadmapBuckets
  next_steps?: string[]
  /** Internal field — visible to admin only, never rendered in PDF */
  hypothesis?: string
  generated_at?: string
  model?: string
  // Export tracking columns (from lead detail API response)
  synthesis_edited_at?: string | null
  synthesis_last_exported_at?: string | null
  synthesis_export_count?: number
}

// ── Catalog types ──────────────────────────────────────────────────────────

export interface ServiceCatalogEntry {
  key: RelatedServiceKey
  nombre: string
  descripcion: string
  cuando_recomendar: string[]
  nota_priorizacion: string | null
}

export interface CatalogResponse {
  services: ServiceCatalogEntry[]
}
