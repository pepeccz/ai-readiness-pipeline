export interface FormState {
  // Section 1 — Empresa
  company_name: string
  sector: string
  sector_other: string
  employee_range: string
  revenue_range: string
  contact_name: string
  contact_role: string
  tech_decision_maker: string

  // Section 2 — Stack tecnológico
  software_used: string[]
  software_other: string
  ai_tools_used: string[]
  ai_tools_other: string
  has_chatbot: string
  chatbot_desc: string
  has_automations: string
  automations_desc: string
  stack_context: string // contexto libre sobre situación tecnológica

  // Section 3 — Atención al cliente
  contact_channels: string[]
  contact_channels_other: string
  daily_queries: string
  support_team_desc: string
  top_repetitive_queries: string
  avg_resolution_time: string
  customer_service_context: string

  // Section 4 — Marketing
  content_generation: string[]
  content_generation_other: string
  lead_acquisition: string[]
  lead_acquisition_other: string
  lead_tracking: string
  lead_tracking_desc: string
  marketing_budget: string
  marketing_context: string

  // Section 5 — Operaciones
  most_time_consuming_process: string
  process_people_count: string
  hours_per_week: string
  data_entry_channels: string[]
  data_entry_other: string
  process_pain_points: string[]
  process_pain_other: string
  operations_context: string

  // Section 6 — Gestión y finanzas
  invoicing_method: string
  cash_flow_control: string
  cash_flow_desc: string
  admin_hours_per_week: string
  finance_context: string

  // Section 7 — RRHH
  is_hiring: string
  hiring_desc: string
  hr_management: string
  hr_hours_per_week: string
  hr_context: string

  // Section 8 — Compliance
  collects_personal_data: string
  data_types: string
  knows_ai_gdpr: string
  has_dpa: string
  dpa_with_whom: string
  knows_ai_act: string
  has_ai_policy: string
  compliance_context: string

  // Section 9 — Presupuesto
  investment_budget: string
  urgency: string
  urgency_date: string
  additional_notes: string
  access_token: string
}
