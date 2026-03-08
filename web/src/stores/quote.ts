/**
 * Quote Store - 实时行情数据
 */

import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/shared/http'
import type { Quote, QuotePolicy } from './types'
import { DEFAULT_QUOTE_POLICY } from './types'

export const useQuoteStore = defineStore('quote', () => {
  // ───────────────────────────────────────────────────────────────
  // State
  // ───────────────────────────────────────────────────────────────

  const quotes = ref<Record<string, Quote>>({})
  const quotePolicy = ref<QuotePolicy>({ ...DEFAULT_QUOTE_POLICY })
  const loading = ref(false)

  // 自动刷新状态
  let autoRefreshConsumers = 0
  let autoRefreshTimer: ReturnType<typeof setTimeout> | null = null
  let quotesInflight: Promise<void> | null = null
  let backgroundQuotesInflight: Promise<void> | null = null

  // ───────────────────────────────────────────────────────────────
  // Helpers
  // ───────────────────────────────────────────────────────────────

  /**
   * NormalizeInterval - 标准化间隔
   */
  function normalizeInterval(sec: unknown, fallback: number): number {
    const n = Number(sec)
    if (!Number.isFinite(n) || n <= 0) return fallback
    return Math.round(n)
  }

  /**
   * ApplyQuotePolicy - 应用行情策略
   */
  function applyQuotePolicy(policy?: Partial<QuotePolicy>) {
    if (!policy) return

    quotePolicy.value = {
      interval_open_sec: normalizeInterval(
        policy.interval_open_sec,
        quotePolicy.value.interval_open_sec || DEFAULT_QUOTE_POLICY.interval_open_sec
      ),
      interval_closed_sec: normalizeInterval(
        policy.interval_closed_sec,
        quotePolicy.value.interval_closed_sec || DEFAULT_QUOTE_POLICY.interval_closed_sec
      ),
      interval_us_extended_sec: normalizeInterval(
        policy.interval_us_extended_sec,
        quotePolicy.value.interval_us_extended_sec || DEFAULT_QUOTE_POLICY.interval_us_extended_sec
      ),
    }
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
   * LoadQuotes - 加载行情
   */
  async function loadQuotes(codes: string[]) {
    if (quotesInflight) {
      return quotesInflight
    }

    quotesInflight = (async () => {
      loading.value = true
      try {
        if (!codes.length) {
          quotes.value = {}
          return
        }
        quotes.value = await api.post<Record<string, Quote>>(
          '/api/prices/batch',
          { codes },
          true
        )
      } finally {
        loading.value = false
      }
    })()

    try {
      await quotesInflight
    } finally {
      quotesInflight = null
    }
  }

  /**
   * LoadQuotesProgressive - 先补前几条，再后台补全量
   */
  async function loadQuotesProgressive(codes: string[], firstBatchSize = 12) {
    const normalizedCodes = Array.from(new Set(codes.filter(Boolean)))
    if (!normalizedCodes.length) {
      quotes.value = {}
      return
    }

    if (normalizedCodes.length <= firstBatchSize) {
      await loadQuotes(normalizedCodes)
      return
    }

    const firstBatch = normalizedCodes.slice(0, firstBatchSize)
    const restBatch = normalizedCodes.slice(firstBatchSize)

    loading.value = true
    try {
      const headQuotes = await api.post<Record<string, Quote>>(
        '/api/prices/batch',
        { codes: firstBatch },
        true
      )
      quotes.value = {
        ...quotes.value,
        ...(headQuotes || {}),
      }
    } finally {
      loading.value = false
    }

    if (!restBatch.length || backgroundQuotesInflight) {
      return
    }

    backgroundQuotesInflight = (async () => {
      try {
        const tailQuotes = await api.post<Record<string, Quote>>(
          '/api/prices/batch',
          { codes: restBatch },
          true
        )
        quotes.value = {
          ...quotes.value,
          ...(tailQuotes || {}),
        }
      } finally {
        backgroundQuotesInflight = null
      }
    })()
  }

  /**
   * GetQuote - 获取单个行情
   */
  function getQuote(code: string): Quote | undefined {
    return quotes.value[code]
  }

  /**
   * GetQuotePrice - 获取行情价格
   */
  function getQuotePrice(code: string): number {
    const quote = quotes.value[code]
    if (!quote) return 0
    return Number(quote.price || quote.regular_price || 0)
  }

  /**
   * GetQuoteYClose - 获取昨收价
   */
  function getQuoteYClose(code: string): number {
    const quote = quotes.value[code]
    if (!quote) return 0
    return Number(quote.yclose || 0)
  }

  /**
   * GetQuoteSession - 获取行情会话
   */
  function getQuoteSession(code: string): string {
    const quote = quotes.value[code]
    if (!quote) return 'closed'
    return normalizeSession(quote.effective_session ?? quote.session)
  }

  /**
   * NextQuoteIntervalMs - 下次行情更新间隔（毫秒）
   */
  function nextQuoteIntervalMs(hasAnyOpenMarket: boolean, hasUsExtendedActive: boolean): number {
    const policy = quotePolicy.value
    const sec = hasAnyOpenMarket
      ? policy.interval_open_sec
      : hasUsExtendedActive
        ? policy.interval_us_extended_sec
        : policy.interval_closed_sec
    return Math.max(1, sec) * 1000
  }

  /**
   * ClearAutoRefreshTimer - 清除自动刷新定时器
   */
  function clearAutoRefreshTimer() {
    if (!autoRefreshTimer) return
    clearTimeout(autoRefreshTimer)
    autoRefreshTimer = null
  }

  /**
   * ScheduleAutoRefresh - 调度自动刷新
   */
  function scheduleAutoRefresh(
    delayMs: number | undefined,
    hasAnyOpenMarket: boolean,
    hasUsExtendedActive: boolean,
    refreshCallback: () => Promise<void>
  ) {
    clearAutoRefreshTimer()
    if (autoRefreshConsumers <= 0) return

    autoRefreshTimer = setTimeout(() => {
      void refreshCallback()
    }, Math.max(0, delayMs ?? nextQuoteIntervalMs(hasAnyOpenMarket, hasUsExtendedActive)))
  }

  /**
   * StartAutoRefresh - 开始自动刷新
   */
  function startAutoRefresh() {
    autoRefreshConsumers += 1
  }

  /**
   * StopAutoRefresh - 停止自动刷新
   */
  function stopAutoRefresh() {
    autoRefreshConsumers = Math.max(0, autoRefreshConsumers - 1)
    if (autoRefreshConsumers === 0) {
      clearAutoRefreshTimer()
    }
  }

  /**
   * ClearQuotes - 清除行情数据
   */
  function clearQuotes() {
    quotes.value = {}
  }

  // ───────────────────────────────────────────────────────────────
  // Return
  // ───────────────────────────────────────────────────────────────

  return {
    // State
    quotes,
    quotePolicy,
    loading,

    // Actions
    loadQuotes,
    loadQuotesProgressive,
    getQuote,
    getQuotePrice,
    getQuoteYClose,
    getQuoteSession,
    nextQuoteIntervalMs,
    clearAutoRefreshTimer,
    scheduleAutoRefresh,
    startAutoRefresh,
    stopAutoRefresh,
    clearQuotes,
    applyQuotePolicy,
  }
})
