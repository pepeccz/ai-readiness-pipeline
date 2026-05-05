/**
 * FieldRenderer — renders a single question based on its type.
 *
 * Supported types:
 *   text | textarea | email | phone | number → TextInput / TextArea
 *   single_choice → RadioGroup
 *   multi_choice  → MultiSelect
 *   composite     → Fieldset with recursive FieldRenderer per sub_field
 *   consent       → Checkbox
 *   matrix        → Grid (basic implementation)
 *
 * show_if evaluation is handled by the parent (getVisibleQuestions).
 * This component always renders what it receives.
 */

import type { Question, FormValues, FormErrors, TextQuestion } from './types/schema'
import { RadioGroup } from '../components/ui/RadioGroup'
import { MultiSelect } from '../components/ui/MultiSelect'
import { TextInput } from '../components/ui/TextInput'
import { TextArea } from '../components/ui/TextArea'
import { FormField } from '../components/ui/FormField'

interface FieldRendererProps {
  question: Question
  values: FormValues
  errors: FormErrors
  onChange: (id: string, value: unknown) => void
}

export function FieldRenderer({ question, values, errors, onChange }: FieldRendererProps) {
  const error = errors[question.id]
  const value = values[question.id]

  switch (question.type) {
    case 'single_choice':
      return (
        <FormField
          label={question.label}
          error={error}
          required={question.required}
        >
          <RadioGroup
            name={question.id}
            options={question.options.map((o) => ({ value: o.value, label: o.label }))}
            value={(value as string) ?? ''}
            onChange={(v) => onChange(question.id, v)}
          />
        </FormField>
      )

    case 'multi_choice':
      return (
        <FormField
          label={question.label}
          error={error}
          required={question.required}
        >
          <MultiSelect
            options={question.options.map((o) => ({ value: o.value, label: o.label }))}
            selected={(value as string[]) ?? []}
            onChange={(v) => onChange(question.id, v)}
          />
        </FormField>
      )

    case 'textarea':
      return (
        <FormField
          label={question.label}
          error={error}
          required={question.required}
        >
          <TextArea
            value={(value as string) ?? ''}
            onChange={(v) => onChange(question.id, v)}
            placeholder={question.placeholder}
          />
        </FormField>
      )

    case 'composite':
      return (
        <fieldset className="border border-neutral-200 rounded-lg p-4 space-y-4">
          <legend className="text-sm font-semibold text-neutral-800 px-2">{question.label}</legend>
          {question.helper_text && (
            <p className="text-xs text-neutral-500">{question.helper_text}</p>
          )}
          {question.sub_fields.map((sub) => (
            <FieldRenderer
              key={sub.id}
              question={sub}
              values={values}
              errors={errors}
              onChange={onChange}
            />
          ))}
        </fieldset>
      )

    case 'consent':
      return (
        <div className="flex items-start gap-2">
          <input
            type="checkbox"
            id={question.id}
            checked={Boolean(value)}
            onChange={(e) => onChange(question.id, e.target.checked)}
            className="mt-1"
          />
          <label htmlFor={question.id} className="text-sm text-neutral-700">
            {question.label}
            {question.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
        </div>
      )

    case 'matrix':
      return (
        <p className="text-xs text-neutral-500">
          Matrix question rendering not yet implemented.
        </p>
      )

    // text | email | phone | number
    default: {
      const q = question as TextQuestion
      return (
        <FormField
          label={q.label}
          error={error}
          required={q.required}
        >
          <TextInput
            type={q.type === 'email' ? 'email' : 'text'}
            value={(value as string) ?? ''}
            onChange={(v) => onChange(q.id, v)}
            placeholder={q.placeholder}
          />
        </FormField>
      )
    }
  }
}
