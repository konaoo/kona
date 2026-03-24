<template>
  <AppShell title="资产分析">
    <div class="analysis-page-layout">
      <!-- 1. 盈亏概览 (Revenue Overview) -->
      <div class="card analysis-overview-card">
        <div class="card-header-row">
          <div class="section-label">盈亏概览</div>
        </div>
        
        <div class="overview-hero">
           <div class="hero-label">{{ periodLabel }}总计盈亏</div>
           <div class="hero-val" :class="valueClass(periodPnl)">{{ formatCny(periodPnl) }}</div>
           <div class="hero-rate" :class="valueClass(periodRate)">
              {{ formatPct(periodRate) }}
           </div>
        </div>

        <div class="period-segmented-control">
          <button class="seg-btn" :class="{ active: overviewPeriod === 'day' }" @click="overviewPeriod = 'day'">当日</button>
          <button class="seg-btn" :class="{ active: overviewPeriod === 'month' }" @click="overviewPeriod = 'month'">本月</button>
          <button class="seg-btn" :class="{ active: overviewPeriod === 'year' }" @click="overviewPeriod = 'year'">本年</button>
          <button class="seg-btn" :class="{ active: overviewPeriod === 'all' }" @click="overviewPeriod = 'all'">全部</button>
        </div>
      </div>

      <!-- 2. 收益日历 (Revenue Calendar) -->
      <div class="card calendar-card analysis-calendar-card">
        <div class="card-header-row">
          <div class="section-label">收益日历</div>
        </div>
        <div class="calendar-controls">
           <div class="calendar-picker-wrap" style="position: relative;">
              <button class="cal-period-btn" v-if="calendarType !== 'year'" @click="showDatePicker = !showDatePicker">
                {{ calendarPeriodButtonText }}
                <span class="cal-arrow">{{ showDatePicker ? '▲' : '▼' }}</span>
              </button>
              <span class="cal-period-btn" v-else>历史年度</span>

              <!-- 日期选择器下拉面板 -->
              <div class="date-picker-dropdown" v-if="showDatePicker && calendarType !== 'year'">
                <div class="dp-columns">
                  <div class="dp-col">
                    <div class="dp-col-title">年</div>
                    <div class="dp-list">
                      <button
                        v-for="y in pickerYears"
                        :key="y"
                        class="dp-item"
                        :class="{ active: y === pickerSelectedYear }"
                        @click="onPickYear(y)"
                      >{{ y }}</button>
                    </div>
                  </div>
                  <div class="dp-divider"></div>
                  <div class="dp-col" v-if="calendarType === 'day'">
                    <div class="dp-col-title">月</div>
                    <div class="dp-list">
                      <button
                        v-for="m in pickerMonths"
                        :key="m"
                        class="dp-item"
                        :class="{ active: m === pickerSelectedMonth }"
                        @click="onPickMonth(m)"
                      >{{ m }}月</button>
                    </div>
                  </div>
                </div>
              </div>
           </div>
           <div class="view-tabs mini-segment">
              <button class="view-tab" :class="{ active: calendarType === 'day' }" @click="onCalendarTypeChange('day')">日</button>
              <button class="view-tab" :class="{ active: calendarType === 'month' }" @click="onCalendarTypeChange('month')">月</button>
              <button class="view-tab" :class="{ active: calendarType === 'year' }" @click="onCalendarTypeChange('year')">年</button>
           </div>
        </div>

        <div class="calendar-grid" :style="calendarGridStyle">
          <div v-for="cell in calendarGrid" :key="cell.key" class="cal-cell" :class="calendarCellClass(cell.pnl)">
             <div class="cal-date">{{ formatCalendarCellLabel(cell.key) }}</div>
             <div class="cal-pnl">{{ formatCalendarCellPnl(cell.pnl) }}</div>
          </div>
        </div>

        <div class="calendar-footer" v-if="calendarState.totalPnl !== null">
          <span class="calendar-footer-label">{{ calendarSummaryLabel }}</span>
          <span class="calendar-footer-value" :class="valueClass(calendarState.totalPnl)">{{ formatCny(calendarState.totalPnl) }}</span>
          <span class="calendar-footer-rate" :class="valueClass(calendarState.totalRate)">{{ formatPct(calendarState.totalRate) }}</span>
        </div>
      </div>

      <!-- 3. 盈亏排行榜 (PnL Ranking) -->
      <div class="card rank-card analysis-rank-card">
        <div class="card-header-row">
          <div class="section-label">盈亏排行榜</div>
          <div class="market-filters mini-segment">
             <button class="view-tab" :class="{ active: rankType === 'profit' }" @click="rankType = 'profit'">盈利榜</button>
             <button class="view-tab" :class="{ active: rankType === 'loss' }" @click="rankType = 'loss'">亏损榜</button>
          </div>
        </div>

        <div class="rank-list">
          <div v-if="filteredRankItems.length === 0" class="empty-rank">暂无数据</div>
          <template v-for="(item, idx) in filteredRankItems" :key="item.code">
            <div v-if="idx < 4 || rankExpanded" class="rank-item-row">
               <div class="rank-info">
                  <span class="rank-badge" :class="rankBadgeClass(idx + 1)">
                     <div class="badge-bg"></div>
                     <span class="badge-num" v-if="idx >= 3">{{ idx + 1 }}</span>
                     <i class="icon-medal" v-else>★</i>
                  </span>
                  <div class="asset-core">
                    <div class="asset-name">{{ item.name || item.code }}</div>
                    <div class="asset-code">{{ formatDisplayCode(item.code) }}</div>
                  </div>
               </div>
               <div class="rank-values" :class="valueClass(rankPnlValue(item))">
                  <div class="val-pnl">{{ formatRankPnl(item) }}</div>
                  <div class="val-rate">{{ formatPct(toNum(item.pnl_rate)) }}</div>
                </div>
            </div>
          </template>
          <button
            v-if="filteredRankItems.length > 4 && !rankExpanded"
            class="rank-expand-btn"
            @click="rankExpanded = true"
          >查看更多</button>
          <button
            v-if="rankExpanded && filteredRankItems.length > 4"
            class="rank-expand-btn"
            @click="rankExpanded = false"
          >收起</button>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import AppShell from '../../layouts/AppShell.vue'
import { toNumber } from '../../shared/format'
import { useKonaStore } from '../../stores/composables'
import {
  useAnalysisStore,
  type AnalysisCalendarType,
  type AnalysisRankItem,
} from '../../stores/analysis'

const konaStore = useKonaStore()
const analysisStore = useAnalysisStore()
const {
  overview,
  calendarState,
  calendarType,
  rankType,
  selectedDayYear,
  selectedDayMonth,
  selectedMonthYear,
  pickerYears,
  pickerSelectedYear,
  pickerMonths,
  pickerSelectedMonth,
  filteredRankItems,
  calendarSummaryLabel,
  calendarGrid,
} = storeToRefs(analysisStore)

const rankExpanded = ref(false)
const overviewPeriod = ref<'day' | 'month' | 'year' | 'all'>('day')
const showDatePicker = ref(false)
let analysisRefreshTimer: number | null = null

function onPickYear(year: number) {
  showDatePicker.value = false
  analysisStore.onPickYear(year)
}

function onPickMonth(month: number) {
  showDatePicker.value = false
  analysisStore.onPickMonth(month)
}

const toNum = toNumber

const periodLabel = computed(() => {
  if (overviewPeriod.value === 'day') return '当日'
  if (overviewPeriod.value === 'month') return '本月'
  if (overviewPeriod.value === 'year') return '今年'
  return '累计'
})

const periodPnl = computed(() => {
  if (overviewPeriod.value === 'day') {
    return toNum(konaStore.summary.value?.todayPnl)
  }
  const key = overviewPeriod.value
  const value = overview.value[key]?.pnl
  return value == null ? null : toNum(value)
})

const periodRate = computed(() => {
  if (overviewPeriod.value === 'day') {
    return toNum(konaStore.summary.value?.dayRate)
  }
  const key = overviewPeriod.value
  const value = overview.value[key]?.pnl_rate
  return value == null ? null : toNum(value)
})

const calendarColumns = computed(() => {
  if (calendarType.value === 'day') return 7
  if (calendarType.value === 'month') return 4
  return 5
})

const calendarGridStyle = computed(() => {
  if (calendarType.value === 'day') {
    return { gridTemplateColumns: 'repeat(7, minmax(0, 1fr))' }
  }
  return { gridTemplateColumns: `repeat(${calendarColumns.value}, minmax(0, 1fr))` }
})

const calendarPeriodButtonText = computed(() => {
  if (calendarType.value === 'day') {
    if (!selectedDayYear.value || !selectedDayMonth.value) return '暂无周期'
    return `${selectedDayYear.value}年${String(selectedDayMonth.value).padStart(2, '0')}月`
  }
  if (calendarType.value === 'month') {
    if (!selectedMonthYear.value) return '暂无周期'
    return `${selectedMonthYear.value}年`
  }
  return ''
})

function valueClass(value: number | null): 'up' | 'down' | 'flat' {
  if (value == null) return 'flat'
  if (value > 0) return 'up'
  if (value < 0) return 'down'
  return 'flat'
}

function formatCny(value: number | null): string {
  if (value == null) return '--'
  const val = Math.round(toNum(value))
  return (val >= 0 ? '+¥ ' : '-¥ ') + Math.abs(val).toLocaleString()
}

function formatPct(value: number | null): string {
  if (value == null) return '--'
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

function formatDisplayCode(code: string) {
  const raw = String(code || '').trim()
  if (!raw) return '-'
  const upper = raw.toUpperCase()
  if (upper.startsWith('FT_')) return upper.slice(3)
  if (upper.startsWith('F_')) return upper.slice(2)
  if (upper.startsWith('GB_')) return upper.slice(3)
  if (upper.startsWith('HK')) return upper.slice(2)
  if (upper.startsWith('SH')) return upper.slice(2)
  if (upper.startsWith('SZ')) return upper.slice(2)
  if (upper.startsWith('BJ')) return upper.slice(2)
  return upper
}

function currencySymbol(curr: unknown): string {
  const code = String(curr || 'CNY').toUpperCase()
  if (code === 'USD') return '$'
  if (code === 'HKD') return 'HK$'
  return '¥'
}

function formatRankPnl(item: AnalysisRankItem): string {
  const pnl = toNum(item.pnl)
  const abs = Math.abs(pnl)
  const symbol = currencySymbol(item.curr)
  const formatted = Math.round(abs).toLocaleString('zh-CN')
  return `${pnl >= 0 ? '+' : '-'}${symbol} ${formatted}`
}

function rankPnlValue(item: AnalysisRankItem): number {
  return toNum(item.pnl)
}
function onCalendarTypeChange(nextType: AnalysisCalendarType) {
  showDatePicker.value = false
  analysisStore.onCalendarTypeChange(nextType)
}

// Redundant masked handler removed

onMounted(() => {
  void analysisStore.initialize()
  konaStore.startAutoRefresh()
  void konaStore.refreshQuotesOnly()
  analysisRefreshTimer = window.setInterval(() => {
    void analysisStore.reload('light', true)
  }, 60_000)
})

onBeforeUnmount(() => {
  konaStore.stopAutoRefresh()
  if (analysisRefreshTimer !== null) {
    window.clearInterval(analysisRefreshTimer)
    analysisRefreshTimer = null
  }
})
</script>

<style scoped>
.analysis-page-layout {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 800px;
  margin: 0 auto;
  padding: 16px;
  min-height: calc(100vh - 64px);
}

.card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-label {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

/* Overview Card */
.analysis-overview-card {
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 32px 24px;
}

[data-theme="light"] .analysis-overview-card,
[data-theme="light"] .analysis-calendar-card,
[data-theme="light"] .analysis-rank-card {
  background: linear-gradient(180deg, #ffffff, #fbfcff);
  border-color: rgba(15, 23, 42, 0.08);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
}

[data-theme="dark"] .analysis-overview-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.07);
}

.overview-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0 24px;
}

.hero-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.hero-val {
  font-size: 42px;
  font-weight: 800;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1.2;
  letter-spacing: -1px;
}

.hero-rate {
  font-size: 16px;
  font-weight: 700;
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Calendar Card */
.analysis-calendar-card {
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid var(--border-color);
}

[data-theme="dark"] .analysis-calendar-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.07);
}

/* Rank Card */
.analysis-rank-card {
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid var(--border-color);
}

[data-theme="dark"] .analysis-rank-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.07);
}

/* ── Date Picker Dropdown ── */
.cal-period-btn {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.11), rgba(255, 255, 255, 0.06));
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 12px;
  padding: 6px 14px;
  min-height: 42px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
  transition: background 0.15s, border-color 0.15s, transform 0.15s;
}
[data-theme="light"] .cal-period-btn {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.04), rgba(15, 23, 42, 0.02));
  border-color: rgba(15, 23, 42, 0.1);
  box-shadow: none;
}
.cal-period-btn:hover {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.09));
  border-color: rgba(91, 141, 239, 0.45);
  transform: translateY(-1px);
}
[data-theme="light"] .cal-period-btn:hover {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.06), rgba(91, 141, 239, 0.05));
  border-color: rgba(91, 141, 239, 0.3);
}
.cal-arrow {
  font-size: 9px;
  opacity: 0.5;
}

.date-picker-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  z-index: 100;
  background: var(--s2, #181b24);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 14px;
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.45);
  min-width: 180px;
}
[data-theme="light"] .date-picker-dropdown {
  background: #ffffff;
  border-color: rgba(15, 23, 42, 0.1);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.12);
}

.dp-columns {
  display: flex;
  gap: 0;
}

.dp-col {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.dp-col-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--muted, #545c72);
  text-align: center;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.dp-divider {
  width: 1px;
  margin: 0 8px;
  background: rgba(255, 255, 255, 0.06);
}
[data-theme="light"] .dp-divider {
  background: rgba(15, 23, 42, 0.08);
}

.dp-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 200px;
  overflow-y: auto;
}

.dp-item {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid transparent;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: var(--sub, #828a9e);
  cursor: pointer;
  text-align: center;
  transition: background 0.12s, color 0.12s;
}
[data-theme="light"] .dp-item {
  background: rgba(15, 23, 42, 0.025);
  color: var(--sub);
}
.dp-item:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}
[data-theme="light"] .dp-item:hover {
  background: rgba(15, 23, 42, 0.05);
  border-color: rgba(15, 23, 42, 0.08);
}
.dp-item.active {
  background: rgba(91, 141, 239, 0.18);
  border-color: rgba(91, 141, 239, 0.45);
  color: #8bb4ff;
  font-weight: 700;
}
[data-theme="light"] .dp-item.active {
  background: rgba(91, 141, 239, 0.1);
  color: var(--blue);
}

/* Segmented Control for Periods */
.period-segmented-control {
  display: flex;
  background: var(--bg-secondary);
  border-radius: 999px;
  padding: 4px;
  margin-top: 8px;
}

.seg-btn {
  flex: 1;
  padding: 8px 0;
  border-radius: 999px;
  border: 0;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.seg-btn.active {
  background: #3F8CFF;
  color: #fff;
  box-shadow: 0 2px 8px rgba(63, 140, 255, 0.3);
}

/* Calendar Controls */
.calendar-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 12px;
}

.mini-segment {
  display: flex;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.04));
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 2px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}
[data-theme="light"] .mini-segment {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.04), rgba(15, 23, 42, 0.02));
  border-color: rgba(15, 23, 42, 0.1);
  box-shadow: none;
}
[data-theme="dark"] .mini-segment {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.09), rgba(255, 255, 255, 0.04));
}

.view-tab {
  padding: 4px 16px;
  min-height: 36px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.16s ease;
}

.view-tab:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
}
[data-theme="light"] .view-tab:hover {
  background: rgba(15, 23, 42, 0.05);
}

.view-tab.active {
  background: rgba(255, 255, 255, 0.92);
  color: #0f172a;
  border-color: rgba(255, 255, 255, 0.95);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.18);
  font-weight: 800;
}
[data-theme="light"] .view-tab.active,
[data-theme="light"] .rank-card .view-tab.active {
  background: #ffffff;
  color: #0f172a;
  border-color: rgba(15, 23, 42, 0.12);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.1);
}
.rank-card .view-tab.active {
  background: rgba(255, 255, 255, 0.92);
  color: #0f172a;
  border-color: rgba(255, 255, 255, 0.95);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.18);
}

/* Calendar Grid */
.calendar-grid {
  display: grid;
  gap: 8px;
  margin-bottom: 18px;
  align-items: stretch;
}

.cal-cell {
  min-height: 74px;
  border-radius: 12px;
  padding: 8px 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  position: relative;
  overflow: hidden;
  text-align: center;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
}
[data-theme="light"] .cal-cell {
  background: rgba(15, 23, 42, 0.025);
  border-color: rgba(15, 23, 42, 0.07);
}

.cal-date {
  font-size: 16px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  opacity: 0.9;
  text-align: center;
  line-height: 1;
}

.cal-pnl {
  font-size: 12px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  text-align: center;
  line-height: 1.15;
  word-break: keep-all;
  width: 100%;
}

.cal-cell.up {
  background: linear-gradient(180deg, rgba(var(--up-rgb, 239, 68, 68), 0.14), rgba(var(--up-rgb, 239, 68, 68), 0.09));
  border-color: rgba(var(--up-rgb, 239, 68, 68), 0.16);
  color: var(--up-color);
}

.cal-cell.down {
  background: linear-gradient(180deg, rgba(var(--down-rgb, 34, 197, 94), 0.14), rgba(var(--down-rgb, 34, 197, 94), 0.09));
  border-color: rgba(var(--down-rgb, 34, 197, 94), 0.16);
  color: var(--down-color);
}

.cal-cell.flat {
  background: rgba(255, 255, 255, 0.025);
  color: var(--text-secondary);
}

.cal-cell.empty {
  opacity: 0.55;
  background: rgba(255, 255, 255, 0.015);
  border: 1px dashed rgba(255, 255, 255, 0.08);
}

.calendar-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.02));
  font-size: 12px;
  font-weight: 600;
}

.calendar-footer-label {
  color: var(--text-secondary);
}

.calendar-footer-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.5px;
}

.calendar-footer-rate {
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}

/* Rank Card */
.rank-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-rank {
  padding: 24px 0;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

.rank-expand-btn {
  display: block;
  margin: 12px auto 0;
  padding: 8px 24px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  color: var(--sub, #828a9e);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.rank-expand-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
}

.rank-item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.4);
  border: 1px solid transparent;
}
[data-theme="dark"] .rank-item-row {
  background: rgba(0, 0, 0, 0.15);
  border-color: rgba(255, 255, 255, 0.03);
}

.rank-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rank-badge {
  width: 24px;
  height: 24px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  color: #fff;
  position: relative;
  overflow: hidden;
  background: var(--border-color);
  color: var(--text-secondary);
}

.badge-bg {
  position: absolute;
  inset: 0;
}

.rank-badge.top1 .badge-bg { background: linear-gradient(135deg, #FFD700, #FFA500); }
.rank-badge.top2 .badge-bg { background: linear-gradient(135deg, #E2E8F0, #94A3B8); }
.rank-badge.top3 .badge-bg { background: linear-gradient(135deg, #CD7F32, #8B4513); }
.rank-badge.top1, .rank-badge.top2, .rank-badge.top3 { color: #0F172A; }

.badge-num, .icon-medal {
  position: relative;
  z-index: 1;
  font-style: normal;
}

.icon-medal {
  font-size: 12px;
}

.asset-core {
  display: flex;
  flex-direction: column;
}

.asset-name {
  font-size: 14px;
  font-weight: 600;
}

.asset-code {
  font-size: 11px;
  color: var(--text-secondary);
  font-family: 'JetBrains Mono', monospace;
}

.rank-values {
  text-align: right;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.val-pnl {
  font-size: 15px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}

.val-rate {
  font-size: 11px;
  font-weight: 600;
}

/* Common status */
.up { color: var(--up-color); }
.down { color: var(--down-color); }
.flat { color: var(--text-secondary); }
.muted { opacity: 0.6; }

@media (max-width: 640px) {
  .analysis-page-layout {
    padding: 12px;
    gap: 16px;
  }
  .card {
    padding: 16px;
  }
}
</style>
