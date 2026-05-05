/**
 * ProgressIndicator — shows how many branches have been submitted.
 */

interface Props {
  total: number
  completed: number
}

export function ProgressIndicator({ total, completed }: Props) {
  const pct = total === 0 ? 0 : Math.round((completed / total) * 100)
  return (
    <div className="mb-6">
      <div className="flex justify-between text-sm text-gray-600 mb-1">
        <span>Progreso</span>
        <span>
          {completed} / {total} secciones completadas
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
