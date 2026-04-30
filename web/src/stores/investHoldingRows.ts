import { buildTrendSparklinePath, type TrendItem } from '@/shared/assetTrend'
import {
  formatLatestNavDateText,
  isDateToday,
  isFundAsset,
  isStaleFund,
  readLatestNavDate
} from '@/shared/assetDisplay'
import {
  isPositionDayPnlAggregateEnabled,
  resolvePositionTotalPnlCny,
  resolvePositionValueCny
} from '@/stores/portfolioMetrics'

type RawHoldingRow = Record<string, any>

export { formatLatestNavDateText, isDateToday, isFundAsset, isStaleFund, readLatestNavDate }

export type InvestHoldingDisplayRow = RawHoldingRow & {
  qty: number
  amount: number
  costPrice: number
  cost: number
  mv: number
  mvCny: number
  dayPnl: number
  dayPnlRaw: number
  dayPnlVisible: boolean
  totalPnl: number
  totalPnlRaw: number
  dayPnlRate: number
  totalPnlRate: number
  pct: number
  price: number
  curr: string
  rateToCny: number
  market: string
  category: string
  unit: string
  quoteReady: boolean
  quotePending: boolean
  navUpdatePending: boolean
  marketOpen: boolean
  marketTradingDay: boolean
  marketStatusReason: string
  dayPnlAggregateEnabled: boolean
  currentDayPnlSortValue: number | null
  spark: string
  sparkReady: boolean
}

export type BuildInvestHoldingRowsOptions = {
  rows: RawHoldingRow[]
  selectedTab: string
  totalMarketValue: number
  trendMap: Record<string, TrendItem>
  now?: Date
}

export function buildInvestHoldingRows({
  rows,
  selectedTab,
  totalMarketValue,
  trendMap,
  now = new Date()
}: BuildInvestHoldingRowsOptions): InvestHoldingDisplayRow[] {
  const baseRows =
    selectedTab === 'all'
      ? rows || []
      : (rows || []).filter(row => (row.category || row.market) === selectedTab)

  return baseRows
    .map(row => {
      const qty = Number(row.qty) || 0
      const currentPrice = Number(row.currentPrice) || 0
      const displayCostPrice = Number(row.displayCostPrice) || 0
      const mv = Number(row.value) || 0
      const cost = Number(row.cost) || 0
      const totalPnlRate = Number(row.totalPnlRate) || 0
      const mvCny = resolvePositionValueCny(row as any) ?? 0
      const pct = (mvCny / (totalMarketValue || 1)) * 100
      const dayPnlVisible =
        !isStaleFund(row) &&
        !Boolean(row.navUpdatePending) &&
        !Boolean(row.quotePending) &&
        isPositionDayPnlAggregateEnabled(row as any)
      const dayPnl = dayPnlVisible
        ? Number(row.dayPnlAggregateCny ?? row.dayPnlAggregate ?? 0) || 0
        : 0
      const dayPnlRaw = dayPnlVisible ? Number(row.dayPnlAggregate ?? 0) || 0 : 0
      const code = String(row.code || '')

      return {
        ...row,
        logo_url: row.logo_url,
        asset_type: row.asset_type,
        qty,
        amount: qty,
        costPrice: displayCostPrice,
        cost,
        mv,
        mvCny,
        dayPnl,
        dayPnlRaw,
        dayPnlVisible,
        totalPnl: resolvePositionTotalPnlCny(row as any) ?? 0,
        totalPnlRaw: Number(row.totalPnl) || 0,
        dayPnlRate: Number(row.dayPnlRateAggregate ?? row.dayPnlRate) || 0,
        totalPnlRate,
        pct,
        price: currentPrice || 0,
        curr: String(row.curr || 'CNY'),
        rateToCny: Number(row.rateToCny) || 1,
        market: String(row.market || ''),
        category: String(row.category || row.market || ''),
        unit: String(row.unit || (isFundAsset(row) ? '份' : '股')),
        quoteReady: Boolean(row.quoteReady),
        quotePending: Boolean(row.quotePending),
        navUpdatePending: Boolean(row.navUpdatePending),
        marketOpen: Boolean(row.marketOpen),
        marketTradingDay: Boolean(row.marketTradingDay),
        marketStatusReason: String(row.marketStatusReason || ''),
        dayPnlAggregateEnabled: row.dayPnlAggregateEnabled !== false,
        currentDayPnlSortValue: resolveCurrentDayPnlSortValue(row, now),
        spark: buildTrendSparklinePath(trendMap[code]?.points || []),
        sparkReady: (trendMap[code]?.points || []).length >= 2
      }
    })
    .sort(compareCurrentDayPnlDesc)
}

export function compareCurrentDayPnlDesc(
  a: Pick<InvestHoldingDisplayRow, 'currentDayPnlSortValue'>,
  b: Pick<InvestHoldingDisplayRow, 'currentDayPnlSortValue'>
): number {
  const pnlA = a.currentDayPnlSortValue
  const pnlB = b.currentDayPnlSortValue
  if (pnlA == null && pnlB == null) return 0
  if (pnlA == null) return 1
  if (pnlB == null) return -1
  return pnlB - pnlA
}

export function resolveCurrentDayPnlSortValue(row: RawHoldingRow, now = new Date()): number | null {
  if (isPreopenOffHoursRow(row, now)) return 0
  if (row?.navUpdatePending === true) return null
  if (row?.dayPnlAggregateEnabled === false) return null
  const yclose = Number(row?.yclose) || 0
  if (yclose <= 0) return null
  const currentPrice = Number(row?.currentPrice) || 0
  const qty = Number(row?.qty) || 0
  const rateToCny = Number(row?.rateToCny) || 1
  return (currentPrice - yclose) * qty * rateToCny
}

export function isPreopenOffHoursRow(row: RawHoldingRow, now = new Date()): boolean {
  const market = String(row?.market || '')
    .trim()
    .toLowerCase()
  if (market !== 'a' && market !== 'hk' && market !== 'fund') return false
  if (row?.marketOpen === true) return false
  if (row?.marketTradingDay !== true) return false
  if (
    String(row?.marketStatusReason || '')
      .trim()
      .toLowerCase() !== 'off_hours'
  ) {
    return false
  }
  const minutes = now.getHours() * 60 + now.getMinutes()
  return minutes < 9 * 60 + 30
}
