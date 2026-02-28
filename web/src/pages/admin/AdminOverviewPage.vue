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
          <tr v-for="item in pagedRows" :key="item.date">
            <td>{{ item.date }}</td>
            <td>{{ item.new_users ?? 0 }}</td>
            <td>{{ item.active_users ?? 0 }}</td>
            <td>{{ formatRate(item.retention_1d) }}</td>
            <td>{{ formatRate(item.retention_3d) }}</td>
            <td>{{ formatRate(item.retention_7d) }}</td>
            <td>{{ formatRate(item.retention_14d) }}</td>
            <td>{{ formatRate(item.retention_30d) }}</td>
          </tr>
          <tr v-if="!retentionRows.length">
            <td colspan="8" class="empty">暂无数据</td>
          </tr>
        </tbody>
      </table>

      <div class="pager-wrap">
        <div class="pager">
          <span class="pager-total">共 {{ totalRows }} 条</span>
          <select v-model.number="pageSize" class="pager-select">
            <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}条/页</option>
          </select>
          <button class="btn pager-btn" :disabled="currentPage <= 1" @click="prevPage">上一页</button>
          <span class="pager-page">第 {{ currentPage }} / {{ totalPages }} 页</span>
          <button class="btn pager-btn" :disabled="currentPage >= totalPages" @click="nextPage">下一页</button>
        </div>
      </div>
    </section>
  </LegacyAdminShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
import { api } from '../../shared/http'

const overview = reactive<Record<string, any>>({
  dashboard: {},
  retention_rows: [],
})
const pageSize = ref(10)
const pageSizeOptions = [10, 20, 50, 100]
const currentPage = ref(1)
const retentionRows = computed(() => (overview.retention_rows || []) as Array<Record<string, any>>)
const totalRows = computed(() => retentionRows.value.length)
const totalPages = computed(() => {
  const total = totalRows.value
  return total > 0 ? Math.ceil(total / pageSize.value) : 1
})
const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return retentionRows.value.slice(start, start + pageSize.value)
})

async function load() {
  const payload = await api.get<Record<string, any>>('/api/admin/overview')
  overview.dashboard = payload?.dashboard || {}
  overview.retention_rows = payload?.retention_rows || []
  currentPage.value = 1
}

function formatRate(value: unknown): string {
  if (value === null || value === undefined || value === '') return '-'
  const num = Number(value)
  if (!Number.isFinite(num)) return '-'
  return `${(num * 100).toFixed(1)}%`
}

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function prevPage() {
  goToPage(currentPage.value - 1)
}

function nextPage() {
  goToPage(currentPage.value + 1)
}

watch(pageSize, () => {
  currentPage.value = 1
})

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
  background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
  border: 1px solid #d7e3f3;
}

.kpi-label {
  color: #46658b;
  font-size: 20px;
  font-weight: 700;
}

.kpi-value {
  margin-top: 8px;
  color: #1f3d63;
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

.head h3 {
  color: #35597f;
}

.table th,
.table td {
  text-align: center;
  vertical-align: middle;
}

.table th:first-child,
.table td:first-child {
  text-align: left;
}

.table th {
  color: #42658b;
  font-weight: 700;
}

.table td {
  color: #233f61;
  font-weight: 600;
}

.pager-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.pager {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pager-total,
.pager-page {
  color: #3f6086;
  font-weight: 600;
}

.pager-select {
  min-width: 110px;
  height: 36px;
  border: 1px solid #c7d7ea;
  border-radius: 8px;
  background: #fff;
  color: #35557d;
  padding: 0 10px;
}

.pager-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.empty {
  color: #5f7a98 !important;
  text-align: center;
  font-weight: 600;
}

@media (max-width: 900px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .kpi-label {
    font-size: 16px;
  }

  .kpi-value {
    font-size: 30px;
  }

  .pager-wrap {
    justify-content: flex-start;
  }

  .pager {
    flex-wrap: wrap;
  }
}
</style>
