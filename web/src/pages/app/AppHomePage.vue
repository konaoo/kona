<template>
  <AppShell title="首页" subtitle="总览与市场状态">
    <div class="grid" style="grid-template-columns: repeat(4, minmax(0, 1fr)); margin-bottom: 16px">
      <section class="panel metric">
        <div class="label">总市值</div>
        <div class="value">{{ money(summary.totalValue) }}</div>
      </section>
      <section class="panel metric">
        <div class="label">累计盈亏</div>
        <div class="value" :class="summary.totalPnl >= 0 ? 'up' : 'down'">{{ money(summary.totalPnl) }}</div>
      </section>
      <section class="panel metric">
        <div class="label">当日盈亏</div>
        <div class="value" :class="summary.todayPnl >= 0 ? 'up' : 'down'">{{ money(summary.todayPnl) }}</div>
      </section>
      <section class="panel metric">
        <div class="label">累计收益率</div>
        <div class="value" :class="summary.totalRate >= 0 ? 'up' : 'down'">{{ pct(summary.totalRate) }}</div>
      </section>
    </div>

    <section class="panel" style="padding: 16px; margin-bottom: 16px">
      <div class="section-head">
        <h3>市场状态</h3>
        <button class="btn" @click="refresh">刷新</button>
      </div>
      <div class="chips">
        <span v-for="market in markets" :key="market.code" class="chip" :class="market.open ? 'open' : 'closed'">
          {{ market.name }} · {{ market.open ? '开市' : '休市' }}
        </span>
      </div>
    </section>

    <section class="panel" style="padding: 16px">
      <h3>持仓预览</h3>
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
            <td :class="row.dayPnl >= 0 ? 'up' : 'down'">{{ money(row.dayPnl, row.curr || 'CNY') }}</td>
            <td :class="row.totalPnl >= 0 ? 'up' : 'down'">{{ money(row.totalPnl, row.curr || 'CNY') }}</td>
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
.metric {
  padding: 16px;
}

.label {
  color: var(--muted);
  font-size: 12px;
}

.value {
  margin-top: 6px;
  font-size: 24px;
  font-weight: 800;
}

.up {
  color: var(--success);
}

.down {
  color: var(--danger);
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chip {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
}

.chip.open {
  border-color: #226f5b;
  color: #70f0c6;
}

.chip.closed {
  border-color: #5e3440;
  color: #ff9fb0;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr !important;
  }
}
</style>
