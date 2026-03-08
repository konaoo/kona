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
                <h2 class="profile-name">{{ user?.nickname || user?.username || '用户' }}</h2>
              </div>
              <div class="profile-subtitle">已在咔咔记录 {{ daysActive }} 天</div>
            </div>
            <button class="edit-icon-btn profile-edit-btn" @click="startEditingName">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
            </button>
          </div>
          
        </div>

        <!-- 2. Preference List -->
        <div class="settings-group">
          <div class="section-label">偏好设置</div>
          <div class="settings-list">
            <div class="setting-item" @click="toggleTheme">
              <div class="s-icon">🌓</div>
              <div class="s-label">色彩模式</div>
              <div class="s-value">{{ themeLabel }}</div>
              <button class="s-arrow">切换</button>
            </div>
            <div class="setting-item" @click="handleCurrencyClick">
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
          <p v-if="message && showPwdModal" class="result-msg" :class="{ ok: ok, error: !ok }">{{ message }}</p>
        </div>
      </div>

      <!-- Nickname Edit Modal -->
      <div v-if="showNameModal" class="modal-overlay" @click.self="showNameModal = false">
        <div class="card modal-card">
          <div class="section-label">修改个人昵称</div>
          <div class="pwd-fields">
            <input v-model.trim="tempNickname" class="pwd-input" placeholder="输入新昵称" @keyup.enter="confirmNameEdit" />
          </div>
          <div class="modal-actions">
            <button class="btn" @click="showNameModal = false">取消</button>
            <button class="btn btn-primary" @click="confirmNameEdit">应用修改</button>
          </div>
          <p v-if="message && showNameModal" class="result-msg" :class="{ ok: ok, error: !ok }">{{ message }}</p>
        </div>
      </div>
      <p v-if="message && !showPwdModal && !showNameModal" class="page-toast ok">{{ message }}</p>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as XLSX from 'xlsx'
import AppShell from '../../layouts/AppShell.vue'
import { api } from '../../shared/http'
import { toAvatarSrc } from '../../shared/avatar'
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
const nickname = ref('')
const avatar = ref('')

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const exporting = ref(false)
const message = ref('')
const ok = ref(true)
const showPwdModal = ref(false)
const showNameModal = ref(false)
const tempNickname = ref('')


const avatarPreview = computed(() => toAvatarSrc(avatar.value || user.value?.avatar || ''))
const avatarFallback = computed(() => {
  const base = String(nickname.value || user.value?.nickname || user.value?.username || 'U').trim()
  return base ? base[0]!.toUpperCase() : 'U'
})


const themeLabel = computed(() => theme.value === 'dark' ? '深色模式' : '浅色模式')

const daysActive = computed(() => {
  const createdAt = user.value?.created_at as string | undefined
  if (!createdAt) return 1
  try {
    const createdDate = new Date(createdAt.replace(' ', 'T')) // 兼容一些日期格式
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - createdDate.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return Math.max(1, diffDays)
  } catch (e) {
    return 1
  }
})



function startEditingName() {
  tempNickname.value = String(user.value?.nickname || user.value?.username || '')
  showNameModal.value = true
}

async function confirmNameEdit() {
  if (!tempNickname.value) return
  nickname.value = tempNickname.value
  await saveProfile()
  if (ok.value) {
    showNameModal.value = false
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
      nickname: showNameModal.value ? tempNickname.value : (user.value?.nickname || user.value?.username || ''),
      avatar: avatar.value || (user.value?.avatar as string) || '',
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

function handleCurrencyClick() {
  message.value = '币种切换功能正在开发中'
  ok.value = true
  setTimeout(() => {
    if (message.value === '币种切换功能正在开发中') {
      message.value = ''
    }
  }, 2000)
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
  display: block;
  max-width: 800px;
  margin: 0 auto;
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
  margin-bottom: 0px;
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
  position: absolute; inset: 0; background: var(--overlay-soft);
  color: white; font-size: 11px; font-weight: 700;
  display: grid; place-items: center; opacity: 0;
  transition: opacity .2s;
}
.avatar-editable:hover .avatar-overlay { opacity: 1; }

.profile-info { flex: 1; }
.profile-name-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.profile-name { font-size: 20px; font-weight: 800; }
.profile-subtitle { font-size: 13px; color: var(--muted); font-weight: 600; margin-top: 2px; }

.profile-edit-btn {
  margin-left: auto;
  opacity: 0.6;
  transition: opacity 0.2s;
}
.profile-edit-btn:hover { opacity: 1; }


.edit-icon-btn { color: var(--muted); cursor: pointer; padding: 4px; border-radius: 4px; }
.edit-icon-btn:hover { background: var(--surface-soft); color: var(--sub); }



/* Settings Lists */
.settings-group { margin-top: 8px; }
.settings-list { display: flex; flex-direction: column; gap: 12px; }

.setting-item {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; background: var(--surface-faint);
  border: 1px solid var(--border); border-radius: 12px;
  cursor: pointer; transition: all .15s;
}
.setting-item:hover { background: var(--surface-soft); border-color: var(--border-b); }
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
  position: fixed; inset: 0; background: var(--overlay-strong); backdrop-filter: blur(8px);
  display: grid; place-items: center; z-index: 1000;
}
.modal-card { width: 320px; padding: 24px; box-shadow: var(--shadow-xl); }
.pwd-fields { display: flex; flex-direction: column; gap: 12px; margin-top: 16px; }
.pwd-input {
  background: var(--panel-muted); border: 1px solid var(--border);
  padding: 12px; border-radius: 10px; color: var(--text); font-size: 13px;
}
.pwd-input:focus { border-color: var(--blue); box-shadow: 0 0 0 3px color-mix(in srgb, var(--blue) 14%, transparent); outline: none; }
.modal-actions { display: flex; gap: 10px; margin-top: 20px; }
.modal-actions .btn { flex: 1; }

.hidden-input { display: none; }
.result-msg { font-size: 12px; margin-top: 12px; text-align: center; }
.result-msg.ok { color: var(--green); }
.result-msg.error { color: var(--red); }

.page-toast { 
  position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%);
  background: var(--blue); color: white; padding: 12px 24px; border-radius: 12px;
  font-size: 14px; font-weight: 700; box-shadow: var(--shadow-xl);
  z-index: 1001; pointer-events: none;
}

.btn {
  padding: 10px 16px; border-radius: 10px; border: 1px solid var(--border);
  background: var(--surface-soft); color: var(--text); font-size: 13px; font-weight: 700;
  cursor: pointer; transition: all .16s;
}
.btn:hover { background: var(--surface-soft-hover); border-color: var(--border-b); }
.btn-primary { background: var(--blue); border-color: transparent; color: white; }
.btn-primary:hover { opacity: .9; }

@media (max-width: 900px) {
  .me-page-layout { grid-template-columns: 1fr; }
}
</style>
