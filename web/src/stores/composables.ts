/**
 * 组合式 API - 统一的数据访问接口
 * 提供类似原 useKonaStore 的接口，便于迁移
 */

import { computed } from 'vue'
import { useAuthStore } from './auth'
import { usePortfolioStore } from './portfolio'
import { useQuoteStore } from './quote'
import { useMarketStore } from './market'
import { useSyncStore } from './sync'

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

  // ───────────────────────────────────────────────────────────────
  // Computed - 向后兼容
  // ───────────────────────────────────────────────────────────────

  const state = computed(() => ({
    bootstrapped: authStore.bootstrapped,
    loading: portfolioStore.loading || quoteStore.loading || marketStore.loading,
    token: authStore.token,
    refreshToken: authStore.refreshToken,
    user: authStore.user,
    authError: authStore.authError,
    portfolio: portfolioStore.portfolio,
    quotes: quoteStore.quotes,
    marketStatus: marketStore.marketStatus,
    allClosed: marketStore.allClosed,
    rates: marketStore.rates,
    quotePolicy: quoteStore.quotePolicy,
    syncVersions: syncStore.syncVersions,
  }))

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
      try {
        await syncStore.loadBootstrap('portfolio' as any)
        if (!portfolioStore.portfolio.length) {
          await portfolioStore.loadPortfolio()
        }
      } catch {
        await Promise.all([marketStore.loadMarketStatus(), portfolioStore.loadPortfolio()])
      }
      await loadQuotes()
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
    } catch {
      await Promise.all([portfolioStore.loadPortfolio(), marketStore.loadMarketStatus()])
    }
  }

  const refreshQuotesOnly = async () => {
    try {
      const changed = await syncStore.loadBootstrap('portfolio' as any)
      if (!portfolioStore.portfolio.length && !changed.has('portfolio')) {
        await portfolioStore.loadPortfolio()
      }
      await loadQuotes()
    } catch {
      await marketStore.loadMarketStatus()
    }

    await loadQuotes()
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
