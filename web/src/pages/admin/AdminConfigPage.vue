<template>
  <LegacyAdminShell title="运营配置" subtitle="邀请码页与用户群页（App内）">
    <section class="panel panel-body">
      <div class="head">
        <h3>邀请码页面配置</h3>
        <button class="btn" :disabled="loadingInvite || savingInvite" @click="loadInvite">刷新</button>
      </div>

      <label class="field">
        <span class="label">文案</span>
        <textarea
          v-model.trim="inviteForm.text"
          class="input textarea"
          maxlength="200"
          placeholder="例如：小红书被限制了，进微信群领邀请码。"
        />
      </label>

      <label class="field">
        <span class="label">图片 URL</span>
        <input
          v-model.trim="inviteForm.image_url"
          class="input"
          type="url"
          maxlength="2048"
          placeholder="https://example.com/invite-qrcode.png"
        />
      </label>

      <div class="actions">
        <button class="btn primary" :disabled="loadingInvite || savingInvite" @click="saveInvite">
          {{ savingInvite ? '保存中...' : '保存邀请码配置' }}
        </button>
      </div>

      <p v-if="inviteMessage" :class="inviteOk ? 'up' : 'down'">{{ inviteMessage }}</p>
    </section>

    <section class="panel panel-body">
      <h3>邀请码页面预览</h3>
      <p class="preview-text">{{ invitePreviewText }}</p>
      <div class="preview-image-wrap">
        <img
          v-if="showInvitePreviewImage"
          :src="inviteImageUrl"
          alt="邀请码页面图片预览"
          class="preview-image"
          @error="inviteImageLoadFailed = true"
          @load="inviteImageLoadFailed = false"
        />
        <div v-else class="preview-empty">
          <span v-if="inviteImageUrl && inviteImageLoadFailed">图片加载失败，请检查 URL</span>
          <span v-else>未配置图片 URL（App 将展示内置占位图）</span>
        </div>
      </div>
    </section>

    <section class="panel panel-body">
      <div class="head">
        <h3>用户群页面配置</h3>
        <button class="btn" :disabled="loadingUserGroup || savingUserGroup" @click="loadUserGroup">刷新</button>
      </div>

      <label class="field">
        <span class="label">文案</span>
        <textarea
          v-model.trim="userGroupForm.text"
          class="input textarea"
          maxlength="200"
          placeholder="例如：加入咔咔用户群"
        />
      </label>

      <label class="field">
        <span class="label">图片 URL</span>
        <input
          v-model.trim="userGroupForm.image_url"
          class="input"
          type="url"
          maxlength="2048"
          placeholder="https://example.com/user-group-qrcode.webp"
        />
      </label>

      <div class="actions">
        <button
          class="btn primary"
          :disabled="loadingUserGroup || savingUserGroup"
          @click="saveUserGroup"
        >
          {{ savingUserGroup ? '保存中...' : '保存用户群配置' }}
        </button>
      </div>

      <p v-if="userGroupMessage" :class="userGroupOk ? 'up' : 'down'">{{ userGroupMessage }}</p>
    </section>

    <section class="panel panel-body">
      <h3>用户群页面预览</h3>
      <p class="preview-text">{{ userGroupPreviewText }}</p>
      <div class="preview-image-wrap">
        <img
          v-if="showUserGroupPreviewImage"
          :src="userGroupImageUrl"
          alt="用户群页面图片预览"
          class="preview-image"
          @error="userGroupImageLoadFailed = true"
          @load="userGroupImageLoadFailed = false"
        />
        <div v-else class="preview-empty">
          <span v-if="userGroupImageUrl && userGroupImageLoadFailed">图片加载失败，请检查 URL</span>
          <span v-else>未配置图片 URL（App 将展示内置占位图）</span>
        </div>
      </div>
    </section>
  </LegacyAdminShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
import { api } from '../../shared/http'

type OpsConfigPayload = {
  text?: string
  image_url?: string
}

const DEFAULT_INVITE_TEXT = '小红书被限制了，进微信群领邀请码。'
const DEFAULT_USER_GROUP_TEXT = '加入咔咔用户群'

const loadingInvite = ref(false)
const savingInvite = ref(false)
const inviteMessage = ref('')
const inviteOk = ref(true)
const inviteImageLoadFailed = ref(false)
const inviteForm = reactive<Required<OpsConfigPayload>>({
  text: '',
  image_url: '',
})

const loadingUserGroup = ref(false)
const savingUserGroup = ref(false)
const userGroupMessage = ref('')
const userGroupOk = ref(true)
const userGroupImageLoadFailed = ref(false)
const userGroupForm = reactive<Required<OpsConfigPayload>>({
  text: '',
  image_url: '',
})

const inviteImageUrl = computed(() => String(inviteForm.image_url || '').trim())
const invitePreviewText = computed(() => String(inviteForm.text || '').trim() || DEFAULT_INVITE_TEXT)
const showInvitePreviewImage = computed(
  () => Boolean(inviteImageUrl.value) && !inviteImageLoadFailed.value,
)

const userGroupImageUrl = computed(() => String(userGroupForm.image_url || '').trim())
const userGroupPreviewText = computed(
  () => String(userGroupForm.text || '').trim() || DEFAULT_USER_GROUP_TEXT,
)
const showUserGroupPreviewImage = computed(
  () => Boolean(userGroupImageUrl.value) && !userGroupImageLoadFailed.value,
)

function flashInvite(msg: string, success: boolean) {
  inviteMessage.value = msg
  inviteOk.value = success
}

function flashUserGroup(msg: string, success: boolean) {
  userGroupMessage.value = msg
  userGroupOk.value = success
}

async function loadInvite() {
  loadingInvite.value = true
  inviteMessage.value = ''
  inviteImageLoadFailed.value = false
  try {
    const payload = await api.get<OpsConfigPayload>('/api/admin/ops/invite_acquire')
    inviteForm.text = String(payload?.text || '')
    inviteForm.image_url = String(payload?.image_url || '')
  } catch (e) {
    flashInvite(e instanceof Error ? e.message : '读取邀请码配置失败', false)
  } finally {
    loadingInvite.value = false
  }
}

async function saveInvite() {
  savingInvite.value = true
  inviteMessage.value = ''
  try {
    const payload = await api.post<OpsConfigPayload>('/api/admin/ops/invite_acquire/update', {
      text: inviteForm.text,
      image_url: inviteForm.image_url,
    })
    inviteForm.text = String(payload?.text || '')
    inviteForm.image_url = String(payload?.image_url || '')
    inviteImageLoadFailed.value = false
    flashInvite('邀请码配置已保存', true)
  } catch (e) {
    flashInvite(e instanceof Error ? e.message : '邀请码配置保存失败', false)
  } finally {
    savingInvite.value = false
  }
}

async function loadUserGroup() {
  loadingUserGroup.value = true
  userGroupMessage.value = ''
  userGroupImageLoadFailed.value = false
  try {
    const payload = await api.get<OpsConfigPayload>('/api/admin/ops/user_group')
    userGroupForm.text = String(payload?.text || '')
    userGroupForm.image_url = String(payload?.image_url || '')
  } catch (e) {
    flashUserGroup(e instanceof Error ? e.message : '读取用户群配置失败', false)
  } finally {
    loadingUserGroup.value = false
  }
}

async function saveUserGroup() {
  savingUserGroup.value = true
  userGroupMessage.value = ''
  try {
    const payload = await api.post<OpsConfigPayload>('/api/admin/ops/user_group/update', {
      text: userGroupForm.text,
      image_url: userGroupForm.image_url,
    })
    userGroupForm.text = String(payload?.text || '')
    userGroupForm.image_url = String(payload?.image_url || '')
    userGroupImageLoadFailed.value = false
    flashUserGroup('用户群配置已保存', true)
  } catch (e) {
    flashUserGroup(e instanceof Error ? e.message : '用户群配置保存失败', false)
  } finally {
    savingUserGroup.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadInvite(), loadUserGroup()])
})
</script>

<style scoped>
.panel-body {
  padding: 16px;
  margin-bottom: 16px;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.field {
  display: grid;
  gap: 6px;
  margin-top: 10px;
}

.label {
  color: var(--text-secondary);
  font-size: 12px;
}

.textarea {
  min-height: 96px;
  resize: vertical;
}

.actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.preview-text {
  margin: 10px 0 12px;
  color: var(--text-primary);
  line-height: 1.6;
}

.preview-image-wrap {
  border: 1px dashed var(--line);
  border-radius: 10px;
  min-height: 180px;
  background: var(--bg-soft);
  display: grid;
  place-items: center;
  overflow: hidden;
}

.preview-image {
  max-width: 100%;
  max-height: 360px;
  object-fit: contain;
}

.preview-empty {
  color: var(--text-secondary);
  font-size: 13px;
  padding: 14px;
  text-align: center;
}

.up {
  color: var(--success);
}

.down {
  color: var(--danger);
}
</style>
