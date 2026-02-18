<template>
  <AppShell title="分析" subtitle="收益概览、日历与排行">
    <section class="panel section">
      <div class="head">
        <h3 class="section-title">收益概览</h3>
        <button class="btn" @click="reload">刷新</button>
      </div>
      <div class="kpi-grid overview-grid">
        <article class="panel item" v-for="(key, idx) in ['day', 'month', 'year', 'all']" :key="idx">
          <div class="label">{{ labels[key] || key }}</div>
          <div class="value" :class="toNum(overview[key]?.pnl) >= 0 ? 'value-up' : 'value-down'">
            {{ money(toNum(overview[key]?.pnl)) }}
          </div>
          <div class="small" :class="toNum(overview[key]?.pnl_rate) >= 0 ? 'value-up' : 'value-down'">
            {{ pct(toNum(overview[key]?.pnl_rate)) }}
          </div>
        </article>
      </div>
    </section>

    <section class="panel section">
      <div class="head">
        <h3 class="section-title">收益日历</h3>
        <div class="filters">
          <select v-model="calendarType" class="input slim">
            <option value="day">按日</option>
            <option value="month">按月</option>
            <option value="year">按年</option>
          </select>
          <button class="btn" @click="loadCalendar">查询</button>
        </div>
      </div>
      <p class="small text-muted">{{ calendar.title || '—' }}</p>
      <table class="table">
        <thead><tr><th>标签</th><th>收益</th></tr></thead>
        <tbody>
          <tr v-for="item in (calendar.items || [])" :key="item.label">
            <td>{{ item.label }}</td>
            <td :class="toNum(item.pnl) >= 0 ? 'value-up' : 'value-down'">{{ money(toNum(item.pnl)) }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="panel section">
      <div class="head">
        <h3 class="section-title">盈亏排行</h3>
        <div class="filters">
          <select v-model="rankMarket" class="input slim">
            <option value="all">全部市场</option>
            <option value="a">A股</option>
            <option value="hk">港股</option>
            <option value="us">美股</option>
            <option value="fund">基金</option>
          </select>
          <button class="btn" @click="loadRank">查询</button>
        </div>
      </div>
      <div class="rank-grid">
        <article class="panel rank-card">
          <h4 class="rank-title">盈利榜</h4>
          <table class="table">
            <tbody>
              <tr v-for="item in (rank.gain || [])" :key="`g-${item.code}`">
                <td>{{ item.code }} {{ item.name }}</td>
                <td class="value-up">{{ money(toNum(item.pnl)) }}</td>
              </tr>
            </tbody>
          </table>
        </article>
        <article class="panel rank-card">
          <h4 class="rank-title">亏损榜</h4>
          <table class="table">
            <tbody>
              <tr v-for="item in (rank.loss || [])" :key="`l-${item.code}`">
                <td>{{ item.code }} {{ item.name }}</td>
                <td class="value-down">{{ money(toNum(item.pnl)) }}</td>
              </tr>
            </tbody>
          </table>
        </article>
      </div>
    </section>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import AppShell from '../../layouts/AppShell.vue'
import { api } from '../../shared/http'
import { money, pct, toNumber } from '../../shared/format'

const overview = reactive<Record<string, { pnl?: number; pnl_rate?: number }>>({})
const calendar = reactive<Record<string, any>>({ items: [] })
const rank = reactive<Record<string, any>>({ gain: [], loss: [] })
const calendarType = ref('day')
const rankMarket = ref('all')
const labels: Record<string, string> = { day: '当日', month: '本月', year: '本年', all: '累计' }

const toNum = toNumber

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
.section {
  padding: 16px;
  margin-bottom: 14px;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.filters {
  display: flex;
  gap: 8px;
}

.slim {
  width: 120px;
  min-height: 40px;
  padding: 8px 10px;
}

.overview-grid {
  margin-top: 12px;
}

.item {
  padding: 14px;
  border-radius: 14px;
  border-color: rgba(87, 118, 171, 0.28);
}

.label,
.small {
  color: var(--muted);
  font-size: 12px;
  letter-spacing: 0.04em;
}

.value {
  font-size: clamp(22px, 2.8vw, 28px);
  font-weight: 760;
  margin-top: 6px;
}

.rank-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.rank-card {
  padding: 12px;
  border-radius: 14px;
  border-color: rgba(87, 118, 171, 0.28);
}

.rank-title {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 680;
}

@media (max-width: 900px) {
  .rank-grid {
    grid-template-columns: 1fr;
  }

  .section {
    padding: 14px;
  }

  .filters {
    width: 100%;
    flex-wrap: wrap;
  }

  .slim {
    flex: 1 1 140px;
  }
}
</style>
