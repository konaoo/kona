/* ═══════════════════════════════════════════════════════════════
   QUOTE TYPES - 行情类型定义
   ═══════════════════════════════════════════════════════════════ */

import type { MarketCode, Session } from './index'

/**
 * 实时行情
 */
export type RealtimeQuote = {
  code: string
  name?: string
  price: number
  yclose: number
  change: number
  change_rate: number
  session: Session
  effective_session?: Session
  extended_active?: boolean
  volume?: number
  market?: MarketCode
  currency?: string
  timestamp?: number
}

/**
 * 批量行情响应
 */
export type QuotesBatchResponse = Record<string, RealtimeQuote>

/**
 * 行情状态
 */
export type QuoteStatus = 'active' | 'delayed' | 'pre_market' | 'after_hours' | 'closed'

/**
 * 行情刷新策略
 */
export type QuoteRefreshStrategy = {
  interval_open: number // 市场开放时的刷新间隔（秒）
  interval_closed: number // 市场关闭时的刷新间隔（秒）
  interval_extended: number // 盘前盘后时的刷新间隔（秒）
}

/**
 * 价格方向
 */
export type PriceDirection = 'up' | 'down' | 'unchanged'

/**
 * 价格变动
 */
export type PriceChange = {
  direction: PriceDirection
  amount: number
  percentage: number
}

/**
 * K线数据
 */
export type KlineData = {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

/**
 * 分时数据
 */
export type IntradayData = {
  time: string
  price: number
  volume: number
}

/**
 * 涨跌榜统计
 */
export type TopMover = {
  code: string
  name: string
  change_rate: number
  volume?: number
  amount?: number
}

/**
 * 市场概览
 */
export type MarketOverview = {
  index_code: string
  index_name: string
  price: number
  change_rate: number
  volume?: number
}

/**
 * 股票搜索结果
 */
export type StockSearchResult = {
  code: string
  name: string
  market: MarketCode
  market_name: string
  currency: string
  type: string
}

/**
 * 股票详情
 */
export type StockDetail = {
  code: string
  name: string
  market: MarketCode
  currency: string
  lot_size?: number
  tick_size?: number
  is_trading: boolean
}

/**
 * 价格提醒
 */
export type PriceAlert = {
  id: string
  code: string
  alert_type: 'above' | 'below'
  target_price: number
  current_price: number
  triggered: boolean
  created_at: string
}

/**
 * 历史价格数据
 */
export type HistoricalPrice = {
  date: string
  open: number
  high: number
  low: number
  close: number
  adjusted_close: number
  volume: number
}
