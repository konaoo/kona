<template>
  <LegacyAdminShell title="运营配置" subtitle="邀请码页与用户群页（App内）">
    <section class="panel panel-body">
      <div class="section-head">
        <div>
          <h3 class="section-title">运营配置</h3>
          <p class="section-sub">点击编辑后在弹窗内修改，保存后将立即生效。</p>
        </div>
        <button class="btn" :disabled="loadingAny" @click="refreshAll">
          {{ loadingAny ? '刷新中...' : '刷新' }}
        </button>
      </div>

      <p v-if="pageMessage" :class="pageOk ? 'up' : 'down'" class="page-message">{{ pageMessage }}</p>

      <div class="config-list">
        <article v-for="scene in SCENES" :key="scene" class="config-item">
          <div class="item-main">
            <div class="item-copy">
              <h4 class="item-title">{{ sceneTitle(scene) }}</h4>
              <p class="item-text">{{ scenePreviewText(scene) }}</p>
              <span :class="['item-meta', sceneImageMetaClass(scene)]">{{ sceneImageMeta(scene) }}</span>
            </div>

            <div class="item-thumb">
              <img
                v-if="showSceneImage(scene)"
                :src="sceneImageUrl(scene)"
                :alt="`${sceneTitle(scene)}缩略图`"
                @error="thumbLoadFailed[scene] = true"
                @load="thumbLoadFailed[scene] = false"
              />
              <span v-else>暂无缩略图</span>
            </div>
          </div>

          <div class="item-actions">
            <button class="btn primary" :disabled="loading[scene]" @click="openEditor(scene)">
              编辑
            </button>
          </div>
        </article>
      </div>
    </section>

    <OpsConfigEditorModal
      :visible="editor.visible"
      :title="currentMeta.modalTitle"
      :draft="editor.draft"
      :default-text="currentMeta.defaultText"
      :saving="editor.saving"
      :message="editor.message"
      :ok="editor.ok"
      @close="closeEditor"
      @save="saveEditor"
      @update:text="editor.draft.text = $event"
      @update:image-url="editor.draft.image_url = $event"
    />
  </LegacyAdminShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
import OpsConfigEditorModal from '../../components/admin/OpsConfigEditorModal.vue'
import { api } from '../../shared/http'

type OpsConfigPayload = {
  text?: string
  image_url?: string
}

const SCENES = ['invite', 'user_group'] as const
type ConfigScene = typeof SCENES[number]

const META: Record<
  ConfigScene,
  {
    title: string
    modalTitle: string
    defaultText: string
    loadPath: string
    savePath: string
    saveSuccess: string
    loadError: string
    saveError: string
  }
> = {
  invite: {
    title: '邀请码页面',
    modalTitle: '邀请码配置',
    defaultText: '小红书被限制了，进微信群领邀请码。',
    loadPath: '/api/admin/ops/invite_acquire',
    savePath: '/api/admin/ops/invite_acquire/update',
    saveSuccess: '邀请码配置已保存',
    loadError: '读取邀请码配置失败',
    saveError: '邀请码配置保存失败',
  },
  user_group: {
    title: '用户群页面',
    modalTitle: '用户群配置',
    defaultText: '加入咔咔用户群',
    loadPath: '/api/admin/ops/user_group',
    savePath: '/api/admin/ops/user_group/update',
    saveSuccess: '用户群配置已保存',
    loadError: '读取用户群配置失败',
    saveError: '用户群配置保存失败',
  },
}

const configForm = reactive<Record<ConfigScene, Required<OpsConfigPayload>>>({
  invite: { text: '', image_url: '' },
  user_group: { text: '', image_url: '' },
})

const loading = reactive<Record<ConfigScene, boolean>>({
  invite: false,
  user_group: false,
})

const thumbLoadFailed = reactive<Record<ConfigScene, boolean>>({
  invite: false,
  user_group: false,
})

const pageMessage = ref('')
const pageOk = ref(true)

const editor = reactive<{
  visible: boolean
  scene: ConfigScene
  saving: boolean
  message: string
  ok: boolean
  draft: Required<OpsConfigPayload>
}>({
  visible: false,
  scene: 'invite',
  saving: false,
  message: '',
  ok: true,
  draft: {
    text: '',
    image_url: '',
  },
})

const loadingAny = computed(() => SCENES.some((scene) => loading[scene]))
const currentMeta = computed(() => META[editor.scene])

function normalizePayload(
  payload: OpsConfigPayload | null | undefined,
  fallback: Required<OpsConfigPayload> = { text: '', image_url: '' },
): Required<OpsConfigPayload> {
  return {
    text: String(payload?.text ?? fallback.text ?? ''),
    image_url: String(payload?.image_url ?? fallback.image_url ?? ''),
  }
}

function flashPage(msg: string, success: boolean) {
  pageMessage.value = msg
  pageOk.value = success
}

function flashEditor(msg: string, success: boolean) {
  editor.message = msg
  editor.ok = success
}

function sceneTitle(scene: ConfigScene): string {
  return META[scene].title
}

function sceneImageUrl(scene: ConfigScene): string {
  return String(configForm[scene].image_url || '').trim()
}

function scenePreviewText(scene: ConfigScene): string {
  if (loading[scene]) return '读取中...'
  const text = String(configForm[scene].text || '').trim()
  return text || META[scene].defaultText
}

function showSceneImage(scene: ConfigScene): boolean {
  const imageUrl = sceneImageUrl(scene)
  return Boolean(imageUrl) && !thumbLoadFailed[scene]
}

function sceneImageMeta(scene: ConfigScene): string {
  if (loading[scene]) return '图片读取中...'
  const imageUrl = sceneImageUrl(scene)
  if (!imageUrl) return '未配置图片（使用占位图）'
  if (thumbLoadFailed[scene]) return '图片链接不可用'
  return '已配置图片'
}

function sceneImageMetaClass(scene: ConfigScene): string {
  return thumbLoadFailed[scene] ? 'is-error' : ''
}

async function loadConfig(scene: ConfigScene) {
  loading[scene] = true
  thumbLoadFailed[scene] = false
  try {
    const payload = await api.get<OpsConfigPayload>(META[scene].loadPath)
    const normalized = normalizePayload(payload)
    configForm[scene].text = normalized.text
    configForm[scene].image_url = normalized.image_url
  } catch (e) {
    flashPage(e instanceof Error ? e.message : META[scene].loadError, false)
  } finally {
    loading[scene] = false
  }
}

async function refreshAll() {
  pageMessage.value = ''
  await Promise.all(SCENES.map((scene) => loadConfig(scene)))
}

function openEditor(scene: ConfigScene) {
  editor.scene = scene
  editor.visible = true
  editor.saving = false
  editor.message = ''
  editor.ok = true
  editor.draft = normalizePayload(configForm[scene])
}

function closeEditor() {
  if (editor.saving) return
  editor.visible = false
  editor.message = ''
}

function validateEditor(): string | null {
  const text = String(editor.draft.text || '').trim()
  const imageUrl = String(editor.draft.image_url || '').trim()

  if (text.length < 1 || text.length > 200) return '文案长度需在 1 到 200 个字符之间'
  if (imageUrl.length > 2048) return '图片链接长度不能超过 2048 个字符'
  if (imageUrl && !/^https?:\/\//i.test(imageUrl)) return '图片链接必须以 http:// 或 https:// 开头'
  return null
}

async function saveEditor() {
  const validation = validateEditor()
  if (validation) {
    flashEditor(validation, false)
    return
  }

  const scene = editor.scene
  const payloadToSave = normalizePayload(editor.draft)
  payloadToSave.text = payloadToSave.text.trim()
  payloadToSave.image_url = payloadToSave.image_url.trim()

  editor.saving = true
  editor.message = ''
  try {
    const payload = await api.post<OpsConfigPayload>(META[scene].savePath, payloadToSave)
    const normalized = normalizePayload(payload, payloadToSave)
    configForm[scene].text = normalized.text
    configForm[scene].image_url = normalized.image_url
    thumbLoadFailed[scene] = false
    flashPage(META[scene].saveSuccess, true)
    closeEditor()
  } catch (e) {
    flashEditor(e instanceof Error ? e.message : META[scene].saveError, false)
  } finally {
    editor.saving = false
  }
}

onMounted(() => {
  void refreshAll()
})
</script>

<style scoped>
.panel-body {
  padding: 18px;
  margin-bottom: 16px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}

.section-title {
  margin: 0;
  color: #1f3f58;
  font-size: 22px;
  font-weight: 800;
}

.section-sub {
  margin: 6px 0 0;
  color: #55708f;
  font-size: 13px;
}

.page-message {
  margin: 0 0 12px;
  font-weight: 600;
}

.config-list {
  display: grid;
  gap: 12px;
}

.config-item {
  border: 1px solid #d6e1ee;
  border-radius: 12px;
  background: #fbfdff;
  padding: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
}

.item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 14px;
}

.item-copy {
  flex: 1;
  min-width: 0;
}

.item-title {
  margin: 0;
  color: #1f3f58;
  font-size: 17px;
  font-weight: 700;
}

.item-text {
  margin: 8px 0 6px;
  color: #10243e;
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-meta {
  color: #55708f;
  font-size: 12px;
  font-weight: 600;
}

.item-meta.is-error {
  color: var(--danger);
}

.item-thumb {
  width: 92px;
  height: 92px;
  border-radius: 10px;
  border: 1px solid #c9d8e8;
  background: #fff;
  overflow: hidden;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
}

.item-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-thumb span {
  padding: 8px;
  text-align: center;
  color: #6b84a3;
  font-size: 12px;
  line-height: 1.4;
}

.item-actions {
  flex: 0 0 auto;
}

.up {
  color: var(--success);
}

.down {
  color: var(--danger);
}

@media (max-width: 760px) {
  .section-head {
    flex-direction: column;
  }

  .config-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .item-main {
    width: 100%;
  }

  .item-thumb {
    width: 76px;
    height: 76px;
  }

  .item-actions {
    width: 100%;
  }

  .item-actions .btn {
    width: 100%;
  }

}
</style>
