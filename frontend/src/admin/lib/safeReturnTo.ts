/**
 * REQ-14 / ADR-11 — safeReturnTo
 *
 * Validates that a returnTo string is a safe relative path that can be used
 * as a post-login redirect destination. Returns null if invalid.
 *
 * Rules:
 *  - Must start with '/' (relative to origin)
 *  - Must NOT start with '//' (protocol-relative URL → open redirect)
 *  - Must NOT contain a scheme (e.g. 'http://', 'javascript:')
 */
export function safeReturnTo(value: string | null | undefined): string | null {
  if (!value) return null

  // Must start with a single /
  if (!value.startsWith('/')) return null

  // Protocol-relative URLs start with //
  if (value.startsWith('//')) return null

  // Reject anything that contains a scheme (e.g. javascript:, http:)
  if (/[a-zA-Z][a-zA-Z0-9+\-.]*:/.test(value)) return null

  return value
}
