/**
 * Pinia Stores 共享类型定义
 */

import type { MarketCode } from '@/types'

export type { MarketCode }

/** 同步域名 */
export const ALL_SYNC_DOMAINS = [
  'portfolio',
  'cash_assets',
  'other_assets',
  'liabilities',
  'history',
  'overview_all',
  'rates',
] as const

export type SyncDomain = typeof ALL_SYNC_DOMAINS[number]

/** 用户类型 */
export type User = {
  id?: string
  username?: string
  nickname?: string
  is_admin?: number | boolean
  [k: string]: unknown
}

/** 投资组合项 */
export type PortfolioItem = {
  code: string
  name?: string
  qty?: number
  price?: number
  curr?: string
  asset_type?: string
  category_type?: string
  logo_url?: string | null
  adjustment?: number
  market?: string
  // 后端口径字段（可选）
  current_price?: number
  yclose?: number
  display_cost_price?: number
  cost?: number
  raw_cost_total?: number
  value?: number
  total_pnl?: number
  total_pnl_rate?: number
  day_pnl?: number
  day_pnl_rate?: number
  day_pnl_display?: number
  day_pnl_rate_display?: number
  day_pnl_aggregate?: number
  day_pnl_rate_aggregate?: number
  nav_update_pending?: boolean
  day_pnl_display_enabled?: boolean
  day_pnl_aggregate_enabled?: boolean
  market_open?: boolean
  market_trading_day?: boolean
  market_status_reason?: string
  rate_to_cny?: number
  value_cny?: number
  cost_cny?: number
  total_pnl_cny?: number
  day_pnl_cny?: number
  day_pnl_aggregate_cny?: number
  quote_price?: number
  quote_change?: number
  quote_change_pct?: number
  quote_ready?: boolean
  quote_pending?: boolean
  [k: string]: unknown
}

/** 市场状态 */
export type MarketStatus = {
  open: boolean
  reason: string
  trading_day: boolean
}

/** 行情数据 */
export type Quote = {
  price?: number
  yclose?: number
  session?: string
  effective_session?: string
  extended_active?: boolean
  [k: string]: unknown
}

/** 行情策略 */
export type QuotePolicy = {
  interval_open_sec: number
  interval_closed_sec: number
  interval_us_extended_sec: number
}

/** Bootstrap 载荷 */
export type BootstrapPayload = {
  versions?: Partial<Record<string, string>>
  changed?: string[]
  data?: Record<string, unknown>
  market_statuses?: Partial<Record<MarketCode, Partial<MarketStatus>>>
  market_status?: Partial<Record<MarketCode, boolean>>
  quote_policy?: Partial<QuotePolicy>
}

/** Store 缓存载荷 */
export type StoreCachePayload = {
  userId: string
  savedAt: number
  quotesSavedAt?: number
  portfolio: PortfolioItem[]
  quotes: Record<string, Quote>
  rates: Record<string, number>
  marketStatus: Record<MarketCode, MarketStatus>
  allClosed: boolean
  quotePolicy: QuotePolicy
}

/** 持仓行数据（计算后） */
export type PositionRow = {
  code: string
  name?: string
  curr?: string
  market: MarketCode
  category: MarketCode
  qty: number
  costPrice: number
  rawCostPrice: number
  displayCostPrice: number
  cost: number
  rawCostTotal: number
  currentPrice: number
  yclose: number
  value: number
  valueCny?: number
  costCny?: number
  totalPnlCny?: number
  dayPnlCny?: number
  dayPnlAggregateCny?: number
  rateToCny?: number
  totalPnl: number
  dayPnl: number
  dayPnlRate: number
  dayPnlDisplay: number
  dayPnlRateDisplay: number
  dayPnlAggregate: number
  dayPnlRateAggregate: number
  totalPnlRate: number
  quotePrice?: number
  quoteChange?: number
  quoteChangePct?: number
  session: string
  marketOpen: boolean
  marketTradingDay: boolean
  marketStatusReason: string
  usExtendedActive: boolean
  navUpdatePending: boolean
  quoteReady: boolean
  quotePending: boolean
  dayPnlDisplayEnabled: boolean
  dayPnlAggregateEnabled: boolean
  asset_type?: string
  category_type?: string
  logo_url?: string | null
  [k: string]: unknown
}

/** 投资组合摘要 */
export type PortfolioSummary = {
  totalValue: number
  totalPnl: number
  todayPnl: number
  totalRate: number
}

/** 市场代码列表 */
export const MARKET_CODES: MarketCode[] = ['a', 'hk', 'us', 'fund']

/** 默认行情策略 */
export const DEFAULT_QUOTE_POLICY: QuotePolicy = {
  interval_open_sec: 5,
  interval_closed_sec: 120,
  interval_us_extended_sec: 10,
}

/** 存储键常量 */
export const STORAGE_KEYS = {
  SYNC_VERSIONS: 'web_sync_versions_v1',
  STORE_CACHE: 'web_store_cache_v1',
} as const

/** TTL 常量 */
export const CACHE_TTL = {
  STATIC: 5 * 60_000,      // 5 分钟
  QUOTES: 60_000,          // 1 分钟
} as const

/** Bootstrap 超时 */
export const AUTH_BOOTSTRAP_TIMEOUT_MS = 2500

/** Bootstrap 包含配置 */
export const SYNC_BOOTSTRAP = {
  STATIC_INCLUDE: [...ALL_SYNC_DOMAINS] as SyncDomain[],
  QUOTE_INCLUDE: ['portfolio', 'rates'] as SyncDomain[],
} as const
