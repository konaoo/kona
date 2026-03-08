<template>
  <div class="container admin-invites">
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
          <div class="user-avatar" :style="avatarStyle"></div>
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
          <h1>邀请码管理</h1>
        </div>
        <div class="header-actions">
          <div class="tool-bar">
            <input 
              class="search-input" 
              v-model.number="count" 
              type="number" 
              min="1" 
              max="50" 
              placeholder="生成数量" 
            />
            <button class="add-btn" @click="generate">生成邀请码</button>
            <button class="refresh-btn" @click="load({ force: true })" title="刷新列表">🔄</button>
          </div>
        </div>
      </div>

      <p v-if="message" :class="ok ? 'up' : 'down'" class="msg-tip">{{ message }}</p>

      <div class="user-stats-section">
        <div class="section-header">
           <div class="tabs-capsule">
             <button :class="{ active: inviteStatus === 'active' }" @click="switchTab('active')">未使用</button>
             <button :class="{ active: inviteStatus === 'used' }" @click="switchTab('used')">已使用</button>
           </div>
           <span class="all-chip">共 {{ totalRows }} 条记录</span>
        </div>
        
        <div class="table-container">
          <table class="data-table">
            <thead v-if="inviteStatus === 'active'">
              <tr>
                <th>创建时间</th>
                <th>邀请码</th>
                <th>状态</th>
              </tr>
            </thead>
            <thead v-else>
              <tr>
                <th>邀请码</th>
                <th>用户名</th>
                <th>使用时间</th>
              </tr>
            </thead>
            
            <tbody v-if="inviteStatus === 'active'">
              <tr v-for="item in invites.items || []" :key="item.code">
                <td>{{ formatDateOnly(item.created_at) }}</td>
                <td><code class="code-text">{{ item.code }}</code></td>
                <td><span class="status-tag">{{ statusLabel(item.status) }}</span></td>
              </tr>
              <tr v-if="!(invites.items || []).length">
                <td colspan="3" class="empty">暂无邀请码</td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr v-for="item in invites.items || []" :key="item.code">
                <td><code class="code-text">{{ item.code }}</code></td>
                <td><strong>{{ item.used_by_username || '-' }}</strong></td>
                <td>{{ shortDateTime(item.used_at) }}</td>
              </tr>
              <tr v-if="!(invites.items || []).length">
                <td colspan="3" class="empty">暂无已使用邀请码</td>
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
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../shared/http'
import { useKonaStore } from '../../stores/composables'
import { shortDateTime } from '../../shared/format'

const router = useRouter()
const store = useKonaStore()

const invites = reactive<Record<string, any>>({ items: [], total: 0 })
const count = ref(5)
const message = ref('')
const ok = ref(true)
const inviteStatus = ref<'active' | 'used'>('active')
const pageSize = ref(10)
const pageSizeOptions = [10, 20, 50, 100]
const currentPage = ref(1)
let lastRequestKey = ''
let inflightKey = ''

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

const totalRows = computed(() => Number(invites.total || 0))
const totalPages = computed(() => {
  const total = totalRows.value
  return total > 0 ? Math.ceil(total / pageSize.value) : 1
})

function flash(msg: string, success: boolean) {
  message.value = msg
  ok.value = success
}

function statusLabel(status: unknown): string {
  const value = String(status || '').toLowerCase()
  if (value === 'active') return '未使用'
  if (value === 'used') return '已使用'
  if (value === 'revoked') return '已撤销'
  return value || '-'
}

function formatDateOnly(value: unknown): string {
  const raw = String(value || '').trim()
  if (!raw) return '-'
  if (raw.length >= 10) return raw.slice(0, 10)
  const d = new Date(raw)
  if (Number.isNaN(d.getTime())) return raw
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

async function load(options: { force?: boolean } = {}) {
  const status = inviteStatus.value
  const limit = pageSize.value
  const offset = (currentPage.value - 1) * pageSize.value
  const force = Boolean(options.force)
  const key = `${status}|${limit}|${offset}|${force ? '1' : '0'}`
  if (!force && (key === lastRequestKey || key === inflightKey)) return
  inflightKey = key
  try {
    const params = new URLSearchParams({
      status,
      limit: String(limit),
      offset: String(offset),
    })
    if (force) params.set('force', '1')
    Object.assign(invites, await api.get(`/api/admin/invites?${params.toString()}`))
    if (!force) lastRequestKey = key
  } finally {
    if (inflightKey === key) inflightKey = ''
  }
}

function switchTab(next: 'active' | 'used') {
  if (inviteStatus.value === next) return
  inviteStatus.value = next
}

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function prevPage() { goToPage(currentPage.value - 1); }
function nextPage() { goToPage(currentPage.value + 1); }

async function generate() {
  try {
    await api.post('/api/admin/invites/generate', { count: count.value })
    flash('生成成功', true)
    currentPage.value = 1
    await load({ force: true })
  } catch (e) {
    flash(e instanceof Error ? e.message : '生成失败', false)
  }
}

async function onLogout() {
  await store.logout()
  await router.push('/admin/login')
}

watch([inviteStatus, pageSize], async () => {
  currentPage.value = 1
  await load()
})

watch(currentPage, async () => {
  await load()
})

onMounted(() => {
  void load()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.container {
  width: 100vw; height: 100vh; background: white;
  overflow: hidden; display: flex; font-family: 'Inter', sans-serif; color: #333;
}

/* Sidebar Copy */
.sidebar {
  width: 260px; background: white; padding: 30px 0 0 0; border-right: 1px solid #f0f0f0;
  display: flex; flex-direction: column; height: 100vh; flex-shrink: 0;
}
.logo { display: flex; align-items: center; gap: 12px; font-weight: 800; font-size: 19px; margin-bottom: 35px; padding: 0 24px; color: #000; letter-spacing: -0.5px; }
.logo-icon { width: 34px; height: 34px; background: #000; border-radius: 9px; display: flex; align-items: center; justify-content: center; color: white; font-size: 18px; }
.nav-item { display: flex; align-items: center; gap: 12px; padding: 13px 18px; margin: 0 12px 6px 12px; border-radius: 14px; cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); color: #666; font-weight: 600; text-decoration: none; font-size: 14.5px; }
.nav-item:hover { background: #f8f9fa; color: #000; }
.nav-item.active { background: #000; color: white; }
.user-profile { margin-top: auto; padding: 24px; border-top: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; background: #fdfdfd; }
.user-info { display: flex; align-items: center; gap: 12px; }
.user-avatar { width: 44px; height: 44px; border-radius: 50%; flex-shrink: 0; }
.user-details { display: flex; flex-direction: column; align-items: flex-start; }
.user-details h4 { font-size: 16px; font-weight: 800; margin: 0; padding: 0; color: #000; line-height: 1; }
.user-details p { font-size: 12px; color: #999; font-weight: 500; margin: 4px 0 0 0; padding: 0; line-height: 1; }
.logout-btn { width: 34px; height: 34px; border-radius: 10px; border: 1px solid #e2e2e2; background: transparent; color: #888; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.logout-btn:hover { background: #2d2d2d; color: #fff; border-color: #444; transform: translateX(2px); }

/* Main Content */
.main-content { flex: 1; padding: 40px 50px; overflow-y: auto; height: 100vh; background: #fafafa; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 35px; }
.header-title h1 { font-size: 32px; font-weight: 800; margin-bottom: 6px; color: #000; letter-spacing: -0.8px; }

.tool-bar { display: flex; gap: 8px; background: white; padding: 6px 6px 6px 16px; border-radius: 14px; border: 1px solid #e5e7eb; }
.search-input { border: none; outline: none; width: 100px; font-size: 14px; font-weight: 600; background: transparent; }
.add-btn { padding: 0 18px; height: 38px; background: #000; color: white; border: none; border-radius: 10px; font-weight: 700; cursor: pointer; transition: all 0.2s; font-size: 13.5px; }
.add-btn:hover { transform: translateY(-1px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
.refresh-btn { border: 1px solid #e5e7eb; background: white; border-radius: 10px; width: 38px; height: 38px; cursor: pointer; }

/* Section Header & Tabs */
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 22px; }
.tabs-capsule { display: flex; background: #eee; padding: 4px; border-radius: 12px; gap: 4px; }
.tabs-capsule button { border: none; background: transparent; padding: 8px 20px; border-radius: 9px; cursor: pointer; font-size: 13.5px; font-weight: 700; color: #666; transition: all 0.2s; }
.tabs-capsule button.active { background: white; color: #000; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.all-chip { background: #f0f0f0; color: #666; font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 99px; }

/* Table Style Sync */
.table-container { background: white; border: 1px solid #edeef1; border-radius: 18px; overflow: hidden; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02); }
.data-table { width: 100%; border-collapse: collapse; }
.data-table thead { background: #fbfbfc; }
.data-table th { padding: 16px 22px; text-align: left; font-weight: 700; font-size: 13px; color: #888; border-bottom: 1px solid #f0f0f2; white-space: nowrap; text-transform: uppercase; letter-spacing: 0.5px; }
.data-table tbody tr { transition: all 0.2s; border-bottom: 1px solid #f8f8fb; }
.data-table tbody tr:hover { background: #fcfcfd; }
.data-table td { padding: 18px 22px; font-size: 14px; color: #444; font-weight: 500; }
.data-table td:first-child { font-weight: 700; color: #000; }

.code-text { font-family: 'Courier New', Courier, monospace; background: #f4f4f4; padding: 4px 8px; border-radius: 6px; font-weight: 700; color: #000; }
.status-tag { padding: 4px 12px; background: #e6f9ee; color: #10b981; border-radius: 99px; font-size: 12px; font-weight: 700; }

.table-footer { display: flex; justify-content: space-between; align-items: center; gap: 20px; }
.page-size-selector { display: flex; align-items: center; gap: 12px; font-size: 13.5px; color: #777; font-weight: 600; }
.page-size-selector select { padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 10px; background: white; cursor: pointer; font-size: 13.5px; font-weight: 600; outline: none; }
.pagination-info { font-size: 13.5px; color: #777; font-weight: 600; }
.pagination-info span { font-weight: 800; color: #000; }
.pagination-controls { display: flex; align-items: center; gap: 6px; }
.page-btn { min-width: 36px; height: 36px; border: 1px solid #e5e7eb; background: white; border-radius: 10px; cursor: pointer; font-size: 13px; font-weight: 700; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.page-btn.active { background: #000; color: white; border-color: #000; }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.msg-tip { margin-bottom: 20px; font-size: 14px; font-weight: 700; }
.up { color: #10b981; }
.down { color: #ef4444; }
.empty { text-align: center; color: #999; padding: 40px; }

@media (max-width: 900px) {
  .sidebar { display: none; }
  .header { flex-direction: column; align-items: flex-start; gap: 20px; }
  .tool-bar { width: 100%; }
}
</style>
