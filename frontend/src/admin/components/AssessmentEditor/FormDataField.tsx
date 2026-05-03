/**
 * FormDataField — editable field wrapper for form_data keys.
 *
 * Mirrors EditorField but targets the form_data JSON blob:
 *   - Reads value from react-hook-form path `form_data.<name>`
 *   - Writes via debouncedPatch.formData(name, value) (single-key API)
 *   - SourceBadge reads field_sources["form_data.<name>"]
 *
 * Supported types:
 *   text | textarea | number | select | boolean | multiselect-free | multiselect-options
 *
 * No enums, no constructor parameter properties (erasableSyntaxOnly).
 */

import { useFormContext } from 'react-hook-form'
import { SourceBadge } from './SourceBadge'
import { MultiSelectChips } from './MultiSelectChips'
import { useDebouncedPatch } from '../../hooks/useDebouncedPatch'

interface SelectOption {
  value: string
  label: string
}

interface Props {
  /** Canonical form_data key (must be in FORM_DATA_KEYS). */
  name: string
  label: string
  assessmentId: string
  fieldSources: Record<string, string>
  type: 'text' | 'textarea' | 'number' | 'select' | 'boolean' | 'multiselect-free' | 'multiselect-options'
  options?: SelectOption[]    // required for select / multiselect-options
  placeholder?: string
  rows?: number               // for textarea; defaults to 4
}

export function FormDataField({
  name,
  label,
  assessmentId,
  fieldSources,
  type,
  options,
  placeholder,
  rows = 4,
}: Props) {
  const { register, getValues, setValue, watch } = useFormContext()
  const debouncedPatch = useDebouncedPatch(assessmentId)

  // react-hook-form nested path for the value inside the form_data object.
  const path = `form_data.${name}`

  // Source badge key: must match how backend writes field_sources entries.
  const sourceKey = `form_data.${name}`

  const baseInput =
    'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500'

  const handleBlur = () => {
    debouncedPatch.formData(name, getValues(path))
  }

  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    // Explicit onChange overrides register spread; update form state too.
    setValue(path, e.target.value)
    debouncedPatch.formData(name, e.target.value)
  }

  const handleBooleanChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Explicit onChange overrides the register spread, so we must call
    // setValue to keep form state in sync (needed for watch() in conditional renders).
    setValue(path, e.target.checked)
    debouncedPatch.formData(name, e.target.checked)
  }

  const handleMultiChange = (next: string[]) => {
    setValue(path, next)
    debouncedPatch.formData(name, next)
  }

  const currentValue = watch(path)

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        <SourceBadge fieldName={sourceKey} fieldSources={fieldSources} />
      </label>

      {(type === 'text' || type === 'number') && (
        <input
          {...register(path)}
          type={type === 'number' ? 'number' : 'text'}
          placeholder={placeholder}
          onBlur={handleBlur}
          className={baseInput}
        />
      )}

      {type === 'textarea' && (
        <textarea
          {...register(path)}
          rows={rows}
          placeholder={placeholder}
          onBlur={handleBlur}
          className={`${baseInput} resize-y`}
        />
      )}

      {type === 'select' && options && (
        <select
          {...register(path)}
          onChange={handleSelectChange}
          className={baseInput}
        >
          <option value="">— Seleccionar —</option>
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      )}

      {type === 'boolean' && (
        <div className="flex items-center gap-2 mt-1">
          <input
            {...register(path)}
            type="checkbox"
            onChange={handleBooleanChange}
            className="rounded border-gray-300 text-teal-500 focus:ring-teal-500"
          />
          <span className="text-sm text-gray-600">{placeholder ?? 'Sí'}</span>
        </div>
      )}

      {type === 'multiselect-free' && (
        <MultiSelectChips
          value={(currentValue as string[]) ?? []}
          onChange={handleMultiChange}
          mode="free"
          placeholder={placeholder}
        />
      )}

      {type === 'multiselect-options' && options && (
        <MultiSelectChips
          value={(currentValue as string[]) ?? []}
          onChange={handleMultiChange}
          mode="options"
          options={options}
          placeholder={placeholder}
        />
      )}
    </div>
  )
}
