/**
 * Refresh Coordinator Store - 统一管理 Web 端刷新编排和页面恢复副作用
 */

import { ref } from 'vue'
import { defineStore } from 'pinia'
import { finishAsyncFlow, startAsyncFlow, type AsyncFlowResult } from '@/shared/asyncFlow'
import { useAuthStore } from './auth'
import { usePortfolioStore } from './portfolio'
import { useQuoteStore } from './quote'
import { useMarketStore } from './market'
import { useSyncStore } from './sync'

let hydratedCacheUserId = ''
let autoRefreshResumeHandlerBound = false
let autoRefreshResumeCallback: null | (() => Promise<void>) = null
let autoRefreshResumeInflight: Promise<void> | null = null

function handleAutoRefreshResume() {
  if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return
  if (!autoRefreshResumeCallback || autoRefreshResumeInflight) return
  autoRefreshResumeInflight = autoRefreshResumeCallback().finally(() => {
    autoRefreshResumeInflight = null
  })
}

function detachAutoRefreshResumeHandlers() {
  if (typeof window === 'undefined' || !autoRefreshResumeHandlerBound) return
  document.removeEventListener('visibilitychange', handleAutoRefreshResume)
  window.removeEventListener('focus', handleAutoRefreshResume)
  autoRefreshResumeHandlerBound = false
}

function attachAutoRefreshResumeHandlers() {
  if (typeof window === 'undefined' || autoRefreshResumeHandlerBound) return
  document.addEventListener('visibilitychange', handleAutoRefreshResume)
  window.addEventListener('focus', handleAutoRefreshResume)
  autoRefreshResumeHandlerBound = true
}

export const useRefreshCoordinatorStore = defineStore('refreshCoordinator', () => {
  const lastRefreshResult = ref<AsyncFlowResult | null>(null)

  function resolveStores() {
    return {
      authStore: useAuthStore(),
      portfolioStore: usePortfolioStore(),
      quoteStore: useQuoteStore(),
      marketStore: useMarketStore(),
      syncStore: useSyncStore(),
    }
  }

  function getPortfolioCodes() {
    const { portfolioStore } = resolveStores()
    return portfolioStore.portfolio.map((item) => String(item.code || '')).filter(Boolean)
  }

  function ensureHydrated() {
    const {
      authStore,
      portfolioStore,
      quoteStore,
      marketStore,
      syncStore,
    } = resolveStores()

    const currentUserId = String(authStore.userId || '').trim() || 'guest'
    if (hydratedCacheUserId === currentUserId) return

    syncStore.hydrateStoreCache(authStore, portfolioStore, marketStore, quoteStore)
    hydratedCacheUserId = currentUserId
  }

  async function refreshStaticOnly() {
    const flow = startAsyncFlow('web.store.refreshStaticOnly')
    const {
      authStore,
      portfolioStore,
      quoteStore,
      marketStore,
      syncStore,
    } = resolveStores()

    try {
      await syncStore.loadBootstrap(['portfolio', 'rates'])
      if (!portfolioStore.portfolio.length) {
        await portfolioStore.loadPortfolio()
      }
      if (!Object.keys(marketStore.rates || {}).length) {
        await marketStore.loadRates()
      }
      syncStore.persistStoreCache(authStore, portfolioStore, marketStore, quoteStore, 'static')
      lastRefreshResult.value = finishAsyncFlow(flow, 'bootstrap-hit')
      return lastRefreshResult.value
    } catch (error) {
      await Promise.all([
        portfolioStore.loadPortfolio(),
        marketStore.loadMarketStatus(),
        marketStore.loadRates(),
      ])
      syncStore.persistStoreCache(authStore, portfolioStore, marketStore, quoteStore, 'static')
      lastRefreshResult.value = finishAsyncFlow(flow, 'fallback-load', error)
      return lastRefreshResult.value
    }
  }

  async function refreshQuotesOnly() {
    const flow = startAsyncFlow('web.store.refreshQuotesOnly')
    const {
      authStore,
      portfolioStore,
      quoteStore,
      marketStore,
      syncStore,
    } = resolveStores()

    try {
      const changed = await syncStore.loadBootstrap(['portfolio'])
      if (!portfolioStore.portfolio.length && !changed.has('portfolio')) {
        await portfolioStore.loadPortfolio()
      }
    } catch (error) {
      await marketStore.loadMarketStatus()
      lastRefreshResult.value = finishAsyncFlow(flow, 'market-status-fallback', error)
    }

    await quoteStore.loadQuotesProgressive(getPortfolioCodes())
    syncStore.persistStoreCache(authStore, portfolioStore, marketStore, quoteStore, 'full')
    lastRefreshResult.value = finishAsyncFlow(flow, 'quotes-finished')
    return lastRefreshResult.value
  }

  async function refreshAll() {
    const flow = startAsyncFlow('web.store.refreshAll')
    const { portfolioStore } = resolveStores()

    portfolioStore.loading = true
    try {
      await refreshStaticOnly()
      void refreshQuotesOnly()
      lastRefreshResult.value = finishAsyncFlow(flow, 'static-finished')
      return lastRefreshResult.value
    } catch (error) {
      lastRefreshResult.value = finishAsyncFlow(flow, 'failed', error)
      throw error
    } finally {
      portfolioStore.loading = false
    }
  }

  async function refreshAllForce() {
    const { syncStore } = resolveStores()
    syncStore.invalidateSyncVersion()
    await refreshAll()
  }

  function startAutoRefresh() {
    const { quoteStore, marketStore } = resolveStores()
    quoteStore.startAutoRefresh()

    const refreshCallback = async () => {
      try {
        await refreshQuotesOnly()
      } finally {
        quoteStore.scheduleAutoRefresh(
          undefined,
          marketStore.hasAnyOpenMarket,
          false,
          refreshCallback
        )
      }
    }

    autoRefreshResumeCallback = async () => {
      await refreshStaticOnly()
      await refreshCallback()
    }
    attachAutoRefreshResumeHandlers()

    quoteStore.scheduleAutoRefresh(
      800,
      marketStore.hasAnyOpenMarket,
      false,
      refreshCallback
    )
  }

  function stopAutoRefresh() {
    const { quoteStore } = resolveStores()
    quoteStore.stopAutoRefresh()
    autoRefreshResumeCallback = null
    detachAutoRefreshResumeHandlers()
  }

  return {
    lastRefreshResult,
    ensureHydrated,
    refreshAll,
    refreshAllForce,
    refreshStaticOnly,
    refreshQuotesOnly,
    startAutoRefresh,
    stopAutoRefresh,
  }
})
