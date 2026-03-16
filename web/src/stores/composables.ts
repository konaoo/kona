/**
 * 组合式 API - 统一的数据访问接口
 * 提供类似原 useKonaStore 的接口，便于迁移
 */

import { computed, reactive, toRef } from 'vue'
import { useAuthStore } from './auth'
import { usePortfolioStore } from './portfolio'
import { useQuoteStore } from './quote'
import { useMarketStore } from './market'
import { useSyncStore } from './sync'
import { useRefreshCoordinatorStore } from './refreshCoordinator'
import { useSessionCoordinatorStore } from './sessionCoordinator'

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
  const refreshCoordinatorStore = useRefreshCoordinatorStore()
  const sessionCoordinatorStore = useSessionCoordinatorStore()

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

  const bootstrap = () => sessionCoordinatorStore.bootstrap()
  const login = (username: string, password: string) => sessionCoordinatorStore.login(username, password)
  const register = (username: string, password: string, inviteCode: string) =>
    sessionCoordinatorStore.register(username, password, inviteCode)
  const logout = () => sessionCoordinatorStore.logout()

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

  const refreshAll = refreshCoordinatorStore.refreshAll
  const refreshAllForce = refreshCoordinatorStore.refreshAllForce
  const refreshStaticOnly = refreshCoordinatorStore.refreshStaticOnly
  const refreshQuotesOnly = refreshCoordinatorStore.refreshQuotesOnly
  const startAutoRefresh = refreshCoordinatorStore.startAutoRefresh
  const stopAutoRefresh = refreshCoordinatorStore.stopAutoRefresh

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
    lastRefreshResult: toRef(refreshCoordinatorStore, 'lastRefreshResult'),
    lastBootstrapResult: toRef(authStore, 'lastBootstrapResult'),

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
