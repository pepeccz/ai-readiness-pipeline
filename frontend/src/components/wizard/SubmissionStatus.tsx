import type { SubmissionState } from '../../hooks/useSubmission'

interface SubmissionStatusProps {
  state: SubmissionState
  error: string
  successMessage: string
  onRetry: () => void
}

function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizes = { sm: 'w-5 h-5', md: 'w-10 h-10', lg: 'w-16 h-16' }
  return (
    <svg
      className={`${sizes[size]} animate-spin text-teal-500`}
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
  )
}

export function SubmissionStatus({ state, error, successMessage, onRetry }: SubmissionStatusProps) {
  if (state === 'submitting') {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16">
        <Spinner size="lg" />
        <p className="text-gray-600 font-medium text-lg">Enviando tu evaluación...</p>
        <p className="text-gray-400 text-sm">Un momento, por favor</p>
      </div>
    )
  }

  if (state === 'success') {
    return (
      <div className="flex flex-col items-center justify-center gap-6 py-16">
        <div className="w-20 h-20 rounded-full bg-teal-50 flex items-center justify-center">
          <svg className="w-10 h-10 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>

        <div className="text-center">
          <h3 className="text-2xl font-bold text-gray-800 mb-3">¡Evaluación recibida!</h3>
          <p className="text-gray-600 text-base max-w-sm mx-auto leading-relaxed">
            {successMessage || 'Recibido. Te enviaremos el reporte por email.'}
          </p>
          <p className="text-gray-400 text-sm mt-4 max-w-xs mx-auto">
            Nuestro equipo analizará tu empresa y te enviará el informe personalizado
            en cuanto esté listo.
          </p>
        </div>
      </div>
    )
  }

  if (state === 'error') {
    return (
      <div className="flex flex-col items-center justify-center gap-6 py-16">
        <div className="w-20 h-20 rounded-full bg-red-50 flex items-center justify-center">
          <svg className="w-10 h-10 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>

        <div className="text-center">
          <h3 className="text-xl font-bold text-gray-800 mb-2">Algo salió mal</h3>
          <p className="text-red-500 text-sm max-w-sm mx-auto">
            {error || 'Se produjo un error inesperado. Por favor, inténtalo de nuevo.'}
          </p>
        </div>

        <button
          type="button"
          onClick={onRetry}
          className="px-8 py-3 bg-teal-500 text-white font-semibold rounded-lg hover:bg-teal-600 transition-colors"
        >
          Intentar de nuevo
        </button>
      </div>
    )
  }

  return null
}
