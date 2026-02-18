export function toNumber(value: unknown, fallback = 0): number {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

export function money(value: number, curr = 'CNY'): string {
  try {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: curr,
      maximumFractionDigits: 2,
    }).format(value)
  } catch {
    return `${curr} ${value.toFixed(2)}`
  }
}

export function marketDisplayCurrency(market: unknown, curr?: unknown): 'CNY' | 'HKD' | 'USD' {
  const marketCode = String(market || '').toLowerCase()
  if (marketCode === 'a') return 'CNY'
  if (marketCode === 'hk') return 'HKD'
  if (marketCode === 'us') return 'USD'
  if (marketCode === 'fund') {
    const fundCurr = String(curr || '').toUpperCase()
    if (fundCurr === 'USD' || fundCurr === 'HKD' || fundCurr === 'CNY') {
      return fundCurr
    }
    return 'CNY'
  }
  const fallbackCurr = String(curr || '').toUpperCase()
  if (fallbackCurr === 'USD' || fallbackCurr === 'HKD') {
    return fallbackCurr
  }
  return 'CNY'
}

export function pct(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

export function shortDateTime(value: unknown): string {
  if (!value) return '-'
  const d = new Date(String(value))
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleString('zh-CN', { hour12: false })
}
