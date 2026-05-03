/**
 * MultiSelectChips — chip-based multi-selection input for list[str] form_data fields.
 *
 * Two modes:
 *   - options: fixed option list; user toggles chips on/off via a dropdown.
 *   - free: arbitrary values; user types and presses Enter (or comma) to add.
 *
 * Always emits string[] (never null). When all chips are removed, emits [].
 *
 * No enums, no constructor parameter properties (erasableSyntaxOnly).
 */

import { useState, useRef } from 'react'

interface SelectOption {
  value: string
  label: string
}

interface Props {
  value: string[]
  onChange: (next: string[]) => void
  mode: 'options' | 'free'
  options?: SelectOption[]   // required when mode='options'
  placeholder?: string
}

export function MultiSelectChips({ value, onChange, mode, options = [], placeholder }: Props) {
  const safeValue = value ?? []

  const handleRemove = (v: string) => {
    onChange(safeValue.filter((x) => x !== v))
  }

  const labelFor = (v: string): string => {
    const opt = options.find((o) => o.value === v)
    return opt ? opt.label : v
  }

  // ── Chip rendering (shared) ─────────────────────────────────────────────
  const chips = (
    <div className="flex flex-wrap gap-1.5">
      {safeValue.map((v) => (
        <span
          key={v}
          className="inline-flex items-center gap-1 bg-teal-50 text-teal-700 rounded px-2 py-0.5 text-xs font-medium"
        >
          {labelFor(v)}
          <button
            type="button"
            onClick={() => handleRemove(v)}
            className="hover:text-teal-900 leading-none"
            aria-label={`Quitar ${labelFor(v)}`}
          >
            ×
          </button>
        </span>
      ))}
    </div>
  )

  // ── Options mode: pick from fixed list via dropdown ──────────────────────
  if (mode === 'options') {
    const remaining = options.filter((o) => !safeValue.includes(o.value))

    return (
      <div className="rounded-lg border border-gray-300 px-2 py-2 min-h-[2.5rem]">
        {chips}
        {remaining.length > 0 && (
          <select
            className="w-full mt-1.5 text-sm border-0 focus:outline-none focus:ring-0 text-gray-500 bg-transparent"
            value=""
            onChange={(e) => {
              if (e.target.value) onChange([...safeValue, e.target.value])
            }}
          >
            <option value="">— Agregar —</option>
            {remaining.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        )}
      </div>
    )
  }

  // ── Free mode: type arbitrary values; Enter or comma adds a chip ─────────
  return <FreeMultiSelectChips value={safeValue} onChange={onChange} chips={chips} placeholder={placeholder} />
}

// Extracted to avoid hook-in-conditional lint errors.
function FreeMultiSelectChips({
  value,
  onChange,
  chips,
  placeholder,
}: {
  value: string[]
  onChange: (next: string[]) => void
  chips: React.ReactNode
  placeholder?: string
}) {
  const [draft, setDraft] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const commit = (raw: string) => {
    const trimmed = raw.trim()
    if (trimmed && !value.includes(trimmed)) {
      onChange([...value, trimmed])
    }
    setDraft('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      commit(draft)
    }
    if (e.key === 'Backspace' && draft === '' && value.length > 0) {
      onChange(value.slice(0, -1))
    }
  }

  const handleBlur = () => {
    if (draft.trim()) commit(draft)
  }

  return (
    <div
      className="rounded-lg border border-gray-300 px-2 py-2 min-h-[2.5rem] cursor-text"
      onClick={() => inputRef.current?.focus()}
    >
      {chips}
      <input
        ref={inputRef}
        type="text"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        placeholder={value.length === 0 ? (placeholder ?? 'Escribí y presioná Enter para agregar') : ''}
        className="mt-1 w-full text-sm border-0 focus:outline-none focus:ring-0 bg-transparent placeholder-gray-400"
      />
    </div>
  )
}
