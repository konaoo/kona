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

        <div class="mobile-invite-list">
          <div v-for="item in invites.items || []" :key="`mobile-${item.code}`" class="mobile-invite-card">
            <div class="mobile-invite-head">
              <div class="mobile-invite-code">
                <span class="mobile-invite-label">邀请码</span>
                <code
                  class="code-text clickable"
                  @click="copyToClipboard(item.code)"
                  title="点击复制"
                >{{ item.code }}</code>
              </div>
              <span
                v-if="inviteStatus === 'active'"
                class="status-tag"
              >{{ statusLabel(item.status) }}</span>
              <span v-else class="mobile-used-tag">已使用</span>
            </div>

            <div v-if="copiedCode === item.code" class="mobile-copy-hint">复制成功</div>

            <div v-if="inviteStatus === 'active'" class="mobile-invite-grid">
              <div class="mobile-metric">
                <span class="metric-label">创建时间</span>
                <strong>{{ formatDateOnly(item.created_at) }}</strong>
              </div>
            </div>

            <div v-else class="mobile-invite-grid">
              <div class="mobile-metric">
                <span class="metric-label">用户名</span>
                <strong>{{ item.used_by_username || '-' }}</strong>
              </div>
              <div class="mobile-metric">
                <span class="metric-label">使用时间</span>
                <strong>{{ shortDateTime(item.used_at) }}</strong>
              </div>
            </div>
          </div>

          <div v-if="!(invites.items || []).length" class="mobile-empty">
            {{ inviteStatus === 'active' ? '暂无邀请码' : '暂无已使用邀请码' }}
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
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '../../shared/http'
import AdminConsoleNav from '../../components/admin/AdminConsoleNav.vue'
import { shortDateTime } from '../../shared/format'
import { storeToRefs } from 'pinia'
import { useAdminStore } from '../../stores/admin'

const adminStore = useAdminStore()
const { invites: invitesState } = storeToRefs(adminStore)

const inviteStatus = computed({
  get: () => invitesState.value.inviteStatus,
  set: (val) => { invitesState.value.inviteStatus = val }
})
const pageSize = computed({
  get: () => invitesState.value.pageSize,
  set: (val) => { invitesState.value.pageSize = val }
})
const currentPage = computed({
  get: () => invitesState.value.currentPage,
  set: (val) => { invitesState.value.currentPage = val }
})

const invites = computed(() => invitesState.value)
const count = ref(10)
const message = ref('')
const ok = ref(true)
const copiedCode = ref('')
const pageSizeOptions = [10, 20, 50, 100]

const totalRows = computed(() => Number(invites.value.total || 0))
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
  try {
    await adminStore.loadInvites(options.force)
  } catch (e) {
    console.error('Failed to load invites', e)
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
.mobile-invite-list { display: none; }
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
.code-wrapper { display: flex; align-items: center; gap: 10px; position: relative; }
.copy-hint { 
  position: absolute; 
  left: 100%; 
  top: 50%; 
  transform: translateY(-50%); 
  margin-left: 10px; 
  white-space: nowrap; 
  font-size: 12px; 
  color: #10b981; 
  font-weight: 700; 
  animation: fadeIn 0.2s ease-out; 
}
@keyframes fadeIn { 
  from { opacity: 0; transform: translateY(-50%) translateX(-5px); } 
  to { opacity: 1; transform: translateY(-50%) translateX(0); } 
}
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
  .header-actions { width: 100%; }
  .tool-bar { width: 100%; }
  .tool-bar .add-btn { flex: 1; }
  .section-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .section-header .all-chip {
    align-self: flex-start;
  }
  .table-container {
    display: none;
  }
  .mobile-invite-list {
    display: grid;
    gap: 14px;
    margin-bottom: 20px;
  }
  .mobile-invite-card {
    position: relative;
    background: linear-gradient(180deg, #ffffff 0%, #fbfbfd 100%);
    border: 1px solid #edeef1;
    border-radius: 22px;
    padding: 18px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
  }
  .mobile-invite-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
  }
  .mobile-invite-code {
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-width: 0;
  }
  .mobile-invite-label {
    font-size: 11px;
    font-weight: 800;
    color: #8a90a1;
    letter-spacing: 0.02em;
  }
  .mobile-invite-code .code-text {
    display: inline-flex;
    width: fit-content;
    max-width: 100%;
    font-size: 16px;
    padding: 8px 10px;
  }
  .mobile-copy-hint {
    position: absolute;
    right: 18px;
    top: 50%;
    transform: translateY(-50%);
    color: #10b981;
    font-size: 11px;
    font-weight: 800;
    background: #e6f9ee;
    padding: 4px 10px;
    border-radius: 8px;
    animation: fadeInMobile 0.2s ease-out;
  }
  @keyframes fadeInMobile {
    from { opacity: 0; transform: translateY(-50%) scale(0.9); }
    to { opacity: 1; transform: translateY(-50%) scale(1); }
  }
  .mobile-used-tag {
    flex-shrink: 0;
    border-radius: 999px;
    padding: 6px 12px;
    background: #eef2ff;
    color: #4f46e5;
    font-size: 12px;
    font-weight: 800;
    line-height: 1;
  }
  .mobile-invite-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin-top: 14px;
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
  }
  .mobile-metric strong {
    display: block;
    font-size: 14px;
    font-weight: 800;
    color: #16181d;
    line-height: 1.25;
    word-break: break-word;
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
