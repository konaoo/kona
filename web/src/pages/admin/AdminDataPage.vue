<template>
  <LegacyAdminShell title="数据管理" subtitle="快照清理与备份操作">
    <section class="panel" style="padding: 16px; margin-bottom: 16px;">
      <div class="toolbar">
        <button class="btn" @click="load">刷新快照</button>
        <button class="btn" @click="previewCleanup">预览休市清理</button>
        <button class="btn danger" @click="runCleanup">执行休市清理</button>
      </div>
      <p v-if="message" :class="ok ? 'up' : 'down'">{{ message }}</p>
    </section>

    <section class="panel" style="padding: 16px; margin-bottom: 16px;">
      <h3>快照列表</h3>
      <table class="table">
        <thead><tr><th>日期</th><th>总资产</th><th>累计收益</th><th>当日收益</th></tr></thead>
        <tbody>
          <tr v-for="row in snapshots.items || []" :key="row.date">
            <td>{{ row.date }}</td>
            <td>{{ row.total_asset }}</td>
            <td>{{ row.total_pnl }}</td>
            <td>{{ row.day_pnl }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="panel" style="padding: 16px;">
      <h3>预览结果</h3>
      <pre>{{ preview }}</pre>
    </section>
  </LegacyAdminShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
import { api } from '../../shared/http'

const snapshots = reactive<Record<string, any>>({ items: [] })
const preview = ref('暂无')
const message = ref('')
const ok = ref(true)

function flash(msg: string, success: boolean) {
  message.value = msg
  ok.value = success
}

async function load() {
  Object.assign(snapshots, await api.get('/api/admin/data/snapshots?limit=120'))
}

async function previewCleanup() {
  try {
    const payload = await api.post<Record<string, unknown>>('/api/admin/data/snapshot/cleanup_market_closed/preview', {
      markets: ['a', 'hk', 'us', 'fund'],
    })
    preview.value = JSON.stringify(payload, null, 2)
    flash('预览完成', true)
  } catch (e) {
    flash(e instanceof Error ? e.message : '预览失败', false)
  }
}

async function runCleanup() {
  const confirmed = confirm('确认执行“休市日收益清理”？')
  if (!confirmed) return
  try {
    const payload = await api.post<Record<string, unknown>>('/api/admin/data/snapshot/cleanup_market_closed', {
      markets: ['a', 'hk', 'us', 'fund'],
    })
    preview.value = JSON.stringify(payload, null, 2)
    flash('执行完成', true)
    await load()
  } catch (e) {
    flash(e instanceof Error ? e.message : '执行失败', false)
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  color: var(--muted);
}

.up {
  color: var(--success);
}

.down {
  color: var(--danger);
}
</style>
