export interface FormState {
  // Section 1 — Empresa
  sector: string
  employee_range: string
  revenue_range: string
  contact_name: string
  contact_role: string
  tech_decision_maker: string

  // Section 2 — Stack tecnológico
  software_used: string[]
  ai_tools_used: string[]
  has_chatbot: string
  chatbot_desc: string
  has_automations: string
  automations_desc: string

  // Section 3 — Atención al cliente
  contact_channels: string[]
  daily_queries: string
  support_team_desc: string
  top_repetitive_queries: string
  avg_resolution_time: string

  // Section 4 — Marketing
  content_generation: string[]
  lead_acquisition: string[]
  lead_tracking: string
  lead_tracking_desc: string
  marketing_budget: string

  // Section 5 — Operaciones
  most_time_consuming_process: string
  process_people_count: string
  hours_per_week: string
  data_entry_channels: string[]
  process_pain_points: string[]

  // Section 6 — Gestión y finanzas
  invoicing_method: string
  cash_flow_control: string
  cash_flow_desc: string
  admin_hours_per_week: string

  // Section 7 — RRHH
  is_hiring: string
  hiring_desc: string
  hr_management: string
  hr_hours_per_week: string

  // Section 8 — Compliance
  collects_personal_data: string
  data_types: string
  knows_ai_gdpr: string
  has_dpa: string
  dpa_with_whom: string
  knows_ai_act: string
  has_ai_policy: string

  // Section 9 — Presupuesto
  investment_budget: string
  urgency: string
  urgency_date: string
  additional_notes: string
}
