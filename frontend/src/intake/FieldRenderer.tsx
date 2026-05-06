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
 *
 * REQ-2: each field wrapper carries data-error="true" when the field has an error,
 * so BlockRenderer can scroll to the first errored field via querySelector.
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
  // REQ-2: data-error attribute for scroll-to-first-error
  const dataError = error ? ('true' as const) : undefined

  switch (question.type) {
    case 'single_choice':
      return (
        <div data-error={dataError}>
          <FormField
            label={question.label}
            error={error}
            required={question.required}
          >
            {/* REQ-3: pass otherValue/onOtherChange; companion key is ${q.id}_other_text.
                Switching away from "otro" calls onChange which hides the input; the
                onOtherChange('') call below removes the companion key from payload. */}
            <RadioGroup
              name={question.id}
              options={question.options.map((o) => ({ value: o.value, label: o.label }))}
              value={(value as string) ?? ''}
              onChange={(v) => {
                onChange(question.id, v)
                // If switching away from "otro", clear companion text
                const prev = value as string
                const OTHER_VALS = ['otro', 'otros', 'other']
                if (OTHER_VALS.includes(prev) && !OTHER_VALS.includes(v)) {
                  onChange(`${question.id}_other_text`, undefined)
                }
              }}
              otherValue={(values[`${question.id}_other_text`] as string) ?? ''}
              onOtherChange={(v) => {
                if (v === '') {
                  onChange(`${question.id}_other_text`, undefined)
                } else {
                  onChange(`${question.id}_other_text`, v)
                }
              }}
            />
          </FormField>
        </div>
      )

    case 'multi_choice':
      return (
        <div data-error={dataError}>
          <FormField
            label={question.label}
            error={error}
            required={question.required}
          >
            {/* REQ-2: pass otherValue/onOtherChange; companion key is ${q.id}_other_text.
                On deselect of "otro", MultiSelect calls onOtherChange('') which removes the key. */}
            <MultiSelect
              options={question.options.map((o) => ({ value: o.value, label: o.label, is_other: (o as any).is_other }))}
              selected={(value as string[]) ?? []}
              onChange={(v) => onChange(question.id, v)}
              otherValue={(values[`${question.id}_other_text`] as string) ?? ''}
              onOtherChange={(v) => {
                if (v === '') {
                  // Remove the companion key by setting undefined signals removal
                  onChange(`${question.id}_other_text`, undefined)
                } else {
                  onChange(`${question.id}_other_text`, v)
                }
              }}
            />
          </FormField>
        </div>
      )

    case 'textarea':
      return (
        <div data-error={dataError}>
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
        </div>
      )

    case 'composite':
      return (
        <fieldset
          data-error={dataError}
          className="border border-neutral-200 rounded-lg p-4 space-y-4"
        >
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
        <div data-error={dataError} className="flex items-start gap-2">
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
        <div data-error={dataError}>
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
        </div>
      )
    }
  }
}
