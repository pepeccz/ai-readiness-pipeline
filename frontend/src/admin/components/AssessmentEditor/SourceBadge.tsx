/**
 * SourceBadge — inline [IA] or [Editado] pill for editor fields.
 *
 * Logic:
 *   field_sources[name] === 'human'       → [Editado] orange
 *   field_sources[name] === 'llm'         → [IA] blue
 *   absent + field starts with 'llm_'     → [IA] blue (default)
 *   absent + other field                  → no badge (form field, human by default)
 */

interface Props {
  fieldName: string
  fieldSources: Record<string, string>
}

export function SourceBadge({ fieldName, fieldSources }: Props) {
  const explicit = fieldSources[fieldName]

  if (explicit === 'human') {
    return (
      <span className="ml-1.5 inline-flex px-1.5 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-700 align-middle">
        Editado
      </span>
    )
  }

  if (explicit === 'llm' || (!explicit && fieldName.startsWith('llm_'))) {
    return (
      <span className="ml-1.5 inline-flex px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 align-middle">
        IA
      </span>
    )
  }

  return null
}
