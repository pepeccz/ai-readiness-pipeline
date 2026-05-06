// REQ-3: otherValue/otherValues/onOtherChange props (Decision 4)
// Mirrors MultiSelect API for parity — FieldRenderer wiring is symmetric.

const DEFAULT_OTHER_VALUES = ['otro', 'otros', 'other']

interface RadioOption {
  value: string
  label: string
}

interface RadioGroupProps {
  name: string
  options: RadioOption[]
  value: string
  onChange: (value: string) => void
  columns?: 1 | 2 | 3 | 4
  /** Current free-text companion value */
  otherValue?: string
  /** Values that trigger the free-text input. Defaults to ['otro','otros','other']. */
  otherValues?: string[]
  /** Placeholder for the free-text input */
  otherText?: string
  /** Called with new text when the companion input changes */
  onOtherChange?: (text: string) => void
}

export function RadioGroup({
  name,
  options,
  value,
  onChange,
  columns = 1,
  otherValue,
  otherValues = DEFAULT_OTHER_VALUES,
  otherText = 'Especifica cuál...',
  onOtherChange,
}: RadioGroupProps) {
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3',
    4: 'grid-cols-2 sm:grid-cols-4',
  }[columns]

  const isOtherSelected = value !== '' && otherValues.includes(value)

  return (
    <div>
      <div className={`grid ${gridCols} gap-1.5`}>
        {options.map(opt => {
          const isSelected = value === opt.value
          return (
            <label
              key={opt.value}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-all select-none ${
                isSelected
                  ? 'border-teal-500 bg-teal-50 text-teal-800'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-teal-300 hover:bg-teal-50/40'
              }`}
            >
              <div
                className={`w-4 h-4 shrink-0 rounded-full border-2 flex items-center justify-center transition-colors ${
                  isSelected ? 'border-teal-500 bg-teal-500' : 'border-gray-300 bg-white'
                }`}
              >
                {isSelected && (
                  <div className="w-1.5 h-1.5 rounded-full bg-white" />
                )}
              </div>
              <input
                type="radio"
                name={name}
                value={opt.value}
                checked={isSelected}
                onChange={() => onChange(opt.value)}
                className="sr-only"
              />
              <span className="text-sm font-medium">{opt.label}</span>
            </label>
          )
        })}
      </div>
      {/* REQ-3: show free-text input when selected value is an "other" trigger */}
      {isOtherSelected && onOtherChange && (
        <input
          type="text"
          value={otherValue || ''}
          onChange={e => onOtherChange(e.target.value)}
          placeholder={otherText}
          className="mt-2 w-full px-3 py-2 border border-teal-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-teal-50/30"
        />
      )}
    </div>
  )
}
