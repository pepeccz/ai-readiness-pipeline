/**
 * IntakeApp — main orchestrator for the consultant intake flow.
 *
 * State machine:
 *   1. Load session state (useIntakeSession)
 *   2. If no area selected → show AreaSelector
 *   3. Show BlockNav + BlockRenderer for current block
 *   4. AnalysisPlaceholder after submit (LLM analysis in B6)
 *
 * Props: leadId — the accepted lead's ID
 */

import { useState } from 'react'
import { useIntakeSchema } from './api/intake'
import { useIntakeSession } from './hooks/useIntakeSession'
import { AreaSelector } from './AreaSelector'
import { BlockRenderer } from './BlockRenderer'
import { BlockNav } from './components/BlockNav'
import { AnalysisPlaceholder } from './components/AnalysisPlaceholder'
import { useBlockPayload } from './api/intake'

interface IntakeAppProps {
  leadId: string
}

export function IntakeApp({ leadId }: IntakeAppProps) {
  const { session, isLoading: sessionLoading, hasAreaSelected, isBlockCompleted } = useIntakeSession(leadId)
  const { data: schemaData, isLoading: schemaLoading } = useIntakeSchema(leadId)
  const [currentBlockId, setCurrentBlockId] = useState<string | null>(null)
  const [lastSubmittedBlock, setLastSubmittedBlock] = useState<string | null>(null)

  // Load block payload for auto-save restoration
  const { data: blockPayload } = useBlockPayload(
    leadId,
    currentBlockId ?? '',
  )

  if (sessionLoading || schemaLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-neutral-400 text-sm">
        Cargando sesión...
      </div>
    )
  }

  // Area not selected yet
  if (!hasAreaSelected()) {
    const areaSelector = schemaData?.area_selector
    if (!areaSelector) {
      return <p className="text-sm text-red-500">Error: no se pudo cargar el selector de área.</p>
    }
    return (
      <div className="max-w-2xl mx-auto py-8 px-4">
        <AreaSelector
          leadId={leadId}
          schema={areaSelector}
          onSuccess={() => {
            // After area selection, schema will re-load via query invalidation
            setCurrentBlockId(schemaData?.blocks_order?.[0] ?? null)
          }}
        />
      </div>
    )
  }

  const blocksOrder = schemaData?.blocks_order ?? []
  const activeBlockId = currentBlockId ?? blocksOrder[0] ?? null
  const activeBlock = schemaData?.blocks?.find((b) => b.id === activeBlockId)

  return (
    <div className="flex gap-6 py-8 px-4 max-w-5xl mx-auto">
      {/* Sidebar */}
      <BlockNav
        blocksOrder={blocksOrder}
        blocksCompleted={session?.blocks_completed ?? []}
        currentBlockId={activeBlockId}
        onSelectBlock={(id) => {
          setCurrentBlockId(id)
          setLastSubmittedBlock(null)
        }}
      />

      {/* Main content */}
      <div className="flex-1 min-w-0">
        {activeBlock ? (
          <>
            <BlockRenderer
              leadId={leadId}
              schema={activeBlock}
              initialPayload={blockPayload?.payload}
              onSubmitSuccess={(blockAnalysisId) => {
                setLastSubmittedBlock(activeBlockId)
              }}
            />
            {lastSubmittedBlock === activeBlockId && (
              <AnalysisPlaceholder
                blockId={activeBlockId}
                status="submitted"
              />
            )}
          </>
        ) : (
          <div className="text-sm text-neutral-500 text-center py-16">
            Seleccioná un bloque para comenzar.
          </div>
        )}
      </div>
    </div>
  )
}
