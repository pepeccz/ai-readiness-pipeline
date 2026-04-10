interface NavigationButtonsProps {
  onPrevious: () => void
  onNext: () => void
  isFirst: boolean
  isLast: boolean
  isSubmitting?: boolean
}

export function NavigationButtons({ onPrevious, onNext, isFirst, isLast, isSubmitting }: NavigationButtonsProps) {
  return (
    <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-100">
      <button
        type="button"
        onClick={onPrevious}
        disabled={isFirst}
        className="px-6 py-2.5 rounded-lg border-2 border-gray-300 text-gray-600 text-sm font-semibold transition-all hover:border-teal-400 hover:text-teal-600 disabled:opacity-0 disabled:pointer-events-none"
      >
        ← Anterior
      </button>

      <button
        type="button"
        onClick={onNext}
        disabled={isSubmitting}
        className="px-8 py-2.5 rounded-lg bg-teal-500 text-white text-sm font-semibold transition-all hover:bg-teal-600 active:bg-teal-700 disabled:opacity-60 disabled:cursor-not-allowed shadow-sm"
      >
        {isSubmitting ? (
          <span className="flex items-center gap-2">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Enviando...
          </span>
        ) : isLast ? (
          'Enviar assessment →'
        ) : (
          'Siguiente →'
        )}
      </button>
    </div>
  )
}
