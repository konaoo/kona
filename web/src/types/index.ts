/* ═══════════════════════════════════════════════════════════════
   TYPES - 类型定义主入口
   ═══════════════════════════════════════════════════════════════ */

/**
 * 市场代码类型
 */
export type MarketCode = 'a' | 'hk' | 'us' | 'fund'

/**
 * 资产类型
 */
export type AssetType = 'stock' | 'fund' | 'bond' | 'cash' | 'other'

/**
 * 币种类型
 */
export type Currency = 'CNY' | 'HKD' | 'USD' | 'EUR' | 'GBP' | 'JPY'

/**
 * 会话类型
 */
export type Session = 'pre' | 'regular' | 'post' | 'closed'

/**
 * 市场状态
 */
export type MarketStatus = {
  open: boolean
  reason: string
  trading_day: boolean
}

/**
 * 行情策略
 */
export type QuotePolicy = {
  interval_open_sec: number
  interval_closed_sec: number
  interval_us_extended_sec: number
}

/**
 * 基础 API 响应
 */
export type ApiResponse<T = unknown> = {
  data?: T
  error?: string
  message?: string
  code?: number
}

/**
 * 分页参数
 */
export type PaginationParams = {
  page?: number
  page_size?: number
  limit?: number
  offset?: number
}

/**
 * 分页响应
 */
export type PaginationResponse<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

// 导出所有类型
export * from './api'
export * from './portfolio'
export * from './quote'
export * from './user'
export * from './ui'
