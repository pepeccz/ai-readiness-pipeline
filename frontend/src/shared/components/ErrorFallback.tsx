/**
 * ErrorFallback — fallback UI for react-error-boundary ErrorBoundary.
 *
 * Used in AdminLayout to catch render errors in both /admin/* and /intake/* trees.
 * REQ-7 / ADR-5.
 */
import type { FallbackProps } from 'react-error-boundary'

export function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center min-h-[40vh] gap-4 p-8 text-center"
    >
      <div className="text-4xl">⚠️</div>
      <h2 className="text-lg font-semibold text-neutral-900">Algo salió mal</h2>
      <p className="text-sm text-neutral-500 max-w-sm">
        {error instanceof Error ? error.message : 'Error inesperado'}
      </p>
      <button
        type="button"
        onClick={resetErrorBoundary}
        className="px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700 transition-colors"
      >
        Reintentar
      </button>
    </div>
  )
}
