/**
 * EditorField — single field wrapper with label, source badge, and debounced PATCH.
 *
 * Supports text, email, number, textarea, and select (via options prop).
 * Fires useDebouncedPatch on blur (text/textarea) or onChange (select/checkbox).
 *
 * Must be rendered inside a react-hook-form FormProvider.
 */

import { useFormContext } from 'react-hook-form'
import { SourceBadge } from './SourceBadge'
import { useDebouncedPatch } from '../../hooks/useDebouncedPatch'

interface SelectOption {
  value: string
  label: string
}

interface Props {
  name: string
  label: string
  assessmentId: string
  fieldSources: Record<string, string>
  type?: 'text' | 'email' | 'number' | 'textarea' | 'select' | 'checkbox'
  options?: SelectOption[]   // only for type='select'
  placeholder?: string
  readOnly?: boolean
}

export function EditorField({
  name,
  label,
  assessmentId,
  fieldSources,
  type = 'text',
  options,
  placeholder,
  readOnly = false,
}: Props) {
  const { register, getValues } = useFormContext()
  const debouncedPatch = useDebouncedPatch(assessmentId)

  const baseInput =
    'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:bg-gray-50 disabled:text-gray-500'

  const handleBlur = () => {
    if (readOnly) return
    const val = getValues(name)
    debouncedPatch({ [name]: val })
  }

  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (readOnly) return
    debouncedPatch({ [name]: e.target.value })
  }

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (readOnly) return
    debouncedPatch({ [name]: e.target.checked })
  }

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        <SourceBadge fieldName={name} fieldSources={fieldSources} />
      </label>

      {type === 'textarea' && (
        <textarea
          {...register(name)}
          rows={4}
          placeholder={placeholder}
          disabled={readOnly}
          onBlur={handleBlur}
          className={`${baseInput} resize-y`}
        />
      )}

      {type === 'select' && options && (
        <select
          {...register(name)}
          disabled={readOnly}
          onChange={handleSelectChange}
          className={baseInput}
        >
          <option value="">— Seleccionar —</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      )}

      {type === 'checkbox' && (
        <div className="flex items-center gap-2 mt-1">
          <input
            {...register(name)}
            type="checkbox"
            disabled={readOnly}
            onChange={handleCheckboxChange}
            className="rounded border-gray-300 text-teal-500 focus:ring-teal-500"
          />
          <span className="text-sm text-gray-600">{placeholder ?? 'Activado'}</span>
        </div>
      )}

      {(type === 'text' || type === 'email' || type === 'number') && (
        <input
          {...register(name)}
          type={type}
          placeholder={placeholder}
          disabled={readOnly}
          onBlur={handleBlur}
          className={baseInput}
        />
      )}
    </div>
  )
}
