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
          <span class="label">图片链接</span>
          <input
            :value="draft.image_url"
            class="ops-editor-input"
            type="url"
            maxlength="2048"
            placeholder="https://example.com/qrcode.webp"
            @input="onImageInput"
          />
        </label>

        <label class="field">
          <span class="label">展示文案</span>
          <textarea
            :value="draft.text"
            class="ops-editor-input textarea"
            maxlength="200"
            placeholder="请输入展示文案"
            @input="onTextInput"
          />
        </label>

        <section class="preview-block">
          <div class="preview-header">
             <h4>视觉预览</h4>
             <span class="preview-badge">实时</span>
          </div>
          <div class="preview-content">
            <p class="preview-text">{{ previewText }}</p>
            <div class="preview-image-wrap">
              <img
                v-if="showPreviewImage"
                :src="imageUrl"
                alt="页面图片预览"
                class="preview-image"
                @error="imageLoadFailed = true"
                @load="imageLoadFailed = false"
              />
              <div v-else class="preview-empty">
                <div class="empty-icon">🖼️</div>
                <p>{{ previewHint }}</p>
              </div>
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
          {{ saving ? '正在保存...' : '保存配置' }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

type Draft = {
  text: string
  image_url: string
}

const props = defineProps<{
  visible: boolean
  title: string
  draft: Draft
  defaultText: string
  saving: boolean
  message: string
  ok: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save'): void
  (e: 'update:text', value: string): void
  (e: 'update:image-url', value: string): void
}>()

const imageLoadFailed = ref(false)

const imageUrl = computed(() => String(props.draft.image_url || '').trim())
const previewText = computed(() => {
  const text = String(props.draft.text || '').trim()
  return text || props.defaultText
})
const showPreviewImage = computed(() => Boolean(imageUrl.value) && !imageLoadFailed.value)
const previewHint = computed(() => {
  if (imageUrl.value && imageLoadFailed.value) return '图片加载失败，请检查链接'
  return '未配置图片，将使用内置占位图'
})

watch(
  () => [props.visible, props.draft.image_url],
  () => {
    imageLoadFailed.value = false
  },
)

function onTextInput(event: Event) {
  const target = event.target as HTMLTextAreaElement | null
  emit('update:text', String(target?.value || ''))
}

function onImageInput(event: Event) {
  const target = event.target as HTMLInputElement | null
  emit('update:image-url', String(target?.value || ''))
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
.textarea { min-height: 100px; resize: none; line-height: 1.6; }

.preview-block {
  margin-top: 24px; border: 1px solid #f0f0f0; border-radius: 18px;
  background: #fafafa; padding: 20px;
}
.preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.preview-header h4 { margin: 0; font-size: 14px; font-weight: 800; color: #000; }
.preview-badge { font-size: 10px; font-weight: 800; background: #000; color: #fff; padding: 2px 8px; border-radius: 4px; }

.preview-content { background: white; border-radius: 12px; padding: 15px; border: 1px solid #eee; }
.preview-text { font-size: 14px; color: #333; line-height: 1.6; margin: 0 0 15px 0; font-weight: 500; }

.preview-image-wrap {
  border-radius: 10px; min-height: 200px; background: #fcfcfc;
  display: flex; align-items: center; justify-content: center; overflow: hidden;
  border: 1px dashed #ddd;
}
.preview-image { max-width: 100%; max-height: 300px; object-fit: contain; }
.preview-empty { text-align: center; color: #aaa; padding: 20px; }
.empty-icon { font-size: 32px; margin-bottom: 8px; }
.preview-empty p { margin: 0; font-size: 12px; font-weight: 600; }

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
