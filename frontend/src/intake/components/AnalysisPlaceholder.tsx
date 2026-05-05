/**
 * AnalysisPlaceholder — shown where AnalysisPanel will live in B6.
 *
 * Displays after a block is submitted (status=submitted).
 * In B6 this will be replaced by the full AnalysisPanel with LLM output.
 */

interface AnalysisPlaceholderProps {
  blockId: string
  status: string
}

export function AnalysisPlaceholder({ blockId, status }: AnalysisPlaceholderProps) {
  if (status !== 'submitted') return null

  return (
    <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
      <div className="flex items-center gap-2 text-amber-700">
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <span className="text-sm font-medium">Bloque guardado</span>
      </div>
      <p className="mt-1 text-xs text-amber-600">
        El análisis IA estará disponible en la próxima versión (Batch 6).
      </p>
    </div>
  )
}
