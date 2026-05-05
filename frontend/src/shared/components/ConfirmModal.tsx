/**
 * ConfirmModal — Reusable headless + Tailwind confirmation dialog (D6).
 *
 * Props:
 *   open          — controls visibility
 *   title         — dialog heading
 *   body          — dialog description text
 *   confirmLabel  — confirm button label
 *   cancelLabel   — cancel button label
 *   onConfirm     — callback when user confirms
 *   onCancel      — callback when user cancels or closes
 *   variant       — 'default' (teal) | 'danger' (red)
 */

interface ConfirmModalProps {
  open: boolean
  title: string
  body: string
  confirmLabel: string
  cancelLabel: string
  onConfirm: () => void
  onCancel: () => void
  variant?: 'default' | 'danger'
}

export function ConfirmModal({
  open,
  title,
  body,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onCancel,
  variant = 'default',
}: ConfirmModalProps) {
  if (!open) return null

  const confirmCls =
    variant === 'danger'
      ? 'bg-red-600 hover:bg-red-700 text-white'
      : 'bg-teal-600 hover:bg-teal-700 text-white'

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-title"
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
        <h2
          id="confirm-modal-title"
          className="text-base font-semibold text-gray-900 mb-2"
        >
          {title}
        </h2>
        <p className="text-sm text-gray-600 mb-6">{body}</p>

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${confirmCls}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
