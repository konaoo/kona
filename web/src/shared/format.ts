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
  const raw = String(value).trim()
  if (!raw) return '-'
  const hasTimezone = /[zZ]|[+-]\d{2}:\d{2}$/.test(raw)
  const normalized = hasTimezone ? raw : `${raw.replace(' ', 'T')}Z`
  const d = new Date(normalized)
  if (Number.isNaN(d.getTime())) return String(value)
  const parts = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).formatToParts(d)
  const map = new Map(parts.map((part) => [part.type, part.value]))
  const y = map.get('year') || '0000'
  const m = map.get('month') || '00'
  const day = map.get('day') || '00'
  const hh = map.get('hour') || '00'
  const mm = map.get('minute') || '00'
  const ss = map.get('second') || '00'
  return `${y}/${m}/${day} ${hh}:${mm}:${ss}`
}
