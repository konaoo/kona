<template>
  <LegacyAdminShell title="用户管理" subtitle="查询、封禁与资产明细">
    <section class="panel" style="padding: 16px; margin-bottom: 16px;">
      <div class="toolbar">
        <input class="input" v-model.trim="query" placeholder="搜索用户名/昵称/手机号" />
        <select class="input slim" v-model="status">
          <option value="all">全部</option>
          <option value="active">active</option>
          <option value="disabled">disabled</option>
        </select>
        <button class="btn" @click="load(true)">查询</button>
      </div>
    </section>

    <section class="panel" style="padding: 16px;">
      <table class="table">
        <thead>
          <tr>
            <th>用户名</th>
            <th>用户昵称</th>
            <th>总资产金额（￥）</th>
            <th>投资资产金额（￥）</th>
            <th>注册时间</th>
            <th>最近活跃时间</th>
            <th>最近活跃地区</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users.items || []" :key="u.id">
            <td>{{ u.username }}</td>
            <td>{{ u.nickname || '-' }}</td>
            <td>{{ formatCny(u.total_asset_cny) }}</td>
            <td>{{ formatCny(u.total_invest_cny) }}</td>
            <td>{{ shortDateTime(u.created_at) }}</td>
            <td>{{ shortDateTime(u.last_active_at || u.last_login) }}</td>
            <td>{{ displayRegion(u.last_active_region || u.last_login_region) }}</td>
            <td class="actions">
              <button class="btn" @click="openDetail(u)">详情</button>
              <button class="btn" @click="toggleStatus(u)">{{ u.status === 'disabled' ? '解封' : '封禁' }}</button>
            </td>
          </tr>
          <tr v-if="!(users.items || []).length">
            <td colspan="8" class="empty">暂无用户数据</td>
          </tr>
        </tbody>
      </table>
      <p v-if="message" :class="ok ? 'up' : 'down'">{{ message }}</p>
    </section>

    <div v-if="detail.visible" class="detail-mask" @click.self="closeDetail">
      <section class="panel detail-panel">
        <div class="detail-head">
          <h3>持仓详情 · {{ detail.username || '-' }}</h3>
          <button class="btn" @click="closeDetail">关闭</button>
        </div>

        <div v-if="detail.loading" class="detail-loading">加载中...</div>

        <table v-else class="table">
          <thead>
            <tr>
              <th>代码</th>
              <th>名称</th>
              <th>数量</th>
              <th>成本价</th>
              <th>币种</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in detail.items" :key="item.code">
              <td>{{ item.code }}</td>
              <td>{{ item.name || '-' }}</td>
              <td>{{ formatQty(item.qty) }}</td>
              <td>{{ formatPrice(item.price) }}</td>
              <td>{{ item.curr || '-' }}</td>
            </tr>
            <tr v-if="!detail.items.length">
              <td colspan="5" class="empty">暂无持仓</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </LegacyAdminShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
import { api } from '../../shared/http'
import { money, shortDateTime } from '../../shared/format'

const query = ref('')
const status = ref('all')
const users = reactive<Record<string, any>>({ items: [], total: 0 })
const message = ref('')
const ok = ref(true)
const detail = reactive<{
  visible: boolean
  loading: boolean
  userId: string
  username: string
  items: Array<Record<string, any>>
}>({
  visible: false,
  loading: false,
  userId: '',
  username: '',
  items: [],
})

function flash(msg: string, success: boolean) {
  message.value = msg
  ok.value = success
}

async function load(force = false) {
  const q = encodeURIComponent(query.value)
  const s = encodeURIComponent(status.value)
  const forcePart = force ? '&force=1' : ''
  Object.assign(users, await api.get(`/api/admin/users?q=${q}&status=${s}&limit=100&offset=0&include_local=0${forcePart}`))
}

async function toggleStatus(user: Record<string, any>) {
  try {
    const next = user.status === 'disabled' ? 'active' : 'disabled'
    if (next === 'disabled') {
      if (!window.confirm(`确认封禁用户 ${user.username} 吗？`)) return
      if (!window.confirm(`二次确认：封禁后 ${user.username} 将无法登录，是否继续？`)) return
    }
    await api.post('/api/admin/users/status', { user_id: user.id, status: next })
    flash('状态已更新', true)
    await load(true)
  } catch (e) {
    flash(e instanceof Error ? e.message : '更新失败', false)
  }
}

async function openDetail(user: Record<string, any>) {
  detail.visible = true
  detail.loading = true
  detail.userId = String(user.id || '')
  detail.username = String(user.username || '')
  detail.items = []
  try {
    const payload = await api.get<Record<string, any>>(
      `/api/admin/users/${encodeURIComponent(detail.userId)}/portfolio`,
    )
    detail.items = Array.isArray(payload?.items) ? payload.items : []
  } catch (e) {
    flash(e instanceof Error ? e.message : '加载详情失败', false)
    detail.items = []
  } finally {
    detail.loading = false
  }
}

function closeDetail() {
  detail.visible = false
  detail.loading = false
  detail.userId = ''
  detail.username = ''
  detail.items = []
}

function formatCny(value: unknown): string {
  const n = Number(value)
  return money(Number.isFinite(n) ? n : 0, 'CNY')
}

function formatQty(value: unknown): string {
  const n = Number(value)
  return Number.isFinite(n) ? n.toLocaleString('zh-CN', { maximumFractionDigits: 4 }) : '-'
}

function formatPrice(value: unknown): string {
  const n = Number(value)
  return Number.isFinite(n) ? n.toLocaleString('zh-CN', { maximumFractionDigits: 4 }) : '-'
}

function displayRegion(value: unknown): string {
  const raw = String(value || '').trim()
  return raw || '未知'
}

onMounted(() => {
  void load()
})
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
  justify-content: center;
  align-items: center;
  flex-wrap: nowrap;
  white-space: nowrap;
  min-width: 170px;
}

.table th:last-child,
.table td:last-child {
  text-align: center;
}

.up {
  color: var(--success);
}

.down {
  color: var(--danger);
}

.empty {
  text-align: center;
  color: #55708f;
  font-weight: 600;
}

.detail-mask {
  position: fixed;
  inset: 0;
  background: rgba(7, 18, 33, 0.58);
  display: grid;
  place-items: center;
  z-index: 90;
  padding: 16px;
}

.detail-panel {
  width: min(980px, 100%);
  max-height: min(78vh, 760px);
  overflow: auto;
  padding: 14px;
}

.detail-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.detail-head h3 {
  margin: 0;
  color: #24496e;
}

.detail-loading {
  padding: 18px 4px;
  color: #46678f;
}

@media (max-width: 900px) {
  .toolbar {
    grid-template-columns: 1fr;
  }

  .actions {
    flex-wrap: wrap;
  }
}
</style>
