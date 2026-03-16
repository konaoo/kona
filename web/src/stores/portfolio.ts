/**
 * Portfolio Store - 投资组合数据管理
 */

import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/shared/http'
import { toNumber } from '@/shared/format'
import { buildPortfolioSummary } from './portfolioMetrics'
import type { MarketCode, PortfolioItem, PositionRow, PortfolioSummary } from './types'
import { useMarketStore } from './market'

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

    function pickNumber(item: PortfolioItem, keys: string[]): number | null {
      for (const key of keys) {
        if (!Object.prototype.hasOwnProperty.call(item, key)) continue
        const value = (item as Record<string, unknown>)[key]
        if (value === undefined || value === null || value === '') continue
        const n = toNumber(value)
        if (Number.isFinite(n)) return n
      }
      return null
    }

    function pickBool(item: PortfolioItem, keys: string[]): boolean | null {
      for (const key of keys) {
        if (!Object.prototype.hasOwnProperty.call(item, key)) continue
        const value = (item as Record<string, unknown>)[key]
        if (value === undefined || value === null) continue
        return Boolean(value)
      }
      return null
    }

    function pickString(item: PortfolioItem, keys: string[]): string {
      for (const key of keys) {
        if (!Object.prototype.hasOwnProperty.call(item, key)) continue
        const value = (item as Record<string, unknown>)[key]
        if (value === undefined || value === null) continue
        return String(value)
      }
      return ''
    }

    function normalizeMarketCode(raw: unknown): MarketCode | null {
      const text = String(raw || '')
        .trim()
        .toLowerCase()
      if (text === 'a' || text === 'hk' || text === 'us' || text === 'fund') {
        return text as MarketCode
      }
      return null
    }

    return portfolio.value.map(item => {
      const marketFromPayload = normalizeMarketCode((item as any).market)
      const market = marketFromPayload ?? inferMarket(item)
      const category = inferCategory(item)
      const qty = toNumber(item.qty)
      const rawCostPrice = toNumber(item.price)
      const marketStatus = marketStore.marketStatus[market]
      const open = Boolean(marketStatus?.open)
      const marketTradingDay = Boolean(marketStatus?.trading_day)

      const currentPrice = pickNumber(item, ['current_price', 'currentPrice']) ?? 0
      const yclose = pickNumber(item, ['yclose']) ?? 0
      const displayCostPrice =
        pickNumber(item, ['display_cost_price', 'displayCostPrice']) ?? rawCostPrice
      const cost = pickNumber(item, ['cost']) ?? pickNumber(item, ['raw_cost_total']) ?? 0
      const rawCostTotal = pickNumber(item, ['raw_cost_total']) ?? cost
      const value = pickNumber(item, ['value']) ?? 0
      const totalPnl = pickNumber(item, ['total_pnl']) ?? 0
      const totalPnlRate = pickNumber(item, ['total_pnl_rate']) ?? 0
      const dayPnlDisplay = pickNumber(item, ['day_pnl_display', 'day_pnl']) ?? 0
      const dayPnlRateDisplay = pickNumber(item, ['day_pnl_rate_display', 'day_pnl_rate']) ?? 0
      const dayPnlAggregate = pickNumber(item, ['day_pnl_aggregate', 'day_pnl']) ?? 0
      const dayPnlRateAggregate = pickNumber(item, ['day_pnl_rate_aggregate', 'day_pnl_rate']) ?? 0
      const navUpdatePending =
        pickBool(item, ['nav_update_pending']) ?? isNavUpdatePendingAsset(item)
      const quotePrice = pickNumber(item, ['quote_price'])
      const quoteReady = pickBool(item, ['quote_ready']) ?? Boolean(quotePrice && quotePrice > 0)
      const quotePending = pickBool(item, ['quote_pending']) ?? false
      const dayPnlDisplayEnabled = pickBool(item, ['day_pnl_display_enabled']) ?? false
      const dayPnlAggregateEnabled = pickBool(item, ['day_pnl_aggregate_enabled']) ?? false
      const marketOpen = pickBool(item, ['market_open']) ?? open
      const marketTradingDayValue = pickBool(item, ['market_trading_day']) ?? marketTradingDay
      const marketStatusReason =
        pickString(item, ['market_status_reason']) || marketStatus?.reason || ''

      return {
        ...item,
        market,
        category,
        curr: String(item.curr || 'CNY'),
        qty,
        costPrice: rawCostPrice,
        rawCostPrice,
        cost,
        rawCostTotal,
        displayCostPrice,
        currentPrice,
        yclose,
        value,
        valueCny: pickNumber(item, ['value_cny']) ?? undefined,
        costCny: pickNumber(item, ['cost_cny']) ?? undefined,
        totalPnlCny: pickNumber(item, ['total_pnl_cny']) ?? undefined,
        dayPnlCny: pickNumber(item, ['day_pnl_cny']) ?? undefined,
        dayPnlAggregateCny: pickNumber(item, ['day_pnl_aggregate_cny']) ?? undefined,
        rateToCny: pickNumber(item, ['rate_to_cny']) ?? undefined,
        totalPnl,
        dayPnl: dayPnlAggregate,
        dayPnlRate: dayPnlRateAggregate,
        dayPnlDisplay,
        dayPnlRateDisplay,
        dayPnlAggregate,
        dayPnlRateAggregate,
        totalPnlRate,
        quotePrice: quotePrice ?? undefined,
        quoteChange: pickNumber(item, ['quote_change']) ?? undefined,
        quoteChangePct: pickNumber(item, ['quote_change_pct']) ?? undefined,
        session: 'closed',
        marketOpen,
        marketTradingDay: marketTradingDayValue,
        marketStatusReason,
        usExtendedActive: false,
        navUpdatePending,
        quoteReady,
        quotePending,
        dayPnlDisplayEnabled,
        dayPnlAggregateEnabled
      }
    })
  })

  /**
   * Summary - 投资组合摘要
   */
  const summary = computed<PortfolioSummary>(() => {
    return buildPortfolioSummary(rows.value)
  })

  /**
   * GroupedByMarket - 按市场分组的持仓
   */
  const groupedByMarket = computed(() => {
    const groups: Record<MarketCode, PositionRow[]> = {
      a: [],
      hk: [],
      us: [],
      fund: []
    }

    for (const row of rows.value) {
      groups[row.category].push(row)
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

  function inferCategory(item: PortfolioItem): MarketCode {
    const category = String(item.category_type || '').toLowerCase()
    if (category === 'hk') return 'hk'
    if (category === 'us') return 'us'
    if (category === 'fund') return 'fund'
    if (category === 'a') return 'a'
    return inferMarket(item)
  }

  /**
   * IsNavUpdatePendingAsset - 是否是 NAV 待更新资产
   */
  function isNavUpdatePendingAsset(item: PortfolioItem): boolean {
    const code = String(item.code || '')
      .trim()
      .toLowerCase()
    return code.startsWith('f_') || code.startsWith('ft_')
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
      const items = await api.get<PortfolioItem[]>('/api/portfolio?type=all&with_metrics=1', true)
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
    clearPortfolio
  }
})
