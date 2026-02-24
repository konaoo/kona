<template>
  <LegacyAppShell>
    <div class="me-container">
      <section class="legacy-section me-card">
        <h2 class="card-title">👤 账号资料</h2>
        <p class="card-desc">可修改昵称与头像。</p>
        <div class="profile-top">
          <button class="avatar-picker" type="button" @click="pickAvatarFile">
            <img v-if="avatarPreview" :src="avatarPreview" alt="头像预览" class="avatar-image" />
            <span v-else class="avatar-fallback">{{ avatarFallback }}</span>
            <span class="avatar-mask">点击上传</span>
          </button>
          <input ref="avatarFileInput" type="file" accept="image/*" class="hidden-input" @change="onAvatarFileChange" />

          <div class="profile-fields">
            <label>
              昵称
              <input v-model.trim="nickname" class="field" />
            </label>
            <div class="avatar-meta">支持 JPG/PNG/WebP，大小不超过 1MB</div>
            <div class="action-group">
              <button class="btn" type="button" @click="pickAvatarFile">上传头像</button>
              <button class="btn" type="button" @click="clearAvatar">清除头像</button>
            </div>
          </div>
        </div>
        <div class="action-group top-gap">
          <button class="btn btn-primary" @click="saveProfile">保存资料</button>
        </div>
      </section>

      <section class="legacy-section me-card">
        <h2 class="card-title">🔐 修改密码</h2>
        <div class="password-grid">
          <label>
            当前密码
            <input v-model="oldPassword" class="field" type="password" autocomplete="current-password" />
          </label>
          <label>
            新密码
            <input v-model="newPassword" class="field" type="password" autocomplete="new-password" />
          </label>
          <label>
            确认新密码
            <input v-model="confirmPassword" class="field" type="password" autocomplete="new-password" />
          </label>
        </div>
        <div class="action-group top-gap">
          <button class="btn btn-primary" @click="changePassword">更新密码</button>
        </div>
      </section>

      <section class="legacy-section me-card">
        <h2 class="card-title">📦 导出数据</h2>
        <p class="card-desc">仅导出：现金资产、投资资产、其他资产、我的负债。</p>
        <div class="action-group">
          <button class="btn btn-primary" :disabled="exporting" @click="exportData">
            {{ exporting ? '导出中...' : '导出 Excel' }}
          </button>
          <button class="btn btn-danger" @click="logout">退出登录</button>
        </div>
      </section>

      <p v-if="message" class="result-msg" :class="{ ok: ok, error: !ok }">{{ message }}</p>
    </div>
  </LegacyAppShell>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as XLSX from 'xlsx'
import LegacyAppShell from '../../layouts/LegacyAppShell.vue'
import { api } from '../../shared/http'
import { useKonaStore } from '../../shared/store'

type AssetRow = Record<string, unknown>

const router = useRouter()
const store = useKonaStore()
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

const avatarPreview = computed(() => String(avatar.value || '').trim())
const avatarFallback = computed(() => {
  const base = String(nickname.value || user.value?.nickname || user.value?.username || 'U').trim()
  return base ? base[0]!.toUpperCase() : 'U'
})

function pickAvatarFile() {
  avatarFileInput.value?.click()
}

function onAvatarFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    message.value = '仅支持图片文件（JPG/PNG/WebP）'
    ok.value = false
    input.value = ''
    return
  }

  if (file.size > 1024 * 1024) {
    message.value = '图片过大，请选择 1MB 以内的文件'
    ok.value = false
    input.value = ''
    return
  }

  const reader = new FileReader()
  reader.onload = () => {
    const dataUrl = String(reader.result || '')
    if (!dataUrl.startsWith('data:image/')) {
      message.value = '图片读取失败，请重试'
      ok.value = false
      return
    }
    avatar.value = dataUrl
    message.value = '头像已更新，点击“保存资料”生效'
    ok.value = true
  }
  reader.onerror = () => {
    message.value = '图片读取失败，请重试'
    ok.value = false
  }
  reader.readAsDataURL(file)
  input.value = ''
}

function clearAvatar() {
  avatar.value = ''
  if (avatarFileInput.value) avatarFileInput.value.value = ''
  message.value = '头像已清除，点击“保存资料”生效'
  ok.value = true
}

async function saveProfile() {
  try {
    const payload = await api.post<Record<string, unknown>>('/api/auth/profile', {
      nickname: nickname.value,
      avatar: avatar.value,
    })
    store.state.user = payload as any
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
  const oldPwd = oldPassword.value.trim()
  const newPwd = newPassword.value.trim()
  const confirmPwd = confirmPassword.value.trim()

  if (!oldPwd || !newPwd || !confirmPwd) {
    message.value = '请完整填写密码字段'
    ok.value = false
    return
  }
  if (newPwd !== confirmPwd) {
    message.value = '两次输入的新密码不一致'
    ok.value = false
    return
  }
  try {
    await api.post('/api/auth/password/change', {
      old_password: oldPwd,
      new_password: newPwd,
    })
    oldPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    message.value = '密码修改成功'
    ok.value = true
  } catch (e) {
    message.value = e instanceof Error ? e.message : '密码修改失败'
    ok.value = false
  }
}

function buildSheet(columns: Array<{ title: string; key: string }>, rows: AssetRow[]) {
  const header = columns.map((c) => c.title)
  if (!rows.length) {
    return XLSX.utils.aoa_to_sheet([header])
  }
  const normalized = rows.map((row) => {
    const out: Record<string, unknown> = {}
    for (const col of columns) {
      out[col.title] = row[col.key] ?? ''
    }
    return out
  })
  return XLSX.utils.json_to_sheet(normalized, { header })
}

function timestampForFile(): string {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`
}

async function exportData() {
  exporting.value = true
  message.value = ''
  try {
    const [cashAssets, portfolio, otherAssets, liabilities] = await Promise.all([
      api.get<AssetRow[]>('/api/cash_assets'),
      api.get<AssetRow[]>('/api/portfolio?type=all'),
      api.get<AssetRow[]>('/api/other_assets'),
      api.get<AssetRow[]>('/api/liabilities'),
    ])

    const wb = XLSX.utils.book_new()

    XLSX.utils.book_append_sheet(
      wb,
      buildSheet(
        [
          { title: 'id', key: 'id' },
          { title: '名称', key: 'name' },
          { title: '金额', key: 'amount' },
          { title: '币种', key: 'curr' },
        ],
        Array.isArray(cashAssets) ? cashAssets : [],
      ),
      '现金资产',
    )

    XLSX.utils.book_append_sheet(
      wb,
      buildSheet(
        [
          { title: '代码', key: 'code' },
          { title: '名称', key: 'name' },
          { title: '数量', key: 'qty' },
          { title: '成本价', key: 'price' },
          { title: '币种', key: 'curr' },
          { title: '资产类型', key: 'asset_type' },
          { title: '调整值', key: 'adjustment' },
        ],
        Array.isArray(portfolio) ? portfolio : [],
      ),
      '投资资产',
    )

    XLSX.utils.book_append_sheet(
      wb,
      buildSheet(
        [
          { title: 'id', key: 'id' },
          { title: '名称', key: 'name' },
          { title: '金额', key: 'amount' },
          { title: '币种', key: 'curr' },
        ],
        Array.isArray(otherAssets) ? otherAssets : [],
      ),
      '其他资产',
    )

    XLSX.utils.book_append_sheet(
      wb,
      buildSheet(
        [
          { title: 'id', key: 'id' },
          { title: '名称', key: 'name' },
          { title: '金额', key: 'amount' },
          { title: '币种', key: 'curr' },
        ],
        Array.isArray(liabilities) ? liabilities : [],
      ),
      '我的负债',
    )

    const wbout = XLSX.write(wb, { type: 'array', bookType: 'xlsx' })
    const blob = new Blob([wbout], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `kaka-user-export-${timestampForFile()}.xlsx`
    link.click()
    URL.revokeObjectURL(url)

    message.value = '导出成功'
    ok.value = true
  } catch (e) {
    message.value = e instanceof Error ? e.message : '导出失败'
    ok.value = false
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
.me-container {
  max-width: 960px;
}

.me-card {
  margin-bottom: 18px;
}

.card-title {
  margin: 0 0 12px;
  font-size: 22px;
}

.card-desc {
  margin: 0 0 14px;
  color: var(--legacy-text-secondary);
  line-height: 1.6;
}

.profile-top {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.avatar-picker {
  position: relative;
  width: 96px;
  height: 96px;
  border-radius: 16px;
  border: 1px solid var(--legacy-border);
  background: var(--legacy-bg-tertiary);
  overflow: hidden;
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-fallback {
  display: grid;
  width: 100%;
  height: 100%;
  place-items: center;
  font-size: 30px;
  font-weight: 700;
  color: var(--legacy-text-primary);
}

.avatar-mask {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 4px 0;
  font-size: 12px;
  color: var(--legacy-text-primary);
  text-align: center;
  background: var(--legacy-surface-strong);
}

.profile-fields {
  min-width: 260px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.password-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

label {
  display: grid;
  gap: 6px;
  color: var(--legacy-text-secondary);
  font-size: 13px;
}

.field {
  border: 1px solid var(--legacy-border);
  border-radius: 10px;
  padding: 10px;
  background: var(--legacy-input-bg);
  color: var(--legacy-input-text);
}

.avatar-meta {
  font-size: 12px;
  color: var(--legacy-text-secondary);
}

.action-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.top-gap {
  margin-top: 14px;
}

.btn {
  border: 1px solid var(--legacy-border);
  background: var(--legacy-bg-tertiary);
  color: var(--legacy-text-primary);
  padding: 10px 16px;
  border-radius: 10px;
  text-decoration: none;
  cursor: pointer;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-color: transparent;
}

.btn-danger {
  border-color: var(--legacy-danger-border);
  color: var(--legacy-danger-text);
}

.hidden-input {
  display: none;
}

.result-msg {
  margin: 10px 0 0;
}

.result-msg.ok {
  color: var(--legacy-status-ok-text);
}

.result-msg.error {
  color: var(--legacy-status-error-text);
}

@media (max-width: 900px) {
  .profile-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .password-grid {
    grid-template-columns: 1fr;
  }
}
</style>
