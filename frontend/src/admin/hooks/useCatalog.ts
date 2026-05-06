/**
 * admin/hooks/useCatalog — Fetches and caches the Zanovix services catalog.
 *
 * Endpoint: GET /api/catalog/services (unauthenticated)
 * Caches for the session via React Query (staleTime: 5 min — catalog rarely changes).
 */

import { useQuery } from '@tanstack/react-query'
import type { ServiceCatalogEntry, CatalogResponse } from '../../types/api'

async function fetchCatalog(): Promise<ServiceCatalogEntry[]> {
  const response = await fetch('/api/catalog/services')
  if (!response.ok) {
    throw new Error(`Failed to fetch catalog: ${response.status}`)
  }
  const data: CatalogResponse = await response.json()
  return data.services
}

/**
 * Hook that returns the Zanovix services catalog.
 *
 * Usage:
 *   const { data: catalog, isLoading, isError } = useServiceCatalog()
 */
export function useServiceCatalog() {
  return useQuery<ServiceCatalogEntry[], Error>({
    queryKey: ['catalog', 'services'],
    queryFn: fetchCatalog,
    staleTime: 5 * 60 * 1000, // 5 minutes — catalog rarely changes
  })
}
