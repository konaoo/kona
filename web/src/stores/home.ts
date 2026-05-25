/**
 * Home Store - 统一管理首页读侧状态和刷新编排
 */

import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/shared/http'
import { toNumber } from '@/shared/format'
import type { TrendItem } from '@/shared/assetTrend'
import { usePortfolioStore } from './portfolio'
import { useRefreshCoordinatorStore } from './refreshCoordinator'
import { useSessionCoordinatorStore } from './sessionCoordinator'
import type { PositionRow } from './types'

export type SimpleAsset = {
  id: number
  icon?: string
  name: string
  amount: number
  curr?: string
}

export type SnapshotPoint = {
  date: string
  total_asset: number
  day_pnl?: number
}

const MARKET_INDICES_CACHE_KEY = 'kaka:web:market-indices'
const HISTORY_POINTS_CACHE_KEY = 'kaka:web:home-history'

let staticRefreshTimer: number | null = null

function clearStaticRefreshTimer() {
  if (staticRefreshTimer !== null) {
    window.clearInterval(staticRefreshTimer)
    staticRefreshTimer = null
  }
}

function normalizeHistoryPoints(raw: unknown): SnapshotPoint[] {
  if (!Array.isArray(raw)) return []
  return raw
    .map((item) => ({
      date: String(item?.date || ''),
      total_asset: toNumber(item?.total_asset, 0),
      day_pnl: toNumber(item?.day_pnl, 0),
    }))
    .filter((item) => item.date)
}

export const useHomeStore = defineStore('home', () => {
  const portfolioStore = usePortfolioStore()
  const refreshCoordinatorStore = useRefreshCoordinatorStore()
  const sessionCoordinatorStore = useSessionCoordinatorStore()

  const pageLoading = ref(true)
  const cashAssets = ref<SimpleAsset[]>([])
  const otherAssets = ref<SimpleAsset[]>([])
  const liabilities = ref<SimpleAsset[]>([])
  const marketIndices = ref<any[]>([])
  const historyPoints = ref<SnapshotPoint[]>([])
  const chartLoading = ref(false)
  const chartError = ref('')
  const trendMap = ref<Record<string, TrendItem>>({})

  const rows = computed<PositionRow[]>(() => portfolioStore.rows)
  const rowTrendSignature = computed(() =>
    rows.value.map((row) => `${row?.code || ''}:${row?.name || ''}`).join('|'),
  )

  function restoreMarketIndicesCache() {
    try {
      const cached = localStorage.getItem(MARKET_INDICES_CACHE_KEY)
      if (!cached) return false
      const parsed = JSON.parse(cached)
      if (!Array.isArray(parsed) || !parsed.length) return false
      marketIndices.value = parsed
      return true
    } catch (error) {
      console.warn('Failed to restore market indices cache:', error)
      return false
    }
  }

  async function loadAssetLists() {
    try {
      const [cashRes, otherRes, liabilityRes] = await Promise.all([
        api.get<SimpleAsset[]>('/api/cash_assets'),
        api.get<SimpleAsset[]>('/api/other_assets'),
        api.get<SimpleAsset[]>('/api/liabilities'),
      ])
      cashAssets.value = cashRes || []
      otherAssets.value = otherRes || []
      liabilities.value = liabilityRes || []
    } catch (error) {
      console.error('Failed to load home asset lists:', error)
    }
  }

  async function loadMarketIndices() {
    try {
      const response = await api.get<any[]>('/api/market/indices')
      marketIndices.value = Array.isArray(response) ? response : []
      try {
        localStorage.setItem(MARKET_INDICES_CACHE_KEY, JSON.stringify(marketIndices.value))
      } catch (error) {
        console.warn('Failed to persist market indices cache:', error)
      }
    } catch (error) {
      console.error('Failed to load market indices:', error)
    }
  }

  async function loadHistory() {
    chartLoading.value = true
    chartError.value = ''
    try {
      const response = await api.get<SnapshotPoint[]>('/api/history?days=5000')
      const points = normalizeHistoryPoints(response)
      historyPoints.value = points
      try {
        localStorage.setItem(HISTORY_POINTS_CACHE_KEY, JSON.stringify(points))
      } catch (cacheError) {
        console.warn('Failed to persist home history cache:', cacheError)
      }
    } catch (error) {
      let cachedPoints: SnapshotPoint[] = []
      try {
        const cachedRaw = localStorage.getItem(HISTORY_POINTS_CACHE_KEY) || '[]'
        cachedPoints = normalizeHistoryPoints(JSON.parse(cachedRaw))
      } catch (cacheError) {
        console.warn('Failed to restore home history cache:', cacheError)
      }
      if (cachedPoints.length) {
        historyPoints.value = cachedPoints
        chartError.value = ''
      } else {
        chartError.value = error instanceof Error ? error.message : '历史快照加载失败'
        historyPoints.value = []
      }
      console.error('Failed to load home history:', error)
    } finally {
      chartLoading.value = false
    }
  }

  async function loadAssetTrends() {
    const items = rows.value
      .filter((row) => row?.code)
      .map((row) => ({
        code: String(row.code || ''),
        name: String(row.name || ''),
        market: String(row.category || row.market || ''),
      }))

    if (!items.length) {
      trendMap.value = {}
      return
    }

    try {
      const payload = await api.post<{ items?: Record<string, TrendItem> }>('/api/asset/trends', {
        items,
        points: 20,
      })
      trendMap.value = payload?.items || {}
    } catch (error) {
      console.error('Failed to load home asset trends:', error)
      trendMap.value = {}
    }
  }

  async function refreshHomeReadState() {
    try {
      await Promise.all([
        refreshCoordinatorStore.refreshStaticOnly(),
        loadAssetLists(),
        loadHistory(),
      ])
      await loadAssetTrends()
      void Promise.all([
        refreshCoordinatorStore.refreshQuotesOnly(),
        loadMarketIndices(),
      ])
    } catch (error) {
      console.error('Failed to refresh home read state:', error)
    }
  }

  function startHomeAutoRefresh() {
    refreshCoordinatorStore.startAutoRefresh()
    if (typeof window === 'undefined') return
    clearStaticRefreshTimer()
    staticRefreshTimer = window.setInterval(() => {
      void refreshHomeReadState()
    }, 60_000)
  }

  function stopHomeAutoRefresh() {
    refreshCoordinatorStore.stopAutoRefresh()
    if (typeof window === 'undefined') return
    clearStaticRefreshTimer()
  }

  async function initializePage() {
    pageLoading.value = true
    try {
      restoreMarketIndicesCache()
      void sessionCoordinatorStore.bootstrap()
      await refreshHomeReadState()
      startHomeAutoRefresh()
    } finally {
      pageLoading.value = false
    }
  }

  function disposePage() {
    stopHomeAutoRefresh()
  }

  return {
    pageLoading,
    cashAssets,
    otherAssets,
    liabilities,
    marketIndices,
    historyPoints,
    chartLoading,
    chartError,
    trendMap,
    rowTrendSignature,
    restoreMarketIndicesCache,
    loadAssetLists,
    loadMarketIndices,
    loadHistory,
    loadAssetTrends,
    refreshHomeReadState,
    initializePage,
    disposePage,
  }
})
