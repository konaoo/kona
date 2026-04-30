/**
 * Pinia Stores 共享类型定义
 */

import {
  GENERATED_AUTH_BOOTSTRAP_TIMEOUT_MS,
  GENERATED_QUOTE_POLICY_DEFAULT,
  GENERATED_SYNC_BOOTSTRAP_DOMAINS,
  GENERATED_SYNC_BOOTSTRAP_QUOTE_INCLUDE,
  GENERATED_WEB_CACHE_TTL_MS,
  type GeneratedSyncDomain
} from './generated_sync_contract'

export type MarketCode = 'a' | 'hk' | 'us' | 'fund'

/** 同步域名 */
export const ALL_SYNC_DOMAINS = GENERATED_SYNC_BOOTSTRAP_DOMAINS

export type SyncDomain = GeneratedSyncDomain

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
  total_pnl_base?: number
  total_pnl_rate?: number
  day_pnl?: number
  day_pnl_base?: number
  day_pnl_rate?: number
  day_pnl_display?: number
  day_pnl_base_display?: number
  day_pnl_rate_display?: number
  day_pnl_aggregate?: number
  day_pnl_base_aggregate?: number
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
  total_pnl_base_cny?: number
  day_pnl_cny?: number
  day_pnl_base_cny?: number
  day_pnl_aggregate_cny?: number
  day_pnl_base_aggregate_cny?: number
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
  totalPnlBase?: number
  totalPnlBaseCny?: number
  dayPnlCny?: number
  dayPnlBase?: number
  dayPnlBaseCny?: number
  dayPnlAggregateCny?: number
  dayPnlBaseAggregateCny?: number
  rateToCny?: number
  totalPnl: number
  dayPnl: number
  dayPnlRate: number
  dayPnlDisplay: number
  dayPnlBaseDisplay?: number
  dayPnlRateDisplay: number
  dayPnlAggregate: number
  dayPnlBaseAggregate: number
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
  totalCostAbs: number
  todayPnl: number
  dayRate: number
  floatPnl: number
  floatRate: number
  totalPnl: number
  totalRate: number
}

export type RealtimeTodayPayload = {
  effective_date?: string
  source?: string
  scope?: {
    ledger_id?: number | null
    mode?: string
  }
  totals?: {
    total_asset?: number
    total_market_value?: number
    total_cash?: number
    total_other?: number
    total_liability?: number
    total_pnl?: number
    total_pnl_rate?: number
    day_pnl?: number
    day_pnl_base?: number
    day_pnl_rate?: number
  }
  breakdown_by_market?: Record<string, {
    day_pnl?: number
    day_pnl_base?: number
  }>
  generated_at?: string
}

/** 市场代码列表 */
export const MARKET_CODES: MarketCode[] = ['a', 'hk', 'us', 'fund']

/** 默认行情策略 */
export const DEFAULT_QUOTE_POLICY: QuotePolicy = {
  interval_open_sec: GENERATED_QUOTE_POLICY_DEFAULT.interval_open_sec,
  interval_closed_sec: GENERATED_QUOTE_POLICY_DEFAULT.interval_closed_sec,
  interval_us_extended_sec: GENERATED_QUOTE_POLICY_DEFAULT.interval_us_extended_sec
}

/** 存储键常量 */
export const STORAGE_KEYS = {
  SYNC_VERSIONS: 'web_sync_versions_v1',
  STORE_CACHE: 'web_store_cache_v1'
} as const

/** TTL 常量 */
export const CACHE_TTL = {
  STATIC: GENERATED_WEB_CACHE_TTL_MS.STATIC,
  QUOTES: GENERATED_WEB_CACHE_TTL_MS.QUOTES
} as const

/** Bootstrap 超时 */
export const AUTH_BOOTSTRAP_TIMEOUT_MS = GENERATED_AUTH_BOOTSTRAP_TIMEOUT_MS

/** Bootstrap 包含配置 */
export const SYNC_BOOTSTRAP = {
  STATIC_INCLUDE: [...ALL_SYNC_DOMAINS] as SyncDomain[],
  QUOTE_INCLUDE: [...GENERATED_SYNC_BOOTSTRAP_QUOTE_INCLUDE] as SyncDomain[]
} as const
