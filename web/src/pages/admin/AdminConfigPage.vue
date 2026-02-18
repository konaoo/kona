<template>
  <LegacyAdminShell title="配置管理" subtitle="读取与更新系统配置">
    <section class="panel" style="padding: 16px; margin-bottom: 16px;">
      <div class="head">
        <h3>配置列表</h3>
        <button class="btn" @click="load">刷新</button>
      </div>
      <table class="table">
        <thead><tr><th>键</th><th>值</th></tr></thead>
        <tbody>
          <tr v-for="(value, key) in config.data || {}" :key="key">
            <td>{{ key }}</td>
            <td>{{ value }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="panel" style="padding: 16px;">
      <h3>更新配置</h3>
      <div class="grid" style="grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px;">
        <input class="input" v-model.trim="key" placeholder="配置键，如 RATELIMIT_STORAGE_URL" />
        <input class="input" v-model.trim="value" placeholder="配置值" />
      </div>
      <div style="margin-top: 8px; display: flex; gap: 8px;">
        <button class="btn primary" @click="update">提交更新</button>
      </div>
      <p v-if="message" :class="ok ? 'up' : 'down'">{{ message }}</p>
    </section>
  </LegacyAdminShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
import { api } from '../../shared/http'

const config = reactive<Record<string, any>>({ data: {} })
const key = ref('')
const value = ref('')
const message = ref('')
const ok = ref(true)

function flash(msg: string, success: boolean) {
  message.value = msg
  ok.value = success
}

async function load() {
  Object.assign(config, await api.get('/api/admin/config'))
}

async function update() {
  try {
    await api.post('/api/admin/config/update', { key: key.value, value: value.value })
    flash('配置已更新', true)
    await load()
  } catch (e) {
    flash(e instanceof Error ? e.message : '更新失败', false)
  }
}

onMounted(load)
</script>

<style scoped>
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.up {
  color: var(--success);
}

.down {
  color: var(--danger);
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr !important;
  }
}
</style>
