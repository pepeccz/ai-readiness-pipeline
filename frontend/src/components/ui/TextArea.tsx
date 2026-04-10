interface TextAreaProps {
  id?: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  rows?: number
  maxLength?: number
  disabled?: boolean
}

export function TextArea({ id, value, onChange, placeholder, rows = 4, maxLength, disabled }: TextAreaProps) {
  return (
    <div className="relative">
      <textarea
        id={id}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        maxLength={maxLength}
        disabled={disabled}
        className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-800 bg-white resize-none focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors placeholder:text-gray-400"
      />
      {maxLength && (
        <span className="absolute bottom-2 right-3 text-xs text-gray-400">
          {value.length}/{maxLength}
        </span>
      )}
    </div>
  )
}
