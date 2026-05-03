/**
 * Canonical form_data key set — TypeScript mirror of backend FORM_DATA_KEYS.
 *
 * This array is manually maintained to stay in sync with:
 *   app/schemas/assessment.py :: FORM_DATA_KEYS  (the source of truth)
 *
 * SYNC RULE: If you add, rename, or remove a key here, you MUST also update
 *   app/schemas/assessment.py :: _FLAT_COLUMN_FIELDS (if moving to flat) OR
 *   app/api/public_routes.py  :: PublicSubmissionPayload (if adding a wizard field).
 *   The backend test `tests/test_form_data_keys.py` asserts that this array
 *   matches FORM_DATA_KEYS exactly — CI will catch any drift.
 *
 * Count: 42 keys
 * Derivation: PublicSubmissionPayload.model_fields (48) minus flat columns
 *   (company_name, sector, employee_range, revenue_range, respondent_email,
 *    auto_publish) = 42.
 */
export const FORM_DATA_KEYS: readonly string[] = [
  // Empresa (3)
  'contact_name',
  'contact_role',
  'tech_decision_maker',

  // Stack (6)
  'software_used',
  'ai_tools_used',
  'has_chatbot',
  'chatbot_desc',
  'has_automations',
  'automations_desc',

  // Cliente — Atención al cliente (5)
  'contact_channels',
  'daily_queries',
  'support_team_desc',
  'top_repetitive_queries',
  'avg_resolution_time',

  // Marketing y ventas (5)
  'content_generation',
  'lead_acquisition',
  'has_lead_tracking',
  'lead_tracking_desc',
  'monthly_marketing_budget',

  // Operaciones (5)
  'most_time_consuming_process',
  'process_people_count',
  'process_hours_per_week',
  'data_entry_channels',
  'process_pain_points',

  // Finanzas (4)
  'invoicing_method',
  'has_cash_flow_control',
  'cash_flow_desc',
  'admin_hours_per_week',

  // RRHH (4)
  'is_hiring',
  'hiring_desc',
  'hr_management_method',
  'hr_hours_per_week',

  // Compliance (7)
  'collects_personal_data',
  'personal_data_types',
  'knows_ai_gdpr',
  'has_dpa',
  'dpa_with_whom',
  'knows_ai_act',
  'has_ai_policy',

  // Presupuesto (3)
  'investment_budget',
  'urgency',
  'additional_notes',
] as const
