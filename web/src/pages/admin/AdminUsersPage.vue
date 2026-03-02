<template>
  <LegacyAdminShell title="用户管理" subtitle="查询、封禁与资产明细">
    <AdminCard class="search-card">
      <AdminSectionHeader title="用户管理" subtitle="当前仅展示总资产 > 0 的用户">
        <template #actions>
          <span class="all-chip">全部（总资产>0）</span>
        </template>
      </AdminSectionHeader>
      <div class="toolbar">
        <input class="input" v-model.trim="query" placeholder="搜索用户名/昵称/手机号" @keyup.enter="onSearch" />
        <AdminButton variant="primary" @click="onSearch">查询</AdminButton>
      </div>
    </AdminCard>

    <AdminCard class="list-card">
      <AdminTable>
        <thead>
          <tr>
            <th>用户名</th>
            <th>用户昵称</th>
            <th>
              <button class="sort-btn" @click="toggleSort('total_asset_cny')">
                总资产金额（￥）<span>{{ sortIcon('total_asset_cny') }}</span>
              </button>
            </th>
            <th>
              <button class="sort-btn" @click="toggleSort('total_invest_cny')">
                投资资产金额（￥）<span>{{ sortIcon('total_invest_cny') }}</span>
              </button>
            </th>
            <th>
              <button class="sort-btn" @click="toggleSort('created_at')">
                注册时间<span>{{ sortIcon('created_at') }}</span>
              </button>
            </th>
            <th>
              <button class="sort-btn" @click="toggleSort('last_active_at')">
                最近活跃时间<span>{{ sortIcon('last_active_at') }}</span>
              </button>
            </th>
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
              <AdminButton size="sm" variant="ghost" @click="openDetail(u)">详情</AdminButton>
              <AdminButton size="sm" :variant="u.status === 'disabled' ? 'secondary' : 'danger'" @click="toggleStatus(u)">
                {{ u.status === 'disabled' ? '解封' : '封禁' }}
              </AdminButton>
            </td>
          </tr>
          <tr v-if="!(users.items || []).length">
            <td colspan="8" class="empty">暂无用户数据</td>
          </tr>
        </tbody>
      </AdminTable>

      <div class="pager-wrap">
        <div class="pager">
          <span class="pager-total">共{{ totalRows }}条</span>
          <select v-model.number="pageSize" class="pager-select">
            <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}条/页</option>
          </select>
          <AdminButton size="sm" variant="ghost" :disabled="currentPage <= 1" @click="prevPage">上一页</AdminButton>
          <span class="pager-page">第 {{ currentPage }} / {{ totalPages }} 页</span>
          <AdminButton size="sm" variant="ghost" :disabled="currentPage >= totalPages" @click="nextPage">下一页</AdminButton>
        </div>
      </div>

      <p v-if="message" :class="ok ? 'up' : 'down'" class="msg">{{ message }}</p>
    </AdminCard>

    <div v-if="detail.visible" class="detail-mask" @click.self="closeDetail">
      <AdminCard class="detail-panel">
        <div class="detail-head">
          <h3>资产详情 · {{ detail.username || '-' }}</h3>
          <AdminButton variant="ghost" @click="closeDetail">关闭</AdminButton>
        </div>

        <div v-if="detail.loading" class="detail-loading">加载中...</div>

        <template v-else>
          <div class="summary-grid">
            <div class="summary-item">
              <div class="summary-label">现金资产</div>
              <div class="summary-value">{{ formatCny(detail.summary.cash_cny) }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">其他资产</div>
              <div class="summary-value">{{ formatCny(detail.summary.other_cny) }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">我的负债</div>
              <div class="summary-value">{{ formatCny(detail.summary.liability_cny) }}</div>
            </div>
          </div>

          <p v-if="detail.cache.cached_at" class="cache-tip">
            数据时间：{{ shortDateTime(detail.cache.cached_at) }}
          </p>

          <div class="detail-sub-title">投资资产 · 持仓明细</div>
          <AdminTable>
            <thead>
              <tr>
                <th>资产名称/代码</th>
                <th>数量</th>
                <th>累计盈亏金额/率</th>
                <th>类型</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in detail.items" :key="`${item.code}-${item.type_label}`">
                <td>
                  <div class="asset-cell">
                    <strong>{{ item.name || '-' }}</strong>
                    <span>{{ item.code || '-' }}</span>
                  </div>
                </td>
                <td>{{ formatQty(item.qty) }}</td>
                <td>
                  <div class="pnl-cell">
                    <span :class="Number(item.pnl_cny || 0) >= 0 ? 'up' : 'down'">
                      {{ formatSignedCny(item.pnl_cny) }}
                    </span>
                    <small :class="Number(item.pnl_rate || 0) >= 0 ? 'up' : 'down'">
                      {{ formatPct(item.pnl_rate) }}
                    </small>
                  </div>
                </td>
                <td>{{ item.type_label || '-' }}</td>
              </tr>
              <tr v-if="!detail.items.length">
                <td colspan="4" class="empty">暂无持仓</td>
              </tr>
            </tbody>
          </AdminTable>
        </template>
      </AdminCard>
    </div>
  </LegacyAdminShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
import AdminCard from '../../components/admin/ui/AdminCard.vue'
import AdminButton from '../../components/admin/ui/AdminButton.vue'
import AdminTable from '../../components/admin/ui/AdminTable.vue'
import AdminSectionHeader from '../../components/admin/ui/AdminSectionHeader.vue'
import { api } from '../../shared/http'
import { money, shortDateTime } from '../../shared/format'

type UserSortBy = 'last_active_at' | 'total_asset_cny' | 'total_invest_cny' | 'created_at'

const query = ref('')
const sortBy = ref<UserSortBy>('last_active_at')
const sortDir = ref<'asc' | 'desc'>('desc')
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
  summary: {
    cash_cny: number
    other_cny: number
    liability_cny: number
    as_of: string
  }
  cache: {
    cached_at: string
    expires_at: string
  }
  items: Array<Record<string, any>>
}>({
  visible: false,
  loading: false,
  userId: '',
  username: '',
  summary: {
    cash_cny: 0,
    other_cny: 0,
    liability_cny: 0,
    as_of: '',
  },
  cache: {
    cached_at: '',
    expires_at: '',
  },
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
    sortBy.value,
    sortDir.value,
    String(pageSize.value),
    String(offset),
    force ? '1' : '0',
  ].join('|')
  if (!force && (key === lastRequestKey || key === inflightKey)) return

  inflightKey = key
  try {
    const params = new URLSearchParams({
      q: query.value,
      status: 'all',
      include_local: '0',
      sort_by: sortBy.value,
      sort_dir: sortDir.value,
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

function toggleSort(field: UserSortBy) {
  if (sortBy.value === field) {
    sortDir.value = sortDir.value === 'desc' ? 'asc' : 'desc'
  } else {
    sortBy.value = field
    sortDir.value = 'desc'
  }
  currentPage.value = 1
  void load({ force: true })
}

function sortIcon(field: UserSortBy): string {
  if (sortBy.value !== field) return '↕'
  return sortDir.value === 'desc' ? '↓' : '↑'
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
  detail.summary = { cash_cny: 0, other_cny: 0, liability_cny: 0, as_of: '' }
  detail.cache = { cached_at: '', expires_at: '' }
  try {
    const payload = await api.get<Record<string, any>>(
      `/api/admin/users/${encodeURIComponent(detail.userId)}/portfolio`,
    )
    detail.items = Array.isArray(payload?.items) ? payload.items : []
    const summary = payload?.summary || {}
    detail.summary = {
      cash_cny: Number(summary.cash_cny || 0),
      other_cny: Number(summary.other_cny || 0),
      liability_cny: Number(summary.liability_cny || 0),
      as_of: String(summary.as_of || ''),
    }
    const cache = payload?.cache || {}
    detail.cache = {
      cached_at: String(cache.cached_at || detail.summary.as_of || ''),
      expires_at: String(cache.expires_at || ''),
    }
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

function formatSignedCny(value: unknown): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return '￥0.00'
  const abs = money(Math.abs(n), 'CNY')
  return n >= 0 ? `+${abs}` : `-${abs}`
}

function formatQty(value: unknown): string {
  const n = Number(value)
  return Number.isFinite(n) ? n.toLocaleString('zh-CN', { maximumFractionDigits: 4 }) : '-'
}

function formatPct(value: unknown): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return '-'
  return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`
}

function displayRegion(value: unknown): string {
  const raw = String(value || '').trim()
  return raw || '未知'
}

watch(pageSize, async () => {
  currentPage.value = 1
  await load()
})

onMounted(() => {
  void load()
})
</script>

<style scoped>
.search-card {
  padding: 16px;
  margin-bottom: 16px;
}

.all-chip {
  display: inline-flex;
  align-items: center;
  border: 1px solid #d2deeb;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 700;
  color: #35567c;
  background: #f4f8fd;
}

.toolbar {
  margin-top: 12px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 90px;
  gap: 8px;
}

.list-card {
  padding: 16px;
}

.sort-btn {
  border: 0;
  background: transparent;
  color: #55708f;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  align-items: center;
  flex-wrap: nowrap;
  white-space: nowrap;
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

.msg {
  margin-top: 10px;
}

.empty {
  text-align: center;
  color: #55708f;
  font-weight: 600;
}

.up {
  color: var(--success);
}

.down {
  color: var(--danger);
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
  width: min(1020px, 100%);
  max-height: min(82vh, 820px);
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

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  column-gap: 20px;
  row-gap: 14px;
  margin-bottom: 12px;
}

.summary-item {
  border: 1px solid #d8e3f0;
  border-radius: 12px;
  background: #f9fbff;
  padding: 12px;
}

.summary-label {
  color: #55708f;
  font-size: 12px;
  font-weight: 700;
}

.summary-value {
  margin-top: 6px;
  color: #1f3f58;
  font-size: 18px;
  font-weight: 800;
}

.cache-tip {
  margin: 0 0 10px;
  color: #55708f;
  font-size: 12px;
}

.detail-sub-title {
  margin: 0 0 10px;
  color: #1f3f58;
  font-size: 16px;
  font-weight: 700;
}

.asset-cell {
  display: grid;
  gap: 2px;
}

.asset-cell strong {
  color: #10243e;
}

.asset-cell span {
  color: #55708f;
  font-size: 12px;
}

.pnl-cell {
  display: grid;
  gap: 2px;
}

.pnl-cell small {
  font-size: 12px;
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

  .detail-head {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
