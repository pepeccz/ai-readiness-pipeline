export class ApiError extends Error {
  status: number
  code: string
  body?: unknown

  constructor(status: number, code: string, message: string, body?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.body = body
  }
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(
      response.status,
      (body as { code?: string }).code ?? 'unknown',
      (body as { detail?: string }).detail ?? 'Request failed',
      body,
    )
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}
