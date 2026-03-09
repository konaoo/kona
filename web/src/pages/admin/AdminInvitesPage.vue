<template>
  <div class="container admin-invites">
    <AdminConsoleNav />

    <!-- Main Content -->
    <div class="main-content">
      <div class="header">
        <div class="header-title">
          <h1>邀请码管理</h1>
        </div>
        <div class="header-actions">
          <div class="tool-bar">
            <button class="add-btn" @click="generate">生成邀请码</button>
            <button class="add-btn secondary" @click="load({ force: true })">刷新</button>
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
                <th>邀请码</th>
                <th>创建时间</th>
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
                <td>
                  <div class="code-wrapper">
                    <code 
                      class="code-text clickable" 
                      @click="copyToClipboard(item.code)"
                      title="点击复制"
                    >{{ item.code }}</code>
                    <span v-if="copiedCode === item.code" class="copy-hint">复制成功</span>
                  </div>
                </td>
                <td>{{ formatDateOnly(item.created_at) }}</td>
                <td><span class="status-tag">{{ statusLabel(item.status) }}</span></td>
              </tr>
              <tr v-if="!(invites.items || []).length">
                <td colspan="3" class="empty">暂无邀请码</td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr v-for="item in invites.items || []" :key="item.code">
                <td>
                  <div class="code-wrapper">
                    <code 
                      class="code-text clickable" 
                      @click="copyToClipboard(item.code)"
                      title="点击复制"
                    >{{ item.code }}</code>
                    <span v-if="copiedCode === item.code" class="copy-hint">复制成功</span>
                  </div>
                </td>
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
import { api } from '../../shared/http'
import AdminConsoleNav from '../../components/admin/AdminConsoleNav.vue'
import { shortDateTime } from '../../shared/format'

const invites = reactive<Record<string, any>>({ items: [], total: 0 })
const count = ref(10)
const message = ref('')
const ok = ref(true)
const copiedCode = ref('')
const inviteStatus = ref<'active' | 'used'>('active')
const pageSize = ref(10)
const pageSizeOptions = [10, 20, 50, 100]
const currentPage = ref(1)
let lastRequestKey = ''
let inflightKey = ''

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
  // 增加 random 和 refresh_id 标识以支持缓存隔离
  const refreshId = Math.random().toString(36).substring(7)
  const key = `${status}|${limit}|${offset}|random|${refreshId}|${force ? '1' : '0'}`
  if (!force && (key === lastRequestKey || key === inflightKey)) return
  inflightKey = key
  try {
    const params = new URLSearchParams({
      status,
      limit: String(limit),
      offset: String(offset),
      random: '1',
      refresh_id: refreshId,
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

function fallbackCopyText(text: string): boolean {
  const value = String(text || '').trim()
  if (!value) return false

  const textarea = document.createElement('textarea')
  textarea.value = value
  textarea.setAttribute('readonly', 'true')
  textarea.style.position = 'fixed'
  textarea.style.top = '-9999px'
  textarea.style.left = '-9999px'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.focus()
  textarea.select()
  textarea.setSelectionRange(0, textarea.value.length)

  try {
    return document.execCommand('copy')
  } catch {
    return false
  } finally {
    document.body.removeChild(textarea)
  }
}

async function copyToClipboard(text: string) {
  const value = String(text || '').trim()
  if (!value) {
    flash('复制失败', false)
    return
  }

  try {
    let copied = false

    if (navigator.clipboard?.writeText && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(value)
        copied = true
      } catch {
        copied = false
      }
    }

    if (!copied) {
      copied = fallbackCopyText(value)
    }

    if (!copied) throw new Error('copy_failed')

    copiedCode.value = value
    setTimeout(() => {
      if (copiedCode.value === value) copiedCode.value = ''
    }, 2000)
  } catch (e) {
    flash('复制失败', false)
  }
}

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
.user-avatar { width: 44px; height: 44px; border-radius: 50%; flex-shrink: 0; object-fit: cover; }
.user-avatar-fallback { display: flex; align-items: center; justify-content: center; color: #fff; font-size: 18px; font-weight: 800; }
.user-details { display: flex; flex-direction: column; align-items: flex-start; }
.user-details h4 { font-size: 16px; font-weight: 800; margin: 0; padding: 0; color: #000; line-height: 1; }
.user-details p { font-size: 12px; color: #999; font-weight: 500; margin: 4px 0 0 0; padding: 0; line-height: 1; }
.logout-btn { width: 34px; height: 34px; border-radius: 10px; border: 1px solid #e2e2e2; background: transparent; color: #888; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.logout-btn:hover { background: #2d2d2d; color: #fff; border-color: #444; transform: translateX(2px); }

/* Main Content */
.main-content { flex: 1; padding: 40px 50px; overflow-y: auto; height: 100vh; background: #fafafa; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 35px; }
.header-title h1 { font-size: 32px; font-weight: 800; margin-bottom: 6px; color: #000; letter-spacing: -0.8px; }

.tool-bar { display: flex; gap: 8px; background: white; padding: 6px; border-radius: 14px; border: 1px solid #e5e7eb; }
.add-btn { padding: 0 18px; height: 38px; background: #000; color: white; border: none; border-radius: 10px; font-weight: 700; cursor: pointer; transition: all 0.2s; font-size: 13.5px; }
.add-btn:hover { transform: translateY(-1px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
.add-btn.secondary { background: white; color: #000; border: 1px solid #e5e7eb; }
.add-btn.secondary:hover { background: #f8f9fa; }

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

.code-text { font-family: 'Courier New', Courier, monospace; background: #f4f4f4; padding: 4px 8px; border-radius: 6px; font-weight: 700; color: #000; transition: all 0.2s; }
.code-text.clickable { cursor: pointer; }
.code-text.clickable:hover { background: #000; color: #fff; }
.code-wrapper { display: flex; align-items: center; gap: 10px; }
.copy-hint { font-size: 12px; color: #10b981; font-weight: 700; animation: fadeIn 0.2s; }
@keyframes fadeIn { from { opacity: 0; transform: translateX(-5px); } to { opacity: 1; transform: translateX(0); } }
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
  .main-content { padding-bottom: calc(112px + env(safe-area-inset-bottom)); }
  .header { flex-direction: column; align-items: flex-start; gap: 20px; }
  .tool-bar { width: 100%; }
}
</style>
