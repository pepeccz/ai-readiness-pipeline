/**
 * EditorTabs — horizontal tab navigator for the assessment editor.
 *
 * 11 tabs mirroring the wizard sections + enrichments + scoring.
 */

const TABS = [
  { key: 'empresa', label: 'Empresa' },
  { key: 'stack', label: 'Stack' },
  { key: 'cliente', label: 'Atención al cliente' },
  { key: 'marketing', label: 'Marketing y ventas' },
  { key: 'operaciones', label: 'Operaciones' },
  { key: 'finanzas', label: 'Finanzas' },
  { key: 'rrhh', label: 'RRHH' },
  { key: 'compliance', label: 'Compliance' },
  { key: 'presupuesto', label: 'Presupuesto' },
  { key: 'enriquecimientos', label: 'Enriquecimientos' },
  { key: 'scoring', label: 'Scoring' },
]

export type TabKey =
  | 'empresa'
  | 'stack'
  | 'cliente'
  | 'marketing'
  | 'operaciones'
  | 'finanzas'
  | 'rrhh'
  | 'compliance'
  | 'presupuesto'
  | 'enriquecimientos'
  | 'scoring'

interface Props {
  activeTab: TabKey
  onTabChange: (tab: TabKey) => void
}

export function EditorTabs({ activeTab, onTabChange }: Props) {
  return (
    <div className="border-b border-gray-200 mb-6">
      <nav className="flex overflow-x-auto -mb-px gap-0">
        {TABS.map((tab) => {
          const isActive = tab.key === activeTab
          return (
            <button
              key={tab.key}
              onClick={() => onTabChange(tab.key as TabKey)}
              className={`
                px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors
                ${isActive
                  ? 'border-teal-500 text-teal-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
              `}
            >
              {tab.label}
            </button>
          )
        })}
      </nav>
    </div>
  )
}
