/**
 * BlockNav — sidebar navigation between CORE blocks.
 *
 * Shows block status: not_started | in_progress | completed | analyzed
 */

interface BlockNavProps {
  blocksOrder: string[]
  blocksCompleted: string[]
  currentBlockId: string | null
  onSelectBlock: (blockId: string) => void
}

const BLOCK_LABELS: Record<string, string> = {
  'block-1-strategic': '1. Estrategia',
  'block-2-process-critical-full': '2. Proceso (completo)',
  'block-2-process-critical-reduced': '2b. Proceso (reducido)',
  'block-2-process-critical-cross-area': '2. Flujo cross-área',
  'block-3-data': '3. Datos',
  'block-4-talent': '4. Talento',
  'block-5-infrastructure': '5. Infraestructura',
  'block-6-compliance': '6. Compliance',
  'block-7-governance': '7. Governance',
}

function blockLabel(id: string): string {
  return BLOCK_LABELS[id] ?? id
}

type BlockStatus = 'not_started' | 'completed'

function getStatus(blockId: string, completed: string[]): BlockStatus {
  return completed.includes(blockId) ? 'completed' : 'not_started'
}

export function BlockNav({ blocksOrder, blocksCompleted, currentBlockId, onSelectBlock }: BlockNavProps) {
  return (
    <nav className="w-56 shrink-0 space-y-1">
      {blocksOrder.map((blockId) => {
        const status = getStatus(blockId, blocksCompleted)
        const isCurrent = blockId === currentBlockId

        return (
          <button
            key={blockId}
            onClick={() => onSelectBlock(blockId)}
            className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors flex items-center gap-2 ${
              isCurrent
                ? 'bg-blue-50 text-blue-700 font-medium'
                : 'text-neutral-600 hover:bg-neutral-50'
            }`}
          >
            {/* Status icon */}
            <span className="shrink-0">
              {status === 'completed' ? (
                <svg className="w-4 h-4 text-green-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-neutral-300" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm0-2a6 6 0 100-12 6 6 0 000 12z" clipRule="evenodd" />
                </svg>
              )}
            </span>
            <span className="truncate">{blockLabel(blockId)}</span>
          </button>
        )
      })}
    </nav>
  )
}
