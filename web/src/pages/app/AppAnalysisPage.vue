<template>
  <AppShell title="资产分析">
    <div class="analysis-page-layout">
      <!-- Main Content Column -->
      <div class="analysis-main">
        <!-- 1. Revenue Overview -->
        <div class="card analysis-overview-card">
          <div class="card-header-row">
            <div class="section-label">盈亏概览</div>
            <div class="summary-tabs">
              <button class="s-tab" :class="{ active: overviewPeriod === 'week' }" @click="overviewPeriod = 'week'">本周</button>
              <button class="s-tab" :class="{ active: overviewPeriod === 'month' }" @click="overviewPeriod = 'month'">本月</button>
              <button class="s-tab" :class="{ active: overviewPeriod === 'year' }" @click="overviewPeriod = 'year'">今年</button>
              <button class="s-tab" :class="{ active: overviewPeriod === 'all' }" @click="overviewPeriod = 'all'">累计</button>
            </div>
            <!-- Header actions removed: now in AppShell's topbar -->
          </div>
          
          <div class="overview-hero">
            <div class="hero-main">
               <div class="hero-label">{{ periodLabel }}总计盈亏</div>
               <div class="hero-val" :class="valueClass(periodPnl)">{{ formatCny(periodPnl) }}</div>
               <div class="hero-rate" :class="valueClass(periodRate)">{{ formatPct(periodRate) }}</div>
            </div>
            <div class="hero-side">
               <div class="side-stat">
                  <div class="s-lab">初始投入</div>
                  <div class="s-val">{{ formatCny(124500) }}</div>
               </div>
               <div class="side-stat">
                  <div class="s-lab">分红再计</div>
                  <div class="s-val up">+¥ 1,240</div>
               </div>
            </div>
          </div>
        </div>

        <!-- 2. Revenue Calendar -->
        <div class="card calendar-card">
          <div class="card-header-row">
            <div class="section-label">盈亏日历</div>
            <div class="calendar-controls">
               <div class="view-tabs mini">
                  <button class="view-tab" :class="{ active: calendarType === 'day' }" @click="onCalendarTypeChange('day')">日</button>
                  <button class="view-tab" :class="{ active: calendarType === 'month' }" @click="onCalendarTypeChange('month')">月</button>
                  <button class="view-tab" :class="{ active: calendarType === 'year' }" @click="onCalendarTypeChange('year')">年</button>
               </div>
               <div class="calendar-picker-wrap" v-if="calendarType !== 'year'">
                  <select v-if="calendarType === 'day'" v-model.number="selectedDayMonth" @change="onDayMonthChange" class="mini-select">
                    <option v-for="m in dayMonthOptions" :key="m" :value="m">{{ m }}月</option>
                  </select>
                  <select v-model.number="currentSelectedYear" @change="handleYearChange" class="mini-select">
                    <option v-for="y in selectableYears" :key="y" :value="y">{{ y }}年</option>
                  </select>
               </div>
            </div>
          </div>

          <div class="calendar-grid" :style="{ gridTemplateColumns: `repeat(${calendarColumns}, minmax(0, 1fr))` }">
            <div v-for="cell in calendarGrid" :key="cell.key" class="cal-cell" :class="calendarCellClass(cell.pnl)">
               <div class="cal-date">{{ formatCalendarCellLabel(cell.key) }}</div>
               <div class="cal-pnl">{{ formatCalendarCellPnl(cell.pnl) }}</div>
            </div>
          </div>

          <div class="calendar-footer" v-if="calendarState.totalPnl">
            <span>{{ calendarSummaryLabel }}:</span>
            <span :class="valueClass(calendarState.totalPnl)">{{ formatCny(calendarState.totalPnl) }}</span>
            <span class="muted">({{ formatPct(calendarState.totalRate) }})</span>
          </div>
        </div>

        <!-- 3. PnL Ranking -->
        <div class="card rank-card">
          <div class="card-header-row">
            <div class="section-label">盈亏红黑榜</div>
            <div class="market-filters">
               <button v-for="tab in marketTabs" :key="tab.key" 
                  class="filter-tag" :class="{ active: rankMarket === tab.key }"
                  @click="onRankMarketChange(tab.key)">
                  {{ tab.label }}
               </button>
            </div>
          </div>

          <div class="rank-list">
            <div v-for="(item, idx) in visibleRankItems" :key="item.code" class="rank-item-row">
               <div class="rank-info">
                  <span class="rank-idx" :class="rankBadgeClass(idx + 1)">{{ idx + 1 }}</span>
                  <div class="asset-core">
                    <div class="asset-name">{{ item.name || item.code }}</div>
                    <div class="asset-code">{{ formatDisplayCode(item.code) }}</div>
                  </div>
               </div>
               <div class="rank-values" :class="valueClass(rankPnlCny(item))">
                  <div class="val-pnl">{{ formatCny(rankPnlCny(item)) }}</div>
                  <div class="val-rate">{{ formatPct(toNum(item.pnl_rate)) }}</div>
               </div>
            </div>
          </div>
          <button v-if="hasMoreRankItems" class="expand-btn" @click="rankExpanded = !rankExpanded">
            {{ rankExpanded ? '收起榜单' : '查看完整榜单' }}
          </button>
        </div>
      </div>

      <!-- Side Stats Column -->
      <aside class="analysis-side">
        <!-- Multi-period cards -->
        <div class="period-cards-stack">
          <div class="card mini-period-card" v-for="p in sidePeriodStats" :key="p.key">
            <div class="p-label">{{ p.label }}盈亏</div>
            <div class="p-val" :class="valueClass(p.pnl)">{{ formatCny(p.pnl) }}</div>
            <div class="p-rate" :class="valueClass(p.rate)">{{ formatPct(p.rate) }}</div>
          </div>
        </div>

        <!-- Annual Trend Chart Placeholder -->
        <div class="card trend-card">
          <div class="section-label">年度收益趋势</div>
          <div class="mock-chart-container">
             <div class="chart-bars">
                <div v-for="b in 12" :key="b" class="bar-wrap">
                   <div class="bar-fill" :style="{ height: (20 + Math.random() * 60) + '%', opacity: 0.3 + (b/12)*0.7 }"></div>
                   <span class="bar-label">{{ b }}月</span>
                </div>
             </div>
          </div>
          <div class="chart-summary">
             <div class="c-item">
                <span class="c-dot up"></span>
                <span>盈利月: 8个</span>
             </div>
             <div class="c-item">
                <span class="c-dot down"></span>
                <span>亏损月: 4个</span>
             </div>
          </div>
        </div>

        <!-- Tips / Help -->
        <div class="card tips-card">
          <div class="section-label">投资分析说明</div>
          <ul class="tips-list">
            <li>• 每周一凌晨自动同步上周汇总</li>
            <li>• 汇率以持仓时的结算汇率为准</li>
            <li>• 累计盈亏包含了由于资产卖出产生的已实现损益</li>
          </ul>
        </div>
      </aside>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import AppShell from '../../layouts/AppShell.vue'
import { api, type ApiError } from '../../shared/http'
import { toNumber } from '../../shared/format'
import { readPageCache, writePageCache } from '../../shared/pageCache'
import { useKonaStore } from '../../stores/composables'

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
  code?: string
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

function invalidCalendarPeriodPayload(error: unknown): CalendarPayload | null {
  const apiError = error as ApiError
  if (!apiError || apiError.status !== 400) return null
  const payload = apiError.payload
  if (!payload || typeof payload !== 'object') return null
  const data = payload as Record<string, unknown>
  if (String(data.code || '') !== 'INVALID_CALENDAR_PERIOD') return null
  return data as CalendarPayload
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
}

const ANALYSIS_CACHE_DOMAIN = 'analysis'
const ANALYSIS_CACHE_KEY = 'page'
const ANALYSIS_CACHE_TTL_MS = 5 * 60_000

const marketTabs = [
  { key: 'all', label: '全部' },
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
const overviewPeriod = ref<'week' | 'month' | 'year' | 'all'>('week')

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
      overview,
      calendarState,
      rank,
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
  Object.assign(rates, cached.rates)
  calendarType.value = cached.calendarType
  rankMarket.value = cached.rankMarket
  selectedDayYear.value = cached.selectedDayYear
  selectedDayMonth.value = cached.selectedDayMonth
  selectedMonthYear.value = cached.selectedMonthYear
  selectableDayYears.value = cached.selectableDayYears
  selectableDayMonthsByYear.value = cached.selectableDayMonthsByYear
  selectableMonthYears.value = cached.selectableMonthYears
  return true
}

function rateToCnyForCurr(curr: unknown): number {
  const code = String(curr || 'CNY').toUpperCase()
  if (code === 'CNY') return 1
  const rate = toNum(store.state.rates?.[code] ?? rates[code], 0)
  return rate > 0 ? rate : 1
}

const realtimeDayOverview = computed(() => {
  let pnl = 0
  let base = 0
  for (const row of store.rows.value) {
    const rate = rateToCnyForCurr((row as any).curr)
    const rowValue = toNum((row as any).value)
    const rowDayPnl = toNum((row as any).dayPnlAggregate)
    pnl += rowDayPnl * rate
    base += (rowValue - rowDayPnl) * rate
  }
  return {
    pnl,
    rate: base > 0 ? (pnl / base) * 100 : 0,
  }
})

const periodLabel = computed(() => {
  if (overviewPeriod.value === 'week') return '本周'
  if (overviewPeriod.value === 'month') return '本月'
  if (overviewPeriod.value === 'year') return '今年'
  return '累计'
})

const periodPnl = computed(() => {
  const key = overviewPeriod.value === 'week' ? 'day' : overviewPeriod.value
  if (key === 'day') return realtimeDayOverview.value.pnl
  return toNum(overview[key]?.pnl)
})

const periodRate = computed(() => {
  const key = overviewPeriod.value === 'week' ? 'day' : overviewPeriod.value
  if (key === 'day') return realtimeDayOverview.value.rate
  return toNum(overview[key]?.pnl_rate)
})

const sidePeriodStats = computed(() => [
  { label: '今日', key: 'day', pnl: realtimeDayOverview.value.pnl, rate: realtimeDayOverview.value.rate },
  { label: '本月', key: 'month', pnl: toNum(overview.month?.pnl), rate: toNum(overview.month?.pnl_rate) },
  { label: '今年', key: 'year', pnl: toNum(overview.year?.pnl), rate: toNum(overview.year?.pnl_rate) },
  { label: '累计', key: 'all', pnl: toNum(overview.all?.pnl), rate: toNum(overview.all?.pnl_rate) },
])

const calendarColumns = computed(() => {
  if (calendarType.value === 'day') return 6
  if (calendarType.value === 'month') return 4
  return 5
})

const dayMonthOptions = computed(() => getDayMonths(selectedDayYear.value))
const selectableYears = computed(() => calendarType.value === 'day' ? selectableDayYears.value : selectableMonthYears.value)
const currentSelectedYear = computed({
  get: () => calendarType.value === 'day' ? selectedDayYear.value : selectedMonthYear.value,
  set: (v) => { if (calendarType.value === 'day') selectedDayYear.value = v; else selectedMonthYear.value = v }
})

const displayRankItems = computed(() => {
  const allItems = [...(rank.gain || []), ...(rank.loss || [])]
  return allItems.sort((a, b) => toNum(b.pnl) - toNum(a.pnl))
})

const hasMoreRankItems = computed(() => displayRankItems.value.length > 5)
const visibleRankItems = computed(() => rankExpanded.value ? displayRankItems.value : displayRankItems.value.slice(0, 5))

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
    for (let i = 0; i < 5; i += 1) grid.push({ key: thisYear - 4 + i, pnl: null })
  }

  const map = new Map<number, number>()
  for (const item of calendarState.items) {
    const key = parseLabelKey(item?.label)
    if (key !== null) map.set(key, toNum(item?.pnl))
  }

  if (calendarType.value === 'day') {
    if (selectedDayYear.value === now.getFullYear() && selectedDayMonth.value === now.getMonth() + 1) {
      map.set(now.getDate(), realtimeDayOverview.value.pnl)
    }
  }

  return grid.map((item) => ({ ...item, pnl: map.has(item.key) ? Number(map.get(item.key)) : null }))
})

function valueClass(value: number): 'up' | 'down' | 'flat' {
  if (value > 0) return 'up'
  if (value < 0) return 'down'
  return 'flat'
}

function formatCny(value: number): string {
  const val = Math.round(toNum(value))
  return (val >= 0 ? '+' : '-') + '¥ ' + Math.abs(val).toLocaleString()
}

function formatPct(value: number): string {
  const val = toNum(value)
  return (val >= 0 ? '+' : '') + val.toFixed(2) + '%'
}

function formatCalendarCellLabel(key: number): string {
  if (calendarType.value === 'day') return String(key)
  if (calendarType.value === 'month') return `${key}月`
  return `${key}年`
}

function formatCalendarCellPnl(value: number | null): string {
  if (value === null) return '-'
  const val = toNum(value)
  const abs = Math.abs(val)
  const sign = val >= 0 ? '+' : '-'
  if (abs >= 10000) return sign + (abs / 10000).toFixed(1) + '万'
  return sign + Math.round(abs).toLocaleString()
}

function calendarCellClass(pnl: number | null): 'up' | 'down' | 'flat' | 'empty' {
  if (pnl === null) return 'empty'
  if (pnl > 0) return 'up'
  if (pnl < 0) return 'down'
  return 'flat'
}

function rankBadgeClass(rankIndex: number): string {
  return rankIndex <= 3 ? `top${rankIndex}` : 'normal'
}

function formatDisplayCode(code: string): string {
  let value = String(code || '')
  if (value.startsWith('gb_')) value = value.slice(3)
  return value.toUpperCase()
}

function rankPnlCny(item: RankItem): number {
  const pnl = toNum(item.pnl)
  const code = String(item.curr || 'CNY').toUpperCase()
  const rate = toNum(rates[code], 1)
  return pnl * rate
}

function parseLabelKey(label: string | number | undefined): number | null {
  const text = String(label ?? '').trim()
  const matches = text.match(/\d+/g)
  return matches ? Number(matches[matches.length - 1]) : null
}

function normalizeYearList(values: unknown[]): number[] {
  return values.map(v => Number(v)).filter(v => v > 0).sort((a,b) => a-b)
}

function getDayMonths(year: number | null): number[] {
  return year ? (selectableDayMonthsByYear.value[String(year)] || []) : []
}

function lastOrNull(values: number[]): number | null {
  return values.length ? (values[values.length - 1] ?? null) : null
}

function ensureDaySelection() {
  const years = selectableDayYears.value
  if (!years.length) return
  if (!selectedDayYear.value || !years.includes(selectedDayYear.value)) selectedDayYear.value = lastOrNull(years)
  const months = getDayMonths(selectedDayYear.value)
  if (!months.length) return
  if (!selectedDayMonth.value || !months.includes(selectedDayMonth.value)) selectedDayMonth.value = lastOrNull(months)
}

function ensureMonthSelection() {
  const years = selectableMonthYears.value
  if (years.length && (!selectedMonthYear.value || !years.includes(selectedMonthYear.value))) selectedMonthYear.value = lastOrNull(years)
}

function handleYearChange() {
  if (calendarType.value === 'day') {
    const months = getDayMonths(selectedDayYear.value)
    if (!months.includes(Number(selectedDayMonth.value))) selectedDayMonth.value = lastOrNull(months)
  }
  void loadCalendar()
}

async function loadOverview() {
  const payload = await api.get<Record<string, OverviewItem>>('/api/analysis/overview?period=all')
  Object.assign(overview, payload)
}

async function loadRates() {
  const payload = await api.get<Record<string, number>>('/api/rates')
  Object.assign(rates, { CNY: 1, ...payload })
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
    const payload = await api.get<CalendarPayload>(`/api/analysis/calendar?${params.toString()}`)
    if (requestId !== calendarRequestId) return
    const daySelectable = payload.selectable?.day
    selectableDayYears.value = normalizeYearList(daySelectable?.years || [])
    selectableDayMonthsByYear.value = daySelectable?.months_by_year || {}
    selectableMonthYears.value = normalizeYearList(payload.selectable?.month?.years || [])
    
    calendarState.title = payload.title || ''
    calendarState.items = payload.items || []
    calendarState.totalPnl = toNum(payload.total_pnl)
    calendarState.totalRate = toNum(payload.total_rate)
  } catch (error) {
    const inv = invalidCalendarPeriodPayload(error)
    if (recoverOnInvalid && inv) {
       selectableDayYears.value = normalizeYearList(inv.selectable?.day?.years || [])
       await loadCalendar(false)
    }
  }
}

async function loadRank() {
  const payload = await api.get<{ gain?: RankItem[]; loss?: RankItem[] }>(`/api/analysis/rank?type=all&market=${rankMarket.value}`)
  rank.gain = payload.gain || []
  rank.loss = payload.loss || []
}

async function reload(mode: 'light' | 'force' = 'light', includeAnalysis = true) {
  if (reloadInflight) return reloadInflight
  reloadInflight = (async () => {
    try {
      if (mode === 'force') await store.refreshAll(); else await store.refreshStaticOnly()
      realtimeDayReady.value = true
    } catch { realtimeDayReady.value = false }
    if (includeAnalysis) {
      await Promise.all([loadOverview(), loadRates()])
      await Promise.all([loadCalendar(), loadRank()])
    }
    persistAnalysisCache()
  })()
  try { await reloadInflight } finally { reloadInflight = null }
}

function onCalendarTypeChange(nextType: CalendarType) {
  calendarType.value = nextType
  if (nextType === 'day') ensureDaySelection()
  else if (nextType === 'month') ensureMonthSelection()
  void loadCalendar()
}

function onDayMonthChange() { void loadCalendar() }
function onRankMarketChange(m: RankMarket) { rankMarket.value = m; void loadRank() }

// Redundant masked handler removed

onMounted(() => {
  restoreAnalysisCache()
  realtimeDayReady.value = store.rows.value.length > 0
  void reload('light', true)
})
</script>

<style scoped>
.analysis-page-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.analysis-main {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0;
}

.analysis-side {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-label {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.action-btn {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.action-btn:hover {
  background: var(--border-color);
  transform: translateY(-2px);
}

/* Overview Card */
.overview-hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.hero-main {
  display: flex;
  flex-direction: column;
}

.hero-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.hero-val {
  font-size: 42px;
  font-weight: 800;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1.2;
}

.hero-rate {
  font-size: 18px;
  font-weight: 600;
  margin-top: 4px;
}

.hero-side {
  display: flex;
  gap: 32px;
  text-align: right;
}

.s-lab {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.s-val {
  font-size: 18px;
  font-weight: 700;
}

.summary-tabs {
  display: flex;
  gap: 4px;
  background: var(--bg-secondary);
  padding: 4px;
  border-radius: 10px;
}

.s-tab {
  padding: 6px 16px;
  border-radius: 8px;
  border: 0;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.s-tab.active {
  background: var(--card-bg);
  color: var(--text-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Calendar Card */
.calendar-controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.calendar-picker-wrap {
  display: flex;
  gap: 8px;
}

.mini-select {
  height: 32px;
  padding: 0 8px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 12px;
}

.calendar-grid {
  display: grid;
  gap: 8px;
  margin-bottom: 16px;
}

.cal-cell {
  height: 80px;
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background: var(--bg-secondary);
  transition: transform 0.2s;
  cursor: default;
}

.cal-cell:hover {
  transform: scale(1.02);
  z-index: 1;
}

.cal-date {
  font-size: 12px;
  font-weight: 700;
  opacity: 0.6;
}

.cal-pnl {
  font-size: 14px;
  font-weight: 800;
  text-align: right;
}

.cal-cell.up {
  background: rgba(var(--up-rgb, 239, 68, 68), 0.1);
  color: var(--up-color);
  border: 1px solid rgba(var(--up-rgb, 239, 68, 68), 0.2);
}

.cal-cell.down {
  background: rgba(var(--down-rgb, 34, 197, 94), 0.1);
  color: var(--down-color);
  border: 1px solid rgba(var(--down-rgb, 34, 197, 94), 0.2);
}

.cal-cell.flat {
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.cal-cell.empty {
  opacity: 0.3;
  background: transparent;
  border: 1px dashed var(--border-color);
}

.calendar-footer {
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
  font-size: 13px;
  font-weight: 600;
}

.muted {
  opacity: 0.6;
}

/* Rank Card */
.market-filters {
  display: flex;
  gap: 8px;
}

.filter-tag {
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
}

.filter-tag.active {
  background: var(--text-primary);
  color: var(--card-bg);
  border-color: var(--text-primary);
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rank-item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-radius: 12px;
  background: var(--bg-secondary);
  transition: all 0.2s;
}

.rank-item-row:hover {
  background: var(--border-color);
}

.rank-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.rank-idx {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 800;
  color: #fff;
}

.rank-idx.top1 { background: linear-gradient(135deg, #FFD700, #FFA500); }
.rank-idx.top2 { background: linear-gradient(135deg, #C0C0C0, #808080); }
.rank-idx.top3 { background: linear-gradient(135deg, #CD7F32, #8B4513); }
.rank-idx.normal { background: var(--border-color); color: var(--text-secondary); }

.asset-core {
  display: flex;
  flex-direction: column;
}

.asset-name {
  font-size: 15px;
  font-weight: 700;
}

.asset-code {
  font-size: 12px;
  color: var(--text-secondary);
}

.rank-values {
  text-align: right;
}

.val-pnl {
  font-size: 16px;
  font-weight: 800;
  font-family: 'JetBrains Mono', monospace;
}

.val-rate {
  font-size: 12px;
  font-weight: 600;
}

.expand-btn {
  width: 100%;
  margin-top: 16px;
  padding: 12px;
  border-radius: 12px;
  border: 1px dashed var(--border-color);
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

/* Sidebar */
.period-cards-stack {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.mini-period-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.p-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.p-val {
  font-size: 16px;
  font-weight: 800;
}

.p-rate {
  font-size: 12px;
  font-weight: 600;
}

.trend-card {
  min-height: 240px;
}

.mock-chart-container {
  height: 140px;
  margin: 20px 0;
  display: flex;
  align-items: flex-end;
}

.chart-bars {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: 100%;
  gap: 4px;
}

.bar-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.bar-fill {
  width: 100%;
  background: var(--text-primary);
  border-radius: 4px 4px 0 0;
  transition: height 1s ease-out;
}

.bar-label {
  font-size: 10px;
  color: var(--text-secondary);
}

.chart-summary {
  display: flex;
  gap: 16px;
}

.c-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.c-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.c-dot.up { background: var(--up-color); }
.c-dot.down { background: var(--down-color); }

.tips-list {
  padding: 0;
  margin: 16px 0 0;
  list-style: none;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.8;
}

/* Common status */
.up { color: var(--up-color); }
.down { color: var(--down-color); }
.flat { color: var(--text-secondary); }

@media (max-width: 1024px) {
  .analysis-page-layout {
    grid-template-columns: 1fr;
  }
  .analysis-side {
    order: -1;
  }
}

@media (max-width: 640px) {
  .overview-hero {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  .hero-side {
    width: 100%;
    justify-content: flex-start;
    text-align: left;
  }
  .hero-val {
    font-size: 32px;
  }
}
</style>
