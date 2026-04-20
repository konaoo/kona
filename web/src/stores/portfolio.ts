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
import { useQuoteStore } from './quote'
import { useLedgerScopeStore } from './ledgerScope'

function isExchangeFundCode(code: string): boolean {
  const lower = String(code || '').trim().toLowerCase()
  let suffix = lower
  if (suffix.startsWith('f_')) suffix = suffix.slice(2)
  else if (suffix.startsWith('ft_')) return false
  else if (suffix.startsWith('gb_')) return false
  else if (suffix.startsWith('hk') || suffix.endsWith('.hk')) return false
  else if (suffix.startsWith('sh') || suffix.startsWith('sz') || suffix.startsWith('bj')) suffix = suffix.slice(2)

  if (!/^\d{6}$/.test(suffix)) return false

  // 11xxxx 里既有场外基金，也有沪市场内 ETF（如 511xxx）。这里只保留明确的场内段。
  if (suffix.startsWith('11') && !suffix.startsWith('511')) return false

  // 深圳场内基金：15/16/18 开头；上海场内基金/ETF：50/51/52/56/58/511 开头
  if (suffix.startsWith('15') || suffix.startsWith('16') || suffix.startsWith('18')) return true
  if (
    suffix.startsWith('50') ||
    suffix.startsWith('51') ||
    suffix.startsWith('52') ||
    suffix.startsWith('56') ||
    suffix.startsWith('58') ||
    suffix.startsWith('511')
  ) {
    return true
  }
  return false
}

const MARKET_PREOPEN_TIMEZONES: Partial<Record<MarketCode, string>> = {
  a: 'Asia/Shanghai',
  hk: 'Asia/Hong_Kong',
  fund: 'Asia/Shanghai',
}

const MARKET_FIRST_SESSION_START_MINUTES: Partial<Record<MarketCode, number>> = {
  a: 9 * 60 + 30,
  hk: 9 * 60 + 30,
  fund: 9 * 60 + 30,
}

function getMarketLocalMinutes(market: MarketCode, now: Date = new Date()): number | null {
  const timeZone = MARKET_PREOPEN_TIMEZONES[market]
  if (!timeZone) return null
  try {
    const parts = new Intl.DateTimeFormat('en-GB', {
      timeZone,
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
    }).formatToParts(now)
    const hour = Number(parts.find(part => part.type === 'hour')?.value ?? '')
    const minute = Number(parts.find(part => part.type === 'minute')?.value ?? '')
    if (!Number.isFinite(hour) || !Number.isFinite(minute)) return null
    return hour * 60 + minute
  } catch {
    return null
  }
}

function isPreopenOffHoursMarket(
  market: MarketCode,
  marketOpen: boolean,
  marketTradingDay: boolean,
  marketStatusReason: string,
): boolean {
  if (!['a', 'hk', 'fund'].includes(market)) return false
  if (marketOpen) return false
  if (!marketTradingDay) return false
  if (String(marketStatusReason || '').trim().toLowerCase() !== 'off_hours') return false
  const minutes = getMarketLocalMinutes(market)
  const firstSessionStart = MARKET_FIRST_SESSION_START_MINUTES[market]
  if (minutes == null || firstSessionStart == null) return false
  return minutes < firstSessionStart
}

function normalizeQuoteSession(raw: unknown): string {
  const text = String(raw || '').trim().toLowerCase()
  if (text === 'pre' || text === 'post' || text === 'regular') return text
  return 'closed'
}

function isUsExtendedSessionActive(
  market: MarketCode,
  quote: Record<string, unknown> | undefined,
): boolean {
  if (market !== 'us' || !quote || typeof quote !== 'object') return false
  const price = toNumber(quote.price ?? quote.regular_price ?? quote.regularPrice)
  const yclose = toNumber(quote.yclose ?? quote.prev_close ?? quote.previous_close)
  if (!(price > 0) || !(yclose > 0)) return false
  if (Boolean(quote.extended_active ?? quote.extendedActive)) return true
  const session = normalizeQuoteSession(
    quote.effective_session ?? quote.effectiveSession ?? quote.session,
  )
  return session === 'pre' || session === 'post'
}

function resolveDayPnlDisplayEnabled(params: {
  explicitEnabled: boolean | null
  market: MarketCode
  marketOpen: boolean
  navUpdatePending: boolean
  suppressPreopen: boolean
  hasResolvedYclose: boolean
  usExtendedActive: boolean
}): boolean {
  const { explicitEnabled, market, marketOpen, navUpdatePending, suppressPreopen, hasResolvedYclose, usExtendedActive } = params
  if (suppressPreopen) return false
  if (explicitEnabled != null) return explicitEnabled
  if (navUpdatePending) return false
  if (!hasResolvedYclose) return false
  if (market === 'us') {
    return marketOpen || usExtendedActive
  }
  return true
}

function resolveDayPnlAggregateEnabled(params: {
  explicitEnabled: boolean | null
  market: MarketCode
  marketOpen: boolean
  navUpdatePending: boolean
  suppressPreopen: boolean
  hasResolvedYclose: boolean
  marketTradingDay: boolean
  usExtendedActive: boolean
}): boolean {
  const {
    explicitEnabled,
    market,
    marketOpen,
    navUpdatePending,
    suppressPreopen,
    hasResolvedYclose,
    marketTradingDay,
    usExtendedActive,
  } = params
  if (suppressPreopen) return false
  if (explicitEnabled != null) return explicitEnabled
  if (navUpdatePending) return false
  if (!hasResolvedYclose) return false
  if (market === 'us') return marketOpen || usExtendedActive
  if (marketTradingDay) return true
  return usExtendedActive
}

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
        if (typeof value === 'boolean') return value
        if (typeof value === 'number') return value !== 0
        if (typeof value === 'string') {
          const normalized = value.trim().toLowerCase()
          if (!normalized) continue
          return normalized === '1' || normalized === 'true' || normalized === 'yes'
        }
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
      const code = String(item.code || '')
      const isExchangeFund = isExchangeFundCode(code)
      const marketFromPayload = normalizeMarketCode((item as any).market)
      let market = marketFromPayload ?? inferMarket(item)
      // 对齐后端口径：场内 ETF（旧数据可能被标成 fund）交易时段和当日盈亏按 A 股市场走。
      if (market === 'fund' && isExchangeFund) {
        market = 'a'
      }
      const category = inferCategory(item)
      const qty = toNumber(item.qty)
      const rawCostPrice = toNumber(item.price)
      const marketStatus = marketStore.marketStatus[market]
      const open = Boolean(marketStatus?.open)
      const marketTradingDay = Boolean(marketStatus?.trading_day)

      const staticCurrentPrice = pickNumber(item, ['current_price', 'currentPrice']) ?? 0
      const staticYclose = pickNumber(item, ['yclose']) ?? 0
      const displayCostPrice =
        pickNumber(item, ['display_cost_price', 'displayCostPrice']) ?? rawCostPrice
      const cost = pickNumber(item, ['cost']) ?? pickNumber(item, ['raw_cost_total']) ?? 0
      const rawCostTotal = pickNumber(item, ['raw_cost_total']) ?? cost
      const staticValue = pickNumber(item, ['value']) ?? 0
      const adjustmentTotal =
        pickNumber(item, ['adjustment_total', 'adjustment']) ?? 0
      const staticTotalPnl = pickNumber(item, ['total_pnl']) ?? 0
      const staticTotalPnlBase = pickNumber(item, ['total_pnl_base']) ?? 0
      const staticTotalPnlRate = pickNumber(item, ['total_pnl_rate']) ?? 0
      const staticDayPnlDisplay = pickNumber(item, ['day_pnl_display', 'day_pnl']) ?? 0
      const staticDayPnlBaseDisplay = pickNumber(item, ['day_pnl_base_display', 'day_pnl_base']) ?? 0
      const staticDayPnlRateDisplay = pickNumber(item, ['day_pnl_rate_display', 'day_pnl_rate']) ?? 0
      const staticDayPnlAggregate = pickNumber(item, ['day_pnl_aggregate', 'day_pnl']) ?? 0
      const staticDayPnlBaseAggregate =
        pickNumber(item, ['day_pnl_base_aggregate', 'day_pnl_base']) ?? 0
      const staticDayPnlRateAggregate =
        pickNumber(item, ['day_pnl_rate_aggregate', 'day_pnl_rate']) ?? 0
      // 场内 ETF 即使历史上误标为 f_，也不应进入“净值待更新”的展示分支：
      // 1) 否则会把“涨幅/当日盈亏”整块隐藏成 --，与 App 口径不一致
      // 2) 场内 ETF 的价格/昨收/当日盈亏应按交易所行情走
      const navUpdatePending = isExchangeFund
        ? false
        : (pickBool(item, ['nav_update_pending']) ?? isNavUpdatePendingAsset(item))
      const staticDayPnlDisplayEnabledRaw =
        pickBool(item, ['day_pnl_display_enabled'])
      const staticDayPnlAggregateEnabledRaw =
        pickBool(item, ['day_pnl_aggregate_enabled'])
      const staticQuotePrice = pickNumber(item, ['quote_price'])
      const rateToCny = pickNumber(item, ['rate_to_cny']) ?? undefined
      const costCny = pickNumber(item, ['cost_cny']) ?? undefined
      const marketOpen = pickBool(item, ['market_open']) ?? open
      const marketTradingDayValue = pickBool(item, ['market_trading_day']) ?? marketTradingDay
      const marketStatusReason =
        pickString(item, ['market_status_reason']) || marketStatus?.reason || ''
      const suppressDayPnlForPreopen = isPreopenOffHoursMarket(
        market,
        marketOpen,
        marketTradingDayValue,
        marketStatusReason,
      )
      const quote = quoteStore.getQuote(code) as Record<string, unknown> | undefined
      const quoteSession = normalizeQuoteSession(
        quote?.effective_session ?? quote?.effectiveSession ?? quote?.session,
      )
      const usExtendedActive = isUsExtendedSessionActive(market, quote)
      const liveQuotePrice =
        quote && typeof quote === 'object'
          ? toNumber(quote.price ?? quote.regular_price ?? quote.regularPrice)
          : 0
      const liveYclose =
        quote && typeof quote === 'object'
          ? toNumber(quote.yclose ?? quote.prev_close ?? quote.previous_close)
          : 0
      const hasLiveQuotePrice = Number.isFinite(liveQuotePrice) && liveQuotePrice > 0
      const hasLiveYclose = Number.isFinite(liveYclose) && liveYclose > 0
      const currentPrice = hasLiveQuotePrice ? liveQuotePrice : staticCurrentPrice
      const yclose = hasLiveYclose ? liveYclose : staticYclose
      const hasResolvedYclose = Number.isFinite(yclose) && yclose > 0
      const value = hasLiveQuotePrice && qty > 0 ? currentPrice * qty : staticValue
      const valueCny = rateToCny != null ? value * rateToCny : pickNumber(item, ['value_cny']) ?? undefined
      const dayPnlDisplayEnabled = resolveDayPnlDisplayEnabled({
        explicitEnabled: staticDayPnlDisplayEnabledRaw,
        market,
        marketOpen,
        navUpdatePending,
        suppressPreopen: suppressDayPnlForPreopen,
        hasResolvedYclose,
        usExtendedActive,
      })
      const dayPnlAggregateEnabled = resolveDayPnlAggregateEnabled({
        explicitEnabled: staticDayPnlAggregateEnabledRaw,
        market,
        marketOpen,
        navUpdatePending,
        suppressPreopen: suppressDayPnlForPreopen,
        hasResolvedYclose,
        marketTradingDay: marketTradingDayValue,
        usExtendedActive,
      })
      const canUseLiveDayPnlDisplay =
        dayPnlDisplayEnabled &&
        hasLiveQuotePrice &&
        hasLiveYclose
      const canUseLiveDayPnlAggregate =
        dayPnlAggregateEnabled &&
        hasLiveQuotePrice &&
        hasLiveYclose
      const liveDayPnlDisplay = canUseLiveDayPnlDisplay ? (currentPrice - yclose) * qty : null
      const liveDayPnlBaseDisplay = canUseLiveDayPnlDisplay ? Math.abs(yclose * qty) : null
      const liveDayPnlAggregate = canUseLiveDayPnlAggregate ? (currentPrice - yclose) * qty : null
      const liveDayPnlBaseAggregate = canUseLiveDayPnlAggregate ? Math.abs(yclose * qty) : null
      const dayPnlDisplay = !dayPnlDisplayEnabled ? 0 : (liveDayPnlDisplay ?? staticDayPnlDisplay)
      const dayPnlBaseDisplay = !dayPnlDisplayEnabled ? 0 : (liveDayPnlBaseDisplay ?? staticDayPnlBaseDisplay)
      const dayPnlRateDisplay =
        !dayPnlDisplayEnabled
          ? 0
          : liveDayPnlDisplay != null && liveDayPnlBaseDisplay != null && liveDayPnlBaseDisplay > 0
          ? (liveDayPnlDisplay / liveDayPnlBaseDisplay) * 100
          : staticDayPnlRateDisplay
      const dayPnlAggregate = !dayPnlAggregateEnabled ? 0 : (liveDayPnlAggregate ?? staticDayPnlAggregate)
      const dayPnlBaseAggregate = !dayPnlAggregateEnabled ? 0 : (liveDayPnlBaseAggregate ?? staticDayPnlBaseAggregate)
      const dayPnlRateAggregate =
        !dayPnlAggregateEnabled
          ? 0
          : liveDayPnlAggregate != null && liveDayPnlBaseAggregate != null && liveDayPnlBaseAggregate > 0
          ? (liveDayPnlAggregate / liveDayPnlBaseAggregate) * 100
          : staticDayPnlRateAggregate
      const totalPnl = hasLiveQuotePrice ? value - cost + adjustmentTotal : staticTotalPnl
      const totalPnlBase = Math.abs(cost) || staticTotalPnlBase
      const totalPnlRate =
        totalPnlBase > 0 ? (totalPnl / totalPnlBase) * 100 : staticTotalPnlRate
      const totalPnlCny = rateToCny != null ? totalPnl * rateToCny : pickNumber(item, ['total_pnl_cny']) ?? undefined
      const dayPnlCny =
        !dayPnlDisplayEnabled
          ? 0
          : liveDayPnlDisplay != null && rateToCny != null
          ? liveDayPnlDisplay * rateToCny
          : pickNumber(item, ['day_pnl_cny']) ?? undefined
      const dayPnlBaseCny =
        !dayPnlDisplayEnabled
          ? 0
          : liveDayPnlBaseDisplay != null && rateToCny != null
          ? liveDayPnlBaseDisplay * rateToCny
          : pickNumber(item, ['day_pnl_base_cny']) ?? undefined
      const dayPnlAggregateCny =
        !dayPnlAggregateEnabled
          ? 0
          : liveDayPnlAggregate != null && rateToCny != null
          ? liveDayPnlAggregate * rateToCny
          : pickNumber(item, ['day_pnl_aggregate_cny']) ?? undefined
      const dayPnlBaseAggregateCny =
        !dayPnlAggregateEnabled
          ? 0
          : liveDayPnlBaseAggregate != null && rateToCny != null
          ? liveDayPnlBaseAggregate * rateToCny
          : pickNumber(item, ['day_pnl_base_aggregate_cny']) ?? undefined
      const quotePrice = hasLiveQuotePrice ? currentPrice : staticQuotePrice
      const quoteReady = hasLiveQuotePrice || (pickBool(item, ['quote_ready']) ?? Boolean(staticQuotePrice && staticQuotePrice > 0))
      const quotePending = hasLiveQuotePrice ? false : (pickBool(item, ['quote_pending']) ?? false)

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
        valueCny,
        costCny,
        totalPnlCny,
        totalPnlBase,
        totalPnlBaseCny:
          costCny != null ? Math.abs(costCny) : pickNumber(item, ['total_pnl_base_cny']) ?? undefined,
        dayPnlCny,
        dayPnlBase: dayPnlBaseAggregate,
        dayPnlBaseCny,
        dayPnlAggregateCny,
        dayPnlBaseAggregate,
        dayPnlBaseAggregateCny,
        rateToCny,
        totalPnl,
        dayPnl: dayPnlAggregate,
        dayPnlRate: dayPnlRateAggregate,
        dayPnlDisplay,
        dayPnlBaseDisplay,
        dayPnlRateDisplay,
        dayPnlAggregate,
        dayPnlRateAggregate,
        totalPnlRate,
        quotePrice: quotePrice ?? undefined,
        quoteChange: pickNumber(item, ['quote_change']) ?? undefined,
        quoteChangePct: pickNumber(item, ['quote_change_pct']) ?? undefined,
        session: quoteSession,
        marketOpen,
        marketTradingDay: marketTradingDayValue,
        marketStatusReason,
        usExtendedActive,
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
      const ledgerScopeStore = useLedgerScopeStore()
      const params = new URLSearchParams({ type: 'all', with_metrics: '1' })
      if (ledgerScopeStore.currentLedgerId != null) {
        params.set('ledger_id', String(ledgerScopeStore.currentLedgerId))
      }
      const items = await api.get<PortfolioItem[]>(`/api/portfolio?${params.toString()}`, true)
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
