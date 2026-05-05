/**
 * Tests for MultiSelect otherValues prop — REQ-2
 * TDD: written RED before implementation (Strict TDD, TA.4)
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MultiSelect } from '../MultiSelect'

const baseOptions = [
  { value: 'a', label: 'Option A' },
  { value: 'b', label: 'Option B' },
  { value: 'otro', label: 'Otro' },
]

describe('MultiSelect — otherValues prop (REQ-2)', () => {
  it('shows free-text input when "otro" is selected (default otherValues)', () => {
    render(
      <MultiSelect
        options={baseOptions}
        selected={['otro']}
        onChange={() => {}}
        onOtherChange={() => {}}
        otherValue=""
      />,
    )
    expect(screen.getByRole('textbox')).toBeTruthy()
  })

  it('shows free-text input when "otros" is selected (default otherValues includes "otros")', () => {
    const opts = [
      { value: 'a', label: 'Option A' },
      { value: 'otros', label: 'Otros' },
    ]
    render(
      <MultiSelect
        options={opts}
        selected={['otros']}
        onChange={() => {}}
        onOtherChange={() => {}}
        otherValue=""
      />,
    )
    expect(screen.getByRole('textbox')).toBeTruthy()
  })

  it('shows free-text input when "other" is selected (default otherValues includes "other")', () => {
    const opts = [
      { value: 'a', label: 'Option A' },
      { value: 'other', label: 'Other' },
    ]
    render(
      <MultiSelect
        options={opts}
        selected={['other']}
        onChange={() => {}}
        onOtherChange={() => {}}
        otherValue=""
      />,
    )
    expect(screen.getByRole('textbox')).toBeTruthy()
  })

  it('shows free-text when option has is_other: true, regardless of value name', () => {
    const opts = [
      { value: 'a', label: 'A' },
      { value: 'custom_other', label: 'Custom Other', is_other: true },
    ]
    render(
      <MultiSelect
        options={opts as any}
        selected={['custom_other']}
        onChange={() => {}}
        onOtherChange={() => {}}
        otherValue=""
      />,
    )
    expect(screen.getByRole('textbox')).toBeTruthy()
  })

  it('does NOT show free-text when no "otro" value is selected', () => {
    render(
      <MultiSelect
        options={baseOptions}
        selected={['a']}
        onChange={() => {}}
        onOtherChange={() => {}}
        otherValue=""
      />,
    )
    expect(screen.queryByRole('textbox')).toBeNull()
  })

  it('calls onOtherChange when deselecting "otro" (via toggle in parent)', () => {
    const onOtherChange = vi.fn()
    const onChange = vi.fn()
    const { rerender } = render(
      <MultiSelect
        options={baseOptions}
        selected={['otro']}
        onChange={onChange}
        onOtherChange={onOtherChange}
        otherValue="some text"
      />,
    )
    // Click on the "Otro" label to toggle it off
    const otroLabel = screen.getByText('Otro').closest('label')!
    fireEvent.click(otroLabel)
    // onChange called with 'otro' removed
    expect(onChange).toHaveBeenCalledWith([])
    // onOtherChange called with '' to clear
    expect(onOtherChange).toHaveBeenCalledWith('')
  })
})
