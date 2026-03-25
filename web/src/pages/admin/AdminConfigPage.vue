<template>
  <div class="container admin-config">
    <AdminConsoleNav />

    <!-- Main Content -->
    <div class="main-content">
      <div class="page-header">
        <h1>运营配置</h1>
      </div>

      <p v-if="pageMessage" :class="pageOk ? 'up' : 'down'" class="msg-tip">{{ pageMessage }}</p>

      <div class="card-grid">
        <button v-for="scene in SCENES" :key="scene" class="entry-card" :disabled="loading[scene]" @click="openEditor(scene)">
          <div class="entry-head">
            <div class="entry-icon">{{ sceneIcon(scene) }}</div>
            <div class="entry-copy">
              <h2>{{ sceneTitle(scene) }}</h2>
            </div>
          </div>
          <p class="entry-desc">{{ sceneDescription(scene) }}</p>
          <p class="entry-preview">{{ scenePreviewText(scene) }}</p>
          <div class="entry-summary">
            <span>{{ scenePreviewTag(scene) }}</span>
            <span :class="{ 'is-error-pill': thumbLoadFailed[scene] }">{{ sceneImageMeta(scene) }}</span>
          </div>
        </button>

        <button class="entry-card" :disabled="loadingAppUpdate" @click="openAppUpdateEditor">
          <div class="entry-head">
            <div class="entry-icon">⬆️</div>
            <div class="entry-copy">
              <h2>{{ APP_UPDATE_META.title }}</h2>
            </div>
          </div>
          <p class="entry-desc">配置 App 检查更新文案和下载链接</p>
          <p class="entry-preview">{{ appUpdatePreviewText }}</p>
          <div class="entry-summary">
            <span>{{ appUpdatePreviewTag }}</span>
            <span :class="{ 'is-error-pill': appUpdateUrlMetaClass === 'is-error' }">{{ appUpdateUrlMeta }}</span>
          </div>
        </button>
      </div>
    </div>

    <!-- Modals -->
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

    <OpsAppUpdateEditorModal
      :visible="appUpdateEditor.visible"
      :title="APP_UPDATE_META.modalTitle"
      :draft="appUpdateEditor.draft"
      :default-text="APP_UPDATE_META.defaultText"
      :default-download-url="APP_UPDATE_META.defaultDownloadUrl"
      :saving="appUpdateEditor.saving"
      :message="appUpdateEditor.message"
      :ok="appUpdateEditor.ok"
      @close="closeAppUpdateEditor"
      @save="saveAppUpdateEditor"
      @update:text="appUpdateEditor.draft.text = $event"
      @update:download-url="appUpdateEditor.draft.download_url = $event"
    />
  </div>
</template>

<script setup lang="ts">

type OpsConfigPayload = { text?: string; image_url?: string }
type OpsAppUpdatePayload = { text?: string; download_url?: string }

const SCENES = ['invite', 'user_group', 'ios_qr'] as const
type ConfigScene = typeof SCENES[number]

const META: Record<ConfigScene, any> = {
  invite: {
    title: '邀请码页面',
    description: '配置邀请码获取文案和配图',
    modalTitle: '邀请码配置',
    defaultText: '进微信群领邀请码。',
    loadPath: '/api/admin/ops/invite_acquire',
    savePath: '/api/admin/ops/invite_acquire/update',
    saveSuccess: '邀请码配置已保存',
    loadError: '读取邀请码配置失败',
    saveError: '邀请码配置保存失败',
  },
  user_group: {
    title: '用户群页面',
    description: '配置用户群入口文案和群二维码',
    modalTitle: '用户群配置',
    defaultText: '加入咔咔用户群',
    loadPath: '/api/admin/ops/user_group',
    savePath: '/api/admin/ops/user_group/update',
    saveSuccess: '用户群配置已保存',
    loadError: '读取用户群配置失败',
    saveError: '用户群配置保存失败',
  },
  ios_qr: {
    title: '苹果版下载二维码',
    description: '配置苹果版下载文案和二维码图',
    modalTitle: '苹果版下载配置',
    defaultText: '扫码下载苹果版',
    loadPath: '/api/admin/ops/ios_qr',
    savePath: '/api/admin/ops/ios_qr/update',
    saveSuccess: '苹果版下载配置已保存',
    loadError: '读取苹果版下载配置失败',
    saveError: '苹果版下载配置保存失败',
  },
}

const APP_UPDATE_META = {
  title: '检查更新配置',
  modalTitle: '检查更新配置',
  defaultText: '1. 修复问题\n2. 优化体验',
  defaultDownloadUrl: '',
  loadPath: '/api/admin/ops/app_update',
  savePath: '/api/admin/ops/app_update/update',
  saveSuccess: '检查更新配置已保存',
  loadError: '读取检查更新配置失败',
  saveError: '检查更新配置保存失败',
}

import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../../shared/http'
import AdminConsoleNav from '../../components/admin/AdminConsoleNav.vue'
import OpsConfigEditorModal from '../../components/admin/OpsConfigEditorModal.vue'
import OpsAppUpdateEditorModal from '../../components/admin/OpsAppUpdateEditorModal.vue'
import { storeToRefs } from 'pinia'
import { useAdminStore } from '../../stores/admin'

const adminStore = useAdminStore()
const { ops: opsState } = storeToRefs(adminStore)

const configForm = computed(() => opsState.value.configs)
const appUpdateState = computed(() => opsState.value.appUpdate)
const thumbLoadFailed = computed(() => opsState.value.thumbLoadFailed)

const loading = reactive<Record<ConfigScene, boolean>>({
  invite: false, user_group: false, ios_qr: false,
})
const loadingAppUpdate = ref(false)

const pageMessage = ref('')
const pageOk = ref(true)

const editor = reactive<{
  visible: boolean; scene: ConfigScene; saving: boolean; message: string; ok: boolean; draft: Required<OpsConfigPayload>
}>({
  visible: false, scene: 'invite', saving: false, message: '', ok: true, draft: { text: '', image_url: '' }
})

const appUpdateEditor = reactive<{
  visible: boolean; saving: boolean; message: string; ok: boolean; draft: Required<OpsAppUpdatePayload>
}>({
  visible: false, saving: false, message: '', ok: true, draft: { text: '', download_url: '' }
})

const currentMeta = computed(() => META[editor.scene])

const appUpdateUrlMeta = computed(() => {
  if (loadingAppUpdate.value) return '下载链接读取中...'
  const url = String(appUpdateState.value.download_url || '').trim()
  if (!url) return '未配置下载链接'
  return /^https?:\/\//i.test(url) ? '已配置下载资源' : '下载链接格式异常'
})

const appUpdateUrlMetaClass = computed(() => {
  const url = String(appUpdateState.value.download_url || '').trim()
  if (!url) return ''
  return /^https?:\/\//i.test(url) ? '' : 'is-error'
})

const appUpdatePreviewTag = computed(() => {
  const text = String(appUpdateState.value.text || '').trim()
  return text ? '已配更新文案' : '默认更新文案'
})

function normalizePayload(p: any, f: any = { text: '', image_url: '' }) {
  return { text: String(p?.text ?? f.text ?? ''), image_url: String(p?.image_url ?? f.image_url ?? '') }
}

function normalizeAppUpdatePayload(p: any, f: any = { text: '', download_url: '' }) {
  return { text: String(p?.text ?? f.text ?? ''), download_url: String(p?.download_url ?? f.download_url ?? '') }
}

function flashPage(msg: string, success: boolean) { pageMessage.value = msg; pageOk.value = success; }
function sceneTitle(scene: ConfigScene): string { return META[scene].title; }
function sceneDescription(scene: ConfigScene): string { return String(META[scene].description || '').trim(); }
function sceneIcon(scene: ConfigScene): string {
  if (scene === 'invite') return '🎟️'
  if (scene === 'user_group') return '👥'
  return '📱'
}
function scenePreviewTag(scene: ConfigScene): string {
  const text = String(configForm.value[scene]?.text || '').trim()
  return text ? '已配文案' : '默认文案'
}
function scenePreviewText(scene: ConfigScene): string {
  const text = String(configForm.value[scene]?.text || '').trim()
  return text || META[scene].defaultText
}
function sceneImageMeta(scene: ConfigScene): string {
  if (loading[scene]) return '图片读取中...';
  const imageUrl = String(configForm.value[scene]?.image_url || '').trim();
  if (!imageUrl) return '未配置图片';
  return thumbLoadFailed.value[scene] ? '图片链接无效' : '已配置预览图';
}

const appUpdatePreviewText = computed(() => {
  const text = String(appUpdateState.value.text || '').trim()
  return text || APP_UPDATE_META.defaultText
})

async function refreshAll(force = false) {
  loading.invite = true; loading.user_group = true; loading.ios_qr = true; loadingAppUpdate.value = true
  pageMessage.value = ''
  try {
    await adminStore.loadOpsConfigs(SCENES, force)
  } catch (e) {
    flashPage(e instanceof Error ? e.message : '加载配置失败', false)
  } finally {
    loading.invite = false; loading.user_group = false; loading.ios_qr = false; loadingAppUpdate.value = false
  }
}

function openEditor(scene: ConfigScene) {
  editor.scene = scene; editor.visible = true; editor.saving = false; editor.message = ''; editor.ok = true;
  editor.draft = normalizePayload(configForm.value[scene])
}
function closeEditor(force = false) {
  if (editor.saving && !force) return
  editor.visible = false
}

function openAppUpdateEditor() {
  appUpdateEditor.visible = true; appUpdateEditor.saving = false; appUpdateEditor.message = ''; appUpdateEditor.ok = true;
  appUpdateEditor.draft = normalizeAppUpdatePayload(appUpdateState.value)
}
function closeAppUpdateEditor(force = false) {
  if (appUpdateEditor.saving && !force) return
  appUpdateEditor.visible = false
}

async function saveEditor() {
  const scene = editor.scene
  const payloadToSave = normalizePayload(editor.draft)
  editor.saving = true; editor.message = '';
  try {
    const payload = await api.post<OpsConfigPayload>(META[scene].savePath, payloadToSave)
    const normalized = normalizePayload(payload, payloadToSave)
    // 更新 Store 中的数据
    adminStore.ops.configs[scene] = {
      text: normalized.text,
      image_url: normalized.image_url
    }
    adminStore.ops.thumbLoadFailed[scene] = false
    flashPage(META[scene].saveSuccess, true)
    closeEditor(true)
  } catch (e) {
    editor.message = e instanceof Error ? e.message : META[scene].saveError
    editor.ok = false
  } finally {
    editor.saving = false
  }
}

async function saveAppUpdateEditor() {
  const payloadToSave = normalizeAppUpdatePayload(appUpdateEditor.draft)
  appUpdateEditor.saving = true; appUpdateEditor.message = '';
  try {
    const payload = await api.post<OpsAppUpdatePayload>(APP_UPDATE_META.savePath, payloadToSave)
    const normalized = normalizeAppUpdatePayload(payload, payloadToSave)
    // 更新 Store 中的数据
    adminStore.ops.appUpdate = {
      text: normalized.text,
      download_url: normalized.download_url
    }
    flashPage(APP_UPDATE_META.saveSuccess, true)
    closeAppUpdateEditor(true)
  } catch (e) {
    appUpdateEditor.message = e instanceof Error ? e.message : APP_UPDATE_META.saveError
    appUpdateEditor.ok = false
  } finally {
    appUpdateEditor.saving = false
  }
}

onMounted(() => {
  void refreshAll()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.container { width: 100vw; height: 100vh; background: white; overflow: hidden; display: flex; font-family: 'Inter', sans-serif; color: #333; }

/* Sidebar Copy */
.sidebar { width: 260px; background: white; padding: 30px 0 0 0; border-right: 1px solid #f0f0f0; display: flex; flex-direction: column; height: 100vh; flex-shrink: 0; }
.logo { display: flex; align-items: center; gap: 12px; font-weight: 800; font-size: 19px; margin-bottom: 35px; padding: 0 24px; color: #000; letter-spacing: -0.5px; }
.logo-icon { width: 34px; height: 34px; background: #000; border-radius: 9px; display: flex; align-items: center; justify-content: center; color: white; font-size: 18px; }
.nav-item { display: flex; align-items: center; gap: 12px; padding: 13px 18px; margin: 0 12px 6px 12px; border-radius: 14px; cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); color: #666; font-weight: 600; text-decoration: none; font-size: 14.5px; }
.nav-item:hover { background: #f8f9fa; color: #000; }
.nav-item.active { background: #000; color: white; }
.user-profile { margin-top: auto; padding: 24px; border-top: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; background: #fdfdfd; }
.user-info { display: flex; align-items: center; gap: 12px; }
.user-avatar { width: 44px; height: 44px; border-radius: 50%; flex-shrink: 0; object-fit: cover; }
.user-avatar-fallback { display: flex; align-items: center; justify-content: center; color: #fff; font-size: 18px; font-weight: 800; }
.user-details { display: flex; flex-direction: column; align-items: flex-start; }
.user-details h4 { font-size: 16px; font-weight: 800; margin: 0; padding: 0; color: #000; line-height: 1; }
.user-details p { font-size: 12px; color: #999; font-weight: 500; margin: 4px 0 0 0; padding: 0; line-height: 1; }
.logout-btn { width: 34px; height: 34px; border-radius: 10px; border: 1px solid #e2e2e2; background: transparent; color: #888; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.logout-btn:hover { background: #2d2d2d; color: #fff; border-color: #444; transform: translateX(2px); }

/* Main Content */
.main-content { flex: 1; overflow-y: auto; padding: 22px; background: #f5f7fb; }
.page-header { margin-bottom: 14px; }
.page-header h1 { margin: 0; color: #111827; font-size: 32px; font-weight: 800; letter-spacing: -0.04em; }

.msg-tip { margin-bottom: 14px; font-weight: 700; font-size: 14px; }
.up { color: #12b76a; }
.down { color: #ef4444; }

.card-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.entry-card {
  min-height: 206px;
  padding: 18px;
  border: 1px solid #e7ebf3;
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.05);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 14px;
  text-align: left;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

button.entry-card {
  width: 100%;
  border: none;
  cursor: pointer;
}

.entry-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 22px 48px rgba(15, 23, 42, 0.08);
  border-color: #d8dfeb;
}

.entry-head {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
}

.entry-icon {
  width: 58px;
  height: 58px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.1);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.entry-copy { min-width: 0; flex: 1; }
.entry-copy h2 {
  margin: 0;
  color: #111827;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.entry-desc {
  margin: 0;
  color: #8a93a5;
  font-size: 12px;
  line-height: 1.45;
}

.entry-preview {
  margin: 0;
  color: #344054;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.entry-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.entry-summary span {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: #f4f7fb;
  color: #667085;
  font-size: 11px;
  font-weight: 700;
}

.entry-summary .is-error-pill {
  background: #fef2f2;
  color: #b42318;
}

@media (max-width: 1200px) {
  .card-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 900px) {
  .sidebar { display: none; }
  .main-content { padding: 18px 18px calc(112px + env(safe-area-inset-bottom)); }
  .page-header {
    margin-bottom: 12px;
  }
  .page-header h1 {
    font-size: 28px;
  }
  .card-grid { grid-template-columns: 1fr; }
  .entry-card {
    min-height: 0;
    padding: 20px;
    gap: 12px;
  }
  .entry-icon {
    width: 54px;
    height: 54px;
    border-radius: 14px;
    font-size: 22px;
  }
  .entry-copy h2 {
    font-size: 18px;
  }
  .entry-preview {
    font-size: 14px;
    -webkit-line-clamp: 3;
  }
  .entry-summary span {
    height: auto;
    min-height: 24px;
    padding: 6px 10px;
    line-height: 1.35;
  }
}
</style>
