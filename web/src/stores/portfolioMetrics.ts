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
  totalPnl: number
  dayRate: number
  totalRate: number
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

export function resolvePositionDayPnlCny(row: PositionRow): number | null {
  return finiteOrNull(row.dayPnlAggregateCny) ?? metricWithRate(row.dayPnlAggregate, row.rateToCny)
}

export function resolvePositionTotalPnlCny(row: PositionRow): number | null {
  return finiteOrNull(row.totalPnlCny) ?? metricWithRate(row.totalPnl, row.rateToCny)
}

export function calcDayPnlRate(todayPnl: number, totalValue: number): number {
  const base = totalValue - todayPnl
  if (base <= 0) return 0
  return (todayPnl / base) * 100
}

export function calcHoldingPnlRate(totalPnl: number, totalCostAbs: number): number {
  if (totalCostAbs <= 0) return 0
  return (totalPnl / totalCostAbs) * 100
}

export function buildPortfolioSummary(rows: PositionRow[]): PortfolioSummary {
  let totalValue = 0
  let totalCostAbs = 0
  let todayPnl = 0
  let totalPnl = 0

  for (const row of rows) {
    totalValue += resolvePositionValueCny(row) ?? 0
    totalCostAbs += Math.abs(resolvePositionCostCny(row) ?? 0)
    todayPnl += resolvePositionDayPnlCny(row) ?? 0
    totalPnl += resolvePositionTotalPnlCny(row) ?? 0
  }

  const floatPnl = totalValue - totalCostAbs

  return {
    totalValue,
    totalCostAbs,
    todayPnl,
    dayRate: calcDayPnlRate(todayPnl, totalValue),
    floatPnl,
    floatRate: calcHoldingPnlRate(floatPnl, totalCostAbs),
    totalPnl,
    totalRate: calcHoldingPnlRate(totalPnl, totalCostAbs)
  }
}

export function buildMarketSummaries(rows: PositionRow[]): PortfolioMarketSummary[] {
  const totals: Record<MarketCode, PortfolioMarketSummary> = {
    a: {
      market: 'a',
      name: MARKET_META.a.name,
      icon: MARKET_META.a.icon,
      mv: 0,
      cost: 0,
      dayPnl: 0,
      totalPnl: 0,
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
      totalPnl: 0,
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
      totalPnl: 0,
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
      totalPnl: 0,
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
    bucket.dayPnl += resolvePositionDayPnlCny(row) ?? 0
    bucket.totalPnl += resolvePositionTotalPnlCny(row) ?? 0
  }

  return (Object.keys(totals) as MarketCode[]).map(market => {
    const bucket = totals[market]
    return {
      ...bucket,
      dayRate: calcDayPnlRate(bucket.dayPnl, bucket.mv),
      totalRate: calcHoldingPnlRate(bucket.totalPnl, bucket.cost)
    }
  })
}
