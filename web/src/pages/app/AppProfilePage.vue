<template>
  <LegacyAppShell>
    <div class="settings-container">
      <section class="legacy-section settings-header">
        <h1 class="page-title">系统设置</h1>
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

      <section class="legacy-section settings-card">
        <h2 class="card-title">👤 账号资料</h2>
        <p class="card-desc">修改昵称、手机号与头像信息。</p>
        <div class="profile-grid">
          <label>
            昵称
            <input v-model.trim="nickname" class="field" />
          </label>
          <label>
            手机
            <input v-model.trim="phone" class="field" />
          </label>
        </div>
        <label class="avatar-field">
          头像(base64 可选)
          <textarea v-model="avatar" class="field" rows="3" />
        </label>
        <div class="action-group top-gap">
          <button class="btn btn-primary" @click="saveProfile">保存资料</button>
          <button class="btn btn-danger" @click="logout">退出登录</button>
        </div>
        <p v-if="message" class="result-msg" :class="{ ok: ok, error: !ok }">{{ message }}</p>
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
const systemInfo = reactive<Record<string, any>>({})
const apiHealth = reactive<Record<string, any>>({})

const nickname = ref('')
const phone = ref('')
const avatar = ref('')
const message = ref('')
const ok = ref(true)

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

async function saveProfile() {
  try {
    const payload = await api.post<{ user?: Record<string, unknown> }>('/api/auth/profile', {
      nickname: nickname.value,
      phone: phone.value,
      avatar: avatar.value,
    })
    if (payload.user) {
      store.state.user = payload.user as any
    }
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
  phone.value = String(user.value?.phone || '')
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

.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

label {
  display: grid;
  gap: 6px;
  color: var(--legacy-text-secondary);
  font-size: 13px;
}

.avatar-field {
  margin-top: 10px;
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
  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
