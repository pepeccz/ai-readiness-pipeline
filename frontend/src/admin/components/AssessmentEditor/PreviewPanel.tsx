/**
 * PreviewPanel — shows the draft PDF in an iframe after preview job completes.
 *
 * The iframe src points to GET /api/admin/assessments/{id}/pdf?draft=true.
 * This works because the admin session cookie is automatically sent (same-origin).
 *
 * Usage: <PreviewPanel assessmentId={id} visible={showPreview} onClose={() => ...} />
 */

import { pdfUrl } from '../../api/assessments'

interface Props {
  assessmentId: string
  visible: boolean
  onClose: () => void
}

export function PreviewPanel({ assessmentId, visible, onClose }: Props) {
  if (!visible) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 flex-shrink-0">
          <h3 className="text-sm font-semibold text-gray-800">Vista previa del PDF (borrador)</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors text-xl leading-none"
          >
            ×
          </button>
        </div>

        {/* PDF iframe */}
        <div className="flex-1 overflow-hidden">
          <iframe
            src={pdfUrl(assessmentId, true)}
            title="Vista previa PDF"
            className="w-full h-full border-0"
          />
        </div>
      </div>
    </div>
  )
}
