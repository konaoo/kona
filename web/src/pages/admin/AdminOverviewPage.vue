<template>
  <LegacyAdminShell title="后台概览" subtitle="运营与审计摘要">
    <section class="grid" style="grid-template-columns: repeat(3, minmax(0, 1fr)); margin-bottom: 16px;">
      <article class="panel card">
        <div class="label">用户总数</div>
        <div class="value">{{ overview.users?.total ?? 0 }}</div>
      </article>
      <article class="panel card">
        <div class="label">快照总数</div>
        <div class="value">{{ overview.snapshots?.total ?? 0 }}</div>
      </article>
      <article class="panel card">
        <div class="label">最新快照日期</div>
        <div class="value small">{{ overview.snapshots?.latest_date ?? '-' }}</div>
      </article>
    </section>

    <section class="panel" style="padding: 16px; margin-bottom: 16px;">
      <div class="head">
        <h3>待办摘要</h3>
        <button class="btn" @click="load">刷新</button>
      </div>
      <table class="table">
        <thead><tr><th>级别</th><th>标题</th><th>描述</th><th>建议</th></tr></thead>
        <tbody>
          <tr v-for="item in (todo.items || [])" :key="item.code">
            <td>{{ item.level }}</td>
            <td>{{ item.title }}</td>
            <td>{{ item.description }}</td>
            <td>{{ item.suggestion }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="panel" style="padding: 16px">
      <h3>最近审计</h3>
      <table class="table">
        <thead><tr><th>时间</th><th>动作</th><th>结果</th><th>操作人</th><th>目标</th></tr></thead>
        <tbody>
          <tr v-for="item in (overview.recent_audits || [])" :key="item.id">
            <td>{{ shortDateTime(item.created_at) }}</td>
            <td>{{ item.action }}</td>
            <td>{{ item.result }}</td>
            <td>{{ item.admin_username || '-' }}</td>
            <td>{{ item.target_type }} / {{ item.target_id }}</td>
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
import { shortDateTime } from '../../shared/format'

const overview = reactive<Record<string, any>>({ users: {}, snapshots: {}, recent_audits: [] })
const todo = reactive<Record<string, any>>({ items: [] })

async function load() {
  Object.assign(overview, await api.get('/api/admin/overview'))
  Object.assign(todo, await api.get('/api/admin/summary/todo'))
}

onMounted(load)
</script>

<style scoped>
.card {
  padding: 14px;
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

.value.small {
  font-size: 15px;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr !important;
  }
}
</style>
