<template>
  <AdminShell title="用户管理" subtitle="查询、禁用与重置密码">
    <section class="panel" style="padding: 16px; margin-bottom: 16px;">
      <div class="toolbar">
        <input class="input" v-model.trim="query" placeholder="搜索用户名/昵称/手机号" />
        <select class="input slim" v-model="status">
          <option value="all">全部</option>
          <option value="active">active</option>
          <option value="disabled">disabled</option>
        </select>
        <button class="btn" @click="load">查询</button>
      </div>
    </section>

    <section class="panel" style="padding: 16px;">
      <table class="table">
        <thead>
          <tr>
            <th>用户名</th>
            <th>昵称</th>
            <th>状态</th>
            <th>管理员</th>
            <th>会话数</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users.items || []" :key="u.id">
            <td>{{ u.username }}</td>
            <td>{{ u.nickname || '-' }}</td>
            <td>{{ u.status }}</td>
            <td>{{ Number(u.is_admin || 0) === 1 ? '是' : '否' }}</td>
            <td>{{ u.active_sessions || 0 }}</td>
            <td class="actions">
              <button class="btn" @click="toggleStatus(u)">{{ u.status === 'disabled' ? '启用' : '停用' }}</button>
              <button class="btn" @click="resetPassword(u)">重置密码</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="message" :class="ok ? 'up' : 'down'">{{ message }}</p>
    </section>
  </AdminShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import AdminShell from '../../layouts/AdminShell.vue'
import { api } from '../../shared/http'

const query = ref('')
const status = ref('all')
const users = reactive<Record<string, any>>({ items: [], total: 0 })
const message = ref('')
const ok = ref(true)

function flash(msg: string, success: boolean) {
  message.value = msg
  ok.value = success
}

async function load() {
  const q = encodeURIComponent(query.value)
  const s = encodeURIComponent(status.value)
  Object.assign(users, await api.get(`/api/admin/users?q=${q}&status=${s}&limit=100&offset=0`))
}

async function toggleStatus(user: Record<string, any>) {
  try {
    const next = user.status === 'disabled' ? 'active' : 'disabled'
    await api.post('/api/admin/users/status', { user_id: user.id, status: next })
    flash('状态已更新', true)
    await load()
  } catch (e) {
    flash(e instanceof Error ? e.message : '更新失败', false)
  }
}

async function resetPassword(user: Record<string, any>) {
  try {
    const newPassword = prompt(`为 ${user.username} 设置新密码（至少8位，含字母和数字）`)
    if (!newPassword) return
    await api.post('/api/admin/users/password/reset', { user_id: user.id, new_password: newPassword })
    flash('密码已重置', true)
  } catch (e) {
    flash(e instanceof Error ? e.message : '重置失败', false)
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 140px 80px;
  gap: 8px;
}

.slim {
  width: 100%;
}

.actions {
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
    grid-template-columns: 1fr;
  }
}
</style>
