<template>
  <LegacyAdminShell title="邀请码管理" subtitle="生成、查询、撤销">
    <section class="panel" style="padding: 16px; margin-bottom: 16px;">
      <div class="toolbar">
        <input class="input" v-model.number="count" type="number" min="1" max="50" placeholder="生成数量" />
        <button class="btn primary" @click="generate">生成邀请码</button>
        <button class="btn" @click="load">刷新列表</button>
      </div>
      <p v-if="message" :class="ok ? 'up' : 'down'">{{ message }}</p>
    </section>

    <section class="panel" style="padding: 16px;">
      <table class="table">
        <thead><tr><th>邀请码</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="item in invites.items || []" :key="item.code">
            <td>{{ item.code }}</td>
            <td>{{ item.status }}</td>
            <td>{{ item.created_at || '-' }}</td>
            <td><button class="btn" @click="revoke(item)">撤销</button></td>
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

const invites = reactive<Record<string, any>>({ items: [] })
const count = ref(5)
const message = ref('')
const ok = ref(true)

function flash(msg: string, success: boolean) {
  message.value = msg
  ok.value = success
}

async function load() {
  Object.assign(invites, await api.get('/api/admin/invites?limit=100'))
}

async function generate() {
  try {
    await api.post('/api/admin/invites/generate', { count: count.value })
    flash('生成成功', true)
    await load()
  } catch (e) {
    flash(e instanceof Error ? e.message : '生成失败', false)
  }
}

async function revoke(item: Record<string, any>) {
  try {
    await api.post('/api/admin/invites/revoke', { code: item.code })
    flash('撤销成功', true)
    await load()
  } catch (e) {
    flash(e instanceof Error ? e.message : '撤销失败', false)
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
}

.up {
  color: var(--success);
}

.down {
  color: var(--danger);
}

@media (max-width: 900px) {
  .toolbar {
    flex-direction: column;
  }
}
</style>
