/**
 * TypeScript mirror of the backend YAML schema Pydantic models.
 * Consumed by BlockRenderer and FieldRenderer.
 */

export type QuestionType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'email'
  | 'phone'
  | 'single_choice'
  | 'multi_choice'
  | 'consent'
  | 'composite'
  | 'matrix'

export interface Option {
  value: string
  label: string
  score?: number
  deep_branches?: string[]
}

export interface ShowIfRule {
  field: string
  op: 'eq' | 'neq' | 'in' | 'not_in' | 'gt' | 'lt' | 'any_of' | 'all_of'
  value: string | number | string[]
}

export interface ValidationRule {
  type: 'required' | 'min_length' | 'max_length' | 'pattern' | 'min' | 'max'
  value?: string | number
  message?: string
}

export interface BaseQuestion {
  id: string
  type: QuestionType
  label: string
  required?: boolean
  layer?: string
  block?: string
  helper_text?: string
  hint_didactic?: string
  hint_commercial?: string
  show_if?: ShowIfRule
  validations?: ValidationRule[]
  ai_context?: string
}

export interface SingleChoiceQuestion extends BaseQuestion {
  type: 'single_choice'
  options: Option[]
  scoring_strategy?: 'sum' | 'max' | 'weighted'
}

export interface MultiChoiceQuestion extends BaseQuestion {
  type: 'multi_choice'
  options: Option[]
  min_selections?: number
  max_selections?: number
}

export interface TextQuestion extends BaseQuestion {
  type: 'text' | 'textarea' | 'email' | 'phone' | 'number'
  placeholder?: string
}

export interface CompositeQuestion extends BaseQuestion {
  type: 'composite'
  sub_fields: Question[]
}

export interface ConsentQuestion extends BaseQuestion {
  type: 'consent'
  policy_version: string
  policy_file?: string
}

export interface MatrixRow {
  id: string
  label: string
}

export interface MatrixColumn {
  id: string
  label: string
}

/**
 * Matrix question — single-select per row.
 * Payload shape (ADR-6): { [rowId: string]: string } (row → selected column id)
 */
export interface MatrixQuestion extends BaseQuestion {
  type: 'matrix'
  rows: MatrixRow[]
  columns: MatrixColumn[]
}

export type Question =
  | SingleChoiceQuestion
  | MultiChoiceQuestion
  | TextQuestion
  | CompositeQuestion
  | ConsentQuestion
  | MatrixQuestion

export interface ClosingAnalysis {
  trigger_event: 'block_completed' | 'session_closing'
  llm_model: 'sonnet' | 'haiku'
  output_schema: Record<string, unknown>
  filters?: string[]
}

export interface DeepTrigger {
  condition: ShowIfRule
  activates_branch: string
}

export interface BlockSchema {
  id: string
  layer: 'core'
  order: number
  estimated_minutes: number
  title: string
  questions: Question[]
  closing_analysis?: ClosingAnalysis
  deep_triggers?: DeepTrigger[]
}

export interface AreaSelectorSchema {
  questions: Question[]
}

export interface CoreSchema {
  blocks_order: string[]
  area_selector: AreaSelectorSchema
  blocks?: BlockSchema[]
}

// ---------------------------------------------------------------------------
// Form state
// ---------------------------------------------------------------------------

export type FormValues = Record<string, unknown>

export interface FormErrors {
  [fieldId: string]: string
}
