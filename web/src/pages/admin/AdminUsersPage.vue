<template>
  <LegacyAdminShell title="用户管理" subtitle="查询、封禁与资产明细">
    <section class="panel" style="padding: 16px; margin-bottom: 16px;">
      <div class="toolbar">
        <input class="input" v-model.trim="query" placeholder="搜索用户名/昵称/手机号" @keyup.enter="onSearch" />
        <select class="input slim" v-model="status">
          <option value="all">全部</option>
          <option value="active">active</option>
          <option value="disabled">disabled</option>
        </select>
        <select class="input slim" v-model="sortBy">
          <option value="last_active_at">最近活跃时间（降序）</option>
          <option value="total_asset_cny">总资产金额（降序）</option>
          <option value="created_at">注册时间（降序）</option>
        </select>
        <button class="btn" @click="onSearch">查询</button>
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

      <div class="pager-wrap">
        <div class="pager">
          <span class="pager-total">共{{ totalRows }}条</span>
          <select v-model.number="pageSize" class="pager-select">
            <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}条/页</option>
          </select>
          <button class="btn pager-btn" :disabled="currentPage <= 1" @click="prevPage">上一页</button>
          <span class="pager-page">第 {{ currentPage }} / {{ totalPages }} 页</span>
          <button class="btn pager-btn" :disabled="currentPage >= totalPages" @click="nextPage">下一页</button>
        </div>
      </div>

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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
import { api } from '../../shared/http'
import { money, shortDateTime } from '../../shared/format'

type UserSortBy = 'last_active_at' | 'total_asset_cny' | 'created_at'

const query = ref('')
const status = ref('all')
const sortBy = ref<UserSortBy>('last_active_at')
const sortDir = 'desc'
const users = reactive<Record<string, any>>({ items: [], total: 0 })
const message = ref('')
const ok = ref(true)
const currentPage = ref(1)
const pageSize = ref(10)
const pageSizeOptions = [10, 20, 50, 100]
let lastRequestKey = ''
let inflightKey = ''

const totalRows = computed(() => Number(users.total || 0))
const totalPages = computed(() => {
  const total = totalRows.value
  return total > 0 ? Math.ceil(total / pageSize.value) : 1
})

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

async function load(options: { force?: boolean } = {}) {
  const force = Boolean(options.force)
  const offset = (currentPage.value - 1) * pageSize.value
  const key = [
    query.value,
    status.value,
    sortBy.value,
    sortDir,
    String(pageSize.value),
    String(offset),
    force ? '1' : '0',
  ].join('|')
  if (!force && (key === lastRequestKey || key === inflightKey)) return

  inflightKey = key
  try {
    const params = new URLSearchParams({
      q: query.value,
      status: status.value,
      include_local: '0',
      sort_by: sortBy.value,
      sort_dir: sortDir,
      limit: String(pageSize.value),
      offset: String(offset),
    })
    if (force) params.set('force', '1')
    Object.assign(users, await api.get(`/api/admin/users?${params.toString()}`))
    if (!force) lastRequestKey = key
  } finally {
    if (inflightKey === key) inflightKey = ''
  }
}

async function onSearch() {
  currentPage.value = 1
  await load({ force: true })
}

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value || page === currentPage.value) return
  currentPage.value = page
  void load()
}

function prevPage() {
  goToPage(currentPage.value - 1)
}

function nextPage() {
  goToPage(currentPage.value + 1)
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
    await load({ force: true })
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

watch([status, sortBy, pageSize], async () => {
  currentPage.value = 1
  await load()
})

onMounted(() => {
  void load()
})
</script>

<style scoped>
.toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 140px 220px 80px;
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

.pager-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.pager {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid #d9e5f2;
  border-radius: 10px;
  background: #f7fbff;
  max-width: 100%;
  overflow-x: auto;
}

.pager-total,
.pager-page {
  color: #3f6086;
  font-weight: 600;
  white-space: nowrap;
  word-break: keep-all;
  line-height: 1.2;
  flex: 0 0 auto;
}

.pager-select {
  width: 120px !important;
  max-width: 120px;
  min-width: 110px;
  height: 36px;
  border: 1px solid #c7d7ea;
  border-radius: 8px;
  background: #fff;
  color: #35557d;
  padding: 0 10px;
  flex: 0 0 auto;
}

.pager-btn {
  white-space: nowrap;
  flex: 0 0 auto;
}

.pager-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

  .pager-wrap {
    justify-content: flex-start;
  }

  .pager {
    flex-wrap: wrap;
  }
}
</style>
