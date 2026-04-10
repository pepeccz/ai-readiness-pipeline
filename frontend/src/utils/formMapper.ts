import type { FormState } from '../types/form'
import type { AssessmentFormPayload } from '../types/api'

function toBool(value: string): boolean {
  return value === 'si'
}

function cleanString(value: string): string {
  return value.trim()
}

function cleanArray(arr: string[]): string[] {
  return arr.filter(v => v.trim().length > 0)
}

export function mapFormToPayload(state: FormState): AssessmentFormPayload {
  return {
    // Section 1
    company_name: cleanString(state.company_name),
    sector: cleanString(state.sector),
    employee_range: cleanString(state.employee_range),
    revenue_range: cleanString(state.revenue_range),
    contact_name: cleanString(state.contact_name),
    contact_role: cleanString(state.contact_role),
    tech_decision_maker: cleanString(state.tech_decision_maker),

    // Section 2
    software_used: cleanArray(state.software_used),
    ai_tools_used: cleanArray(state.ai_tools_used),
    has_chatbot: toBool(state.has_chatbot),
    ...(state.has_chatbot === 'si' && state.chatbot_desc.trim()
      ? { chatbot_desc: cleanString(state.chatbot_desc) }
      : {}),
    has_automations: toBool(state.has_automations),
    ...(state.has_automations === 'si' && state.automations_desc.trim()
      ? { automations_desc: cleanString(state.automations_desc) }
      : {}),

    // Section 3
    contact_channels: cleanArray(state.contact_channels),
    daily_queries: cleanString(state.daily_queries),
    support_team_desc: cleanString(state.support_team_desc),
    top_repetitive_queries: cleanString(state.top_repetitive_queries),
    avg_resolution_time: cleanString(state.avg_resolution_time),

    // Section 4
    content_generation: cleanArray(state.content_generation),
    lead_acquisition: cleanArray(state.lead_acquisition),
    lead_tracking: toBool(state.lead_tracking),
    ...(state.lead_tracking === 'si' && state.lead_tracking_desc.trim()
      ? { lead_tracking_desc: cleanString(state.lead_tracking_desc) }
      : {}),
    marketing_budget: cleanString(state.marketing_budget),

    // Section 5
    most_time_consuming_process: cleanString(state.most_time_consuming_process),
    process_people_count: cleanString(state.process_people_count),
    hours_per_week: cleanString(state.hours_per_week),
    data_entry_channels: cleanArray(state.data_entry_channels),
    process_pain_points: cleanArray(state.process_pain_points),

    // Section 6
    invoicing_method: cleanString(state.invoicing_method),
    cash_flow_control: toBool(state.cash_flow_control),
    ...(state.cash_flow_control === 'si' && state.cash_flow_desc.trim()
      ? { cash_flow_desc: cleanString(state.cash_flow_desc) }
      : {}),
    admin_hours_per_week: cleanString(state.admin_hours_per_week),

    // Section 7
    is_hiring: toBool(state.is_hiring),
    ...(state.is_hiring === 'si' && state.hiring_desc.trim()
      ? { hiring_desc: cleanString(state.hiring_desc) }
      : {}),
    hr_management: cleanString(state.hr_management),
    hr_hours_per_week: cleanString(state.hr_hours_per_week),

    // Section 8
    collects_personal_data: toBool(state.collects_personal_data),
    ...(state.collects_personal_data === 'si' && state.data_types.trim()
      ? { data_types: cleanString(state.data_types) }
      : {}),
    knows_ai_gdpr: cleanString(state.knows_ai_gdpr),
    has_dpa: cleanString(state.has_dpa),
    ...(state.has_dpa === 'si' && state.dpa_with_whom.trim()
      ? { dpa_with_whom: cleanString(state.dpa_with_whom) }
      : {}),
    knows_ai_act: cleanString(state.knows_ai_act),
    has_ai_policy: cleanString(state.has_ai_policy),

    // Section 9
    investment_budget: cleanString(state.investment_budget),
    urgency: cleanString(state.urgency),
    ...(state.urgency === 'temporada_alta' && state.urgency_date.trim()
      ? { urgency_date: cleanString(state.urgency_date) }
      : {}),
    ...(state.additional_notes.trim()
      ? { additional_notes: cleanString(state.additional_notes) }
      : {}),

    // Auth token (used in header, not body)
    _token: state.access_token || '',
  }
}
