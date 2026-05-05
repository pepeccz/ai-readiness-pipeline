/**
 * T3.3 — ErrorFallback renders on child render error; happy path transparent (REQ-7)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ErrorBoundary } from 'react-error-boundary'
import { ErrorFallback } from '../ErrorFallback'

// Suppress React's console.error for expected error boundary noise
beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {})
})
afterEach(() => {
  vi.restoreAllMocks()
})

// Component that throws on command
function Bomber({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) throw new Error('Test render error')
  return <div>Children rendered OK</div>
}

describe('ErrorFallback — REQ-7', () => {
  it('renders children normally when no error (happy path transparent)', () => {
    render(
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        <Bomber shouldThrow={false} />
      </ErrorBoundary>,
    )
    expect(screen.getByText('Children rendered OK')).toBeInTheDocument()
    expect(screen.queryByText(/reintentar/i)).not.toBeInTheDocument()
  })

  it('renders fallback UI with reset button when a child throws', () => {
    render(
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        <Bomber shouldThrow={true} />
      </ErrorBoundary>,
    )
    // Fallback must render some error indication
    expect(screen.queryByText('Children rendered OK')).not.toBeInTheDocument()
    // Must have a reset / reintentar button
    expect(screen.getByRole('button', { name: /reintentar/i })).toBeInTheDocument()
  })

  it('calls resetErrorBoundary when reset button is clicked', async () => {
    const user = userEvent.setup()
    const resetFn = vi.fn()

    render(
      <ErrorFallback
        error={new Error('Test')}
        resetErrorBoundary={resetFn}
      />,
    )

    await user.click(screen.getByRole('button', { name: /reintentar/i }))
    expect(resetFn).toHaveBeenCalledOnce()
  })
})
