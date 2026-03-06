/* ═══════════════════════════════════════════════════════════════
   API TYPES - API 接口类型定义
   ═══════════════════════════════════════════════════════════════ */

import type { Currency, MarketCode, MarketStatus, QuotePolicy, Session } from './index'
import type { User } from './user'

/**
 * 登录请求
 */
export type LoginRequest = {
  username: string
  password: string
}

/**
 * 登录响应
 */
export type LoginResponse = {
  access_token: string
  refresh_token: string
  user: User
}

/**
 * 注册请求
 */
export type RegisterRequest = {
  username: string
  password: string
  invite_code: string
}

/**
 * Bootstrap 请求
 */
export type BootstrapRequest = {
  include: SyncDomain[]
  client_versions: Partial<Record<SyncDomain, string>>
}

/**
 * 同步域
 */
export type SyncDomain =
  | 'portfolio'
  | 'cash_assets'
  | 'other_assets'
  | 'liabilities'
  | 'history'
  | 'overview_all'
  | 'rates'

/**
 * Bootstrap 响应
 */
export type BootstrapResponse = {
  versions?: Partial<Record<SyncDomain, string>>
  changed?: SyncDomain[]
  data?: Record<string, unknown>
  market_statuses?: Partial<Record<MarketCode, MarketStatus>>
  market_status?: Partial<Record<MarketCode, boolean>>
  quote_policy?: QuotePolicy
}

/**
 * 投资组合项
 */
export type PortfolioItem = {
  code: string
  name?: string
  qty: number
  price: number
  curr?: Currency
  asset_type?: string
  adjustment?: number
  market?: MarketCode
  [key: string]: unknown
}

/**
 * 行情数据
 */
export type Quote = {
  price?: number
  yclose?: number
  session?: Session
  effective_session?: Session
  extended_active?: boolean
  change?: number
  change_rate?: number
  [key: string]: unknown
}

/**
 * 批量行情请求
 */
export type BatchQuotesRequest = {
  codes: string[]
}

/**
 * 批量行情响应
 */
export type BatchQuotesResponse = Record<string, Quote>

/**
 * 汇率响应
 */
export type RatesResponse = Record<string, number>

/**
 * 市场状态响应
 */
export type MarketStatusResponse = {
  markets?: Partial<Record<MarketCode, MarketStatus>>
  all_closed?: boolean
}

/**
 * 历史记录类型
 */
export type HistoryType = 'trade' | 'dividend' | 'split' | 'transfer'

/**
 * 历史记录项
 */
export type HistoryItem = {
  id?: string
  type: HistoryType
  code: string
  date: string
  qty?: number
  price?: number
  amount?: number
  note?: string
  created_at?: string
}

/**
 * 新闻分类
 */
export type NewsCategory = 'macro' | 'company' | 'trade' | 'policy'

/**
 * 新闻影响
 */
export type NewsImpact = 'up' | 'down' | 'neu'

/**
 * 新闻项
 */
export type NewsItem = {
  id: string
  category: NewsCategory
  source: string
  title: string
  summary: string
  symbol?: string
  impact_text: string
  impact: NewsImpact
  important: boolean
  published_at: string
  created_at?: string
}

/**
 * 收益记录
 */
export type PnLRecord = {
  date: string
  pnl: number
  rate: number
  cost: number
  value: number
}

/**
 * 账户类型
 */
export type AccountType = 'cash' | 'other' | 'debt'

/**
 * 资金账户
 */
export type CashAccount = {
  id: string
  name: string
  type: AccountType
  currency: Currency
  amount: number
  emoji?: string
  color?: string
  created_at?: string
}

/**
 * 添加资产请求
 */
export type AddAssetRequest = {
  code: string
  market: MarketCode
  qty: number
  price: number
  account_id?: string
}

/**
 * 更新资产请求
 */
export type UpdateAssetRequest = {
  id: string
  qty?: number
  price?: number
  adjustment?: number
}

/**
 * 删除资产请求
 */
export type DeleteAssetRequest = {
  id: string
}

/**
 * Web 配置
 */
export type WebConfig = {
  apk_download_url?: string
  ios_qr_text?: string
  ios_qr_image_url?: string
}

/**
 * API 错误响应
 */
export type ApiErrorResponse = {
  error: string
  code?: number
  message?: string
}
