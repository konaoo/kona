/**
 * Sync Store - 数据同步和缓存管理
 */

import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/shared/http'
import { toNumber } from '@/shared/format'
import type {
  SyncDomain,
  BootstrapPayload,
  StoreCachePayload,
} from './types'
import {
  ALL_SYNC_DOMAINS,
  STORAGE_KEYS,
  CACHE_TTL,
  SYNC_BOOTSTRAP,
} from './types'
import { useAuthStore } from './auth'
import { usePortfolioStore } from './portfolio'
import { useMarketStore } from './market'
import { useQuoteStore } from './quote'

export const useSyncStore = defineStore('sync', () => {
  // ───────────────────────────────────────────────────────────────
  // State
  // ───────────────────────────────────────────────────────────────

  const syncVersions = ref<Partial<Record<SyncDomain, string>>>({})
  const loading = ref(false)

  // 请求去重
  const bootstrapInflight = new Map<string, Promise<Set<SyncDomain>>>()

  // ───────────────────────────────────────────────────────────────
  // Helpers
  // ───────────────────────────────────────────────────────────────

  /**
   * ReadSyncVersions - 读取同步版本
   */
  function readSyncVersions(): Partial<Record<SyncDomain, string>> {
    if (typeof window === 'undefined') return {}
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.SYNC_VERSIONS)
      if (!raw) return {}
      const parsed = JSON.parse(raw) as Partial<Record<SyncDomain, string>>
      return parsed && typeof parsed === 'object' ? parsed : {}
    } catch {
      return {}
    }
  }

  /**
   * PersistSyncVersions - 持久化同步版本
   */
  function persistSyncVersions(versions: Partial<Record<SyncDomain, string>>) {
    if (typeof window === 'undefined') return
    try {
      localStorage.setItem(STORAGE_KEYS.SYNC_VERSIONS, JSON.stringify(versions))
    } catch {
      // ignore storage errors
    }
  }

  /**
   * ApplyBootstrapVersions - 应用 bootstrap 版本
   */
  function applyBootstrapVersions(versions?: Partial<Record<string, string>>) {
    if (!versions) return

    let dirty = false
    for (const domain of ALL_SYNC_DOMAINS) {
      const next = String(versions[domain] || '').trim()
      if (!next) continue
      if (syncVersions.value[domain] !== next) {
        syncVersions.value[domain] = next
        dirty = true
      }
    }

    if (dirty) {
      persistSyncVersions(syncVersions.value)
    }
  }

  /**
   * IsSyncDomain - 判断是否是同步域
   */
  function isSyncDomain(value: string): value is SyncDomain {
    return (ALL_SYNC_DOMAINS as readonly string[]).includes(value)
  }

  /**
   * BootstrapIncludeKey - 生成 include 键
   */
  function bootstrapIncludeKey(include: SyncDomain[]): string {
    return [...new Set(include)].sort().join(',')
  }

  /**
   * NormalizeInterval - 标准化间隔
   */
  function normalizeInterval(sec: unknown, fallback: number): number {
    const n = Number(sec)
    if (!Number.isFinite(n) || n <= 0) return fallback
    return Math.round(n)
  }

  /**
   * NormalizeUserId - 标准化用户 ID
   */
  function normalizeUserId(userId: string): string {
    const id = String(userId || '').trim()
    return id || 'guest'
  }

  /**
   * ReadStoreCacheRaw - 读取原始缓存
   */
  function readStoreCacheRaw(): StoreCachePayload | null {
    if (typeof window === 'undefined') return null
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.STORE_CACHE)
      if (!raw) return null
      const parsed = JSON.parse(raw) as StoreCachePayload
      if (!parsed || typeof parsed !== 'object') return null
      return parsed
    } catch {
      return null
    }
  }

  /**
   * ClearStoreCache - 清除缓存
   */
  function clearStoreCache() {
    if (typeof window === 'undefined') return
    try {
      localStorage.removeItem(STORAGE_KEYS.STORE_CACHE)
    } catch {
      // ignore storage errors
    }
  }

  /**
   * PersistStoreCache - 持久化缓存
   */
  function persistStoreCache(
    authStore: ReturnType<typeof useAuthStore>,
    portfolioStore: ReturnType<typeof usePortfolioStore>,
    marketStore: ReturnType<typeof useMarketStore>,
    quoteStore: ReturnType<typeof useQuoteStore>,
    mode: 'static' | 'full' = 'full'
  ) {
    if (typeof window === 'undefined') return

    const prev = readStoreCacheRaw()
    const now = Date.now()

    const nextQuotes =
      mode === 'full'
        ? quoteStore.quotes
        : Object.keys(quoteStore.quotes || {}).length
          ? quoteStore.quotes
          : (prev?.quotes || {})

    const payload: StoreCachePayload = {
      userId: normalizeUserId(authStore.userId),
      savedAt: now,
      quotesSavedAt: mode === 'full' ? now : Number(prev?.quotesSavedAt || 0),
      portfolio: portfolioStore.portfolio,
      quotes: nextQuotes,
      rates: marketStore.rates,
      marketStatus: marketStore.marketStatus,
      allClosed: marketStore.allClosed,
      quotePolicy: quoteStore.quotePolicy,
    }

    try {
      localStorage.setItem(STORAGE_KEYS.STORE_CACHE, JSON.stringify(payload))
    } catch {
      // ignore storage errors
    }
  }

  /**
   * HydrateStoreCache - 恢复缓存
   */
  function hydrateStoreCache(
    authStore: ReturnType<typeof useAuthStore>,
    portfolioStore: ReturnType<typeof usePortfolioStore>,
    marketStore: ReturnType<typeof useMarketStore>,
    quoteStore: ReturnType<typeof useQuoteStore>
  ) {
    const cached = readStoreCacheRaw()
    if (!cached) return

    if (cached.userId !== normalizeUserId(authStore.userId)) {
      clearStoreCache()
      return
    }

    const now = Date.now()
    const staticAge = now - Number(cached.savedAt || 0)
    if (!Number.isFinite(staticAge) || staticAge > CACHE_TTL.STATIC) return

    // 恢复投资组合
    portfolioStore.portfolio = Array.isArray(cached.portfolio) ? cached.portfolio : []

    // 恢复汇率
    const nextRates: Record<string, number> = {}
    if (cached.rates && typeof cached.rates === 'object') {
      for (const [k, v] of Object.entries(cached.rates)) {
        nextRates[k] = toNumber(v, 1)
      }
    }
    marketStore.rates = nextRates

    // 恢复市场状态
    marketStore.marketStatus = cached.marketStatus && typeof cached.marketStatus === 'object'
      ? cached.marketStatus
      : {} as typeof marketStore.marketStatus
    marketStore.allClosed = Boolean(cached.allClosed)

    // 恢复行情策略
    if (cached.quotePolicy && typeof cached.quotePolicy === 'object') {
      quoteStore.quotePolicy = {
        interval_open_sec: normalizeInterval(
          cached.quotePolicy.interval_open_sec,
          quoteStore.quotePolicy.interval_open_sec
        ),
        interval_closed_sec: normalizeInterval(
          cached.quotePolicy.interval_closed_sec,
          quoteStore.quotePolicy.interval_closed_sec
        ),
        interval_us_extended_sec: normalizeInterval(
          cached.quotePolicy.interval_us_extended_sec,
          quoteStore.quotePolicy.interval_us_extended_sec
        ),
      }
    }

    // 恢复行情（如果未过期）
    const quotesAge = now - Number(cached.quotesSavedAt || 0)
    if (Number.isFinite(quotesAge) && quotesAge <= CACHE_TTL.QUOTES) {
      quoteStore.quotes = cached.quotes && typeof cached.quotes === 'object' ? cached.quotes : {}
    }
  }

  // ───────────────────────────────────────────────────────────────
  // Actions
  // ───────────────────────────────────────────────────────────────

  /**
   * LoadBootstrap - 加载 bootstrap 数据
   */
  async function loadBootstrap(include: SyncDomain[] = SYNC_BOOTSTRAP.QUOTE_INCLUDE): Promise<Set<SyncDomain>> {
    const authStore = useAuthStore()
    const portfolioStore = usePortfolioStore()
    const marketStore = useMarketStore()
    const quoteStore = useQuoteStore()

    const includeKey = bootstrapIncludeKey(include)
    const inflight = bootstrapInflight.get(includeKey)

    if (inflight) {
      return inflight
    }

    const request = (async () => {
      loading.value = true

      const clientVersions = include.reduce<Partial<Record<SyncDomain, string>>>((acc, domain) => {
        acc[domain] = syncVersions.value[domain] || ''
        return acc
      }, {})

      const payload = await api.post<BootstrapPayload>(
        '/api/sync/bootstrap',
        {
          include,
          client_versions: clientVersions,
        },
        true
      )

      loading.value = false

      // 应用版本
      applyBootstrapVersions(payload.versions)

      // 应用市场状态
      marketStore.applyMarketStatuses(payload.market_statuses, payload.market_status)

      // 应用行情策略
      quoteStore.applyQuotePolicy(payload.quote_policy)

      // 解析变更的域
      const changed = new Set(
        (payload.changed || [])
          .map((x) => String(x))
          .filter((x): x is SyncDomain => isSyncDomain(x))
      )

      // 应用数据
      const data = payload.data || {}

      if (Object.prototype.hasOwnProperty.call(data, 'portfolio')) {
        const portfolio = data.portfolio
        portfolioStore.portfolio = Array.isArray(portfolio) ? portfolio : []
      }

      if (Object.prototype.hasOwnProperty.call(data, 'rates')) {
        const rates = data.rates as Record<string, unknown>
        const nextRates: Record<string, number> = {}
        if (rates && typeof rates === 'object') {
          for (const [k, v] of Object.entries(rates)) {
            nextRates[k] = toNumber(v, 1)
          }
        }
        marketStore.rates = nextRates
      }

      return changed
    })()

    bootstrapInflight.set(includeKey, request)

    try {
      return await request
    } finally {
      bootstrapInflight.delete(includeKey)
    }
  }

  /**
   * InvalidateSyncVersion - 使同步版本失效
   */
  function invalidateSyncVersion(domain?: SyncDomain) {
    if (!domain) {
      for (const key of Object.keys(syncVersions.value) as SyncDomain[]) {
        delete syncVersions.value[key]
      }
      persistSyncVersions(syncVersions.value)
      return
    }

    if (syncVersions.value[domain]) {
      delete syncVersions.value[domain]
      persistSyncVersions(syncVersions.value)
    }
  }

  /**
   * MarkPortfolioDirty - 标记投资组合为脏
   */
  function markPortfolioDirty() {
    invalidateSyncVersion('portfolio')
  }

  /**
   * MarkRatesDirty - 标记汇率为脏
   */
  function markRatesDirty() {
    invalidateSyncVersion('rates')
  }

  // ───────────────────────────────────────────────────────────────
  // Initialization
  // ───────────────────────────────────────────────────────────────

  // 初始化时读取同步版本
  syncVersions.value = readSyncVersions()

  // ───────────────────────────────────────────────────────────────
  // Return
  // ───────────────────────────────────────────────────────────────

  return {
    // State
    syncVersions,
    loading,

    // Actions
    loadBootstrap,
    invalidateSyncVersion,
    markPortfolioDirty,
    markRatesDirty,
    clearStoreCache,
    persistStoreCache,
    hydrateStoreCache,
  }
})
