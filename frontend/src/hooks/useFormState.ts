import { useState } from 'react'
import type { FormState } from '../types/form'

const initialState: FormState = {
  // Section 1
  sector: '',
  employee_range: '',
  revenue_range: '',
  contact_name: '',
  contact_role: '',
  tech_decision_maker: '',

  // Section 2
  software_used: [],
  ai_tools_used: [],
  has_chatbot: '',
  chatbot_desc: '',
  has_automations: '',
  automations_desc: '',

  // Section 3
  contact_channels: [],
  daily_queries: '',
  support_team_desc: '',
  top_repetitive_queries: '',
  avg_resolution_time: '',

  // Section 4
  content_generation: [],
  lead_acquisition: [],
  lead_tracking: '',
  lead_tracking_desc: '',
  marketing_budget: '',

  // Section 5
  most_time_consuming_process: '',
  process_people_count: '',
  hours_per_week: '',
  data_entry_channels: [],
  process_pain_points: [],

  // Section 6
  invoicing_method: '',
  cash_flow_control: '',
  cash_flow_desc: '',
  admin_hours_per_week: '',

  // Section 7
  is_hiring: '',
  hiring_desc: '',
  hr_management: '',
  hr_hours_per_week: '',

  // Section 8
  collects_personal_data: '',
  data_types: '',
  knows_ai_gdpr: '',
  has_dpa: '',
  dpa_with_whom: '',
  knows_ai_act: '',
  has_ai_policy: '',

  // Section 9
  investment_budget: '',
  urgency: '',
  urgency_date: '',
  additional_notes: '',
}

export function useFormState() {
  const [state, setState] = useState<FormState>(initialState)

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setState(prev => ({ ...prev, [key]: value }))
  }

  function resetForm() {
    setState(initialState)
  }

  return { state, updateField, resetForm }
}
