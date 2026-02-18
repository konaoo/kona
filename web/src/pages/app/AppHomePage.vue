<template>
  <AppShell title="首页" subtitle="总览与市场状态">
    <div class="kpi-grid metrics">
      <section class="panel metric metric-primary">
        <div class="label">总市值</div>
        <div class="value">{{ money(summary.totalValue) }}</div>
      </section>
      <section class="panel metric">
        <div class="label">累计盈亏</div>
        <div class="value" :class="summary.totalPnl >= 0 ? 'value-up' : 'value-down'">{{ money(summary.totalPnl) }}</div>
      </section>
      <section class="panel metric">
        <div class="label">当日盈亏</div>
        <div class="value" :class="summary.todayPnl >= 0 ? 'value-up' : 'value-down'">{{ money(summary.todayPnl) }}</div>
      </section>
      <section class="panel metric">
        <div class="label">累计收益率</div>
        <div class="value" :class="summary.totalRate >= 0 ? 'value-up' : 'value-down'">{{ pct(summary.totalRate) }}</div>
      </section>
    </div>

    <section class="panel section">
      <div class="section-head">
        <h3 class="section-title">市场状态</h3>
        <button class="btn" @click="refresh">刷新</button>
      </div>
      <div class="chips">
        <span v-for="market in markets" :key="market.code" class="chip" :class="market.open ? 'open' : 'closed'">
          {{ market.name }} · {{ market.open ? '开市' : '休市' }}
        </span>
      </div>
    </section>

    <section class="panel section">
      <h3 class="section-title">持仓预览</h3>
      <table class="table">
        <thead>
          <tr>
            <th>代码</th>
            <th>名称</th>
            <th>市场</th>
            <th>现价</th>
            <th>当日盈亏</th>
            <th>累计盈亏</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows.slice(0, 12)" :key="row.code">
            <td>{{ row.code }}</td>
            <td>{{ row.name }}</td>
            <td>{{ row.market }}</td>
            <td>{{ money(row.currentPrice, row.curr || 'CNY') }}</td>
            <td :class="row.dayPnl >= 0 ? 'value-up' : 'value-down'">{{ money(row.dayPnl, row.curr || 'CNY') }}</td>
            <td :class="row.totalPnl >= 0 ? 'value-up' : 'value-down'">{{ money(row.totalPnl, row.curr || 'CNY') }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import AppShell from '../../layouts/AppShell.vue'
import { money, pct } from '../../shared/format'
import { useKonaStore } from '../../shared/store'

const store = useKonaStore()
const rows = computed(() => store.rows.value)
const summary = computed(() => store.summary.value)

const markets = computed(() => {
  const statuses = store.state.marketStatus
  return [
    { code: 'a', name: 'A股', open: Boolean(statuses.a?.open) },
    { code: 'hk', name: '港股', open: Boolean(statuses.hk?.open) },
    { code: 'us', name: '美股', open: Boolean(statuses.us?.open) },
    { code: 'fund', name: '基金', open: Boolean(statuses.fund?.open) },
  ]
})

async function refresh() {
  await store.refreshAll()
}

onMounted(refresh)
</script>

<style scoped>
.metrics {
  margin-bottom: 14px;
}

.metric {
  padding: 18px;
}

.metric-primary {
  background:
    radial-gradient(220px 120px at 12% -16%, rgba(131, 174, 255, 0.24), rgba(131, 174, 255, 0)),
    linear-gradient(150deg, #14233d, #112035);
}

.label {
  color: var(--muted);
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.value {
  margin-top: 8px;
  font-size: clamp(24px, 2.8vw, 30px);
  font-weight: 780;
  line-height: 1.1;
}

.section-head {
  margin-bottom: 10px;
}

.section {
  padding: 16px;
  margin-bottom: 14px;
}

.chips {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.chip {
  border: 1px solid var(--line-soft);
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 12px;
  letter-spacing: 0.02em;
  background: rgba(10, 20, 37, 0.62);
}

.chip.open {
  border-color: #2a7d67;
  color: #80f5cf;
}

.chip.closed {
  border-color: #6d3f49;
  color: #ffacba;
}

@media (max-width: 900px) {
  .section {
    padding: 14px;
  }
}
</style>
