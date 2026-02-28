<template>
  <LegacyAdminShell title="接口策略" subtitle="健康检查与策略开关">
    <section class="panel" style="padding: 16px; margin-bottom: 16px;">
      <div class="toolbar">
        <button class="btn" @click="load(true)">刷新</button>
      </div>
    </section>

    <section class="panel" style="padding: 16px; margin-bottom: 16px;">
      <h3>接口健康</h3>
      <pre>{{ JSON.stringify(health, null, 2) }}</pre>
    </section>

    <section class="panel" style="padding: 16px;">
      <h3>策略列表</h3>
      <table class="table">
        <thead><tr><th>scope</th><th>enabled</th><th>limit_per_min</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="item in policies.items || []" :key="item.scope_key">
            <td>{{ item.scope_key }}</td>
            <td>{{ item.enabled ? 'true' : 'false' }}</td>
            <td>{{ item.limit_per_min }}</td>
            <td>
              <button class="btn" @click="toggle(item)">{{ item.enabled ? '禁用' : '启用' }}</button>
            </td>
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

const health = reactive<Record<string, any>>({})
const policies = reactive<Record<string, any>>({ items: [] })

async function load(force = false) {
  const healthForcePart = force ? '?force=1' : ''
  const policyForcePart = force ? '&force=1' : ''
  Object.assign(health, await api.get(`/api/admin/apis/health${healthForcePart}`))
  Object.assign(policies, await api.get(`/api/admin/apis/policies?scope_type=all${policyForcePart}`))
}

async function toggle(item: Record<string, any>) {
  await api.post('/api/admin/apis/policies/update', {
    scope_key: item.scope_key,
    enabled: !item.enabled,
    limit_per_min: item.limit_per_min,
  })
  await load(true)
}

onMounted(() => {
  void load()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  color: var(--muted);
}
</style>
