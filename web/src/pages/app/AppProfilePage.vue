<template>
  <LegacyAppShell>
    <div class="settings-container">
      <section class="legacy-section settings-header">
        <h1 class="page-title">系统设置</h1>
      </section>

      <section class="legacy-section settings-card">
        <h2 class="card-title">👤 账号资料</h2>
        <p class="card-desc">仅可修改昵称和头像。</p>
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
          <button class="btn btn-danger" @click="logout">退出登录</button>
        </div>
        <p v-if="message" class="result-msg" :class="{ ok: ok, error: !ok }">{{ message }}</p>
      </section>

      <section class="legacy-section settings-card">
        <h2 class="card-title">💾 数据管理</h2>
        <p class="card-desc">
          您的数据存储在本地数据库中。建议定期备份，以防数据丢失。恢复数据将覆盖当前记录，请谨慎操作。
        </p>
        <div class="action-group">
          <a href="/api/settings/backup" target="_blank" class="btn btn-primary">⬇️ 下载备份 (.db)</a>
          <button class="btn" @click="pickFile">⬆️ 恢复数据</button>
          <input ref="fileInput" type="file" accept=".db" class="hidden-input" @change="restoreData" />
        </div>
      </section>

      <section class="legacy-section settings-card">
        <h2 class="card-title">🌐 API 接口检测</h2>
        <p class="card-desc">检测当前使用的数据源连通性。如果行情或快讯加载失败，可在此排查。</p>
        <div class="api-list">
          <article class="api-item" v-for="item in apiStatusList" :key="item.key">
            <div class="api-info">
              <span class="api-name">{{ item.name }}</span>
              <span class="api-url">{{ item.url }}</span>
            </div>
            <span class="api-status" :class="statusClass(item.status)">{{ statusText(item.status, item.latency, item.error) }}</span>
          </article>
        </div>
        <div class="action-group top-gap">
          <button class="btn" @click="checkApiStatus">🔄 重新检测</button>
        </div>
      </section>

      <section class="legacy-section settings-card">
        <h2 class="card-title">ℹ️ 关于系统</h2>
        <div class="version-info">
          <div>版本: {{ systemInfo.version || '-' }}</div>
          <div>Git Commit: <span class="commit-hash">{{ systemInfo.commit_hash || '-' }}</span></div>
          <div>最后更新: {{ systemInfo.last_update || '-' }}</div>
        </div>
        <p class="card-desc">如需更新或回退版本，请使用 git 操作代码仓库。</p>
      </section>
    </div>
  </LegacyAppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import LegacyAppShell from '../../layouts/LegacyAppShell.vue'
import { api } from '../../shared/http'
import { useKonaStore } from '../../shared/store'

const router = useRouter()
const store = useKonaStore()
const user = computed(() => store.state.user as Record<string, unknown> | null)

const fileInput = ref<HTMLInputElement | null>(null)
const avatarFileInput = ref<HTMLInputElement | null>(null)
const systemInfo = reactive<Record<string, any>>({})
const apiHealth = reactive<Record<string, any>>({})

const nickname = ref('')
const avatar = ref('')
const message = ref('')
const ok = ref(true)

const avatarPreview = computed(() => {
  const value = String(avatar.value || '').trim()
  if (!value) return ''
  return value
})

const avatarFallback = computed(() => {
  const base = String(nickname.value || user.value?.nickname || user.value?.username || 'U').trim()
  return base ? base[0]!.toUpperCase() : 'U'
})

const apiStatusList = computed(() => [
  {
    key: 'price',
    name: '股价接口 (Sina/Tencent)',
    url: 'hq.sinajs.cn',
    ...normalizeStatus(apiHealth.price),
  },
  {
    key: 'rate',
    name: '汇率接口',
    url: 'hq.sinajs.cn (Forex)',
    ...normalizeStatus(apiHealth.rate),
  },
  {
    key: 'news',
    name: '快讯接口 (Sina)',
    url: 'zhibo.sina.com.cn',
    ...normalizeStatus(apiHealth.news),
  },
])

function normalizeStatus(raw: Record<string, unknown> | undefined) {
  if (!raw) return { status: 'loading', latency: 0, error: '' }
  return {
    status: raw.ok ? 'ok' : 'error',
    latency: Number(raw.latency || 0),
    error: String(raw.error || ''),
  }
}

function statusClass(status: string) {
  if (status === 'ok') return 'ok'
  if (status === 'error') return 'error'
  return ''
}

function statusText(status: string, latency: number, error: string) {
  if (status === 'ok') return `正常 (${latency}ms)`
  if (status === 'error') return `异常: ${error || 'Timeout'}`
  return '检测中...'
}

function pickFile() {
  fileInput.value?.click()
}

async function restoreData(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return
  const file = input.files[0]
  if (!file) return
  const confirmed = confirm(`确定从 "${file.name}" 恢复数据吗？当前数据会被覆盖。`)
  if (!confirmed) {
    input.value = ''
    return
  }
  const formData = new FormData()
  formData.append('file', file)
  try {
    const resp = await fetch('/api/settings/restore', { method: 'POST', body: formData })
    const payload = await resp.json()
    if (!resp.ok) throw new Error(String(payload.error || '恢复失败'))
    alert('数据恢复成功，页面将刷新。')
    window.location.reload()
  } catch (e) {
    alert(e instanceof Error ? e.message : '恢复失败')
  } finally {
    input.value = ''
  }
}

async function checkApiStatus() {
  Object.assign(apiHealth, await api.get('/api/settings/check_api'))
}

async function loadSystemInfo() {
  Object.assign(systemInfo, await api.get('/api/settings/info'))
}

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

async function logout() {
  await store.logout()
  await router.push('/app/login')
}

onMounted(async () => {
  nickname.value = String(user.value?.nickname || '')
  avatar.value = String(user.value?.avatar || '')
  await Promise.all([loadSystemInfo(), checkApiStatus()])
})
</script>

<style scoped>
.settings-container {
  max-width: 900px;
}

.settings-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 30px;
  margin: 0;
}

.settings-card {
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
  border-color: rgba(239, 68, 68, 0.4);
  color: #ff9ea0;
}

.hidden-input {
  display: none;
}

.api-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.api-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--legacy-bg-tertiary);
  border-radius: 10px;
  border: 1px solid var(--legacy-border);
}

.api-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.api-name {
  font-weight: 600;
}

.api-url {
  font-size: 12px;
  color: var(--legacy-text-secondary);
}

.api-status {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  background: #334155;
  color: #94a3b8;
}

.api-status.ok {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.api-status.error {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.version-info {
  background: rgba(0, 0, 0, 0.18);
  padding: 14px;
  border-radius: 10px;
  font-family: monospace;
  margin-bottom: 10px;
}

.commit-hash {
  color: #8ab4ff;
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
  color: #dbeafe;
  text-align: center;
  background: rgba(15, 23, 42, 0.75);
}

.profile-fields {
  min-width: 260px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.avatar-meta {
  font-size: 12px;
  color: var(--legacy-text-secondary);
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
  background: rgba(0, 0, 0, 0.2);
  color: #fff;
}

.result-msg {
  margin: 10px 0 0;
}

.result-msg.ok {
  color: #10b981;
}

.result-msg.error {
  color: #ef4444;
}

@media (max-width: 900px) {
  .profile-top {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
