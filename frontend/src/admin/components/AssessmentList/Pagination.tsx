/**
 * Pagination — prev/next navigation + page size selector.
 */

const PAGE_SIZES = [25, 50, 100]

interface Props {
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
}

export function Pagination({ page, pageSize, total, onPageChange, onPageSizeChange }: Props) {
  const totalPages = Math.ceil(total / pageSize)
  const start = (page - 1) * pageSize + 1
  const end = Math.min(page * pageSize, total)

  return (
    <div className="flex items-center justify-between mt-4">
      <p className="text-sm text-gray-500">
        {total === 0 ? 'Sin resultados' : `Mostrando ${start}–${end} de ${total}`}
      </p>

      <div className="flex items-center gap-3">
        {/* Page size */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500">Por página:</label>
          <select
            value={pageSize}
            onChange={(e) => {
              onPageSizeChange(Number(e.target.value))
              onPageChange(1)
            }}
            className="rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            {PAGE_SIZES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Prev / Next */}
        <div className="flex items-center gap-1">
          <button
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            className="px-3 py-1.5 rounded border border-gray-300 text-sm text-gray-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
          >
            ← Anterior
          </button>
          <span className="px-3 py-1.5 text-sm text-gray-600">
            {page} / {totalPages || 1}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
            className="px-3 py-1.5 rounded border border-gray-300 text-sm text-gray-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
          >
            Siguiente →
          </button>
        </div>
      </div>
    </div>
  )
}
