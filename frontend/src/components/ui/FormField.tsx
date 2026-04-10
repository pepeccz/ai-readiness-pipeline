import type { ReactNode } from 'react'

interface FormFieldProps {
  label: string
  htmlFor?: string
  error?: string
  required?: boolean
  children: ReactNode
}

export function FormField({ label, htmlFor, error, required, children }: FormFieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={htmlFor}
        className="text-sm font-medium text-gray-700"
      >
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {children}
      {error && (
        <p className="text-sm text-red-500 mt-0.5">{error}</p>
      )}
    </div>
  )
}
