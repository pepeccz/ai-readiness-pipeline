/**
 * TD.1 — ConfirmModal renders title, body, buttons; calls correct callbacks (REQ-1/D6)
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import { ConfirmModal } from '../ConfirmModal'

describe('ConfirmModal — REQ-1 D6', () => {
  const baseProps = {
    open: true,
    title: 'Cerrar sesión',
    body: '¿Confirmar acción?',
    confirmLabel: 'Confirmar',
    cancelLabel: 'Cancelar',
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  }

  it('renders title and body when open', () => {
    render(<ConfirmModal {...baseProps} />)
    expect(screen.getByText('Cerrar sesión')).toBeInTheDocument()
    expect(screen.getByText('¿Confirmar acción?')).toBeInTheDocument()
  })

  it('renders confirm and cancel buttons', () => {
    render(<ConfirmModal {...baseProps} />)
    expect(screen.getByRole('button', { name: /confirmar/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument()
  })

  it('calls onConfirm when confirm button clicked', () => {
    const onConfirm = vi.fn()
    render(<ConfirmModal {...baseProps} onConfirm={onConfirm} />)
    fireEvent.click(screen.getByRole('button', { name: /confirmar/i }))
    expect(onConfirm).toHaveBeenCalledOnce()
  })

  it('calls onCancel when cancel button clicked', () => {
    const onCancel = vi.fn()
    render(<ConfirmModal {...baseProps} onCancel={onCancel} />)
    fireEvent.click(screen.getByRole('button', { name: /cancelar/i }))
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('does not render when open=false', () => {
    render(<ConfirmModal {...baseProps} open={false} />)
    expect(screen.queryByText('Cerrar sesión')).not.toBeInTheDocument()
  })

  it('applies danger styling when variant="danger"', () => {
    render(<ConfirmModal {...baseProps} variant="danger" />)
    const confirmBtn = screen.getByRole('button', { name: /confirmar/i })
    expect(confirmBtn.className).toMatch(/red/)
  })

  it('applies default styling when variant="default"', () => {
    render(<ConfirmModal {...baseProps} variant="default" />)
    const confirmBtn = screen.getByRole('button', { name: /confirmar/i })
    expect(confirmBtn.className).not.toMatch(/red/)
  })
})
