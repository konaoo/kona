import { ref, type Ref } from 'vue'
import { api } from '@/shared/http'
import type { TrendItem } from '@/shared/assetTrend'
import { useKonaStore } from '@/stores/composables'
import { useRealtimeTodayStore } from '@/stores/realtimeToday'

type TrendRequestItem = {
  code: string
  name: string
  market: string
}

type InvestReadStateStore = {
  refreshStaticOnly: () => Promise<unknown>
  refreshQuotesOnly: () => unknown
  startAutoRefresh: () => void
  stopAutoRefresh: () => void
}

type InvestRealtimeTodayStore = {
  load: () => Promise<unknown>
}

type TimerId = ReturnType<typeof setInterval>

export type CreateInvestReadStateDeps = {
  rows: Ref<Record<string, unknown>[]>
  trendMap: Ref<Record<string, TrendItem>>
  apiPost: <T>(url: string, body?: unknown) => Promise<T>
  store: InvestReadStateStore
  realtimeTodayStore: InvestRealtimeTodayStore
  setIntervalFn?: (handler: () => void, timeout: number) => TimerId
  clearIntervalFn?: (timerId: TimerId) => void
}

export function createInvestReadState({
  rows,
  trendMap,
  apiPost,
  store,
  realtimeTodayStore,
  setIntervalFn,
  clearIntervalFn
}: CreateInvestReadStateDeps) {
  let staticRefreshTimer: TimerId | null = null

  function buildTrendRequestItems(): TrendRequestItem[] {
    return (rows.value || [])
      .filter(row => row?.code)
      .map(row => ({
        code: String(row.code || ''),
        name: String(row.name || ''),
        market: String(row.category || row.market || '')
      }))
  }

  async function loadAssetTrends() {
    const items = buildTrendRequestItems()

    if (!items.length) {
      trendMap.value = {}
      return
    }

    try {
      const payload = await apiPost<{ items?: Record<string, TrendItem> }>('/api/asset/trends', {
        items,
        points: 20
      })
      trendMap.value = payload?.items || {}
    } catch (error) {
      console.error('Failed to load invest asset trends', error)
      trendMap.value = {}
    }
  }

  async function refreshInvestReadState() {
    try {
      await store.refreshStaticOnly()
      await realtimeTodayStore.load()
      await loadAssetTrends()
      void store.refreshQuotesOnly()
    } catch (error) {
      console.error('Failed to refresh invest data', error)
    }
  }

  function clearStaticRefreshTimer() {
    if (staticRefreshTimer == null || !clearIntervalFn) return
    clearIntervalFn(staticRefreshTimer)
    staticRefreshTimer = null
  }

  function startInvestAutoRefresh() {
    store.startAutoRefresh()
    if (!setIntervalFn) return
    clearStaticRefreshTimer()
    staticRefreshTimer = setIntervalFn(() => {
      void refreshInvestReadState()
    }, 60_000)
  }

  function stopInvestAutoRefresh() {
    store.stopAutoRefresh()
    clearStaticRefreshTimer()
  }

  return {
    trendMap,
    buildTrendRequestItems,
    loadAssetTrends,
    refreshInvestReadState,
    startInvestAutoRefresh,
    stopInvestAutoRefresh
  }
}

export function useInvestReadState(rows: Ref<Record<string, unknown>[]>) {
  const store = useKonaStore()
  const realtimeTodayStore = useRealtimeTodayStore()
  const trendMap = ref<Record<string, TrendItem>>({})
  const hasWindow = typeof window !== 'undefined'

  return createInvestReadState({
    rows,
    trendMap,
    apiPost: (url, body) => api.post(url, body),
    store,
    realtimeTodayStore,
    setIntervalFn: hasWindow ? window.setInterval.bind(window) : undefined,
    clearIntervalFn: hasWindow ? window.clearInterval.bind(window) : undefined
  })
}
