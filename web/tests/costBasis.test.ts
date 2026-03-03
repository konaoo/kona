import { describe, expect, it } from 'vitest'
import { computeDisplayCostPrice } from '../src/shared/costBasis'

describe('computeDisplayCostPrice', () => {
  it('calculates diluted cost after partial profit taking', () => {
    expect(computeDisplayCostPrice(10, 100, 200)).toBeCloseTo(8, 8)
  })

  it('keeps negative diluted cost when realized gain exceeds principal', () => {
    expect(computeDisplayCostPrice(10, 60, 800)).toBeCloseTo(-3.3333333333, 8)
  })

  it('falls back to raw cost when qty is zero', () => {
    expect(computeDisplayCostPrice(10, 0, 999)).toBeCloseTo(10, 8)
  })
})
