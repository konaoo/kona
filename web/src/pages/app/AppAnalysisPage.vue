<template>
  <LegacyAppShell>
    <section class="legacy-section">
      <div class="section-header">
        <h2 class="section-title">收益概览</h2>
        <button class="legacy-btn-primary" @click="onManualRefresh">刷新</button>
      </div>
      <div class="milestone-grid">
        <article class="milestone-card" v-for="item in overviewCards" :key="item.key">
          <div class="milestone-title">{{ item.label }}</div>
          <div class="milestone-main" :class="valueClass(item.pnl)">
            {{ formatCny(item.pnl) }}
          </div>
          <div class="milestone-rate" :class="valueClass(item.rate)">
            {{ formatPct(item.rate) }}
          </div>
        </article>
      </div>
    </section>

    <section class="legacy-section">
      <div class="section-header calendar-section-header">
        <h2 class="section-title">收益日历</h2>
        <div class="calendar-header-controls">
          <div class="calendar-period-picker" v-if="calendarType !== 'year'">
            <template v-if="calendarType === 'day'">
              <select class="period-select" v-model.number="selectedDayYear" @change="onDayYearChange">
                <option v-for="year in selectableDayYears" :key="`day-year-${year}`" :value="year">
                  {{ year }}年
                </option>
              </select>
              <select class="period-select" v-model.number="selectedDayMonth" @change="onDayMonthChange">
                <option v-for="month in dayMonthOptions" :key="`day-month-${month}`" :value="month">
                  {{ month }}月
                </option>
              </select>
            </template>
            <template v-else>
              <select class="period-select" v-model.number="selectedMonthYear" @change="onMonthYearChange">
                <option v-for="year in selectableMonthYears" :key="`month-year-${year}`" :value="year">
                  {{ year }}年
                </option>
              </select>
            </template>
          </div>

          <div class="view-tabs">
            <button class="view-tab" :class="{ active: calendarType === 'day' }" @click="onCalendarTypeChange('day')">日</button>
            <button class="view-tab" :class="{ active: calendarType === 'month' }" @click="onCalendarTypeChange('month')">月</button>
            <button class="view-tab" :class="{ active: calendarType === 'year' }" @click="onCalendarTypeChange('year')">年</button>
          </div>
        </div>
      </div>

      <div class="calendar-title">{{ calendarState.title || '收益日历' }}</div>

      <div class="calendar-grid-shell">
        <div class="calendar-grid" :style="{ gridTemplateColumns: `repeat(${calendarColumns}, minmax(0, 1fr))` }">
          <article
            class="calendar-cell"
            v-for="cell in calendarGrid"
            :key="`calendar-${calendarType}-${cell.key}`"
            :class="calendarCellClass(cell.pnl)"
          >
            <div class="calendar-cell-label">{{ formatCalendarCellLabel(cell.key) }}</div>
            <div class="calendar-cell-value" v-if="cell.pnl !== null">{{ formatCalendarCellPnl(cell.pnl) }}</div>
            <div class="calendar-cell-value" v-else>-</div>
          </article>
        </div>
      </div>

      <div class="calendar-summary">
        <span>{{ calendarSummaryLabel }}</span>
        <span :class="valueClass(calendarState.totalPnl)">{{ formatCny(calendarState.totalPnl) }}</span>
        <span :class="valueClass(calendarState.totalRate)">({{ formatPct(calendarState.totalRate) }})</span>
      </div>
    </section>

    <section class="legacy-section">
      <div class="section-header rank-section-header">
        <h2 class="section-title">盈亏排行</h2>
        <button class="legacy-btn-primary" @click="loadRank">刷新排行</button>
      </div>

      <div class="rank-controls">
        <div class="market-tabs">
          <button
            v-for="tab in marketTabs"
            :key="tab.key"
            class="market-tab"
            :class="{ active: rankMarket === tab.key }"
            @click="onRankMarketChange(tab.key)"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>

      <div class="rank-list" v-if="visibleRankItems.length">
        <article class="rank-item" v-for="(item, idx) in visibleRankItems" :key="`rank-${item.code}-${idx}`">
          <div class="rank-left">
            <span class="rank-badge" :class="rankBadgeClass(idx + 1)">{{ idx + 1 }}</span>
            <div class="rank-asset-meta">
              <span class="rank-asset-name">{{ item.name || item.code }}</span>
              <span class="rank-asset-code">{{ formatDisplayCode(item.code) }}</span>
            </div>
          </div>

          <div class="rank-right" :class="valueClass(rankPnlCny(item))">
            <div class="rank-pnl">{{ formatCny(rankPnlCny(item)) }}</div>
            <div class="rank-rate">{{ formatPct(toNum(item.pnl_rate)) }}</div>
          </div>
        </article>

        <button
          v-if="hasMoreRankItems"
          class="rank-expand-btn"
          @click="rankExpanded = !rankExpanded"
        >
          {{ rankExpanded ? '收起' : '查看更多' }}
        </button>
      </div>

      <div class="rank-empty" v-else>
        暂无数据
      </div>
    </section>
  </LegacyAppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import LegacyAppShell from '../../layouts/LegacyAppShell.vue'
import { api } from '../../shared/http'
import { toNumber } from '../../shared/format'
import { readPageCache, writePageCache } from '../../shared/pageCache'
import { useKonaStore } from '../../shared/store'

type CalendarType = 'day' | 'month' | 'year'
type RankMarket = 'all' | 'a' | 'hk' | 'us' | 'fund'
type PeriodKey = 'day' | 'month' | 'year' | 'all'

type OverviewItem = {
  pnl?: number
  pnl_rate?: number
}

type CalendarItem = {
  label?: string | number
  pnl?: number | null
}

type CalendarPayload = {
  title?: string
  items?: CalendarItem[]
  total_pnl?: number
  total_rate?: number
  period?: {
    time_type?: CalendarType
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

type RankItem = {
  code: string
  name?: string
  pnl?: number
  pnl_rate?: number
  market?: RankMarket | string
  curr?: string
}

type AnalysisCachePayload = {
  overview: Record<PeriodKey, OverviewItem>
  calendarState: {
    title: string
    items: CalendarItem[]
    totalPnl: number
    totalRate: number
  }
  rank: {
    gain: RankItem[]
    loss: RankItem[]
  }
  rates: Record<string, number>
  calendarType: CalendarType
  rankMarket: RankMarket
  selectedDayYear: number | null
  selectedDayMonth: number | null
  selectedMonthYear: number | null
  selectableDayYears: number[]
  selectableDayMonthsByYear: Record<string, number[]>
  selectableMonthYears: number[]
  storePortfolio: unknown[]
  storeQuotes: Record<string, unknown>
  storeRates: Record<string, number>
  storeMarketStatus: Record<string, unknown>
  storeAllClosed: boolean
}

const ANALYSIS_CACHE_DOMAIN = 'analysis'
const ANALYSIS_CACHE_KEY = 'page'
const ANALYSIS_CACHE_TTL_MS = 5 * 60_000

const periods: Record<PeriodKey, { label: string }> = {
  day: { label: '今日' },
  month: { label: '本月' },
  year: { label: '今年' },
  all: { label: '累计' },
}

const marketTabs = [
  { key: 'all', label: '全部市场' },
  { key: 'a', label: 'A股' },
  { key: 'hk', label: '港股' },
  { key: 'us', label: '美股' },
  { key: 'fund', label: '基金' },
] as const

const overview = reactive<Record<PeriodKey, OverviewItem>>({
  day: {},
  month: {},
  year: {},
  all: {},
})

const calendarState = reactive({
  title: '',
  items: [] as CalendarItem[],
  totalPnl: 0,
  totalRate: 0,
})

const rank = reactive<{ gain: RankItem[]; loss: RankItem[] }>({
  gain: [],
  loss: [],
})

const rates = reactive<Record<string, number>>({})
const store = useKonaStore()
const realtimeDayReady = ref(false)
let reloadInflight: Promise<void> | null = null

const calendarType = ref<CalendarType>('day')
const rankMarket = ref<RankMarket>('all')
const rankExpanded = ref(false)

const selectedDayYear = ref<number | null>(null)
const selectedDayMonth = ref<number | null>(null)
const selectedMonthYear = ref<number | null>(null)

const selectableDayYears = ref<number[]>([])
const selectableDayMonthsByYear = ref<Record<string, number[]>>({})
const selectableMonthYears = ref<number[]>([])

const toNum = toNumber
let calendarRequestId = 0

function cacheUserId(): string {
  return String(store.state.user?.id || 'guest')
}

function persistAnalysisCache() {
  writePageCache<AnalysisCachePayload>(
    ANALYSIS_CACHE_DOMAIN,
    ANALYSIS_CACHE_KEY,
    cacheUserId(),
    {
      overview: {
        day: overview.day || {},
        month: overview.month || {},
        year: overview.year || {},
        all: overview.all || {},
      },
      calendarState: {
        title: calendarState.title,
        items: calendarState.items,
        totalPnl: calendarState.totalPnl,
        totalRate: calendarState.totalRate,
      },
      rank: {
        gain: rank.gain,
        loss: rank.loss,
      },
      rates: {
        CNY: toNum(rates.CNY, 1),
        HKD: toNum(rates.HKD, 1),
        USD: toNum(rates.USD, 1),
      },
      calendarType: calendarType.value,
      rankMarket: rankMarket.value,
      selectedDayYear: selectedDayYear.value,
      selectedDayMonth: selectedDayMonth.value,
      selectedMonthYear: selectedMonthYear.value,
      selectableDayYears: selectableDayYears.value,
      selectableDayMonthsByYear: selectableDayMonthsByYear.value,
      selectableMonthYears: selectableMonthYears.value,
      storePortfolio: store.state.portfolio as unknown[],
      storeQuotes: store.state.quotes as Record<string, unknown>,
      storeRates: store.state.rates,
      storeMarketStatus: store.state.marketStatus as Record<string, unknown>,
      storeAllClosed: Boolean(store.state.allClosed),
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

  for (const key of Object.keys(periods) as PeriodKey[]) {
    overview[key] = cached.overview?.[key] || {}
  }
  calendarState.title = String(cached.calendarState?.title || '')
  calendarState.items = Array.isArray(cached.calendarState?.items) ? cached.calendarState.items : []
  calendarState.totalPnl = toNum(cached.calendarState?.totalPnl)
  calendarState.totalRate = toNum(cached.calendarState?.totalRate)
  rank.gain = Array.isArray(cached.rank?.gain) ? cached.rank.gain : []
  rank.loss = Array.isArray(cached.rank?.loss) ? cached.rank.loss : []

  if (cached.rates && typeof cached.rates === 'object') {
    rates.CNY = toNum(cached.rates.CNY, 1)
    rates.HKD = toNum(cached.rates.HKD, 1)
    rates.USD = toNum(cached.rates.USD, 1)
  }

  if (cached.calendarType === 'day' || cached.calendarType === 'month' || cached.calendarType === 'year') {
    calendarType.value = cached.calendarType
  }
  if (cached.rankMarket === 'all' || cached.rankMarket === 'a' || cached.rankMarket === 'hk' || cached.rankMarket === 'us' || cached.rankMarket === 'fund') {
    rankMarket.value = cached.rankMarket
  }
  selectedDayYear.value = cached.selectedDayYear ?? null
  selectedDayMonth.value = cached.selectedDayMonth ?? null
  selectedMonthYear.value = cached.selectedMonthYear ?? null
  selectableDayYears.value = Array.isArray(cached.selectableDayYears) ? cached.selectableDayYears : []
  selectableDayMonthsByYear.value = cached.selectableDayMonthsByYear || {}
  selectableMonthYears.value = Array.isArray(cached.selectableMonthYears) ? cached.selectableMonthYears : []

  if (Array.isArray(cached.storePortfolio)) {
    store.state.portfolio = cached.storePortfolio as typeof store.state.portfolio
  }
  if (cached.storeQuotes && typeof cached.storeQuotes === 'object') {
    store.state.quotes = cached.storeQuotes as typeof store.state.quotes
  }
  if (cached.storeRates && typeof cached.storeRates === 'object') {
    store.state.rates = cached.storeRates
  }
  if (cached.storeMarketStatus && typeof cached.storeMarketStatus === 'object') {
    store.state.marketStatus = cached.storeMarketStatus as typeof store.state.marketStatus
  }
  store.state.allClosed = Boolean(cached.storeAllClosed)
  return true
}

function rateToCnyForCurr(curr: unknown): number {
  const code = String(curr || 'CNY').toUpperCase()
  if (code === 'CNY') return 1
  const rate = toNum(store.state.rates[code] ?? rates[code], 0)
  return rate > 0 ? rate : 1
}

const realtimeDayOverview = computed(() => {
  let pnl = 0
  let base = 0
  for (const row of store.rows.value) {
    const rate = rateToCnyForCurr((row as Record<string, unknown>).curr)
    const rowValue = toNum((row as Record<string, unknown>).value)
    const rowDayPnl = toNum((row as Record<string, unknown>).dayPnlAggregate)
    pnl += rowDayPnl * rate
    base += (rowValue - rowDayPnl) * rate
  }
  return {
    pnl,
    rate: base > 0 ? (pnl / base) * 100 : 0,
  }
})

const dayOverviewPnl = computed(() =>
  realtimeDayReady.value ? realtimeDayOverview.value.pnl : toNum(overview.day?.pnl),
)

const dayOverviewRate = computed(() =>
  realtimeDayReady.value ? realtimeDayOverview.value.rate : toNum(overview.day?.pnl_rate),
)

const overviewCards = computed(() => {
  return (Object.keys(periods) as PeriodKey[]).map((key) => ({
    key,
    label: periods[key].label,
    pnl: key === 'day' ? dayOverviewPnl.value : toNum(overview[key]?.pnl),
    rate: key === 'day' ? dayOverviewRate.value : toNum(overview[key]?.pnl_rate),
  }))
})

const calendarColumns = computed(() => {
  if (calendarType.value === 'day') return 6
  if (calendarType.value === 'month') return 4
  return 5
})

const dayMonthOptions = computed(() => {
  return getDayMonths(selectedDayYear.value)
})

const displayRankItems = computed(() => {
  const allItems = [...(rank.gain || []), ...(rank.loss || [])]
  return allItems.sort((a, b) => toNum(b.pnl) - toNum(a.pnl))
})

const hasMoreRankItems = computed(() => displayRankItems.value.length > 5)

const visibleRankItems = computed(() => {
  if (rankExpanded.value) return displayRankItems.value
  return displayRankItems.value.slice(0, 5)
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
    for (let day = 1; day <= daysInMonth; day += 1) {
      grid.push({ key: day, pnl: null })
    }
  } else if (calendarType.value === 'month') {
    for (let month = 1; month <= 12; month += 1) {
      grid.push({ key: month, pnl: null })
    }
  } else {
    const thisYear = now.getFullYear()
    for (let i = 0; i < 5; i += 1) {
      grid.push({ key: thisYear - 4 + i, pnl: null })
    }
  }

  const map = new Map<number, number>()
  for (const item of calendarState.items) {
    const key = parseLabelKey(item?.label)
    if (key === null) continue
    const pnl = Number(item?.pnl)
    if (!Number.isFinite(pnl)) continue
    map.set(key, pnl)
  }

  if (calendarType.value === 'day') {
    const nowYear = now.getFullYear()
    const nowMonth = now.getMonth() + 1
    if (selectedDayYear.value === nowYear && selectedDayMonth.value === nowMonth) {
      const today = now.getDate()
      map.set(today, dayOverviewPnl.value)
    }
  }

  return grid.map((item) => ({
    ...item,
    pnl: map.has(item.key) ? Number(map.get(item.key)) : null,
  }))
})

function valueClass(value: number): 'up' | 'down' | 'flat' {
  if (value > 0) return 'up'
  if (value < 0) return 'down'
  return 'flat'
}

function formatCny(value: number): string {
  const rounded = Math.round(toNum(value))
  const sign = rounded > 0 ? '+' : rounded < 0 ? '-' : ''
  const absValue = Math.abs(rounded)
  return `${sign}¥ ${absValue.toLocaleString('zh-CN')}`
}

function formatPct(value: number): string {
  const val = toNum(value)
  return `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`
}

function formatCalendarCellLabel(key: number): string {
  if (calendarType.value === 'day') return String(key)
  if (calendarType.value === 'month') return `${key}月`
  return `${key}年`
}

function formatCalendarCellPnl(value: number): string {
  const val = toNum(value)
  const abs = Math.abs(val)
  const sign = val > 0 ? '+' : val < 0 ? '-' : ''

  if (abs >= 100000000) {
    return `${sign}${(abs / 100000000).toFixed(1)}亿`
  }
  if (abs >= 10000) {
    return `${sign}${(abs / 10000).toFixed(1)}万`
  }
  return `${sign}${Math.round(abs).toLocaleString('zh-CN')}`
}

function calendarCellClass(pnl: number | null): 'up' | 'down' | 'flat' | 'empty' {
  if (pnl === null) return 'empty'
  if (pnl > 0) return 'up'
  if (pnl < 0) return 'down'
  return 'flat'
}

function rankBadgeClass(rankIndex: number): 'top1' | 'top2' | 'top3' | 'normal' {
  if (rankIndex === 1) return 'top1'
  if (rankIndex === 2) return 'top2'
  if (rankIndex === 3) return 'top3'
  return 'normal'
}

function formatDisplayCode(code: string): string {
  if (!code) return '-'
  const customMap: Record<string, string> = { ft_LU1116320737: 'BLK' }
  if (customMap[code]) return customMap[code]

  let value = String(code)
  const lower = value.toLowerCase()
  if (lower.startsWith('gb_')) value = value.slice(3).toUpperCase()
  else if (lower.startsWith('f_')) value = value.slice(2)
  else if (lower.startsWith('ft_')) value = value.slice(3)
  else if (lower.startsWith('sh') || lower.startsWith('sz') || lower.startsWith('bj')) value = value.slice(2)

  if (value.toUpperCase().endsWith('.HK')) {
    value = value.slice(0, -3)
  }
  return value
}

function currencyForRankItem(item: RankItem): 'CNY' | 'HKD' | 'USD' {
  const curr = String(item.curr || '').toUpperCase()
  if (curr === 'HKD' || curr === 'USD' || curr === 'CNY') {
    return curr
  }
  const market = String(item.market || '').toLowerCase()
  if (market === 'hk') return 'HKD'
  if (market === 'us') return 'USD'
  return 'CNY'
}

function toCny(value: number, curr: 'CNY' | 'HKD' | 'USD'): number {
  const rate = toNum(rates[curr], 1) || 1
  return value * rate
}

function rankPnlCny(item: RankItem): number {
  const pnl = toNum(item.pnl)
  return toCny(pnl, currencyForRankItem(item))
}

function parseLabelKey(label: string | number | undefined): number | null {
  const text = String(label ?? '').trim()
  if (!text) return null
  const matches = text.match(/\d+/g)
  if (!matches || matches.length === 0) return null
  const parsed = Number(matches[matches.length - 1])
  return Number.isFinite(parsed) ? parsed : null
}

function normalizeYearList(values: unknown[]): number[] {
  return values
    .map((v) => Number(v))
    .filter((v) => Number.isFinite(v) && v > 0)
    .sort((a, b) => a - b)
}

function normalizeMonthList(values: unknown[]): number[] {
  return values
    .map((v) => Number(v))
    .filter((v) => Number.isFinite(v) && v >= 1 && v <= 12)
    .sort((a, b) => a - b)
}

function getDayMonths(year: number | null): number[] {
  if (!year) return []
  return selectableDayMonthsByYear.value[String(year)] || []
}

function lastOrNull(values: number[]): number | null {
  return values.length ? (values[values.length - 1] ?? null) : null
}

function ensureDaySelection() {
  const years = selectableDayYears.value
  if (!years.length) {
    selectedDayYear.value = null
    selectedDayMonth.value = null
    return
  }

  if (!selectedDayYear.value || !years.includes(selectedDayYear.value)) {
    selectedDayYear.value = lastOrNull(years)
  }

  const months = getDayMonths(selectedDayYear.value)
  if (!months.length) {
    selectedDayMonth.value = null
    return
  }

  if (!selectedDayMonth.value || !months.includes(selectedDayMonth.value)) {
    selectedDayMonth.value = lastOrNull(months)
  }
}

function ensureMonthSelection() {
  const years = selectableMonthYears.value
  if (!years.length) {
    selectedMonthYear.value = null
    return
  }
  if (!selectedMonthYear.value || !years.includes(selectedMonthYear.value)) {
    selectedMonthYear.value = lastOrNull(years)
  }
}

function applySelectable(payload: CalendarPayload) {
  const daySelectable = payload.selectable?.day
  const monthSelectable = payload.selectable?.month

  const years = normalizeYearList(Array.isArray(daySelectable?.years) ? daySelectable?.years : [])
  const monthsByYearRaw = daySelectable?.months_by_year || {}
  const monthsByYear: Record<string, number[]> = {}
  for (const year of years) {
    const key = String(year)
    const months = normalizeMonthList(Array.isArray(monthsByYearRaw[key]) ? monthsByYearRaw[key] : [])
    monthsByYear[key] = months
  }

  selectableDayYears.value = years
  selectableDayMonthsByYear.value = monthsByYear

  const monthYears = normalizeYearList(Array.isArray(monthSelectable?.years) ? monthSelectable?.years : years)
  selectableMonthYears.value = monthYears
}

function applyPeriod(payload: CalendarPayload) {
  const period = payload.period || {}
  const periodType = String(period.time_type || calendarType.value)

  if (periodType === 'day') {
    const year = Number(period.year)
    const month = Number(period.month)
    if (Number.isFinite(year) && year > 0) selectedDayYear.value = year
    if (Number.isFinite(month) && month >= 1 && month <= 12) selectedDayMonth.value = month
  }

  if (periodType === 'month') {
    const year = Number(period.year)
    if (Number.isFinite(year) && year > 0) selectedMonthYear.value = year
  }
}

async function loadOverview() {
  const payload = await api.get<Record<string, OverviewItem>>('/api/analysis/overview?period=all')
  for (const key of Object.keys(periods) as PeriodKey[]) {
    overview[key] = payload?.[key] || {}
  }
}

async function loadRates() {
  const storeRates = store.state.rates || {}
  const hkdFromStore = toNum(storeRates.HKD, 0)
  const usdFromStore = toNum(storeRates.USD, 0)
  if (hkdFromStore > 0 || usdFromStore > 0) {
    rates.CNY = 1
    rates.HKD = toNum(storeRates.HKD, 1)
    rates.USD = toNum(storeRates.USD, 1)
    return
  }
  const payload = await api.get<Record<string, number>>('/api/rates')
  const next: Record<string, number> = {
    CNY: 1,
    HKD: toNum(payload?.HKD, 1),
    USD: toNum(payload?.USD, 1),
  }
  for (const [key, value] of Object.entries(next)) {
    rates[key] = value
  }
}

async function loadCalendar() {
  const requestId = ++calendarRequestId

  const params = new URLSearchParams({ type: calendarType.value })
  if (calendarType.value === 'day') {
    ensureDaySelection()
    if (selectedDayYear.value && selectedDayMonth.value) {
      params.set('year', String(selectedDayYear.value))
      params.set('month', String(selectedDayMonth.value))
    }
  } else if (calendarType.value === 'month') {
    ensureMonthSelection()
    if (selectedMonthYear.value) {
      params.set('year', String(selectedMonthYear.value))
    }
  }

  const payload = await api.get<CalendarPayload>(`/api/analysis/calendar?${params.toString()}`)
  if (requestId !== calendarRequestId) return

  applySelectable(payload)
  applyPeriod(payload)
  if (calendarType.value === 'day') ensureDaySelection()
  if (calendarType.value === 'month') ensureMonthSelection()

  calendarState.title = String(payload.title || '')
  calendarState.items = Array.isArray(payload.items) ? payload.items : []
  calendarState.totalPnl = toNum(payload.total_pnl)
  calendarState.totalRate = toNum(payload.total_rate)
  persistAnalysisCache()
}

async function loadRank() {
  const payload = await api.get<{ gain?: RankItem[]; loss?: RankItem[] }>(
    `/api/analysis/rank?type=all&market=${rankMarket.value}`,
  )
  rank.gain = Array.isArray(payload?.gain) ? payload.gain : []
  rank.loss = Array.isArray(payload?.loss) ? payload.loss : []
  rankExpanded.value = false
  persistAnalysisCache()
}

async function reload(mode: 'light' | 'force' = 'light', includeAnalysis = true) {
  if (reloadInflight) {
    return reloadInflight
  }
  reloadInflight = (async () => {
    try {
      if (mode === 'force') await store.refreshAll()
      else await store.refreshStaticOnly()
      realtimeDayReady.value = store.rows.value.length > 0
    } catch {
      realtimeDayReady.value = false
    }

    if (includeAnalysis) {
      await Promise.all([loadOverview(), loadRates()])
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

function onManualRefresh() {
  void reload('force', true)
}

function onCalendarTypeChange(nextType: CalendarType) {
  if (calendarType.value === nextType) return
  calendarType.value = nextType
  if (nextType === 'day') {
    ensureDaySelection()
  } else if (nextType === 'month') {
    ensureMonthSelection()
  }
  void loadCalendar()
}

function onDayYearChange() {
  const months = getDayMonths(selectedDayYear.value)
  if (!months.includes(Number(selectedDayMonth.value))) {
    selectedDayMonth.value = lastOrNull(months)
  }
  void loadCalendar()
}

function onDayMonthChange() {
  void loadCalendar()
}

function onMonthYearChange() {
  void loadCalendar()
}

function onRankMarketChange(market: RankMarket) {
  if (rankMarket.value === market) return
  rankMarket.value = market
  void loadRank()
}

onMounted(() => {
  const restored = restoreAnalysisCache()
  realtimeDayReady.value = store.rows.value.length > 0
  if (restored) {
    void reload('light', false)
    window.setTimeout(() => {
      void reload('light', true)
    }, 1200)
    return
  }
  void reload('light', true)
})
</script>

<style scoped>
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--legacy-border);
  padding-bottom: 14px;
}

.section-title {
  margin: 0;
  font-size: 26px;
}

.milestone-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.milestone-card {
  background: var(--legacy-bg-tertiary);
  border: 1px solid var(--legacy-border);
  border-radius: var(--legacy-radius-sm);
  padding: 16px;
}

.milestone-title {
  color: var(--legacy-text-secondary);
  font-size: 13px;
}

.milestone-main {
  margin-top: 10px;
  font-size: 30px;
  font-weight: 700;
}

.milestone-rate {
  margin-top: 8px;
  font-size: 13px;
}

.calendar-section-header {
  align-items: flex-start;
}

.calendar-header-controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.calendar-period-picker {
  display: flex;
  align-items: center;
  gap: 8px;
}

.period-select {
  min-width: 96px;
  height: 34px;
  border-radius: 8px;
  border: 1px solid var(--legacy-border);
  background: var(--legacy-bg-tertiary);
  color: var(--legacy-text-primary);
  padding: 0 10px;
}

.view-tabs {
  display: flex;
  background: var(--legacy-version-bg);
  padding: 4px;
  border-radius: 8px;
  border: 1px solid var(--legacy-border);
}

.view-tab {
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  border: 0;
  color: var(--legacy-text-secondary);
  background: transparent;
}

.view-tab.active {
  background: var(--legacy-bg-tertiary);
  color: var(--legacy-text-primary);
}

.calendar-title {
  margin-bottom: 12px;
  color: var(--legacy-text-secondary);
  font-size: 14px;
}

.calendar-grid-shell {
  border: 1px solid var(--legacy-border);
  background: var(--legacy-bg-tertiary);
  border-radius: var(--legacy-radius-sm);
  padding: 12px;
}

.calendar-grid {
  display: grid;
  gap: 8px;
}

.calendar-cell {
  min-height: 82px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 6px;
  text-align: center;
  background: var(--legacy-bg-secondary);
}

.calendar-cell-label {
  font-size: 13px;
  font-weight: 700;
}

.calendar-cell-value {
  margin-top: 4px;
  font-size: 12px;
  font-weight: 600;
}

.calendar-cell.up {
  background: var(--legacy-up-soft-bg);
  color: var(--legacy-red);
}

.calendar-cell.down {
  background: var(--legacy-down-soft-bg);
  color: var(--legacy-green);
}

.calendar-cell.flat {
  background: var(--legacy-bg-tertiary);
  color: var(--legacy-text-secondary);
}

.calendar-cell.empty {
  background: var(--legacy-bg-secondary);
  color: var(--legacy-text-secondary);
}

.calendar-summary {
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  background: var(--legacy-bg-secondary);
  border: 1px solid var(--legacy-border);
  font-size: 14px;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  color: var(--legacy-text-secondary);
}

.rank-section-header {
  margin-bottom: 12px;
}

.rank-controls {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
}

.market-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.market-tab {
  border: 1px solid var(--legacy-border);
  border-radius: 8px;
  padding: 8px 14px;
  background: var(--legacy-bg-tertiary);
  color: var(--legacy-text-secondary);
  cursor: pointer;
}

.market-tab.active {
  color: var(--legacy-text-primary);
  border-color: rgba(59, 130, 246, 0.5);
  background: rgba(59, 130, 246, 0.18);
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rank-expand-btn {
  align-self: center;
  border: 1px solid rgba(59, 130, 246, 0.5);
  border-radius: 999px;
  padding: 8px 16px;
  background: rgba(59, 130, 246, 0.14);
  color: var(--legacy-text-primary);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
}

.rank-expand-btn:hover {
  background: rgba(59, 130, 246, 0.24);
}

.rank-item {
  border: 1px solid var(--legacy-border);
  border-radius: var(--legacy-radius-sm);
  background: var(--legacy-bg-tertiary);
  padding: 12px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.rank-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.rank-badge {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
}

.rank-badge.top1 {
  background: linear-gradient(135deg, #f59e0b, #ef4444);
}

.rank-badge.top2 {
  background: linear-gradient(135deg, #06b6d4, #3b82f6);
}

.rank-badge.top3 {
  background: linear-gradient(135deg, #22c55e, #14b8a6);
}

.rank-badge.normal {
  color: var(--legacy-text-secondary);
  border: 1px solid var(--legacy-border);
  background: var(--legacy-bg-secondary);
}

.rank-asset-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.rank-asset-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--legacy-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rank-asset-code {
  font-size: 12px;
  color: var(--legacy-text-secondary);
}

.rank-right {
  text-align: right;
}

.rank-pnl {
  font-size: 20px;
  font-weight: 700;
}

.rank-rate {
  margin-top: 3px;
  font-size: 13px;
  font-weight: 600;
}

.rank-empty {
  border: 1px dashed var(--legacy-border);
  border-radius: var(--legacy-radius-sm);
  padding: 26px;
  text-align: center;
  color: var(--legacy-text-secondary);
  background: var(--legacy-bg-secondary);
}

.up {
  color: var(--legacy-red);
}

.down {
  color: var(--legacy-green);
}

.flat {
  color: var(--legacy-text-secondary);
}

@media (max-width: 1200px) {
  .milestone-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .calendar-header-controls {
    width: 100%;
    justify-content: space-between;
  }

  .calendar-cell {
    min-height: 72px;
  }

  .rank-item {
    align-items: flex-start;
    flex-direction: column;
  }

  .rank-right {
    width: 100%;
    text-align: left;
  }
}

@media (max-width: 600px) {
  .milestone-grid {
    grid-template-columns: 1fr;
  }

  .calendar-header-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .calendar-period-picker {
    width: 100%;
  }

  .period-select {
    flex: 1;
    min-width: 0;
  }
}
</style>
