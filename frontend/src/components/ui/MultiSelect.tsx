interface MultiSelectOption {
  value: string
  label: string
}

interface MultiSelectProps {
  options: MultiSelectOption[]
  selected: string[]
  onChange: (selected: string[]) => void
  columns?: 1 | 2 | 3
}

export function MultiSelect({ options, selected, onChange, columns = 2 }: MultiSelectProps) {
  function toggle(value: string) {
    if (selected.includes(value)) {
      onChange(selected.filter(v => v !== value))
    } else {
      onChange([...selected, value])
    }
  }

  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3',
  }[columns]

  return (
    <div className={`grid ${gridCols} gap-2`}>
      {options.map(opt => {
        const isChecked = selected.includes(opt.value)
        return (
          <label
            key={opt.value}
            className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg border cursor-pointer transition-all select-none ${
              isChecked
                ? 'border-teal-500 bg-teal-50 text-teal-800'
                : 'border-gray-200 bg-white text-gray-700 hover:border-teal-300 hover:bg-teal-50/40'
            }`}
          >
            <div
              className={`w-4 h-4 shrink-0 rounded border-2 flex items-center justify-center transition-colors ${
                isChecked ? 'bg-teal-500 border-teal-500' : 'border-gray-300 bg-white'
              }`}
            >
              {isChecked && (
                <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              )}
            </div>
            <input
              type="checkbox"
              className="sr-only"
              checked={isChecked}
              onChange={() => toggle(opt.value)}
            />
            <span className="text-sm font-medium">{opt.label}</span>
          </label>
        )
      })}
    </div>
  )
}
