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
  asset_type: string
  qty: number
  cost_price: number
  display_cost_price: number
  current_price: number
  yclose: number

  // 价值相关
  value: number
  cost: number
  total_pnl: number
  total_pnl_rate: number

  // 今日盈亏
  day_pnl: number
  day_pnl_rate: number
  day_pnl_display: number
  day_pnl_rate_display: number
  day_pnl_aggregate: number
  day_pnl_rate_aggregate: number

  // 市场状态
  market_open: boolean
  market_trading_day: boolean
  market_status_reason: string
  us_extended_active: boolean
  session: Session
  nav_update_pending: boolean
  day_pnl_display_enabled: boolean
  day_pnl_aggregate_enabled: boolean

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
  total_value: number
  total_cost: number
  total_pnl: number
  today_pnl: number
  total_rate: number
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
