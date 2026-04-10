import type { FormState } from '../types/form'

export type ValidationErrors = Record<string, string>

function section1(state: FormState): ValidationErrors | null {
  const errors: ValidationErrors = {}

  if (!state.sector) errors.sector = 'Por favor, selecciona tu sector de actividad'
  if (!state.employee_range) errors.employee_range = 'Por favor, indica el número de empleados'
  if (!state.contact_name.trim()) errors.contact_name = 'El nombre de contacto es obligatorio'

  return Object.keys(errors).length > 0 ? errors : null
}

function section2(_state: FormState): ValidationErrors | null {
  return null
}

function section3(_state: FormState): ValidationErrors | null {
  return null
}

function section4(_state: FormState): ValidationErrors | null {
  return null
}

function section5(state: FormState): ValidationErrors | null {
  const errors: ValidationErrors = {}

  if (!state.most_time_consuming_process.trim()) {
    errors.most_time_consuming_process = 'Por favor, describe el proceso que más tiempo consume'
  }

  return Object.keys(errors).length > 0 ? errors : null
}

function section6(_state: FormState): ValidationErrors | null {
  return null
}

function section7(_state: FormState): ValidationErrors | null {
  return null
}

function section8(_state: FormState): ValidationErrors | null {
  return null
}

function section9(state: FormState): ValidationErrors | null {
  const errors: ValidationErrors = {}

  if (!state.investment_budget) errors.investment_budget = 'Por favor, indica el presupuesto disponible'
  if (!state.urgency) errors.urgency = 'Por favor, indica el nivel de urgencia'
  if (!state.access_token.trim()) errors.access_token = 'El código de acceso es necesario para generar el informe'

  return Object.keys(errors).length > 0 ? errors : null
}

const VALIDATORS: Record<number, (state: FormState) => ValidationErrors | null> = {
  1: section1,
  2: section2,
  3: section3,
  4: section4,
  5: section5,
  6: section6,
  7: section7,
  8: section8,
  9: section9,
}

export function validateSection(sectionNumber: number, state: FormState): ValidationErrors | null {
  const validator = VALIDATORS[sectionNumber]
  return validator ? validator(state) : null
}
