<template>
  <LegacyAdminShell title="后台概览" subtitle="用户增长与留存">
    <section class="kpi-grid">
      <article class="panel kpi-card">
        <div class="kpi-label">新增用户数（当日）</div>
        <div class="kpi-value">{{ overview.dashboard?.new_users_today ?? 0 }}</div>
      </article>
      <article class="panel kpi-card">
        <div class="kpi-label">活跃用户数（当日）</div>
        <div class="kpi-value">{{ overview.dashboard?.active_users_today ?? 0 }}</div>
      </article>
      <article class="panel kpi-card">
        <div class="kpi-label">累计用户数（历史）</div>
        <div class="kpi-value">{{ overview.dashboard?.total_users ?? 0 }}</div>
      </article>
    </section>

    <section class="panel retention-panel">
      <div class="head">
        <h3>用户增长与留存</h3>
        <button class="btn" @click="load">刷新</button>
      </div>
      <table class="table">
        <thead>
          <tr>
            <th>日期</th>
            <th>新增用户数</th>
            <th>活跃用户数</th>
            <th>用户次留</th>
            <th>3留</th>
            <th>7留</th>
            <th>14留</th>
            <th>30留</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in (overview.retention_rows || [])" :key="item.date">
            <td>{{ item.date }}</td>
            <td>{{ item.new_users ?? 0 }}</td>
            <td>{{ item.active_users ?? 0 }}</td>
            <td>{{ formatRate(item.retention_1d) }}</td>
            <td>{{ formatRate(item.retention_3d) }}</td>
            <td>{{ formatRate(item.retention_7d) }}</td>
            <td>{{ formatRate(item.retention_14d) }}</td>
            <td>{{ formatRate(item.retention_30d) }}</td>
          </tr>
          <tr v-if="!(overview.retention_rows || []).length">
            <td colspan="8" class="empty">暂无数据</td>
          </tr>
        </tbody>
      </table>
    </section>
  </LegacyAdminShell>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
import { api } from '../../shared/http'

const overview = reactive<Record<string, any>>({
  dashboard: {},
  retention_rows: [],
})

async function load() {
  const payload = await api.get<Record<string, any>>('/api/admin/overview')
  overview.dashboard = payload?.dashboard || {}
  overview.retention_rows = payload?.retention_rows || []
}

function formatRate(value: unknown): string {
  if (value === null || value === undefined || value === '') return '-'
  const num = Number(value)
  if (!Number.isFinite(num)) return '-'
  return `${(num * 100).toFixed(1)}%`
}

onMounted(load)
</script>

<style scoped>
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.kpi-card {
  padding: 18px;
}

.kpi-label {
  color: var(--muted);
  font-size: 13px;
}

.kpi-value {
  margin-top: 8px;
  font-size: 38px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.retention-panel {
  padding: 16px;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.empty {
  color: var(--muted);
  text-align: center;
}

@media (max-width: 900px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .kpi-value {
    font-size: 30px;
  }
}
</style>
