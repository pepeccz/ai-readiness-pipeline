interface SelectOption {
  value: string
  label: string
}

interface SelectFieldProps {
  id?: string
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  placeholder?: string
  disabled?: boolean
}

export function SelectField({ id, value, onChange, options, placeholder, disabled }: SelectFieldProps) {
  return (
    <select
      id={id}
      value={value}
      onChange={e => onChange(e.target.value)}
      disabled={disabled}
      className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {options.map(opt => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}
