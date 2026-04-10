export function useVisibleSections(employeeRange: string): number[] {
  const sections: number[] = [1, 2]

  // Section 3 — Atención al cliente: visible if NOT solo (1-5)
  if (employeeRange !== '1-5') {
    sections.push(3)
  }

  // Section 4 — Marketing: always visible
  sections.push(4)

  // Section 5 — Operaciones: always visible
  sections.push(5)

  // Section 6 — Finanzas: visible if NOT 1-5
  if (employeeRange !== '1-5') {
    sections.push(6)
  }

  // Section 7 — RRHH: visible if NOT 1-5 and NOT 6-10
  if (employeeRange !== '1-5' && employeeRange !== '6-10') {
    sections.push(7)
  }

  // Sections 8 and 9 always visible
  sections.push(8)
  sections.push(9)

  return sections
}
