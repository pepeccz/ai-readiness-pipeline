import type { SubmissionState } from '../../hooks/useSubmission'

interface SubmissionStatusProps {
  state: SubmissionState
  error: string
  onDownload: () => void
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

function AnimatedDots() {
  return (
    <span className="inline-flex gap-1 items-end ml-1">
      <span className="w-1.5 h-1.5 bg-teal-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
      <span className="w-1.5 h-1.5 bg-teal-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
      <span className="w-1.5 h-1.5 bg-teal-500 rounded-full animate-bounce" />
    </span>
  )
}

export function SubmissionStatus({ state, error, onDownload, onRetry }: SubmissionStatusProps) {
  if (state === 'submitting') {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16">
        <Spinner size="lg" />
        <p className="text-gray-600 font-medium text-lg">Enviando tu evaluación...</p>
        <p className="text-gray-400 text-sm">Un momento, por favor</p>
      </div>
    )
  }

  if (state === 'polling') {
    return (
      <div className="flex flex-col items-center justify-center gap-6 py-16">
        <Spinner size="lg" />
        <div className="text-center">
          <p className="text-gray-700 font-semibold text-xl mb-2">
            Generando tu informe personalizado
            <AnimatedDots />
          </p>
          <p className="text-gray-500 text-sm max-w-sm mx-auto">
            Nuestro sistema de IA está analizando tu empresa en detalle.
            Esto puede tardar hasta 2 minutos.
          </p>
        </div>
        <div className="flex flex-col items-center gap-2 mt-4">
          <div className="flex items-center gap-2 text-sm text-teal-600">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Evaluando tu stack tecnológico
          </div>
          <div className="flex items-center gap-2 text-sm text-teal-600">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Identificando oportunidades de automatización
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Preparando recomendaciones específicas...
          </div>
        </div>
      </div>
    )
  }

  if (state === 'ready' || state === 'downloading') {
    return (
      <div className="flex flex-col items-center justify-center gap-6 py-16">
        <div className="w-20 h-20 rounded-full bg-teal-50 flex items-center justify-center">
          <svg className="w-10 h-10 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>

        <div className="text-center">
          <h3 className="text-2xl font-bold text-gray-800 mb-2">¡Tu informe está listo!</h3>
          <p className="text-gray-500 text-sm max-w-sm mx-auto">
            Hemos completado el análisis de AI Readiness de tu empresa.
            Descarga el informe para ver las recomendaciones personalizadas.
          </p>
        </div>

        <button
          type="button"
          onClick={onDownload}
          disabled={state === 'downloading'}
          className="flex items-center gap-3 px-8 py-4 bg-teal-500 text-white text-base font-semibold rounded-xl hover:bg-teal-600 active:bg-teal-700 transition-all shadow-lg shadow-teal-500/25 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {state === 'downloading' ? (
            <>
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Descargando...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Descargar informe PDF
            </>
          )}
        </button>

        <p className="text-xs text-gray-400">El informe incluye un análisis detallado y un roadmap de implementación</p>
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
