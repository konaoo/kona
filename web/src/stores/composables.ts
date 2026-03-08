/**
 * 组合式 API - 统一的数据访问接口
 * 提供类似原 useKonaStore 的接口，便于迁移
 */

import { computed, reactive } from 'vue'
import { useAuthStore } from './auth'
import { usePortfolioStore } from './portfolio'
import { useQuoteStore } from './quote'
import { useMarketStore } from './market'
import { useSyncStore } from './sync'

let hydratedCacheUserId = ''

/**
 * useKonaStore - 统一的数据访问接口
 * 向后兼容原 useKonaStore 的接口
 */
export function useKonaStore() {
  const authStore = useAuthStore()
  const portfolioStore = usePortfolioStore()
  const quoteStore = useQuoteStore()
  const marketStore = useMarketStore()
  const syncStore = useSyncStore()

  const currentUserId = String(authStore.userId || '').trim() || 'guest'
  if (hydratedCacheUserId !== currentUserId) {
    syncStore.hydrateStoreCache(authStore, portfolioStore, marketStore, quoteStore)
    hydratedCacheUserId = currentUserId
  }

  // ───────────────────────────────────────────────────────────────
  // Computed - 向后兼容
  // ───────────────────────────────────────────────────────────────

  const state = reactive({
    get bootstrapped() { return authStore.bootstrapped },
    get loading() { return portfolioStore.loading || quoteStore.loading || marketStore.loading },
    get token() { return authStore.token },
    get refreshToken() { return authStore.refreshToken },
    get user() { return authStore.user },
    get authError() { return authStore.authError },
    get portfolio() { return portfolioStore.portfolio },
    get quotes() { return quoteStore.quotes },
    get marketStatus() { return marketStore.marketStatus },
    get allClosed() { return marketStore.allClosed },
    get rates() { return marketStore.rates },
    get quotePolicy() { return quoteStore.quotePolicy },
    get syncVersions() { return syncStore.syncVersions },
  })

  const rows = computed(() => portfolioStore.rows)
  const summary = computed(() => portfolioStore.summary)

  const isAuthenticated = computed(() => authStore.isAuthenticated)
  const isAdmin = computed(() => authStore.isAdmin)

  // ───────────────────────────────────────────────────────────────
  // Auth Actions
  // ───────────────────────────────────────────────────────────────

  const bootstrap = () => authStore.bootstrap()
  const login = (username: string, password: string) => authStore.login(username, password)
  const register = (username: string, password: string, inviteCode: string) =>
    authStore.register(username, password, inviteCode)
  const logout = () => authStore.logout()

  // ───────────────────────────────────────────────────────────────
  // Portfolio Actions
  // ───────────────────────────────────────────────────────────────

  const loadPortfolio = () => portfolioStore.loadPortfolio()
  const markPortfolioDirty = () => syncStore.markPortfolioDirty()

  // ───────────────────────────────────────────────────────────────
  // Quote Actions
  // ───────────────────────────────────────────────────────────────

  const loadQuotes = async () => {
    const codes = portfolioStore.portfolio.map((item) => String(item.code || '')).filter(Boolean)
    await quoteStore.loadQuotes(codes)
  }

  const loadQuotesProgressive = async () => {
    const codes = portfolioStore.portfolio.map((item) => String(item.code || '')).filter(Boolean)
    await quoteStore.loadQuotesProgressive(codes)
  }

  // ───────────────────────────────────────────────────────────────
  // Market Actions
  // ───────────────────────────────────────────────────────────────

  const loadMarketStatus = () => marketStore.loadMarketStatus()
  const markRatesDirty = () => syncStore.markRatesDirty()

  // ───────────────────────────────────────────────────────────────
  // Sync Actions
  // ───────────────────────────────────────────────────────────────

  const refreshAll = async () => {
    portfolioStore.loading = true
    try {
      await refreshStaticOnly()
      void refreshQuotesOnly()
    } finally {
      portfolioStore.loading = false
    }
  }

  const refreshAllForce = async () => {
    syncStore.invalidateSyncVersion()
    await refreshAll()
  }

  const refreshStaticOnly = async () => {
    try {
      await syncStore.loadBootstrap('portfolio' as any)
      if (!portfolioStore.portfolio.length) {
        await portfolioStore.loadPortfolio()
      }
      if (!Object.keys(marketStore.rates || {}).length) {
        await marketStore.loadRates()
      }
    } catch {
      await Promise.all([
        portfolioStore.loadPortfolio(),
        marketStore.loadMarketStatus(),
        marketStore.loadRates(),
      ])
    }
    syncStore.persistStoreCache(authStore, portfolioStore, marketStore, quoteStore, 'static')
  }

  const refreshQuotesOnly = async () => {
    try {
      const changed = await syncStore.loadBootstrap('portfolio' as any)
      if (!portfolioStore.portfolio.length && !changed.has('portfolio')) {
        await portfolioStore.loadPortfolio()
      }
    } catch {
      await marketStore.loadMarketStatus()
    }

    await loadQuotesProgressive()
    syncStore.persistStoreCache(authStore, portfolioStore, marketStore, quoteStore, 'full')
  }

  const startAutoRefresh = () => {
    quoteStore.startAutoRefresh()
    // 启动定时刷新
    const refreshCallback = () => refreshQuotesOnly()
    quoteStore.scheduleAutoRefresh(
      800,
      marketStore.hasAnyOpenMarket,
      false, // TODO: 实现 hasUsExtendedActive
      refreshCallback
    )
  }

  const stopAutoRefresh = () => {
    quoteStore.stopAutoRefresh()
  }

  // ───────────────────────────────────────────────────────────────
  // Return
  // ───────────────────────────────────────────────────────────────

  return {
    // State（向后兼容）
    state,
    rows,
    summary,

    // Computed（向后兼容）
    isAuthenticated,
    isAdmin,

    // Auth Actions
    bootstrap,
    login,
    register,
    logout,

    // Portfolio Actions
    loadPortfolio,
    markPortfolioDirty,

    // Quote Actions
    loadQuotes,
    loadQuotesProgressive,

    // Market Actions
    loadMarketStatus,
    markRatesDirty,

    // Sync Actions
    refreshAll,
    refreshAllForce,
    refreshStaticOnly,
    refreshQuotesOnly,
    startAutoRefresh,
    stopAutoRefresh,
  }
}

/**
 * useAuth - 认证相关快捷访问
 */
export function useAuth() {
  const authStore = useAuthStore()
  return {
    ...authStore,
    isAuthenticated: authStore.isAuthenticated,
    isAdmin: authStore.isAdmin,
  }
}

/**
 * usePortfolio - 投资组合相关快捷访问
 */
export function usePortfolio() {
  const portfolioStore = usePortfolioStore()
  return {
    ...portfolioStore,
    summary: portfolioStore.summary,
  }
}

/**
 * useMarket - 市场相关快捷访问
 */
export function useMarket() {
  const marketStore = useMarketStore()
  return {
    ...marketStore,
    hasAnyOpenMarket: marketStore.hasAnyOpenMarket,
  }
}

/**
 * useQuote - 行情相关快捷访问
 */
export function useQuote() {
  const quoteStore = useQuoteStore()
  return {
    ...quoteStore,
  }
}
