/* ═══════════════════════════════════════════════════════════════
   PORTFOLIO TYPES - 投资组合类型定义
   ═══════════════════════════════════════════════════════════════ */

import type { MarketCode, Session } from './index'

/**
 * 持仓行（计算后）
 */
export type PositionRow = {
  // 基础信息
  code: string
  name?: string
  market: MarketCode
  category?: MarketCode
  asset_type: string
  category_type?: string
  qty: number
  costPrice: number
  displayCostPrice: number
  currentPrice: number
  yclose: number

  // 价值相关
  value: number
  cost: number
  totalPnl: number
  totalPnlRate: number

  // 今日盈亏
  dayPnl: number
  dayPnlRate: number
  dayPnlDisplay: number
  dayPnlRateDisplay: number
  dayPnlAggregate: number
  dayPnlRateAggregate: number

  // 市场状态
  marketOpen: boolean
  marketTradingDay: boolean
  marketStatusReason: string
  usExtendedActive: boolean
  session: Session
  navUpdatePending: boolean
  dayPnlDisplayEnabled: boolean
  dayPnlAggregateEnabled: boolean

  // 其他
  adjustment?: number
  [key: string]: unknown
}

/**
 * 市场分组统计
 */
export type MarketGroup = {
  key: MarketCode
  name: string
  icon: string
  mv: number // 市值
  day_pnl: number // 今日盈亏
  day_rate: number // 今日涨跌
  float_pnl: number // 持仓盈亏
  float_rate: number // 持仓收益率
  total_pnl: number // 累计盈亏
  total_rate: number // 累计收益率
}

/**
 * 资产分布项
 */
export type AllocationItem = {
  market: MarketCode
  name: string
  color: string
  value: number
  percentage: number
}

/**
 * 期间统计
 */
export type PeriodStats = {
  label: string
  pnl: number
  rate: number
}

/**
 * 投资组合摘要
 */
export type PortfolioSummary = {
  totalValue: number
  totalCost: number
  totalPnl: number
  todayPnl: number
  totalRate: number
}

/**
 * 资产分类统计
 */
export type AssetClassStats = {
  cash: number
  invest: {
    mv: number
    pnl: number
  }
  other: number
}

/**
 * 顶部排名项
 */
export type RankingItem = {
  code: string
  name: string
  pnl: number
  rate: string
  rank: number
}

/**
 * 持仓筛选条件
 */
export type PositionFilter = {
  market?: MarketCode
  search?: string
  sort_by?: 'code' | 'value' | 'day_pnl' | 'total_pnl'
  sort_order?: 'asc' | 'desc'
}

/**
 * 持仓分页
 */
export type PositionPagination = {
  page: number
  page_size: number
  total: number
}

/**
 * 导出格式
 */
export type ExportFormat = 'xlsx' | 'csv' | 'json'

/**
 * 导出选项
 */
export type ExportOptions = {
  format: ExportFormat
  include_cost_basis: boolean
  include_history: boolean
  date_range?: {
    start: string
    end: string
  }
}
