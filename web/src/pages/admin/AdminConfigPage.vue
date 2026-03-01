<template>
  <LegacyAdminShell title="运营配置" subtitle="邀请码获取页（App内）">
    <section class="panel panel-body">
      <div class="head">
        <h3>页面内容</h3>
        <button class="btn" :disabled="loading || saving" @click="load">刷新</button>
      </div>

      <label class="field">
        <span class="label">文案</span>
        <textarea
          v-model.trim="form.text"
          class="input textarea"
          maxlength="200"
          placeholder="例如：小红书被限制了，进微信群领邀请码。"
        />
      </label>

      <label class="field">
        <span class="label">图片 URL</span>
        <input
          v-model.trim="form.image_url"
          class="input"
          type="url"
          maxlength="2048"
          placeholder="https://example.com/invite-qrcode.png"
        />
      </label>

      <div class="actions">
        <button class="btn primary" :disabled="loading || saving" @click="save">
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>

      <p v-if="message" :class="ok ? 'up' : 'down'">{{ message }}</p>
    </section>

    <section class="panel panel-body">
      <h3>预览</h3>
      <p class="preview-text">{{ previewText }}</p>
      <div class="preview-image-wrap">
        <img
          v-if="showPreviewImage"
          :src="normalizedImageUrl"
          alt="邀请码页面图片预览"
          class="preview-image"
          @error="imageLoadFailed = true"
          @load="imageLoadFailed = false"
        />
        <div v-else class="preview-empty">
          <span v-if="normalizedImageUrl && imageLoadFailed">图片加载失败，请检查 URL</span>
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

type InviteAcquireConfigPayload = {
  text?: string
  image_url?: string
}

const DEFAULT_TEXT = '小红书被限制了，进微信群领邀请码。'

const loading = ref(false)
const saving = ref(false)
const message = ref('')
const ok = ref(true)
const imageLoadFailed = ref(false)
const form = reactive<Required<InviteAcquireConfigPayload>>({
  text: '',
  image_url: '',
})

const normalizedImageUrl = computed(() => String(form.image_url || '').trim())
const previewText = computed(() => String(form.text || '').trim() || DEFAULT_TEXT)
const showPreviewImage = computed(() => Boolean(normalizedImageUrl.value) && !imageLoadFailed.value)

function flash(msg: string, success: boolean) {
  message.value = msg
  ok.value = success
}

async function load() {
  loading.value = true
  message.value = ''
  imageLoadFailed.value = false
  try {
    const payload = await api.get<InviteAcquireConfigPayload>('/api/admin/ops/invite_acquire')
    form.text = String(payload?.text || '')
    form.image_url = String(payload?.image_url || '')
  } catch (e) {
    flash(e instanceof Error ? e.message : '读取配置失败', false)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  message.value = ''
  try {
    const payload = await api.post<InviteAcquireConfigPayload>('/api/admin/ops/invite_acquire/update', {
      text: form.text,
      image_url: form.image_url,
    })
    form.text = String(payload?.text || '')
    form.image_url = String(payload?.image_url || '')
    imageLoadFailed.value = false
    flash('运营配置已保存', true)
  } catch (e) {
    flash(e instanceof Error ? e.message : '保存失败', false)
  } finally {
    saving.value = false
  }
}

onMounted(load)
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
