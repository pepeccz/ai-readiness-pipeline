export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface SubmissionResponse {
  task_id: string
  status: TaskStatus
  message?: string
}

export interface StatusResponse {
  task_id: string
  status: TaskStatus
  progress?: number
  message?: string
  error?: string
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
  lead_tracking: boolean
  lead_tracking_desc?: string
  marketing_budget: string

  // Section 5
  most_time_consuming_process: string
  process_people_count: string
  hours_per_week: string
  data_entry_channels: string[]
  process_pain_points: string[]

  // Section 6
  invoicing_method: string
  cash_flow_control: boolean
  cash_flow_desc?: string
  admin_hours_per_week: string

  // Section 7
  is_hiring: boolean
  hiring_desc?: string
  hr_management: string
  hr_hours_per_week: string

  // Section 8
  collects_personal_data: boolean
  data_types?: string
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
