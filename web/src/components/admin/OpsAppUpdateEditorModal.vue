<template>
  <div v-if="visible" class="editor-mask" @click.self="onClose">
    <section class="ops-editor-panel">
      <div class="editor-head">
        <div class="head-info">
          <h3>{{ title }}</h3>
        </div>
        <button class="close-btn" :disabled="saving" @click="onClose">✕</button>
      </div>

      <div class="editor-body">
        <label class="field">
          <span class="label">更新说明文案</span>
          <textarea
            :value="draft.text"
            class="ops-editor-input textarea"
            maxlength="500"
            placeholder="请输入更新说明（支持换行）"
            @input="onTextInput"
          />
        </label>

        <label class="field">
          <span class="label">下载链接 (URL)</span>
          <input
            :value="draft.download_url"
            class="ops-editor-input"
            type="url"
            maxlength="2048"
            placeholder="https://example.com/kaka-latest.apk"
            @input="onDownloadUrlInput"
          />
        </label>

        <section class="preview-block">
          <div class="preview-header">
             <h4>最终效果预览</h4>
             <span class="preview-badge">实时</span>
          </div>
          <div class="preview-content">
            <p class="preview-text">{{ previewText }}</p>
            <div class="url-badge">
               <span class="url-icon">🔗</span>
               <span class="preview-url">{{ previewUrl }}</span>
            </div>
          </div>
        </section>

        <p v-if="message" :class="ok ? 'up' : 'down'" class="editor-message">
          {{ message }}
        </p>
      </div>

      <div class="actions">
        <button class="btn btn-secondary" :disabled="saving" @click="onClose">取消</button>
        <button class="btn btn-primary" :disabled="saving" @click="onSave">
          {{ saving ? '正在保存...' : '确认发布更新' }}
        </button>
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
  position: fixed; inset: 0; z-index: 1000; padding: 20px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(4px);
}

.ops-editor-panel {
  width: min(700px, 100%); max-height: 90vh;
  background: white; border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  display: flex; flex-direction: column; overflow: hidden;
}

.editor-head {
  padding: 24px 30px; border-bottom: 1px solid #f0f0f0;
  display: flex; justify-content: space-between; align-items: center;
}
.head-info h3 { font-size: 20px; font-weight: 800; color: #000; margin: 0; }

.close-btn {
  width: 36px; height: 36px; border-radius: 50%; border: none; background: #f5f5f5;
  color: #888; cursor: pointer; font-size: 16px; display: flex; align-items: center;
  justify-content: center; transition: all 0.2s;
}
.close-btn:hover { background: #000; color: #fff; transform: rotate(90deg); }

.editor-body { padding: 24px 30px; overflow-y: auto; flex: 1; }

.field { display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px; }
.label { font-size: 13px; font-weight: 700; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }

.ops-editor-input {
  width: 100%; padding: 12px 16px; border: 1px solid #e5e7eb; border-radius: 12px;
  font-size: 14px; color: #333; font-weight: 500; transition: all 0.2s;
}
.ops-editor-input:focus { outline: none; border-color: #000; background: #fafafa; }
.textarea { min-height: 140px; resize: none; line-height: 1.6; }

.preview-block {
  margin-top: 24px; border: 1px solid #f0f0f0; border-radius: 18px;
  background: #fafafa; padding: 20px;
}
.preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.preview-header h4 { margin: 0; font-size: 14px; font-weight: 800; color: #000; }
.preview-badge { font-size: 10px; font-weight: 800; background: #000; color: #fff; padding: 2px 8px; border-radius: 4px; }

.preview-content { background: white; border-radius: 12px; padding: 15px; border: 1px solid #eee; }
.preview-text { font-size: 14px; color: #333; line-height: 1.6; margin: 0 0 12px 0; font-weight: 500; white-space: pre-wrap; }

.url-badge {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  background: #f8f8f8; border-radius: 8px; border: 1px solid #eee;
}
.url-icon { font-size: 14px; }
.preview-url { font-size: 12px; color: #666; font-weight: 600; word-break: break-all; }

.editor-message { margin-top: 15px; font-size: 13px; font-weight: 700; }
.up { color: #10b981; }
.down { color: #ef4444; }

.actions { padding: 20px 30px; background: #fdfdfd; border-top: 1px solid #f0f0f0; display: flex; justify-content: flex-end; gap: 12px; }

.btn {
  height: 44px; padding: 0 24px; border-radius: 12px; font-size: 14px; font-weight: 700;
  cursor: pointer; transition: all 0.2s; border: none; display: flex; align-items: center; justify-content: center;
}
.btn-primary { background: #000; color: #fff; }
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
.btn-secondary { background: #f0f0f0; color: #666; }
.btn-secondary:hover { background: #e5e5e5; color: #333; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; box-shadow: none !important; }

@media (max-width: 700px) {
  .ops-editor-panel { border-radius: 0; width: 100%; height: 100%; max-height: 100%; }
  .actions { flex-direction: column; }
  .btn { width: 100%; }
}
</style>
