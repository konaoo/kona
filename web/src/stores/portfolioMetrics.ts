import type { MarketCode, PortfolioSummary, PositionRow } from './types'

const MARKET_META: Record<MarketCode, { name: string; icon: string }> = {
  a: { name: 'A股', icon: '🇨🇳' },
  hk: { name: '港股', icon: '🇭🇰' },
  us: { name: '美股', icon: '🇺🇸' },
  fund: { name: '基金', icon: '📈' }
}

export type PortfolioMarketSummary = {
  market: MarketCode
  name: string
  icon: string
  mv: number
  cost: number
  dayPnl: number
  dayPnlEnabled: boolean
  totalPnl: number
  dayRate: number
  totalRate: number
}

type PortfolioMarketBucket = PortfolioMarketSummary & {
  dayPnlBase: number
  dayPnlEnabledCount: number
  totalPnlDenominator: number
}

function finiteOrNull(value: unknown): number | null {
  if (typeof value !== 'number' || !Number.isFinite(value)) return null
  return value
}

function metricWithRate(value: unknown, rateToCny: unknown): number | null {
  const metric = finiteOrNull(value)
  if (metric == null) return null
  const rate = finiteOrNull(rateToCny)
  if (rate != null && rate > 0) return metric * rate
  return metric
}

export function resolvePositionValueCny(row: PositionRow): number | null {
  return finiteOrNull(row.valueCny) ?? metricWithRate(row.value, row.rateToCny)
}

export function resolvePositionCostCny(row: PositionRow): number | null {
  return finiteOrNull(row.costCny) ?? metricWithRate(row.cost, row.rateToCny)
}

export function resolvePositionTotalPnlDenominatorCny(row: PositionRow): number | null {
  const fallbackCostCny = resolvePositionCostCny(row)
  return (
    finiteOrNull(row.totalPnlBaseCny) ??
    metricWithRate(row.totalPnlBase, row.rateToCny) ??
    (fallbackCostCny == null ? null : Math.abs(fallbackCostCny)) ??
    null
  )
}

export function resolvePositionDayPnlBaseCny(row: PositionRow): number | null {
  return (
    finiteOrNull(row.dayPnlBaseAggregateCny) ??
    metricWithRate(row.dayPnlBaseAggregate, row.rateToCny) ??
    null
  )
}

export function resolvePositionDayPnlCny(row: PositionRow): number | null {
  return finiteOrNull(row.dayPnlAggregateCny) ?? metricWithRate(row.dayPnlAggregate, row.rateToCny)
}

export function isPositionDayPnlAggregateEnabled(row: PositionRow): boolean {
  return row.dayPnlAggregateEnabled !== false
}

export function resolvePositionTotalPnlCny(row: PositionRow): number | null {
  return finiteOrNull(row.totalPnlCny) ?? metricWithRate(row.totalPnl, row.rateToCny)
}

export function calcDayPnlRate(todayPnl: number, dayPnlBase: number): number {
  if (dayPnlBase <= 0) return 0
  return (todayPnl / dayPnlBase) * 100
}

export function calcHoldingPnlRate(totalPnl: number, totalCostAbs: number): number {
  if (totalCostAbs <= 0) return 0
  return (totalPnl / totalCostAbs) * 100
}

export function buildPortfolioSummary(rows: PositionRow[]): PortfolioSummary {
  let totalValue = 0
  let totalCostAbs = 0
  let totalDayPnlBase = 0
  let totalPnlDenominator = 0
  let todayPnl = 0
  let totalPnl = 0

  for (const row of rows) {
    totalValue += resolvePositionValueCny(row) ?? 0
    totalCostAbs += Math.abs(resolvePositionCostCny(row) ?? 0)
    totalPnlDenominator += resolvePositionTotalPnlDenominatorCny(row) ?? 0
    totalPnl += resolvePositionTotalPnlCny(row) ?? 0

    if (isPositionDayPnlAggregateEnabled(row)) {
      totalDayPnlBase += resolvePositionDayPnlBaseCny(row) ?? 0
      todayPnl += resolvePositionDayPnlCny(row) ?? 0
    }
  }

  const floatPnl = totalValue - totalCostAbs

  return {
    totalValue,
    totalCostAbs,
    todayPnl,
    dayRate: calcDayPnlRate(todayPnl, totalDayPnlBase),
    floatPnl,
    floatRate: calcHoldingPnlRate(floatPnl, totalCostAbs),
    totalPnl,
    totalRate: calcHoldingPnlRate(totalPnl, totalPnlDenominator)
  }
}

export function buildMarketSummaries(rows: PositionRow[]): PortfolioMarketSummary[] {
  const totals: Record<MarketCode, PortfolioMarketBucket> = {
    a: {
      market: 'a',
      name: MARKET_META.a.name,
      icon: MARKET_META.a.icon,
      mv: 0,
      cost: 0,
      dayPnl: 0,
      dayPnlEnabled: false,
      dayPnlBase: 0,
      dayPnlEnabledCount: 0,
      totalPnl: 0,
      totalPnlDenominator: 0,
      dayRate: 0,
      totalRate: 0
    },
    hk: {
      market: 'hk',
      name: MARKET_META.hk.name,
      icon: MARKET_META.hk.icon,
      mv: 0,
      cost: 0,
      dayPnl: 0,
      dayPnlEnabled: false,
      dayPnlBase: 0,
      dayPnlEnabledCount: 0,
      totalPnl: 0,
      totalPnlDenominator: 0,
      dayRate: 0,
      totalRate: 0
    },
    us: {
      market: 'us',
      name: MARKET_META.us.name,
      icon: MARKET_META.us.icon,
      mv: 0,
      cost: 0,
      dayPnl: 0,
      dayPnlEnabled: false,
      dayPnlBase: 0,
      dayPnlEnabledCount: 0,
      totalPnl: 0,
      totalPnlDenominator: 0,
      dayRate: 0,
      totalRate: 0
    },
    fund: {
      market: 'fund',
      name: MARKET_META.fund.name,
      icon: MARKET_META.fund.icon,
      mv: 0,
      cost: 0,
      dayPnl: 0,
      dayPnlEnabled: false,
      dayPnlBase: 0,
      dayPnlEnabledCount: 0,
      totalPnl: 0,
      totalPnlDenominator: 0,
      dayRate: 0,
      totalRate: 0
    }
  }

  for (const row of rows) {
    const market = row.category || row.market
    if (!market || !(market in totals)) continue
    const bucket = totals[market]
    bucket.mv += resolvePositionValueCny(row) ?? 0
    bucket.cost += Math.abs(resolvePositionCostCny(row) ?? 0)
    bucket.totalPnl += resolvePositionTotalPnlCny(row) ?? 0
    bucket.totalPnlDenominator += resolvePositionTotalPnlDenominatorCny(row) ?? 0

    if (isPositionDayPnlAggregateEnabled(row)) {
      bucket.dayPnl += resolvePositionDayPnlCny(row) ?? 0
      bucket.dayPnlBase += resolvePositionDayPnlBaseCny(row) ?? 0
      bucket.dayPnlEnabledCount += 1
      bucket.dayPnlEnabled = true
    }
  }

  return (Object.keys(totals) as MarketCode[]).map(market => {
    const bucket = totals[market]
    const { dayPnlBase, dayPnlEnabledCount, totalPnlDenominator, ...summary } = bucket
    return {
      ...summary,
      dayRate: calcDayPnlRate(bucket.dayPnl, dayPnlBase),
      dayPnlEnabled: dayPnlEnabledCount > 0,
      totalRate: calcHoldingPnlRate(bucket.totalPnl, totalPnlDenominator)
    }
  })
}
