<template>
  <div class="container admin-users">
    <!-- Sidebar -->
    <div class="sidebar">
      <div class="logo">
        <div class="logo-icon">🏠</div>
        <span>咔咔管理后台</span>
      </div>

      <nav>
        <RouterLink 
          v-for="item in nav" 
          :key="item.path" 
          :to="item.path"
          class="nav-item"
          active-class="active"
        >
          <span>{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="user-profile">
        <div class="user-info">
          <img v-if="avatarSrc" :src="avatarSrc" alt="头像" class="user-avatar" />
          <div v-else class="user-avatar user-avatar-fallback" :style="avatarStyle">{{ avatarInitial }}</div>
          <div class="user-details">
            <h4>{{ store.state.user?.username || '管理员' }}</h4>
            <p>管理员</p>
          </div>
        </div>
        <div class="user-actions">
          <button class="logout-btn" @click="onLogout" title="退出登录">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
      <div class="header">
        <div class="header-title">
          <h1>用户管理</h1>
        </div>
        <div class="header-actions">
          <div class="search-bar">
            <input 
              class="search-input" 
              v-model.trim="query" 
              placeholder="搜索用户名/昵称/手机号" 
              @keyup.enter="onSearch" 
            />
            <button class="add-btn" @click="onSearch">查询</button>
          </div>
        </div>
      </div>

      <div class="user-stats-section">
        <div class="section-header">
           <h2 class="section-title">活跃用户</h2>
           <span class="all-chip">共 {{ totalRows }} 位用户</span>
        </div>
        
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>用户名</th>
                <th>用户昵称</th>
                <th>
                  <button class="sort-btn" @click="toggleSort('total_asset_cny')">
                    总资产 <span>{{ sortIcon('total_asset_cny') }}</span>
                  </button>
                </th>
                <th>
                  <button class="sort-btn" @click="toggleSort('total_invest_cny')">
                    投资资产 <span>{{ sortIcon('total_invest_cny') }}</span>
                  </button>
                </th>
                <th>
                  <button class="sort-btn" @click="toggleSort('created_at')">
                    注册时间 <span>{{ sortIcon('created_at') }}</span>
                  </button>
                </th>
                <th>
                  <button class="sort-btn" @click="toggleSort('last_active_at')">
                    最近活跃 <span>{{ sortIcon('last_active_at') }}</span>
                  </button>
                </th>
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
                <td class="actions">
                  <button class="action-btn-sm secondary" @click="openDetail(u)">详情</button>
                  <button 
                    class="action-btn-sm" 
                    :class="u.status === 'disabled' ? 'secondary' : 'danger'"
                    @click="toggleStatus(u)"
                  >
                    {{ u.status === 'disabled' ? '解封' : '封禁' }}
                  </button>
                </td>
              </tr>
              <tr v-if="!(users.items || []).length">
                <td colspan="7" style="text-align: center; color: #999; padding: 40px;">暂无匹配用户</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="table-footer">
          <div class="page-size-selector">
            <label>每页显示：</label>
            <select v-model.number="pageSize">
              <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}条/页</option>
            </select>
          </div>
          
          <div class="pagination-info">
             第 <span>{{ currentPage }}</span> / <span>{{ totalPages }}</span> 页
          </div>

          <div class="pagination-controls">
            <button class="page-btn" @click="goToPage(1)" :disabled="currentPage === 1">«</button>
            <button class="page-btn" @click="prevPage" :disabled="currentPage === 1">‹</button>
            <button class="page-btn active">{{ currentPage }}</button>
            <button class="page-btn" @click="nextPage" :disabled="currentPage === totalPages">›</button>
            <button class="page-btn" @click="goToPage(totalPages)" :disabled="currentPage === totalPages">»</button>
          </div>
        </div>
        
        <p v-if="message" :class="ok ? 'up' : 'down'" class="msg">{{ message }}</p>
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="detail.visible" class="detail-mask" @click.self="closeDetail">
      <div class="detail-panel">
        <div class="detail-head">
          <div class="head-info">
            <h3>资产明细</h3>
            <p>{{ detail.username }}</p>
          </div>
          <button class="close-btn" @click="closeDetail">✕</button>
        </div>

        <div v-if="detail.loading" class="detail-loading">加载中...</div>

        <template v-else>
          <div class="summary-grid-simple">
            <div class="summary-item-simple cash">
              <div class="label">现金资产</div>
              <div class="value">{{ formatCny(detail.summary.cash_cny) }}</div>
            </div>
            <div class="summary-item-simple invest">
              <div class="label">其他资产</div>
              <div class="value">{{ formatCny(detail.summary.other_cny) }}</div>
            </div>
            <div class="summary-item-simple debt">
              <div class="label">我的负债</div>
              <div class="value">{{ formatCny(detail.summary.liability_cny) }}</div>
            </div>
          </div>

          <p v-if="detail.cache.cached_at" class="cache-tip">
            数据快照：{{ shortDateTime(detail.cache.cached_at) }}
          </p>

          <div class="table-container sub-table">
            <table class="data-table">
              <thead>
                <tr>
                  <th>资产名称/代码</th>
                  <th>持仓数量</th>
                  <th>盈亏金额/率</th>
                  <th>类型</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in detail.items" :key="`${item.code}-${item.type_label}`">
                  <td>
                    <div class="asset-cell">
                      <strong>{{ item.name || '-' }}</strong>
                      <small>{{ item.code || '-' }}</small>
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
                  <td colspan="4" class="empty">暂无持仓明细</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../shared/http'
import { toAvatarSrc } from '../../shared/avatar'
import { useKonaStore } from '../../stores/composables'
import { money, shortDateTime } from '../../shared/format'

const router = useRouter()
const store = useKonaStore()

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

const nav = [
  { path: '/admin/overview', label: '数据概览', icon: '📊' },
  { path: '/admin/users', label: '用户管理', icon: '👥' },
  { path: '/admin/invites', label: '邀请码管理', icon: '🛡️' },
  { path: '/admin/config', label: '运营配置', icon: '⚙️' },
  { path: '/admin/apis', label: '接口管理', icon: '🔌' },
]

const avatarStyle = computed(() => ({
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
}))

const avatarSrc = computed(() => toAvatarSrc(store.state.user?.avatar))
const avatarInitial = computed(() => {
  const raw = String(store.state.user?.nickname || store.state.user?.username || '管').trim()
  return raw.slice(0, 1).toUpperCase()
})

const detail = reactive<{
  visible: boolean
  loading: boolean
  userId: string
  username: string
  summary: { cash_cny: number; other_cny: number; liability_cny: number; as_of: string }
  cache: { cached_at: string; expires_at: string }
  items: Array<Record<string, any>>
}>({
  visible: false,
  loading: false,
  userId: '',
  username: '',
  summary: { cash_cny: 0, other_cny: 0, liability_cny: 0, as_of: '' },
  cache: { cached_at: '', expires_at: '' },
  items: [],
})

function flash(msg: string, success: boolean) {
  message.value = msg
  ok.value = success
}

async function load(options: { force?: boolean } = {}) {
  const force = Boolean(options.force)
  const offset = (currentPage.value - 1) * pageSize.value
  const key = [query.value, sortBy.value, sortDir.value, String(pageSize.value), String(offset), force ? '1' : '0'].join('|')
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

function prevPage() { goToPage(currentPage.value - 1); }
function nextPage() { goToPage(currentPage.value + 1); }

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
  try {
    const payload = await api.get<Record<string, any>>(`/api/admin/users/${encodeURIComponent(detail.userId)}/portfolio`)
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
    flash(e instanceof Error ? e.message : '加载失败', false)
  } finally {
    detail.loading = false
  }
}

function closeDetail() {
  detail.visible = false
  detail.loading = false
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

async function onLogout() {
  await store.logout()
  await router.push('/admin/login')
}

watch(pageSize, () => {
  currentPage.value = 1
  void load()
})

onMounted(() => {
  void load()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.container {
  width: 100vw;
  height: 100vh;
  background: white;
  overflow: hidden;
  display: flex;
  font-family: 'Inter', sans-serif;
  color: #333;
}

/* Sidebar Copy */
.sidebar {
  width: 260px;
  background: white;
  padding: 30px 0 0 0;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 800;
  font-size: 19px;
  margin-bottom: 35px;
  padding: 0 24px;
  color: #000;
  letter-spacing: -0.5px;
}

.logo-icon {
  width: 34px;
  height: 34px;
  background: #000;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 18px;
  margin: 0 12px 6px 12px;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: #666;
  font-weight: 600;
  text-decoration: none;
  font-size: 14.5px;
}

.nav-item:hover {
  background: #f8f9fa;
  color: #000;
}

.nav-item.active {
  background: #000;
  color: white;
}

.user-profile {
  margin-top: auto;
  padding: 24px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fdfdfd;
}

.user-info { display: flex; align-items: center; gap: 12px; }
.user-avatar { width: 44px; height: 44px; border-radius: 50%; flex-shrink: 0; object-fit: cover; }
.user-avatar-fallback { display: flex; align-items: center; justify-content: center; color: #fff; font-size: 18px; font-weight: 800; }
.user-details { display: flex; flex-direction: column; align-items: flex-start; }
.user-details h4 { font-size: 16px; font-weight: 800; margin: 0; padding: 0; color: #000; line-height: 1; }
.user-details p { font-size: 12px; color: #999; font-weight: 500; margin: 4px 0 0 0; padding: 0; line-height: 1; }
.user-actions { display: flex; align-items: center; }

.logout-btn {
  width: 34px; height: 34px; border-radius: 10px; border: 1px solid #e2e2e2;
  background: transparent; color: #888; cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all 0.2s;
}
.logout-btn svg { width: 17px; height: 17px; }
.logout-btn:hover { background: #2d2d2d; color: #fff; border-color: #444; transform: translateX(2px); }

/* Main Content */
.main-content {
  flex: 1; padding: 40px 50px; overflow-y: auto; height: 100vh; background: #fafafa;
}

.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 35px; }

.header-title h1 {
  font-size: 32px; font-weight: 800; margin-bottom: 6px; color: #000; letter-spacing: -0.8px;
}

.header-actions { display: flex; gap: 12px; align-items: center; }

.search-bar {
  display: flex; gap: 8px; background: white; padding: 6px 6px 6px 16px; 
  border-radius: 14px; border: 1px solid #e5e7eb; width: 340px;
}

.search-input {
  border: none; outline: none; flex: 1; font-size: 14px; font-weight: 500; color: #333; background: transparent;
}

.add-btn {
  padding: 0 18px; height: 38px; background: #000; color: white; border: none; border-radius: 10px;
  font-weight: 700; cursor: pointer; transition: all 0.2s; font-size: 13.5px;
}
.add-btn:hover { transform: translateY(-1px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }

/* Section Header */
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 22px; }
.section-title { font-size: 18px; font-weight: 800; color: #000; margin: 0; }
.all-chip { 
  background: #f0f0f0; color: #666; font-size: 12px; font-weight: 700; 
  padding: 4px 12px; border-radius: 99px; 
}

/* Table Style Sync */
.table-container {
  background: white; border: 1px solid #edeef1; border-radius: 18px; 
  overflow: hidden; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
}

.data-table { width: 100%; border-collapse: collapse; }
.data-table thead { background: #fbfbfc; }
.data-table th {
  padding: 16px 22px; text-align: left; font-weight: 700; font-size: 13px; color: #888;
  border-bottom: 1px solid #f0f0f2; white-space: nowrap; text-transform: uppercase; letter-spacing: 0.5px;
}
.data-table tbody tr { transition: all 0.2s; border-bottom: 1px solid #f8f8fb; }
.data-table tbody tr:hover { background: #fcfcfd; }
.data-table td { padding: 18px 22px; font-size: 14px; color: #444; font-weight: 500; }
.data-table td:first-child { font-weight: 700; color: #000; }

.sort-btn {
  border: 0; background: transparent; color: inherit; font-family: inherit;
  font-size: inherit; font-weight: inherit; cursor: pointer; 
  display: inline-flex; align-items: center; gap: 4px; padding: 0;
}

.actions { display: flex; gap: 8px; }
.action-btn-sm {
  border-radius: 8px; border: 1px solid #e5e7eb; background: white;
  padding: 6px 12px; font-size: 12px; font-weight: 700; cursor: pointer; transition: all 0.2s;
}
.action-btn-sm.secondary { background: #f8f9fa; color: #666; }
.action-btn-sm.danger { background: #fff5f5; color: #fa5252; border-color: #ffe3e3; }
.action-btn-sm:hover { border-color: #000; transform: translateY(-1px); }
.action-btn-sm.danger:hover { background: #fa5252; color: white; border-color: #fa5252; }

/* Table Footer Sync */
.table-footer { display: flex; justify-content: space-between; align-items: center; gap: 20px; padding: 5px 0; }
.page-size-selector { display: flex; align-items: center; gap: 12px; font-size: 13.5px; color: #777; font-weight: 600; }
.page-size-selector select {
  padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 10px;
  background: white; cursor: pointer; font-size: 13.5px; font-weight: 600; outline: none;
}
.pagination-info { font-size: 13.5px; color: #777; font-weight: 600; }
.pagination-info span { font-weight: 800; color: #000; }
.pagination-controls { display: flex; align-items: center; gap: 6px; }
.page-btn {
  min-width: 36px; height: 36px; border: 1px solid #e5e7eb; background: white;
  border-radius: 10px; cursor: pointer; font-size: 13px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; transition: all 0.2s;
}
.page-btn.active { background: #000; color: white; border-color: #000; }
.page-btn:hover:not(:disabled):not(.active) { border-color: #000; }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.msg { margin-top: 15px; font-size: 13px; font-weight: 600; }
.up { color: #10b981; }
.down { color: #ef4444; }

/* Modal Styling */
.detail-mask {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px;
}

.detail-panel {
  background: white; width: 100%; max-width: 900px; max-height: 90vh;
  border-radius: 24px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden; display: flex; flex-direction: column;
}

.detail-head {
  padding: 24px 30px; border-bottom: 1px solid #f0f0f0; display: flex;
  justify-content: space-between; align-items: center; background: #fff;
}
.head-info h3 { font-size: 20px; font-weight: 800; color: #000; margin: 0; }
.head-info p { font-size: 14px; color: #666; margin: 4px 0 0 0; font-weight: 500; }
.close-btn {
  width: 36px; height: 36px; border-radius: 50%; border: none; background: #f5f5f5;
  color: #888; cursor: pointer; font-size: 18px; display: flex; align-items: center;
  justify-content: center; transition: all 0.2s;
}
.close-btn:hover { background: #000; color: #fff; transform: rotate(90deg); }

.detail-loading { padding: 60px; text-align: center; color: #999; font-weight: 600; }

.summary-grid-simple {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; padding: 24px 30px; background: #fafafa;
}
.summary-item-simple { padding: 18px; border-radius: 16px; border: 1px solid #f0f0f0; background: white; }
.summary-item-simple .label { font-size: 12px; font-weight: 700; color: #999; text-transform: uppercase; letter-spacing: 0.5px; }
.summary-item-simple .value { font-size: 20px; font-weight: 800; color: #000; margin-top: 6px; }

.cache-tip { padding: 0 30px; color: #aaa; font-size: 12px; margin: 10px 0; }

.sub-table { margin: 0 30px 30px 30px; max-height: 400px; overflow-y: auto; }
.asset-cell { display: flex; flex-direction: column; gap: 2px; }
.asset-cell strong { font-size: 14px; color: #000; }
.asset-cell small { font-size: 11px; color: #999; }
.pnl-cell { display: flex; flex-direction: column; gap: 2px; }
.pnl-cell small { font-size: 11px; font-weight: 600; }

@media (max-width: 900px) {
  .sidebar { display: none; }
  .main-content { padding: 30px 20px; }
  .header { flex-direction: column; align-items: flex-start; gap: 20px; }
  .search-bar { width: 100%; }
  .summary-grid-simple { grid-template-columns: 1fr; }
}
</style>
