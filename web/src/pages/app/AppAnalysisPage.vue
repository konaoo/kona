<template>
  <LegacyAppShell>
    <section class="legacy-section">
      <div class="section-header">
        <h2 class="section-title">收益概览</h2>
        <button class="legacy-btn-primary" @click="reload">刷新</button>
      </div>
      <div class="milestone-grid">
        <article class="milestone-card" v-for="(period, key) in periods" :key="key">
          <div class="milestone-title">{{ period.label }}</div>
          <div class="milestone-main" :class="valueClass(toNum(overview[key]?.pnl))">
            {{ formatCny(toNum(overview[key]?.pnl)) }}
          </div>
          <div class="milestone-rate" :class="valueClass(toNum(overview[key]?.pnl_rate))">
            {{ formatPct(toNum(overview[key]?.pnl_rate)) }}
          </div>
        </article>
      </div>
    </section>

    <section class="legacy-section">
      <div class="section-header">
        <h2 class="section-title">收益日历</h2>
        <div class="calendar-header-controls">
          <div class="view-tabs">
            <button class="view-tab" :class="{ active: calendarType === 'day' }" @click="calendarType = 'day'">日</button>
            <button class="view-tab" :class="{ active: calendarType === 'month' }" @click="calendarType = 'month'">月</button>
            <button class="view-tab" :class="{ active: calendarType === 'year' }" @click="calendarType = 'year'">年</button>
          </div>
          <button class="legacy-btn-primary" @click="loadCalendar">查询</button>
        </div>
      </div>
      <div class="calendar-title">{{ calendar.title || '收益日历' }}</div>
      <table class="rank-table">
        <thead>
          <tr>
            <th>标签</th>
            <th>收益</th>
          </tr>
        </thead>
        <tbody>
          <tr class="rank-row" v-for="item in calendar.items || []" :key="item.label">
            <td>{{ item.label }}</td>
            <td :class="valueClass(toNum(item.pnl))">{{ formatCny(toNum(item.pnl)) }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="legacy-section">
      <div class="section-header">
        <h2 class="section-title">盈亏排行</h2>
        <button class="legacy-btn-primary" @click="loadRank">刷新排行</button>
      </div>
      <div class="market-tabs">
        <button
          v-for="tab in marketTabs"
          :key="tab.key"
          class="market-tab"
          :class="{ active: rankMarket === tab.key }"
          @click="rankMarket = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="rank-grid">
        <article class="rank-card">
          <div class="rank-title">盈利榜</div>
          <table class="rank-table">
            <tbody>
              <tr class="rank-row" v-for="item in rank.gain || []" :key="`g-${item.code}`">
                <td>
                  <div class="asset-name-col">
                    <span class="asset-name-main">{{ item.name || item.code }}</span>
                    <span class="asset-code-sub">{{ item.code }}</span>
                  </div>
                </td>
                <td class="up">{{ formatCny(toNum(item.pnl)) }}</td>
              </tr>
            </tbody>
          </table>
        </article>
        <article class="rank-card">
          <div class="rank-title">亏损榜</div>
          <table class="rank-table">
            <tbody>
              <tr class="rank-row" v-for="item in rank.loss || []" :key="`l-${item.code}`">
                <td>
                  <div class="asset-name-col">
                    <span class="asset-name-main">{{ item.name || item.code }}</span>
                    <span class="asset-code-sub">{{ item.code }}</span>
                  </div>
                </td>
                <td class="down">{{ formatCny(toNum(item.pnl)) }}</td>
              </tr>
            </tbody>
          </table>
        </article>
      </div>
    </section>
  </LegacyAppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import LegacyAppShell from '../../layouts/LegacyAppShell.vue'
import { api } from '../../shared/http'
import { toNumber } from '../../shared/format'

const periods: Record<string, { label: string }> = {
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

const overview = reactive<Record<string, { pnl?: number; pnl_rate?: number }>>({})
const calendar = reactive<Record<string, any>>({ items: [] })
const rank = reactive<Record<string, any>>({ gain: [], loss: [] })

const calendarType = ref<'day' | 'month' | 'year'>('day')
const rankMarket = ref<'all' | 'a' | 'hk' | 'us' | 'fund'>('all')

const toNum = toNumber

function formatCny(value: number): string {
  const sign = value > 0 ? '+' : ''
  return `${sign}¥ ${Math.round(value).toLocaleString('zh-CN')}`
}

function formatPct(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function valueClass(value: number): 'up' | 'down' {
  return value >= 0 ? 'up' : 'down'
}

async function loadOverview() {
  const payload = await api.get<Record<string, { pnl?: number; pnl_rate?: number }>>('/api/analysis/overview?period=all')
  Object.assign(overview, payload)
}

async function loadCalendar() {
  const payload = await api.get<Record<string, any>>(`/api/analysis/calendar?type=${calendarType.value}`)
  Object.assign(calendar, payload)
}

async function loadRank() {
  const payload = await api.get<Record<string, any>>(`/api/analysis/rank?type=all&market=${rankMarket.value}`)
  Object.assign(rank, payload)
}

async function reload() {
  await Promise.all([loadOverview(), loadCalendar(), loadRank()])
}

onMounted(reload)
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

.calendar-header-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.view-tabs {
  display: flex;
  background: rgba(0, 0, 0, 0.18);
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
}

.market-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
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

.rank-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.rank-card {
  border: 1px solid var(--legacy-border);
  border-radius: var(--legacy-radius-sm);
  background: var(--legacy-bg-tertiary);
  padding: 12px;
}

.rank-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 8px;
}

.rank-table {
  width: 100%;
  border-collapse: collapse;
}

.rank-table th,
.rank-table td {
  text-align: left;
  padding: 10px;
  border-bottom: 1px solid var(--legacy-border);
}

.rank-row:hover {
  background: rgba(255, 255, 255, 0.04);
}

.asset-name-col {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.asset-name-main {
  font-weight: 600;
}

.asset-code-sub {
  font-size: 12px;
  color: var(--legacy-text-secondary);
}

.up { color: var(--legacy-red); }
.down { color: var(--legacy-green); }

@media (max-width: 1200px) {
  .milestone-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .rank-grid {
    grid-template-columns: 1fr;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}

@media (max-width: 600px) {
  .milestone-grid {
    grid-template-columns: 1fr;
  }
}
</style>
