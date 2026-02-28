<template>
  <LegacyAdminShell title="操作审计" subtitle="后台操作日志与追溯">
    <section class="panel" style="padding: 16px; margin-bottom: 16px;">
      <div class="toolbar">
        <input class="input" v-model.trim="action" placeholder="按 action 过滤" />
        <button class="btn" @click="load(true)">查询</button>
      </div>
    </section>

    <section class="panel" style="padding: 16px;">
      <table class="table">
        <thead>
          <tr>
            <th>时间</th>
            <th>管理员</th>
            <th>动作</th>
            <th>目标</th>
            <th>结果</th>
            <th>错误</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in logs.items || []" :key="item.id">
            <td>{{ shortDateTime(item.created_at) }}</td>
            <td>{{ item.admin_username || '-' }}</td>
            <td>{{ item.action }}</td>
            <td>{{ item.target_type }} / {{ item.target_id }}</td>
            <td>{{ item.result }}</td>
            <td>{{ item.error_code || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </LegacyAdminShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
import { api } from '../../shared/http'
import { shortDateTime } from '../../shared/format'

const action = ref('')
const logs = reactive<Record<string, any>>({ items: [] })

async function load(force = false) {
  const q = encodeURIComponent(action.value)
  const suffix = force ? '&force=1' : ''
  Object.assign(logs, await api.get(`/api/admin/audit/logs?action=${q}&limit=200${suffix}`))
}

onMounted(() => {
  void load()
})
</script>

<style scoped>
.toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 80px;
  gap: 8px;
}

@media (max-width: 900px) {
  .toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
