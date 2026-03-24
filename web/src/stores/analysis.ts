/**
 * Analysis Store - 统一管理分析页的数据加载、缓存和周期选择
 */

import { computed, reactive, ref } from 'vue'
import { defineStore } from 'pinia'
import { api, type ApiError } from '@/shared/http'
import { toNumber } from '@/shared/format'
import { readPageCache, writePageCache } from '@/shared/pageCache'
import { useAuthStore } from './auth'
import { useRefreshCoordinatorStore } from './refreshCoordinator'

export type AnalysisCalendarType = 'day' | 'month' | 'year'
export type AnalysisPeriodKey = 'day' | 'month' | 'year' | 'all'

type AnalysisOverviewItem = {
  pnl?: number
  pnl_rate?: number
}

type AnalysisCalendarItem = {
  label?: string | number
  pnl?: number | null
}

type AnalysisCalendarPayload = {
  code?: string
  title?: string
  items?: AnalysisCalendarItem[]
  total_pnl?: number
  total_rate?: number
  period?: {
    time_type?: AnalysisCalendarType
    year?: number
    month?: number
  }
  selectable?: {
    day?: {
      years?: number[]
      months_by_year?: Record<string, number[]>
    }
    month?: {
      years?: number[]
    }
  }
}

export type AnalysisRankItem = {
  code: string
  name?: string
  pnl?: number
  pnl_rate?: number
  market?: string
  curr?: string
  ledger_name?: string
}

type AnalysisCachePayload = {
  overview: Record<AnalysisPeriodKey, AnalysisOverviewItem>
  calendarState: {
    title: string
    items: AnalysisCalendarItem[]
    totalPnl: number | null
    totalRate: number | null
  }
  rank: {
    gain: AnalysisRankItem[]
    loss: AnalysisRankItem[]
  }
  calendarType: AnalysisCalendarType
  rankType: 'profit' | 'loss'
  selectedDayYear: number | null
  selectedDayMonth: number | null
  selectedMonthYear: number | null
  selectableDayYears: number[]
  selectableDayMonthsByYear: Record<string, number[]>
  selectableMonthYears: number[]
}

const ANALYSIS_CACHE_DOMAIN = 'analysis'
const ANALYSIS_CACHE_KEY = 'page'
const ANALYSIS_CACHE_TTL_MS = 5 * 60_000

function invalidCalendarPeriodPayload(error: unknown): AnalysisCalendarPayload | null {
  const apiError = error as ApiError
  if (!apiError || apiError.status !== 400) return null
  const payload = apiError.payload
  if (!payload || typeof payload !== 'object') return null
  const data = payload as Record<string, unknown>
  if (String(data.code || '') !== 'INVALID_CALENDAR_PERIOD') return null
  return data as AnalysisCalendarPayload
}

function parseLabelKey(label: string | number | undefined): number | null {
  const text = String(label ?? '').trim()
  const matches = text.match(/\d+/g)
  return matches ? Number(matches[matches.length - 1]) : null
}

function normalizeYearList(values: unknown[]): number[] {
  return values.map((value) => Number(value)).filter((value) => value > 0).sort((a, b) => a - b)
}

function lastOrNull(values: number[]): number | null {
  return values.length ? (values[values.length - 1] ?? null) : null
}

export const useAnalysisStore = defineStore('analysis', () => {
  const authStore = useAuthStore()
  const refreshCoordinatorStore = useRefreshCoordinatorStore()

  const overview = reactive<Record<AnalysisPeriodKey, AnalysisOverviewItem>>({
    day: {},
    month: {},
    year: {},
    all: {},
  })

  const calendarState = reactive({
    title: '',
    items: [] as AnalysisCalendarItem[],
    totalPnl: null as number | null,
    totalRate: null as number | null,
  })

  const rank = reactive<{ gain: AnalysisRankItem[]; loss: AnalysisRankItem[] }>({
    gain: [],
    loss: [],
  })

  const calendarType = ref<AnalysisCalendarType>('day')
  const rankType = ref<'profit' | 'loss'>('profit')
  const selectedDayYear = ref<number | null>(null)
  const selectedDayMonth = ref<number | null>(null)
  const selectedMonthYear = ref<number | null>(null)
  const selectableDayYears = ref<number[]>([])
  const selectableDayMonthsByYear = ref<Record<string, number[]>>({})
  const selectableMonthYears = ref<number[]>([])

  const pickerYears = computed(() => {
    if (calendarType.value === 'day') return selectableDayYears.value
    if (calendarType.value === 'month') return selectableMonthYears.value
    return []
  })

  const pickerSelectedYear = computed(() => {
    if (calendarType.value === 'day') return selectedDayYear.value
    if (calendarType.value === 'month') return selectedMonthYear.value
    return null
  })

  const pickerMonths = computed(() => {
    if (calendarType.value !== 'day') return []
    const year = selectedDayYear.value
    if (!year) return []
    return selectableDayMonthsByYear.value[String(year)] || []
  })

  const pickerSelectedMonth = computed(() => selectedDayMonth.value)

  const filteredRankItems = computed(() => {
    const source = rankType.value === 'profit' ? rank.gain : rank.loss
    return [...(source || [])].slice(0, 10)
  })

  const calendarSummaryLabel = computed(() => {
    if (calendarType.value === 'day') return '当月累计'
    if (calendarType.value === 'month') return '当年累计'
    return '历史累计'
  })

  const calendarGrid = computed(() => {
    const now = new Date()
    const grid: Array<{ key: number; pnl: number | null }> = []

    if (calendarType.value === 'day') {
      const year = selectedDayYear.value ?? now.getFullYear()
      const month = selectedDayMonth.value ?? now.getMonth() + 1
      const daysInMonth = new Date(year, month, 0).getDate()
      for (let day = 1; day <= daysInMonth; day += 1) grid.push({ key: day, pnl: null })
    } else if (calendarType.value === 'month') {
      for (let month = 1; month <= 12; month += 1) grid.push({ key: month, pnl: null })
    } else {
      const thisYear = now.getFullYear()
      for (let index = 0; index < 5; index += 1) grid.push({ key: thisYear - 4 + index, pnl: null })
    }

    const pnlMap = new Map<number, number>()
    for (const item of calendarState.items) {
      const key = parseLabelKey(item?.label)
      if (key !== null) pnlMap.set(key, toNumber(item?.pnl))
    }

    return grid.map((item) => ({
      ...item,
      pnl: pnlMap.has(item.key) ? Number(pnlMap.get(item.key)) : null,
    }))
  })

  let reloadInflight: Promise<void> | null = null
  let calendarRequestId = 0

  function cacheUserId(): string {
    return String(authStore.user?.id || 'guest')
  }

  function getDayMonths(year: number | null): number[] {
    return year ? (selectableDayMonthsByYear.value[String(year)] || []) : []
  }

  function persistAnalysisCache() {
    writePageCache<AnalysisCachePayload>(
      ANALYSIS_CACHE_DOMAIN,
      ANALYSIS_CACHE_KEY,
      cacheUserId(),
      {
        overview,
        calendarState,
        rank,
        calendarType: calendarType.value,
        rankType: rankType.value,
        selectedDayYear: selectedDayYear.value,
        selectedDayMonth: selectedDayMonth.value,
        selectedMonthYear: selectedMonthYear.value,
        selectableDayYears: selectableDayYears.value,
        selectableDayMonthsByYear: selectableDayMonthsByYear.value,
        selectableMonthYears: selectableMonthYears.value,
      },
      ANALYSIS_CACHE_TTL_MS,
    )
  }

  function restoreAnalysisCache(): boolean {
    const cached = readPageCache<AnalysisCachePayload>(
      ANALYSIS_CACHE_DOMAIN,
      ANALYSIS_CACHE_KEY,
      cacheUserId(),
      ANALYSIS_CACHE_TTL_MS,
    )
    if (!cached) return false
    Object.assign(overview, cached.overview)
    Object.assign(calendarState, cached.calendarState)
    Object.assign(rank, cached.rank)
    calendarType.value = cached.calendarType
    rankType.value = cached.rankType || 'profit'
    selectedDayYear.value = cached.selectedDayYear
    selectedDayMonth.value = cached.selectedDayMonth
    selectedMonthYear.value = cached.selectedMonthYear
    selectableDayYears.value = cached.selectableDayYears
    selectableDayMonthsByYear.value = cached.selectableDayMonthsByYear
    selectableMonthYears.value = cached.selectableMonthYears
    return true
  }

  function ensureDaySelection() {
    const years = selectableDayYears.value
    if (!years.length) return
    if (!selectedDayYear.value || !years.includes(selectedDayYear.value)) {
      selectedDayYear.value = lastOrNull(years)
    }
    const months = getDayMonths(selectedDayYear.value)
    if (!months.length) return
    if (!selectedDayMonth.value || !months.includes(selectedDayMonth.value)) {
      selectedDayMonth.value = lastOrNull(months)
    }
  }

  function ensureMonthSelection() {
    const years = selectableMonthYears.value
    if (years.length && (!selectedMonthYear.value || !years.includes(selectedMonthYear.value))) {
      selectedMonthYear.value = lastOrNull(years)
    }
  }

  function applyCalendarSelectable(payload: AnalysisCalendarPayload) {
    const daySelectable = payload.selectable?.day
    selectableDayYears.value = normalizeYearList(daySelectable?.years || [])
    selectableDayMonthsByYear.value = daySelectable?.months_by_year || {}
    selectableMonthYears.value = normalizeYearList(payload.selectable?.month?.years || [])
  }

  function syncCalendarSelectionFromPayload(payload: AnalysisCalendarPayload) {
    const period = payload.period
    if (calendarType.value === 'day') {
      const nextYear = Number(period?.year)
      const nextMonth = Number(period?.month)
      if (Number.isFinite(nextYear) && nextYear > 0) {
        selectedDayYear.value = nextYear
      }
      if (Number.isFinite(nextMonth) && nextMonth > 0) {
        selectedDayMonth.value = nextMonth
      }
      ensureDaySelection()
      return
    }

    if (calendarType.value === 'month') {
      const nextYear = Number(period?.year)
      if (Number.isFinite(nextYear) && nextYear > 0) {
        selectedMonthYear.value = nextYear
      }
      ensureMonthSelection()
    }
  }

  async function loadOverview() {
    const payload = await api.get<Record<string, AnalysisOverviewItem>>('/api/analysis/overview?period=all')
    Object.assign(overview, payload)
  }

  async function loadCalendar(recoverOnInvalid = true) {
    const requestId = ++calendarRequestId
    const params = new URLSearchParams({ type: calendarType.value })

    if (calendarType.value === 'day') {
      ensureDaySelection()
      if (selectedDayYear.value && selectedDayMonth.value) {
        params.set('year', String(selectedDayYear.value))
        params.set('month', String(selectedDayMonth.value))
      }
    } else if (calendarType.value === 'month' && selectedMonthYear.value) {
      params.set('year', String(selectedMonthYear.value))
    }

    try {
      const payload = await api.get<AnalysisCalendarPayload>(`/api/analysis/calendar?${params.toString()}`)
      if (requestId !== calendarRequestId) return

      applyCalendarSelectable(payload)
      syncCalendarSelectionFromPayload(payload)
      calendarState.title = payload.title || ''
      calendarState.items = payload.items || []
      calendarState.totalPnl = payload.total_pnl == null ? null : toNumber(payload.total_pnl)
      calendarState.totalRate = payload.total_rate == null ? null : toNumber(payload.total_rate)
    } catch (error) {
      const invalidPayload = invalidCalendarPeriodPayload(error)
      if (recoverOnInvalid && invalidPayload) {
        applyCalendarSelectable(invalidPayload)
        syncCalendarSelectionFromPayload(invalidPayload)
        await loadCalendar(false)
      }
    }
  }

  async function loadRank() {
    const payload = await api.get<{ gain?: AnalysisRankItem[]; loss?: AnalysisRankItem[] }>(
      '/api/analysis/rank?type=all&market=all'
    )
    rank.gain = payload.gain || []
    rank.loss = payload.loss || []
  }

  async function reload(mode: 'light' | 'force' = 'light', includeAnalysis = true) {
    if (reloadInflight) return reloadInflight

    reloadInflight = (async () => {
      try {
        if (mode === 'force') await refreshCoordinatorStore.refreshAll()
        else await refreshCoordinatorStore.refreshStaticOnly()
      } catch {
        // 静态刷新失败时，分析页自己的接口仍然继续兜底加载
      }

      if (includeAnalysis) {
        await Promise.all([loadOverview()])
        await Promise.all([loadCalendar(), loadRank()])
      }
      persistAnalysisCache()
    })()

    try {
      await reloadInflight
    } finally {
      reloadInflight = null
    }
  }

  function onPickYear(year: number) {
    if (calendarType.value === 'day') {
      selectedDayYear.value = year
      const months = selectableDayMonthsByYear.value[String(year)] || []
      if (months.length && (!selectedDayMonth.value || !months.includes(selectedDayMonth.value))) {
        selectedDayMonth.value = months[months.length - 1] ?? null
      }
      void loadCalendar().then(() => persistAnalysisCache())
    } else if (calendarType.value === 'month') {
      selectedMonthYear.value = year
      void loadCalendar().then(() => persistAnalysisCache())
    }
  }

  function onPickMonth(month: number) {
    selectedDayMonth.value = month
    void loadCalendar().then(() => persistAnalysisCache())
  }

  function onCalendarTypeChange(nextType: AnalysisCalendarType) {
    calendarType.value = nextType
    if (nextType === 'day') ensureDaySelection()
    else if (nextType === 'month') ensureMonthSelection()
    void loadCalendar().then(() => persistAnalysisCache())
  }

  function initialize() {
    restoreAnalysisCache()
    void reload('light', true)
  }

  return {
    overview,
    calendarState,
    rank,
    calendarType,
    rankType,
    selectedDayYear,
    selectedDayMonth,
    selectedMonthYear,
    selectableDayYears,
    selectableDayMonthsByYear,
    selectableMonthYears,
    pickerYears,
    pickerSelectedYear,
    pickerMonths,
    pickerSelectedMonth,
    filteredRankItems,
    calendarSummaryLabel,
    calendarGrid,
    restoreAnalysisCache,
    loadOverview,
    loadCalendar,
    loadRank,
    reload,
    onPickYear,
    onPickMonth,
    onCalendarTypeChange,
    initialize,
  }
})
