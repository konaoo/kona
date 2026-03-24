import { toNumber } from './format'

export function computeDisplayCostPrice(
  price: unknown,
  qty: unknown,
  adjustment: unknown,
): number {
  const normalizedPrice = toNumber(price)
  const normalizedQty = toNumber(qty)
  const normalizedAdjustment = toNumber(adjustment)

  if (Math.abs(normalizedQty) <= 1e-9) {
    return normalizedPrice
  }

  return (normalizedPrice * normalizedQty - normalizedAdjustment) / normalizedQty
}
