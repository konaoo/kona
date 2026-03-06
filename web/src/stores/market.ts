/**
 * Market Store - 市场状态和汇率
 */

import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/shared/http'
import { toNumber } from '@/shared/format'
import type { MarketCode, MarketStatus } from './types'
import { MARKET_CODES, DEFAULT_QUOTE_POLICY } from './types'

export const useMarketStore = defineStore('market', () => {
  // ───────────────────────────────────────────────────────────────
  // State
  // ───────────────────────────────────────────────────────────────

  const marketStatus = ref<Record<MarketCode, MarketStatus>>({} as Record<MarketCode, MarketStatus>)
  const allClosed = ref(false)
  const rates = ref<Record<string, number>>({})
  const loading = ref(false)

  // ───────────────────────────────────────────────────────────────
  // Computed
  // ───────────────────────────────────────────────────────────────

  const hasAnyOpenMarket = computed(() => {
    return MARKET_CODES.some((m) => Boolean(marketStatus.value[m]?.open))
  })

  // ───────────────────────────────────────────────────────────────
  // Helpers
  // ───────────────────────────────────────────────────────────────

  /**
   * InferReason - 推断原因
   */
  function inferReason(open: boolean): string {
    return open ? 'open_session' : 'off_hours'
  }

  /**
   * InferTradingDayFromReason - 从原因推断交易日
   */
  function inferTradingDayFromReason(reason: string, open: boolean): boolean {
    if (open) return true
    const key = String(reason || '').toLowerCase()
    if (key === 'holiday_or_weekend') return false
    if (key === 'off_hours' || key === 'open_session') return true
    if (key === 'override') return false
    return true
  }

  /**
   * NormalizeMarketStatus - 标准化市场状态
   */
  function normalizeMarketStatus(
    detail: Partial<MarketStatus> | undefined,
    openFallback: boolean
  ): MarketStatus {
    const hasDetail = !!detail && Object.keys(detail).length > 0
    const open = typeof detail?.open === 'boolean' ? detail.open : openFallback
    const reason = String(detail?.reason || inferReason(open))
      .trim()
      .toLowerCase() || inferReason(open)
    const tradingDay = typeof detail?.trading_day === 'boolean'
      ? detail.trading_day
      : hasDetail
        ? inferTradingDayFromReason(reason, open)
        : open

    return {
      open,
      reason,
      trading_day: tradingDay,
    }
  }

  /**
   * ApplyMarketStatuses - 应用市场状态
   */
  function applyMarketStatuses(
    details?: Partial<Record<MarketCode, Partial<MarketStatus>>>,
    booleans?: Partial<Record<MarketCode, boolean>>
  ) {
    if (!details && !booleans) return

    const next = {} as Record<MarketCode, MarketStatus>
    for (const m of MARKET_CODES) {
      next[m] = normalizeMarketStatus(details?.[m], Boolean(booleans?.[m]))
    }
    marketStatus.value = next
    allClosed.value = MARKET_CODES.every((m) => !next[m]?.open)
  }

  // ───────────────────────────────────────────────────────────────
  // Actions
  // ───────────────────────────────────────────────────────────────

  /**
   * LoadMarketStatus - 加载市场状态
   */
  async function loadMarketStatus() {
    loading.value = true
    try {
      const payload = await api.get<{
        markets?: Partial<Record<MarketCode, Partial<MarketStatus>>>
        all_closed?: boolean
      }>('/api/market/status', false)

      applyMarketStatuses(payload.markets)
      allClosed.value = Boolean(payload.all_closed)
    } finally {
      loading.value = false
    }
  }

  /**
   * LoadRates - 加载汇率
   */
  async function loadRates() {
    loading.value = true
    try {
      const data = await api.get<Record<string, number>>('/api/rates', false)
      const nextRates: Record<string, number> = {}

      if (data && typeof data === 'object') {
        for (const [k, v] of Object.entries(data)) {
          nextRates[k] = toNumber(v, 1)
        }
      }

      rates.value = nextRates
    } finally {
      loading.value = false
    }
  }

  /**
   * GetMarketStatus - 获取单个市场状态
   */
  function getMarketStatus(market: MarketCode): MarketStatus | undefined {
    return marketStatus.value[market]
  }

  /**
   * IsMarketOpen - 判断市场是否开市
   */
  function isMarketOpen(market: MarketCode): boolean {
    return Boolean(marketStatus.value[market]?.open)
  }

  /**
   * GetRate - 获取汇率
   */
  function getRate(from: string, to: string): number {
    const key = `${from}_${to}`
    return rates.value[key] || 1
  }

  // ───────────────────────────────────────────────────────────────
  // Return
  // ───────────────────────────────────────────────────────────────

  return {
    // State
    marketStatus,
    allClosed,
    rates,
    loading,

    // Computed
    hasAnyOpenMarket,

    // Actions
    loadMarketStatus,
    loadRates,
    getMarketStatus,
    isMarketOpen,
    getRate,
    applyMarketStatuses,
  }
})
