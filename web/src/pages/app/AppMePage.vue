<template>
  <AppShell title="个人中心">
    <div class="me-page-layout">
      <!-- Left Column: Main Info & Settings -->
      <div class="me-main-column">
        <!-- 1. Profile Card -->
        <div class="card profile-card">
          <div class="profile-hero">
            <div class="profile-avatar-wrap">
              <button class="avatar-editable" @click="pickAvatarFile">
                <img v-if="avatarPreview" :src="avatarPreview" alt="头像" class="avatar-img" />
                <span v-else class="avatar-fallback">{{ avatarFallback }}</span>
                <div class="avatar-overlay">更换</div>
              </button>
              <input ref="avatarFileInput" type="file" accept="image/*" class="hidden-input" @change="onAvatarFileChange" />
            </div>
            <div class="profile-info">
              <div class="profile-name-row">
                <h2 class="profile-name" v-if="!isEditingName">{{ nickname }}</h2>
                <input v-else v-model.trim="nickname" class="name-input" @blur="stopEditingName" @keyup.enter="stopEditingName" />
                <span class="rank-badge">银牌分析师</span>
                <button class="edit-icon-btn" @click="toggleEditName">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                </button>
              </div>
              <div class="profile-meta">
                <span>ID: {{ userIdShort }}</span>
                <span class="dot-sep">•</span>
                <span>注册于 {{ registerDate }}</span>
              </div>
            </div>
          </div>
          
          <div class="profile-stats-row">
            <div class="p-stat">
              <div class="p-stat-val">{{ store.rows.value.length }}</div>
              <div class="p-stat-lab">持仓资产</div>
            </div>
            <div class="p-stat">
              <div class="p-stat-val">¥{{ totalAssetFormatted }}</div>
              <div class="p-stat-lab">资产总额</div>
            </div>
            <div class="p-stat">
              <div class="p-stat-val">{{ winRate }}%</div>
              <div class="p-stat-lab">当前胜率</div>
            </div>
          </div>
        </div>

        <!-- 2. Preference List -->
        <div class="settings-group">
          <div class="section-label">偏好设置</div>
          <div class="settings-list">
            <div class="setting-item">
              <div class="s-icon">🌓</div>
              <div class="s-label">色彩模式</div>
              <div class="s-value">{{ themeLabel }}</div>
              <button class="s-arrow" @click="toggleTheme">切换</button>
            </div>
            <div class="setting-item">
              <div class="s-icon">🌐</div>
              <div class="s-label">界面语言</div>
              <div class="s-value">简体中文</div>
              <div class="s-arrow"></div>
            </div>
            <div class="setting-item">
              <div class="s-icon">💵</div>
              <div class="s-label">基准币种</div>
              <div class="s-value">CNY / 人民币</div>
              <div class="s-arrow"></div>
            </div>
          </div>
        </div>

        <!-- 3. Account Security & Data -->
        <div class="settings-group">
          <div class="section-label">账号与数据</div>
          <div class="settings-list">
            <div class="setting-item" @click="showPwdModal = true">
              <div class="s-icon">🔐</div>
              <div class="s-label">账户密码</div>
              <div class="s-value">修改密码</div>
              <div class="s-arrow"></div>
            </div>
            <div class="setting-item" @click="exportData">
              <div class="s-icon">📦</div>
              <div class="s-label">数据管家</div>
              <div class="s-value">{{ exporting ? '导出中...' : '导出 Excel' }}</div>
              <div class="s-arrow"></div>
            </div>
            <div class="setting-item logout" @click="logout">
              <div class="s-icon">🚪</div>
              <div class="s-label">安全退出</div>
              <div class="s-value">退出登录</div>
              <div class="s-arrow"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Stats & Misc -->
      <!-- No content for now (Removed accounting and currency cards) -->

      <!-- Password Change Modal (Simplified) -->
      <div v-if="showPwdModal" class="modal-overlay" @click.self="showPwdModal = false">
        <div class="card modal-card">
          <div class="section-label">修改账户密码</div>
          <div class="pwd-fields">
            <input v-model="oldPassword" class="pwd-input" type="password" placeholder="当前密码" />
            <input v-model="newPassword" class="pwd-input" type="password" placeholder="新密码" />
            <input v-model="confirmPassword" class="pwd-input" type="password" placeholder="确认新密码" />
          </div>
          <div class="modal-actions">
            <button class="btn" @click="showPwdModal = false">取消</button>
            <button class="btn btn-primary" @click="changePassword">立即更新</button>
          </div>
          <p v-if="message" class="result-msg" :class="{ ok: ok, error: !ok }">{{ message }}</p>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as XLSX from 'xlsx'
import AppShell from '../../layouts/AppShell.vue'
import { api } from '../../shared/http'
import { useKonaStore } from '../../stores/composables'
import { useAuthStore } from '../../stores/auth'
import { useWebTheme } from '../../shared/webTheme'

type AssetRow = Record<string, unknown>

const router = useRouter()
const store = useKonaStore()
const authStore = useAuthStore()
const { theme, toggleTheme } = useWebTheme()

const user = computed(() => store.state.user as Record<string, unknown> | null)

const avatarFileInput = ref<HTMLInputElement | null>(null)
const nickname = ref(String(user.value?.nickname || ''))
const avatar = ref(String(user.value?.avatar || ''))
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const exporting = ref(false)
const message = ref('')
const ok = ref(true)
const showPwdModal = ref(false)
const isEditingName = ref(false)

const avatarPreview = computed(() => String(avatar.value || '').trim())
const avatarFallback = computed(() => {
  const base = String(nickname.value || user.value?.nickname || user.value?.username || 'U').trim()
  return base ? base[0]!.toUpperCase() : 'U'
})

const userIdShort = computed(() => String(user.value?.id || '----').slice(0, 8).toUpperCase())
const registerDate = computed(() => {
  const dateStr = String(user.value?.created_at || '')
  return dateStr ? dateStr.split(' ')[0] : '2024-01-01'
})

const themeLabel = computed(() => theme.value === 'dark' ? '深色模式' : '浅色模式')

const totalAssetFormatted = computed(() => {
  const total = store.summary.value?.totalValue || 0
  if (total >= 1000000) return (total / 10000).toFixed(1) + '万'
  return total.toLocaleString(undefined, { maximumFractionDigits: 0 })
})

const winRate = computed(() => {
  const rows = store.rows.value
  if (!rows.length) return 0
  const winners = rows.filter(r => (r.totalPnl || 0) > 0)
  return Math.round((winners.length / rows.length) * 100)
})


function toggleEditName() {
  isEditingName.value = !isEditingName.value
}

async function stopEditingName() {
  isEditingName.value = false
  if (nickname.value !== user.value?.nickname) {
    await saveProfile()
  }
}

function pickAvatarFile() {
  avatarFileInput.value?.click()
}

function onAvatarFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    message.value = '仅支持图片文件'
    ok.value = false
    return
  }
  if (file.size > 1024 * 1024) {
    message.value = '图片需小于 1MB'
    ok.value = false
    return
  }

  const reader = new FileReader()
  reader.onload = async () => {
    avatar.value = String(reader.result || '')
    await saveProfile()
  }
  reader.readAsDataURL(file)
}

async function saveProfile() {
  try {
    const payload = await api.post<Record<string, unknown>>('/api/auth/profile', {
      nickname: nickname.value,
      avatar: avatar.value,
    })
    if (authStore.user && typeof authStore.user === 'object') {
       Object.assign(authStore.user, payload)
    }
    nickname.value = String(payload.nickname || nickname.value || '')
    avatar.value = String(payload.avatar || '')
    message.value = '保存成功'
    ok.value = true
  } catch (e) {
    message.value = e instanceof Error ? e.message : '保存失败'
    ok.value = false
  }
}

async function changePassword() {
  if (!oldPassword.value || !newPassword.value) return
  try {
    await api.post('/api/auth/password/change', {
      old_password: oldPassword.value,
      new_password: newPassword.value,
    })
    message.value = '修改成功'
    ok.value = true
    setTimeout(() => { showPwdModal.value = false; message.value = '' }, 1500)
  } catch (e) {
    message.value = '修改失败'
    ok.value = false
  }
}

async function exportData() {
  exporting.value = true
  try {
    const [cashAssets, portfolio] = await Promise.all([
      api.get<AssetRow[]>('/api/cash_assets'),
      api.get<AssetRow[]>('/api/portfolio?type=all'),
    ])

    const wb = XLSX.utils.book_new()
    const build = (cols: any, rows: any) => {
      const header = cols.map((c: any) => c.title)
      return XLSX.utils.json_to_sheet(rows.map((r: any) => {
        const o: any = {}; cols.forEach((c: any) => o[c.title] = r[c.key] ?? ''); return o
      }), { header })
    }

    XLSX.utils.book_append_sheet(wb, build([{ title: '名称', key: 'name' }, { title: '金额', key: 'amount' }, { title: '币种', key: 'curr' }], cashAssets), '现金资产')
    XLSX.utils.book_append_sheet(wb, build([{ title: '代码', key: 'code' }, { title: '名称', key: 'name' }, { title: '持仓', key: 'qty' }, { title: '成本', key: 'price' }], portfolio), '投资资产')

    const wbout = XLSX.write(wb, { type: 'array', bookType: 'xlsx' })
    const blob = new Blob([wbout], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `kaka-export-${Date.now()}.xlsx`
    link.click()
  } catch {
    message.value = '导出失败'
  } finally {
    exporting.value = false
  }
}

async function logout() {
  await store.logout()
  await router.push('/app/login')
}
</script>

<style scoped>
.me-page-layout {
  display: block; /* Changed to block as the right column is removed */
}

.me-main-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Profile Card */
.profile-card {
  padding: 24px;
}

.profile-hero {
  display: flex;
  gap: 20px;
  align-items: center;
  margin-bottom: 24px;
}

.profile-avatar-wrap {
  position: relative;
  width: 80px;
  height: 80px;
  flex-shrink: 0;
}

.avatar-editable {
  width: 100%;
  height: 100%;
  border-radius: 20px;
  overflow: hidden;
  border: 2px solid var(--border);
  background: var(--s3);
  padding: 0;
  cursor: pointer;
}

.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-fallback { 
  display: grid; place-items: center; width: 100%; height: 100%;
  font-size: 32px; font-weight: 800; color: var(--sub);
}

.avatar-overlay {
  position: absolute; inset: 0; background: rgba(0,0,0,0.4);
  color: white; font-size: 11px; font-weight: 700;
  display: grid; place-items: center; opacity: 0;
  transition: opacity .2s;
}
.avatar-editable:hover .avatar-overlay { opacity: 1; }

.profile-info { flex: 1; }
.profile-name-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.profile-name { font-size: 20px; font-weight: 800; }
.name-input { 
  font-size: 20px; font-weight: 800; background: var(--s3);
  border: 1px solid var(--blue); color: var(--text); padding: 2px 8px; border-radius: 6px;
  width: 160px;
}

.rank-badge {
  font-size: 10px; font-weight: 700; color: var(--gold);
  background: rgba(212, 175, 100, 0.12); padding: 2px 8px; border-radius: 6px;
}

.edit-icon-btn { color: var(--muted); cursor: pointer; padding: 4px; border-radius: 4px; }
.edit-icon-btn:hover { background: rgba(255,255,255,0.05); color: var(--sub); }

.profile-meta { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--muted); }
.dot-sep { opacity: .3; }

.profile-stats-row {
  display: grid; grid-template-columns: repeat(3, 1fr);
  background: rgba(255,255,255,0.02); border-radius: 12px; padding: 16px;
}
.p-stat { text-align: center; }
.p-stat:not(:last-child) { border-right: 1px solid var(--border); }
.p-stat-val { font-family: var(--font-family-mono); font-size: 16px; font-weight: 700; margin-bottom: 4px; }
.p-stat-lab { font-size: 10px; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: .05em; }

/* Settings Lists */
.settings-group { margin-top: 8px; }
.settings-list { display: flex; flex-direction: column; gap: 2px; }

.setting-item {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; background: rgba(255,255,255,0.025);
  border: 1px solid var(--border); border-radius: 12px;
  cursor: pointer; transition: all .15s;
}
.setting-item:hover { background: rgba(255,255,255,0.05); border-color: var(--border-b); }
.setting-item.logout:hover { border-color: rgba(240,90,85,0.3); }

.s-icon { font-size: 16px; }
.s-label { flex: 1; font-size: 13px; font-weight: 600; color: var(--sub); }
.s-value { font-size: 12px; color: var(--muted); }
.s-arrow {
  width: 14px; height: 14px; border: 1.5px solid var(--muted);
  border-left: 0; border-bottom: 0; transform: rotate(45deg);
  opacity: .4; margin-left: 8px;
}
button.s-arrow {
  background: none; border: 1px solid var(--border); padding: 4px 10px;
  border-radius: 6px; font-size: 10px; font-weight: 700; color: var(--blue);
  transform: none; opacity: 1; width: auto; height: auto;
}


/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.8); backdrop-filter: blur(8px);
  display: grid; place-items: center; z-index: 1000;
}
.modal-card { width: 320px; padding: 24px; box-shadow: var(--shadow-xl); }
.pwd-fields { display: flex; flex-direction: column; gap: 12px; margin-top: 16px; }
.pwd-input {
  background: rgba(255,255,255,0.03); border: 1px solid var(--border);
  padding: 12px; border-radius: 10px; color: var(--text); font-size: 13px;
}
.pwd-input:focus { border-color: var(--blue); }
.modal-actions { display: flex; gap: 10px; margin-top: 20px; }
.modal-actions .btn { flex: 1; }

.hidden-input { display: none; }
.result-msg { font-size: 12px; margin-top: 12px; text-align: center; }
.result-msg.ok { color: var(--green); }
.result-msg.error { color: var(--red); }

.btn {
  padding: 10px 16px; border-radius: 10px; border: 1px solid var(--border);
  background: rgba(255,255,255,0.05); color: var(--text); font-size: 13px; font-weight: 700;
  cursor: pointer; transition: all .16s;
}
.btn:hover { background: rgba(255,255,255,0.08); border-color: var(--border-b); }
.btn-primary { background: var(--blue); border-color: transparent; color: white; }
.btn-primary:hover { opacity: .9; }

@media (max-width: 900px) {
  .me-page-layout { grid-template-columns: 1fr; }
}
</style>
