<template>
  <div v-if="visible" class="editor-mask" @click.self="onClose">
    <section class="panel editor-panel">
      <div class="editor-head">
        <h3>{{ title }}</h3>
        <button class="btn ghost" :disabled="saving" @click="onClose">关闭</button>
      </div>

      <label class="field">
        <span class="label">文案</span>
        <textarea
          :value="draft.text"
          class="input textarea"
          maxlength="500"
          placeholder="请输入更新说明"
          @input="onTextInput"
        />
      </label>

      <label class="field">
        <span class="label">下载链接</span>
        <input
          :value="draft.download_url"
          class="input"
          type="url"
          maxlength="2048"
          placeholder="https://example.com/kaka-latest.apk"
          @input="onDownloadUrlInput"
        />
      </label>

      <section class="preview-block">
        <h4>预览</h4>
        <p class="preview-text">{{ previewText }}</p>
        <p class="preview-url">{{ previewUrl }}</p>
      </section>

      <p v-if="message" :class="ok ? 'up' : 'down'" class="editor-message">
        {{ message }}
      </p>

      <div class="actions">
        <button class="btn primary" :disabled="saving" @click="onSave">
          {{ saving ? '保存中...' : '保存' }}
        </button>
        <button class="btn secondary" :disabled="saving" @click="onClose">取消</button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type Draft = {
  text: string
  download_url: string
}

const props = defineProps<{
  visible: boolean
  title: string
  draft: Draft
  defaultText: string
  defaultDownloadUrl: string
  saving: boolean
  message: string
  ok: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save'): void
  (e: 'update:text', value: string): void
  (e: 'update:download-url', value: string): void
}>()

const previewText = computed(() => {
  const text = String(props.draft.text || '').trim()
  return text || props.defaultText
})

const previewUrl = computed(() => {
  const url = String(props.draft.download_url || '').trim()
  if (url) return url
  const fallback = String(props.defaultDownloadUrl || '').trim()
  if (fallback) return fallback
  return '未配置下载链接'
})

function onTextInput(event: Event) {
  const target = event.target as HTMLTextAreaElement | null
  emit('update:text', String(target?.value || ''))
}

function onDownloadUrlInput(event: Event) {
  const target = event.target as HTMLInputElement | null
  emit('update:download-url', String(target?.value || ''))
}

function onClose() {
  emit('close')
}

function onSave() {
  emit('save')
}
</script>

<style scoped>
.editor-mask {
  position: fixed;
  inset: 0;
  z-index: 90;
  padding: 16px;
  display: grid;
  place-items: center;
  background: rgba(7, 18, 33, 0.58);
}

.editor-panel {
  width: min(760px, 100%);
  max-height: min(88vh, 820px);
  overflow: auto;
  padding: 18px;
}

.editor-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.editor-head h3 {
  margin: 0;
  color: #1f3f58;
  font-size: 20px;
  font-weight: 800;
}

.field {
  display: grid;
  gap: 6px;
  margin-top: 10px;
}

.label {
  color: #55708f;
  font-size: 12px;
  font-weight: 700;
}

.textarea {
  min-height: 140px;
  resize: vertical;
}

.preview-block {
  margin-top: 14px;
  padding: 12px;
  border: 1px solid #d6e1ee;
  border-radius: 10px;
  background: #f8fbff;
}

.preview-block h4 {
  margin: 0;
  color: #1f3f58;
  font-size: 15px;
  font-weight: 700;
}

.preview-text {
  margin: 10px 0 10px;
  color: #10243e;
  line-height: 1.6;
  white-space: pre-wrap;
}

.preview-url {
  margin: 0;
  color: #35557d;
  line-height: 1.5;
  word-break: break-all;
}

.editor-message {
  margin-top: 10px;
  font-weight: 600;
}

.actions {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn.secondary {
  background: #e8eff7;
  color: #1f3f58;
  border: 1px solid #c8d6e7;
}

.btn.ghost {
  background: transparent;
  color: #35557d;
  border: 1px solid #c8d6e7;
  box-shadow: none;
}

.up {
  color: var(--success);
}

.down {
  color: var(--danger);
}

@media (max-width: 760px) {
  .actions {
    flex-direction: column-reverse;
  }

  .actions .btn {
    width: 100%;
  }
}
</style>
