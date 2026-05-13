<template>
  <div class="container admin-users">
    <AdminConsoleNav />

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
                <th>AI 积分</th>
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
                <td>{{ formatCredits(u.ai_credits_balance) }}</td>
                <td>{{ shortDateTime(u.last_active_at || u.last_login) }}</td>
                <td class="actions">
                  <button class="action-btn-sm secondary" @click="openDetail(u)">详情</button>
                  <button
                    class="action-btn-sm warning"
                    :disabled="resetPassword.submitting"
                    @click="resetUserPassword(u)"
                  >
                    重置密码
                  </button>
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
                <td colspan="8" style="text-align: center; color: #999; padding: 40px;">暂无匹配用户</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="mobile-user-list">
          <div v-for="u in users.items || []" :key="`mobile-${u.id}`" class="mobile-user-card">
            <div class="mobile-user-head">
              <div class="mobile-user-primary">
                <strong>{{ u.nickname || u.username }}</strong>
                <span>@{{ u.username }}</span>
              </div>
              <span
                class="mobile-status-chip"
                :class="u.status === 'disabled' ? 'is-disabled' : 'is-active'"
              >
                {{ u.status === 'disabled' ? '已封禁' : '正常' }}
              </span>
            </div>

            <div class="mobile-user-grid">
              <div class="mobile-metric">
                <span class="metric-label">总资产</span>
                <strong>{{ formatCny(u.total_asset_cny) }}</strong>
              </div>
              <div class="mobile-metric">
                <span class="metric-label">投资资产</span>
                <strong>{{ formatCny(u.total_invest_cny) }}</strong>
              </div>
              <div class="mobile-metric">
                <span class="metric-label">注册时间</span>
                <strong>{{ shortDateTime(u.created_at) }}</strong>
              </div>
              <div class="mobile-metric">
                <span class="metric-label">AI 积分</span>
                <strong>{{ formatCredits(u.ai_credits_balance) }}</strong>
              </div>
              <div class="mobile-metric">
                <span class="metric-label">最近活跃</span>
                <strong>{{ shortDateTime(u.last_active_at || u.last_login) }}</strong>
              </div>
            </div>

            <div class="mobile-user-actions">
              <button class="action-btn-sm secondary" @click="openDetail(u)">查看详情</button>
              <button
                class="action-btn-sm warning"
                :disabled="resetPassword.submitting"
                @click="resetUserPassword(u)"
              >
                重置密码
              </button>
              <button
                class="action-btn-sm"
                :class="u.status === 'disabled' ? 'secondary' : 'danger'"
                @click="toggleStatus(u)"
              >
                {{ u.status === 'disabled' ? '解除封禁' : '封禁用户' }}
              </button>
            </div>
          </div>

          <div v-if="!(users.items || []).length" class="mobile-empty">
            暂无匹配用户
          </div>
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

          <div class="ai-credit-section">
            <div class="ai-credit-card">
              <div class="ai-credit-head">
                <div>
                  <h4>AI 积分</h4>
                  <p>用于控制小咔助手对话成本，按次扣减。</p>
                </div>
                <div class="ai-credit-balance">{{ formatCredits(detail.aiCreditsBalance) }}</div>
              </div>

              <div class="ai-credit-form">
                <label class="ai-credit-field">
                  <span>变动值</span>
                  <input
                    v-model.number="detail.grantDelta"
                    type="number"
                    step="1"
                    placeholder="例如 5 或 -1"
                  />
                </label>
                <label class="ai-credit-field ai-credit-reason">
                  <span>原因</span>
                  <input
                    v-model.trim="detail.grantReason"
                    type="text"
                    maxlength="40"
                    placeholder="例如 后台发放 / 人工扣减"
                  />
                </label>
                <button
                  class="action-btn-sm dark"
                  :disabled="detail.grantSubmitting"
                  @click="submitAiCreditsGrant"
                >
                  {{ detail.grantSubmitting ? '提交中...' : '提交积分调整' }}
                </button>
              </div>
            </div>

            <div class="ledger-card">
              <div class="ledger-head">
                <h4>最近积分流水</h4>
                <span>{{ detail.aiCreditLedger.length }} 条</span>
              </div>
              <div v-if="detail.aiCreditLedger.length" class="ledger-list">
                <div
                  v-for="entry in detail.aiCreditLedger"
                  :key="entry.id || `${entry.created_at}-${entry.delta}`"
                  class="ledger-item"
                >
                  <div class="ledger-main">
                    <strong :class="Number(entry.delta || 0) >= 0 ? 'up' : 'down'">
                      {{ formatSignedCredits(entry.delta) }}
                    </strong>
                    <span>{{ entry.reason || entry.source || '-' }}</span>
                  </div>
                  <div class="ledger-meta">
                    <span>余额 {{ formatCredits(entry.balance_after) }}</span>
                    <span>{{ shortDateTime(entry.created_at) }}</span>
                  </div>
                </div>
              </div>
              <div v-else class="ledger-empty">暂无积分流水</div>
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

    <div v-if="resetPassword.visible" class="detail-mask" @click.self="closeResetPasswordModal">
      <div class="password-reset-panel">
        <div class="detail-head">
          <div class="head-info">
            <h3>临时密码</h3>
            <p>{{ resetPassword.username }}</p>
          </div>
          <button class="close-btn" @click="closeResetPasswordModal">✕</button>
        </div>

        <div class="password-reset-body">
          <div class="password-reset-tip">
            用户下次登录必须修改密码，旧登录状态已失效。关闭后本页面不再保留这次临时密码。
          </div>
          <div class="password-value-row">
            <code>{{ resetPassword.tempPassword }}</code>
            <button class="action-btn-sm dark" @click="copyTempPassword">
              {{ resetPassword.copied ? '已复制' : '复制密码' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../../shared/http'
import AdminConsoleNav from '../../components/admin/AdminConsoleNav.vue'
import { money, shortDateTime } from '../../shared/format'
import { storeToRefs } from 'pinia'
import { useAdminStore } from '../../stores/admin'

type UserSortBy = 'last_active_at' | 'total_asset_cny' | 'total_invest_cny' | 'created_at'

const adminStore = useAdminStore()
const { users: usersState } = storeToRefs(adminStore)

const query = computed({
  get: () => usersState.value.query,
  set: (val) => { usersState.value.query = val }
})
const sortBy = computed({
  get: () => usersState.value.sortBy,
  set: (val) => { usersState.value.sortBy = val as any }
})
const sortDir = computed({
  get: () => usersState.value.sortDir,
  set: (val) => { usersState.value.sortDir = val }
})
const currentPage = computed({
  get: () => usersState.value.currentPage,
  set: (val) => { usersState.value.currentPage = val }
})
const pageSize = computed({
  get: () => usersState.value.pageSize,
  set: (val) => { usersState.value.pageSize = val }
})

const users = computed(() => usersState.value)
const message = ref('')
const ok = ref(true)
const pageSizeOptions = [10, 20, 50, 100]

const resetPassword = reactive({
  visible: false,
  submitting: false,
  username: '',
  tempPassword: '',
  copied: false,
})

const totalRows = computed(() => Number(users.value.total || 0))
const totalPages = computed(() => {
  const total = totalRows.value
  return total > 0 ? Math.ceil(total / pageSize.value) : 1
})

const detail = reactive<{
  visible: boolean
  loading: boolean
  userId: string
  username: string
  aiCreditsBalance: number
  aiCreditLedger: Array<Record<string, any>>
  grantDelta: number
  grantReason: string
  grantSubmitting: boolean
  summary: { cash_cny: number; other_cny: number; liability_cny: number; as_of: string }
  cache: { cached_at: string; expires_at: string }
  items: Array<Record<string, any>>
}>({
  visible: false,
  loading: false,
  userId: '',
  username: '',
  aiCreditsBalance: 0,
  aiCreditLedger: [],
  grantDelta: 1,
  grantReason: '',
  grantSubmitting: false,
  summary: { cash_cny: 0, other_cny: 0, liability_cny: 0, as_of: '' },
  cache: { cached_at: '', expires_at: '' },
  items: [],
})

function flash(msg: string, success: boolean) {
  message.value = msg
  ok.value = success
}

async function load(options: { force?: boolean } = {}) {
  try {
    await adminStore.loadUsers(options.force)
  } catch (e) {
    console.error('Failed to load users', e)
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

async function resetUserPassword(user: Record<string, any>) {
  const userId = String(user.id || '')
  const username = String(user.username || '')
  if (!userId || resetPassword.submitting) return
  if (!window.confirm(`确认重置用户 ${username} 的密码吗？用户当前登录状态将失效，下次登录必须修改密码。`)) return

  resetPassword.submitting = true
  try {
    const payload = await api.post<Record<string, any>>('/api/admin/users/password/reset', {
      user_id: userId,
      force_change: true,
    })
    resetPassword.username = username
    resetPassword.tempPassword = String(payload?.temp_password || '')
    resetPassword.copied = false
    resetPassword.visible = true
    flash('密码已重置', true)
    await load({ force: true })
  } catch (e) {
    flash(e instanceof Error ? e.message : '重置密码失败', false)
  } finally {
    resetPassword.submitting = false
  }
}

async function copyTempPassword() {
  if (!resetPassword.tempPassword) return
  try {
    await navigator.clipboard.writeText(resetPassword.tempPassword)
    resetPassword.copied = true
  } catch (e) {
    console.error('Failed to copy temp password', e)
    flash('复制失败，请手动复制', false)
  }
}

function closeResetPasswordModal() {
  resetPassword.visible = false
  resetPassword.username = ''
  resetPassword.tempPassword = ''
  resetPassword.copied = false
}

async function openDetail(user: Record<string, any>) {
  detail.visible = true
  detail.loading = true
  detail.userId = String(user.id || '')
  detail.username = String(user.username || '')
  detail.aiCreditsBalance = Number(user.ai_credits_balance || 0)
  detail.aiCreditLedger = []
  detail.grantDelta = 1
  detail.grantReason = ''
  detail.grantSubmitting = false
  detail.items = []
  detail.summary = { cash_cny: 0, other_cny: 0, liability_cny: 0, as_of: '' }
  try {
    const [userPayload, payload] = await Promise.all([
      api.get<Record<string, any>>(`/api/admin/users/${encodeURIComponent(detail.userId)}`),
      api.get<Record<string, any>>(`/api/admin/users/${encodeURIComponent(detail.userId)}/portfolio`),
    ])
    detail.username = String(userPayload?.username || detail.username)
    detail.aiCreditsBalance = Number(userPayload?.ai_credits_balance || 0)
    detail.aiCreditLedger = Array.isArray(userPayload?.ai_credit_ledger)
      ? userPayload.ai_credit_ledger
      : []
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

async function refreshDetail() {
  if (!detail.userId) return
  await openDetail({
    id: detail.userId,
    username: detail.username,
    ai_credits_balance: detail.aiCreditsBalance,
  })
}

async function submitAiCreditsGrant() {
  if (!detail.username) {
    flash('缺少用户名，无法调整积分', false)
    return
  }
  if (!Number.isInteger(detail.grantDelta) || detail.grantDelta === 0) {
    flash('积分变动值必须是非 0 整数', false)
    return
  }
  if (!detail.grantReason.trim()) {
    flash('请先填写调整原因', false)
    return
  }
  detail.grantSubmitting = true
  try {
    await api.post('/api/admin/users/ai_credits/grant', {
      username: detail.username,
      delta: detail.grantDelta,
      reason: detail.grantReason.trim(),
    })
    flash('AI 积分已更新', true)
    detail.grantDelta = 1
    detail.grantReason = ''
    await Promise.all([load({ force: true }), refreshDetail()])
  } catch (e) {
    flash(e instanceof Error ? e.message : '积分调整失败', false)
  } finally {
    detail.grantSubmitting = false
  }
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

function formatCredits(value: unknown): string {
  const n = Number(value)
  return Number.isFinite(n) ? `${Math.trunc(n)} 积分` : '0 积分'
}

function formatSignedCredits(value: unknown): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return '0'
  return `${n >= 0 ? '+' : ''}${Math.trunc(n)}`
}

function formatPct(value: unknown): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return '-'
  return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`
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

.mobile-user-list {
  display: none;
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
.action-btn-sm.warning { background: #fffbeb; color: #b45309; border-color: #fde68a; }
.action-btn-sm.danger { background: #fff5f5; color: #fa5252; border-color: #ffe3e3; }
.action-btn-sm.dark { background: #111827; color: #fff; border-color: #111827; }
.action-btn-sm:hover { border-color: #000; transform: translateY(-1px); }
.action-btn-sm.warning:hover { background: #f59e0b; color: #fff; border-color: #f59e0b; }
.action-btn-sm.danger:hover { background: #fa5252; color: white; border-color: #fa5252; }
.action-btn-sm.dark:hover { background: #000; color: #fff; border-color: #000; }
.action-btn-sm:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }

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

.password-reset-panel {
  background: white;
  width: 100%;
  max-width: 520px;
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
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

.password-reset-body {
  padding: 24px 30px 30px;
}

.password-reset-tip {
  border: 1px solid #fde68a;
  background: #fffbeb;
  color: #92400e;
  border-radius: 16px;
  padding: 14px 16px;
  font-size: 13px;
  line-height: 1.6;
  font-weight: 700;
}

.password-value-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  margin-top: 18px;
}

.password-value-row code {
  min-height: 46px;
  display: flex;
  align-items: center;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 0 14px;
  background: #f9fafb;
  color: #111827;
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 0.02em;
  overflow-wrap: anywhere;
}

.summary-grid-simple {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; padding: 24px 30px; background: #fafafa;
}
.summary-item-simple { padding: 18px; border-radius: 16px; border: 1px solid #f0f0f0; background: white; }
.summary-item-simple .label { font-size: 12px; font-weight: 700; color: #999; text-transform: uppercase; letter-spacing: 0.5px; }
.summary-item-simple .value { font-size: 20px; font-weight: 800; color: #000; margin-top: 6px; }

.cache-tip { padding: 0 30px; color: #aaa; font-size: 12px; margin: 10px 0; }

.ai-credit-section {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 20px;
  padding: 0 30px 20px;
}

.ai-credit-card,
.ledger-card {
  background: #fff;
  border: 1px solid #edeef1;
  border-radius: 18px;
  padding: 18px;
}

.ai-credit-head,
.ledger-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.ai-credit-head h4,
.ledger-head h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: #111;
}

.ai-credit-head p {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: #7b8190;
}

.ai-credit-balance {
  flex-shrink: 0;
  border-radius: 999px;
  padding: 8px 12px;
  background: #f4f7ff;
  color: #2b5ee6;
  font-size: 13px;
  font-weight: 800;
}

.ai-credit-form {
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr) auto;
  gap: 12px;
  margin-top: 16px;
}

.ai-credit-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ai-credit-field span {
  font-size: 12px;
  font-weight: 700;
  color: #7b8190;
}

.ai-credit-field input {
  width: 100%;
  min-height: 42px;
  border: 1px solid #dde2ea;
  border-radius: 12px;
  padding: 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: #111;
  background: #fff;
  outline: none;
}

.ai-credit-field input:focus {
  border-color: #111827;
}

.ai-credit-reason {
  min-width: 0;
}

.ledger-head span {
  font-size: 12px;
  font-weight: 700;
  color: #7b8190;
}

.ledger-list {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}

.ledger-item {
  border: 1px solid #eef0f4;
  border-radius: 14px;
  padding: 12px 14px;
  background: #fafbfc;
}

.ledger-main,
.ledger-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.ledger-main strong {
  font-size: 15px;
  font-weight: 800;
}

.ledger-main span,
.ledger-meta span {
  font-size: 12px;
  color: #6b7280;
}

.ledger-meta {
  margin-top: 8px;
}

.ledger-empty {
  margin-top: 16px;
  border: 1px dashed #d8dde6;
  border-radius: 14px;
  padding: 18px;
  text-align: center;
  color: #8a90a1;
  font-weight: 700;
}

.sub-table { margin: 0 30px 30px 30px; max-height: 400px; overflow-y: auto; }
.asset-cell { display: flex; flex-direction: column; gap: 2px; }
.asset-cell strong { font-size: 14px; color: #000; }
.asset-cell small { font-size: 11px; color: #999; }
.pnl-cell { display: flex; flex-direction: column; gap: 2px; }
.pnl-cell small { font-size: 11px; font-weight: 600; }

@media (max-width: 900px) {
  .sidebar { display: none; }
  .main-content { padding: 30px 20px calc(112px + env(safe-area-inset-bottom)); }
  .header { flex-direction: column; align-items: flex-start; gap: 20px; }
  .header-actions { width: 100%; }
  .search-bar { width: 100%; }
  .summary-grid-simple { grid-template-columns: 1fr; }
  .ai-credit-section {
    grid-template-columns: 1fr;
    padding: 0 20px 18px;
  }
  .ai-credit-form {
    grid-template-columns: 1fr;
  }
  .table-container {
    display: none;
  }
  .mobile-user-list {
    display: grid;
    gap: 14px;
    margin-bottom: 20px;
  }
  .mobile-user-card {
    background: linear-gradient(180deg, #ffffff 0%, #fbfbfd 100%);
    border: 1px solid #edeef1;
    border-radius: 22px;
    padding: 18px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
  }
  .mobile-user-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 16px;
  }
  .mobile-user-primary {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }
  .mobile-user-primary strong {
    font-size: 18px;
    font-weight: 800;
    color: #111;
    line-height: 1.15;
  }
  .mobile-user-primary span {
    font-size: 13px;
    color: #7b8190;
    font-weight: 600;
    line-height: 1;
  }
  .mobile-status-chip {
    flex-shrink: 0;
    border-radius: 999px;
    padding: 7px 12px;
    font-size: 12px;
    font-weight: 800;
    line-height: 1;
  }
  .mobile-status-chip.is-active {
    background: #ecfdf3;
    color: #067647;
  }
  .mobile-status-chip.is-disabled {
    background: #fff1f2;
    color: #be123c;
  }
  .mobile-user-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }
  .mobile-metric {
    background: #f8f9fb;
    border: 1px solid #eef0f4;
    border-radius: 16px;
    padding: 12px 14px;
    min-width: 0;
  }
  .metric-label {
    display: block;
    font-size: 11px;
    font-weight: 800;
    color: #8a90a1;
    margin-bottom: 8px;
    letter-spacing: 0.02em;
  }
  .mobile-metric strong {
    display: block;
    font-size: 14px;
    font-weight: 800;
    color: #16181d;
    line-height: 1.25;
    word-break: break-word;
  }
  .mobile-user-actions {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin-top: 14px;
  }
  .mobile-user-actions .action-btn-sm {
    min-height: 42px;
    border-radius: 14px;
    font-size: 13px;
  }
  .mobile-empty {
    background: white;
    border: 1px dashed #d8dde6;
    border-radius: 18px;
    padding: 32px 18px;
    text-align: center;
    color: #8a90a1;
    font-weight: 700;
  }
  .table-footer {
    flex-direction: column;
    align-items: stretch;
    gap: 14px;
  }
  .page-size-selector,
  .pagination-info,
  .pagination-controls {
    justify-content: center;
  }
}
</style>
