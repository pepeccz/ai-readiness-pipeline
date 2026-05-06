/**
 * tests/hooks/useCatalog.test.ts — Unit tests for useServiceCatalog hook.
 *
 * E.2: hook returns 3 services on success; isError on failure.
 */

import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { useServiceCatalog } from '../useCatalog'
import type { ServiceCatalogEntry } from '../../../types/api'

const mockCatalogResponse = {
  services: [
    {
      key: 'diagnostico_profundo',
      nombre: 'Diagnóstico Profundo de Procesos',
      descripcion: 'Mapeo end-to-end...',
      cuando_recomendar: ['cuando...'],
      nota_priorizacion: null,
    },
    {
      key: 'desarrollo_acompanamiento',
      nombre: 'Desarrollo y Acompañamiento de Implementación',
      descripcion: 'Implementación técnica...',
      cuando_recomendar: ['cuando...'],
      nota_priorizacion: null,
    },
    {
      key: 'formacion_personalizada',
      nombre: 'Formación Personalizada en IA',
      descripcion: 'Capacitación a medida...',
      cuando_recomendar: ['cuando...'],
      nota_priorizacion: 'Preferir cuando aplique',
    },
  ] as ServiceCatalogEntry[],
}

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children)
}

describe('useServiceCatalog', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns three services on success', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockCatalogResponse), { status: 200 })
    )

    const { result } = renderHook(() => useServiceCatalog(), {
      wrapper: makeWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveLength(3)
    expect(result.current.data?.[0].key).toBe('diagnostico_profundo')
  })

  it('sets isError on network failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useServiceCatalog(), {
      wrapper: makeWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
