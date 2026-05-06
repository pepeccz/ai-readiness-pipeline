/**
 * TA.1 — ApiError class contract (REQ-4 / ADR-5)
 * Strict TDD — RED written before implementation changes.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { fetchJson, ApiError } from './client'

const mockFetch = vi.fn()

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch)
})

afterEach(() => {
  vi.restoreAllMocks()
})

function makeResponse(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response
}

describe('ApiError', () => {
  it('is an instance of Error', () => {
    const err = new ApiError(404, 'not_found', 'Not found')
    expect(err).toBeInstanceOf(Error)
    expect(err).toBeInstanceOf(ApiError)
  })

  it('preserves .message (non-empty)', () => {
    const err = new ApiError(500, 'server_error', 'Something broke')
    expect(err.message).toBe('Something broke')
    expect(err.message.length).toBeGreaterThan(0)
  })

  it('has .status property', () => {
    const err = new ApiError(422, 'validation_error', 'Invalid')
    expect(err.status).toBe(422)
  })

  it('has .body property when set (ADR-5 compat)', () => {
    const body = { detail: 'bad input', code: 'validation_error' }
    const err = new ApiError(422, 'validation_error', 'Invalid', body)
    expect(err.body).toEqual(body)
  })

  it('name is ApiError', () => {
    const err = new ApiError(400, 'bad_request', 'Bad')
    expect(err.name).toBe('ApiError')
  })
})

describe('fetchJson — non-ok response throws ApiError', () => {
  it('throws ApiError for 4xx response', async () => {
    mockFetch.mockResolvedValue(makeResponse(404, { code: 'not_found', detail: 'Not found' }))

    await expect(fetchJson('/some-path')).rejects.toBeInstanceOf(ApiError)
  })

  it('throws ApiError for 5xx response', async () => {
    mockFetch.mockResolvedValue(makeResponse(500, { code: 'server_error', detail: 'Server error' }))

    await expect(fetchJson('/some-path')).rejects.toBeInstanceOf(ApiError)
  })

  it('ApiError thrown for 4xx has correct .status', async () => {
    mockFetch.mockResolvedValue(makeResponse(403, { code: 'forbidden', detail: 'Forbidden' }))

    try {
      await fetchJson('/some-path')
      expect.fail('should have thrown')
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
      expect((err as ApiError).status).toBe(403)
    }
  })

  it('ApiError.message is non-empty', async () => {
    mockFetch.mockResolvedValue(makeResponse(400, { code: 'bad_request', detail: 'Bad request' }))

    try {
      await fetchJson('/some-path')
      expect.fail('should have thrown')
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
      expect((err as ApiError).message.length).toBeGreaterThan(0)
    }
  })

  it('network TypeError propagates as-is (NOT wrapped in ApiError)', async () => {
    const networkError = new TypeError('Failed to fetch')
    mockFetch.mockRejectedValue(networkError)

    try {
      await fetchJson('/some-path')
      expect.fail('should have thrown')
    } catch (err) {
      expect(err).toBeInstanceOf(TypeError)
      expect(err).not.toBeInstanceOf(ApiError)
    }
  })

  it('resolves for 2xx response', async () => {
    mockFetch.mockResolvedValue(makeResponse(200, { data: 'ok' }))

    const result = await fetchJson('/some-path')
    expect(result).toEqual({ data: 'ok' })
  })
})
