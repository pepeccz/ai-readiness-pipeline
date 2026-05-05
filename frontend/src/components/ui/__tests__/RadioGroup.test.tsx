/**
 * Tests for RadioGroup otherValue/otherValues/onOtherChange props — REQ-3
 * TDD: written RED before implementation (Strict TDD, TA.7)
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { RadioGroup } from '../RadioGroup'

const baseOptions = [
  { value: 'a', label: 'Option A' },
  { value: 'b', label: 'Option B' },
  { value: 'otro', label: 'Otro' },
]

describe('RadioGroup — otherValue/otherValues/onOtherChange props (REQ-3)', () => {
  it('shows free-text input when "otro" is selected', () => {
    render(
      <RadioGroup
        name="q1"
        options={baseOptions}
        value="otro"
        onChange={() => {}}
        onOtherChange={() => {}}
        otherValue=""
      />,
    )
    expect(screen.getByRole('textbox')).toBeTruthy()
  })

  it('does NOT show free-text when "otro" is not selected', () => {
    render(
      <RadioGroup
        name="q1"
        options={baseOptions}
        value="a"
        onChange={() => {}}
        onOtherChange={() => {}}
        otherValue=""
      />,
    )
    expect(screen.queryByRole('textbox')).toBeNull()
  })

  it('does NOT show free-text when no value selected', () => {
    render(
      <RadioGroup
        name="q1"
        options={baseOptions}
        value=""
        onChange={() => {}}
        onOtherChange={() => {}}
        otherValue=""
      />,
    )
    expect(screen.queryByRole('textbox')).toBeNull()
  })

  it('shows free-text when custom otherValues matches selected value', () => {
    const opts = [
      { value: 'a', label: 'A' },
      { value: 'ninguna', label: 'Ninguna' },
    ]
    render(
      <RadioGroup
        name="q2"
        options={opts}
        value="ninguna"
        onChange={() => {}}
        onOtherChange={() => {}}
        otherValue=""
        otherValues={['ninguna']}
      />,
    )
    expect(screen.getByRole('textbox')).toBeTruthy()
  })

  it('calls onChange when switching from "otro" to another option', () => {
    const onChange = vi.fn()
    render(
      <RadioGroup
        name="q1"
        options={baseOptions}
        value="otro"
        onChange={onChange}
        onOtherChange={() => {}}
        otherValue="custom text"
      />,
    )
    const labelA = screen.getByText('Option A').closest('label')!
    fireEvent.click(labelA)
    expect(onChange).toHaveBeenCalledWith('a')
  })

  it('renders current otherValue text inside the free-text input', () => {
    render(
      <RadioGroup
        name="q1"
        options={baseOptions}
        value="otro"
        onChange={() => {}}
        onOtherChange={() => {}}
        otherValue="my custom value"
      />,
    )
    const input = screen.getByRole('textbox') as HTMLInputElement
    expect(input.value).toBe('my custom value')
  })
})
