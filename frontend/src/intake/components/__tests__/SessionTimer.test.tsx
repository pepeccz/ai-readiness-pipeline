/**
 * SessionTimer — TDD RED tests (REQ-10)
 *
 * Tests written BEFORE implementation. All should fail on first run.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import type { TimerState } from '../../api/intake'

// Mock useTimerActions so SessionTimer tests are isolated
const mockPause = vi.fn()
const mockResume = vi.fn()
const mockReset = vi.fn()
const mockAdjust = vi.fn()

vi.mock('../../hooks/useTimerActions', () => ({
  useTimerActions: vi.fn(() => ({
    pause: { mutate: mockPause, isPending: false },
    resume: { mutate: mockResume, isPending: false },
    reset: { mutate: mockReset, isPending: false },
    adjust: { mutate: mockAdjust, isPending: false },
    isPending: false,
  })),
}))

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children)
}

const pausedTimer: TimerState = {
  started_at: null,
  paused_at: '2026-05-07T10:00:00Z',
  accumulated_seconds: 3661, // 1h 1m 1s
  is_running: false,
  server_now: '2026-05-07T10:00:00Z',
}

const runningTimer: TimerState = {
  started_at: '2026-05-07T10:00:00Z',
  paused_at: null,
  accumulated_seconds: 0,
  is_running: true,
  server_now: '2026-05-07T10:00:00Z',
}

describe('SessionTimer — REQ-10', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    mockPause.mockReset()
    mockResume.mockReset()
    mockReset.mockReset()
    mockAdjust.mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders paused timer in HH:MM:SS format', async () => {
    const { SessionTimer } = await import('../SessionTimer')
    render(
      <SessionTimer leadId="lead-1" timer={pausedTimer} sessionState="in_progress" />,
      { wrapper: makeWrapper() },
    )
    // 3661 seconds = 01:01:01
    expect(screen.getByText('01:01:01')).toBeInTheDocument()
  })

  it('shows gray dot when timer is paused', async () => {
    const { SessionTimer } = await import('../SessionTimer')
    const { container } = render(
      <SessionTimer leadId="lead-1" timer={pausedTimer} sessionState="in_progress" />,
      { wrapper: makeWrapper() },
    )
    // Gray status dot for paused state
    const dot = container.querySelector('[data-testid="timer-status-dot"]')
    expect(dot).toBeInTheDocument()
    expect(dot?.className).toMatch(/gray/)
  })

  it('shows green dot when timer is running', async () => {
    const { SessionTimer } = await import('../SessionTimer')
    // started_at in the past so elapsed >= 0
    const past = new Date(Date.now() - 5000).toISOString()
    const timer: TimerState = { ...runningTimer, started_at: past }

    const { container } = render(
      <SessionTimer leadId="lead-1" timer={timer} sessionState="in_progress" />,
      { wrapper: makeWrapper() },
    )
    const dot = container.querySelector('[data-testid="timer-status-dot"]')
    expect(dot?.className).toMatch(/green/)
  })

  it('display advances by 1 after 1s interval when running', async () => {
    const { SessionTimer } = await import('../SessionTimer')
    // Set started_at to exactly now so accumulated_seconds + (now-started_at)=0 on mount
    const startMs = Date.now()
    const timer: TimerState = {
      ...runningTimer,
      started_at: new Date(startMs).toISOString(),
      accumulated_seconds: 0,
    }

    render(
      <SessionTimer leadId="lead-1" timer={timer} sessionState="in_progress" />,
      { wrapper: makeWrapper() },
    )

    // Initially 00:00:00
    expect(screen.getByText('00:00:00')).toBeInTheDocument()

    // Advance 1 second
    await act(async () => {
      vi.advanceTimersByTime(1000)
    })
    expect(screen.getByText('00:00:01')).toBeInTheDocument()
  })

  it('display does NOT advance when paused', async () => {
    const { SessionTimer } = await import('../SessionTimer')
    render(
      <SessionTimer leadId="lead-1" timer={pausedTimer} sessionState="in_progress" />,
      { wrapper: makeWrapper() },
    )

    const before = screen.getByText('01:01:01').textContent

    await act(async () => {
      vi.advanceTimersByTime(3000)
    })

    expect(screen.getByText('01:01:01').textContent).toBe(before)
  })

  it('pause button calls pause mutation', async () => {
    const { SessionTimer } = await import('../SessionTimer')
    const past = new Date(Date.now() - 5000).toISOString()
    const timer: TimerState = { ...runningTimer, started_at: past }

    render(
      <SessionTimer leadId="lead-1" timer={timer} sessionState="in_progress" />,
      { wrapper: makeWrapper() },
    )

    fireEvent.click(screen.getByRole('button', { name: /pausar/i }))
    expect(mockPause).toHaveBeenCalledOnce()
  })

  it('resume button calls resume mutation when paused', async () => {
    const { SessionTimer } = await import('../SessionTimer')
    render(
      <SessionTimer leadId="lead-1" timer={pausedTimer} sessionState="in_progress" />,
      { wrapper: makeWrapper() },
    )

    fireEvent.click(screen.getByRole('button', { name: /reanudar/i }))
    expect(mockResume).toHaveBeenCalledOnce()
  })

  it('all buttons disabled when sessionState=closed', async () => {
    const { SessionTimer } = await import('../SessionTimer')
    render(
      <SessionTimer leadId="lead-1" timer={pausedTimer} sessionState="closed" />,
      { wrapper: makeWrapper() },
    )

    const buttons = screen.getAllByRole('button')
    for (const btn of buttons) {
      expect(btn).toBeDisabled()
    }
  })

  it('reset button triggers confirm then calls reset mutation', async () => {
    const { SessionTimer } = await import('../SessionTimer')
    const past = new Date(Date.now() - 5000).toISOString()
    const timer: TimerState = { ...runningTimer, started_at: past }

    render(
      <SessionTimer leadId="lead-1" timer={timer} sessionState="in_progress" />,
      { wrapper: makeWrapper() },
    )

    fireEvent.click(screen.getByRole('button', { name: /reiniciar/i }))
    // Confirm modal should appear
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    // Confirm
    fireEvent.click(screen.getByRole('button', { name: /confirmar/i }))
    expect(mockReset).toHaveBeenCalledOnce()
  })
})
