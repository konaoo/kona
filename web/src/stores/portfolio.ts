/**
 * Portfolio Store - 投资组合数据管理
 */

import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/shared/http'
import { toNumber } from '@/shared/format'
import { computeDisplayCostPrice } from '@/shared/costBasis'
import type {
  MarketCode,
  PortfolioItem,
  PositionRow,
  PortfolioSummary,
} from './types'
import { useMarketStore } from './market'
import { useQuoteStore } from './quote'

export const usePortfolioStore = defineStore('portfolio', () => {
  // ───────────────────────────────────────────────────────────────
  // State
  // ───────────────────────────────────────────────────────────────

  const portfolio = ref<PortfolioItem[]>([])
  const loading = ref(false)

  // ───────────────────────────────────────────────────────────────
  // Computed
  // ───────────────────────────────────────────────────────────────

  /**
   * Rows - 计算后的持仓行数据
   */
  const rows = computed<PositionRow[]>(() => {
    const marketStore = useMarketStore()
    const quoteStore = useQuoteStore()

    return portfolio.value.map((item) => {
      const quote = quoteStore.quotes[item.code] || {}
      const qty = toNumber(item.qty)
      const rawCostPrice = toNumber(item.price)
      const yclose = toNumber(quote.yclose)

      const currentPrice = firstPositiveNumber(
        quote.price,
        quote.regular_price,
        quote.premarket_price,
        quote.after_hours_price,
        yclose,
        rawCostPrice
      )

      const adjustment = toNumber(item.adjustment)
      const market = inferMarket(item)
      const marketStatus = marketStore.marketStatus[market]
      const open = Boolean(marketStatus?.open)
      const marketTradingDay = Boolean(marketStatus?.trading_day)
      const navUpdatePending = isNavUpdatePendingAsset(item)

      const effectiveSession = normalizeSession(quote.effective_session ?? quote.session)
      const usExtendedActive =
        market === 'us' &&
        (Boolean(quote.extended_active) || effectiveSession === 'pre' || effectiveSession === 'post')

      const dayPnlDisplayEnabled = !navUpdatePending && currentPrice > 0 && yclose > 0
      const dayPnlAggregateEnabled = dayPnlDisplayEnabled && (marketTradingDay || usExtendedActive)

      const value = currentPrice * qty
      const cost = rawCostPrice * qty
      const displayCostPrice = computeDisplayCostPrice(rawCostPrice, qty, adjustment)
      const totalPnl = value - cost + adjustment
      const dayPnlDisplay = dayPnlDisplayEnabled ? (currentPrice - yclose) * qty : 0
      const dayPnlRateDisplay = dayPnlDisplayEnabled ? ((currentPrice - yclose) / yclose) * 100 : 0
      const dayPnlAggregate = dayPnlAggregateEnabled ? dayPnlDisplay : 0
      const dayPnlRateAggregate = dayPnlAggregateEnabled ? dayPnlRateDisplay : 0
      const totalPnlRate = Math.abs(cost) > 0 ? (totalPnl / Math.abs(cost)) * 100 : 0

      return {
        ...item,
        market,
        qty,
        costPrice: rawCostPrice,
        rawCostPrice,
        displayCostPrice,
        currentPrice,
        yclose,
        value,
        totalPnl,
        dayPnl: dayPnlDisplay,
        dayPnlRate: dayPnlRateDisplay,
        dayPnlDisplay,
        dayPnlRateDisplay,
        dayPnlAggregate,
        dayPnlRateAggregate,
        totalPnlRate,
        session: effectiveSession,
        marketOpen: open,
        marketTradingDay,
        marketStatusReason: marketStatus?.reason || '',
        usExtendedActive,
        navUpdatePending,
        dayPnlDisplayEnabled,
        dayPnlAggregateEnabled,
      }
    })
  })

  /**
   * Summary - 投资组合摘要
   */
  const summary = computed<PortfolioSummary>(() => {
    const totalValue = rows.value.reduce((sum, row) => sum + row.value, 0)
    const totalPnl = rows.value.reduce((sum, row) => sum + row.totalPnl, 0)
    const todayPnl = rows.value.reduce((sum, row) => sum + row.dayPnlAggregate, 0)
    const totalCostAbs = rows.value.reduce((sum, row) => sum + Math.abs(row.costPrice * row.qty), 0)

    return {
      totalValue,
      totalPnl,
      todayPnl,
      totalRate: totalCostAbs > 0 ? (totalPnl / totalCostAbs) * 100 : 0,
    }
  })

  /**
   * GroupedByMarket - 按市场分组的持仓
   */
  const groupedByMarket = computed(() => {
    const groups: Record<MarketCode, PositionRow[]> = {
      a: [],
      hk: [],
      us: [],
      fund: [],
    }

    for (const row of rows.value) {
      groups[row.market].push(row)
    }

    return groups
  })

  // ───────────────────────────────────────────────────────────────
  // Helpers
  // ───────────────────────────────────────────────────────────────

  /**
   * InferMarket - 推断市场
   */
  function inferMarket(item: PortfolioItem): MarketCode {
    const kind = String(item.asset_type || '').toLowerCase()
    if (kind === 'hk') return 'hk'
    if (kind === 'us') return 'us'
    if (kind === 'fund') return 'fund'
    if (kind === 'a') return 'a'

    const code = String(item.code || '').toLowerCase()
    if (code.startsWith('hk')) return 'hk'
    if (code.startsWith('gb_') || /^[a-z][a-z.\-]*$/i.test(code)) return 'us'
    if (code.startsWith('f_') || code.startsWith('ft_')) return 'fund'
    return 'a'
  }

  /**
   * IsNavUpdatePendingAsset - 是否是 NAV 待更新资产
   */
  function isNavUpdatePendingAsset(item: PortfolioItem): boolean {
    const code = String(item.code || '').trim().toLowerCase()
    return code.startsWith('f_') || code.startsWith('ft_')
  }

  /**
   * FirstPositiveNumber - 获取第一个正数
   */
  function firstPositiveNumber(...values: unknown[]): number {
    for (const value of values) {
      const n = Number(value)
      if (Number.isFinite(n) && n > 0) {
        return n
      }
    }
    return 0
  }

  /**
   * NormalizeSession - 标准化会话
   */
  function normalizeSession(raw: unknown): string {
    const text = String(raw || '').trim().toLowerCase()
    if (text === 'pre' || text === 'post' || text === 'regular') return text
    return 'closed'
  }

  // ───────────────────────────────────────────────────────────────
  // Actions
  // ───────────────────────────────────────────────────────────────

  /**
   * LoadPortfolio - 加载投资组合
   */
  async function loadPortfolio() {
    loading.value = true
    try {
      const items = await api.get<PortfolioItem[]>('/api/portfolio?type=all', true)
      portfolio.value = Array.isArray(items) ? items : []
    } finally {
      loading.value = false
    }
  }

  /**
   * UpdatePortfolioItem - 更新单个持仓项
   */
  function updatePortfolioItem(code: string, updates: Partial<PortfolioItem>) {
    const index = portfolio.value.findIndex(item => item.code === code)
    if (index !== -1) {
      portfolio.value[index] = { ...portfolio.value[index], ...updates } as PortfolioItem
    }
  }

  /**
   * RemovePortfolioItem - 移除持仓项
   */
  function removePortfolioItem(code: string) {
    const index = portfolio.value.findIndex(item => item.code === code)
    if (index !== -1) {
      portfolio.value.splice(index, 1)
    }
  }

  /**
   * AddPortfolioItem - 添加持仓项
   */
  function addPortfolioItem(item: PortfolioItem) {
    portfolio.value.push(item)
  }

  /**
   * GetPortfolioItem - 获取持仓项
   */
  function getPortfolioItem(code: string): PortfolioItem | undefined {
    return portfolio.value.find(item => item.code === code)
  }

  /**
   * ClearPortfolio - 清空投资组合
   */
  function clearPortfolio() {
    portfolio.value = []
  }

  // ───────────────────────────────────────────────────────────────
  // Return
  // ───────────────────────────────────────────────────────────────

  return {
    // State
    portfolio,
    loading,

    // Computed
    rows,
    summary,
    groupedByMarket,

    // Actions
    loadPortfolio,
    updatePortfolioItem,
    removePortfolioItem,
    addPortfolioItem,
    getPortfolioItem,
    clearPortfolio,
  }
})
