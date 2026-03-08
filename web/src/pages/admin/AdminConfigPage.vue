<template>
  <div class="container admin-config">
    <!-- Sidebar -->
    <div class="sidebar">
      <div class="logo">
        <div class="logo-icon">🏠</div>
        <span>咔咔管理后台</span>
      </div>

      <nav>
        <RouterLink 
          v-for="item in nav" 
          :key="item.path" 
          :to="item.path"
          class="nav-item"
          active-class="active"
        >
          <span>{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="user-profile">
        <div class="user-info">
          <div class="user-avatar" :style="avatarStyle"></div>
          <div class="user-details">
            <h4>{{ store.state.user?.username || '管理员' }}</h4>
            <p>管理员</p>
          </div>
        </div>
        <div class="user-actions">
          <button class="logout-btn" @click="onLogout" title="退出登录">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
      <div class="header">
        <div class="header-title">
          <h1>运营配置</h1>
        </div>
        <div class="header-actions">
          <button class="add-btn" :disabled="loadingAny" @click="refreshAll">
            <span>🔄</span>
            <span>{{ loadingAny ? '正在刷新' : '刷新配置' }}</span>
          </button>
        </div>
      </div>

      <p v-if="pageMessage" :class="pageOk ? 'up' : 'down'" class="msg-tip">{{ pageMessage }}</p>

      <div class="config-grid">
        <!-- Scene Config Cards -->
        <div v-for="scene in SCENES" :key="scene" class="config-card">
          <div class="card-body">
            <div class="info-side">
               <h3 class="card-title">{{ sceneTitle(scene) }}</h3>
               <p class="card-preview">{{ scenePreviewText(scene) }}</p>
               <span class="card-meta" :class="{ 'is-error': thumbLoadFailed[scene] }">
                 {{ sceneImageMeta(scene) }}
               </span>
            </div>
            <div class="thumb-side">
               <div class="thumb-box">
                 <img
                    v-if="showSceneImage(scene)"
                    :src="sceneImageUrl(scene)"
                    :alt="sceneTitle(scene)"
                    @error="thumbLoadFailed[scene] = true"
                    @load="thumbLoadFailed[scene] = false"
                  />
                  <div v-else class="thumb-empty">无图</div>
               </div>
            </div>
          </div>
          <div class="card-footer">
             <button class="action-btn" :disabled="loading[scene]" @click="openEditor(scene)">编辑配置</button>
          </div>
        </div>

        <!-- App Update Card -->
        <div class="config-card update-card">
          <div class="card-body">
            <div class="info-side">
               <h3 class="card-title">{{ APP_UPDATE_META.title }}</h3>
               <p class="card-preview update-preview">{{ appUpdatePreviewText }}</p>
               <div class="url-line" :class="{ 'is-error': appUpdateUrlMetaClass === 'is-error' }">
                 <span class="url-icon">📁</span>
                 <span class="url-text">{{ appUpdateUrlMeta }}</span>
               </div>
            </div>
          </div>
          <div class="card-footer">
             <button class="action-btn" :disabled="loadingAppUpdate" @click="openAppUpdateEditor">编辑更新</button>
          </div>
        </div>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../shared/http'
import { useKonaStore } from '../../stores/composables'
import OpsConfigEditorModal from '../../components/admin/OpsConfigEditorModal.vue'
import OpsAppUpdateEditorModal from '../../components/admin/OpsAppUpdateEditorModal.vue'

const router = useRouter()
const store = useKonaStore()

type OpsConfigPayload = { text?: string; image_url?: string }
type OpsAppUpdatePayload = { text?: string; download_url?: string }

const SCENES = ['invite', 'user_group', 'ios_qr'] as const
type ConfigScene = typeof SCENES[number]

const META: Record<ConfigScene, any> = {
  invite: {
    title: '邀请码页面',
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

const configForm = reactive<Record<ConfigScene, Required<OpsConfigPayload>>>({
  invite: { text: '', image_url: '' },
  user_group: { text: '', image_url: '' },
  ios_qr: { text: '', image_url: '' },
})

const loading = reactive<Record<ConfigScene, boolean>>({
  invite: false, user_group: false, ios_qr: false,
})

const loadingAppUpdate = ref(false)
const thumbLoadFailed = reactive<Record<ConfigScene, boolean>>({
  invite: false, user_group: false, ios_qr: false,
})

const appUpdateState = reactive<Required<OpsAppUpdatePayload>>({
  text: '', download_url: '',
})

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

const nav = [
  { path: '/admin/overview', label: '数据概览', icon: '📊' },
  { path: '/admin/users', label: '用户管理', icon: '👥' },
  { path: '/admin/invites', label: '邀请码管理', icon: '🛡️' },
  { path: '/admin/config', label: '运营配置', icon: '⚙️' },
  { path: '/admin/apis', label: '接口管理', icon: '🔌' },
]

const avatarStyle = computed(() => ({
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
}))

const loadingAny = computed(() => SCENES.some((scene) => loading[scene]) || loadingAppUpdate.value)
const currentMeta = computed(() => META[editor.scene])

const appUpdatePreviewText = computed(() => {
  if (loadingAppUpdate.value) return '读取中...'
  return String(appUpdateState.text || '').trim() || APP_UPDATE_META.defaultText
})

const appUpdateUrlMeta = computed(() => {
  if (loadingAppUpdate.value) return '下载链接读取中...'
  const url = String(appUpdateState.download_url || '').trim()
  if (!url) return '未配置下载链接'
  return /^https?:\/\//i.test(url) ? '已配置下载资源' : '下载链接格式异常'
})

const appUpdateUrlMetaClass = computed(() => {
  const url = String(appUpdateState.download_url || '').trim()
  if (!url) return ''
  return /^https?:\/\//i.test(url) ? '' : 'is-error'
})

function normalizePayload(p: any, f: any = { text: '', image_url: '' }) {
  return { text: String(p?.text ?? f.text ?? ''), image_url: String(p?.image_url ?? f.image_url ?? '') }
}

function normalizeAppUpdatePayload(p: any, f: any = { text: '', download_url: '' }) {
  return { text: String(p?.text ?? f.text ?? ''), download_url: String(p?.download_url ?? f.download_url ?? '') }
}

function flashPage(msg: string, success: boolean) { pageMessage.value = msg; pageOk.value = success; }
function sceneTitle(scene: ConfigScene): string { return META[scene].title; }
function sceneImageUrl(scene: ConfigScene): string { return String(configForm[scene].image_url || '').trim(); }
function scenePreviewText(scene: ConfigScene): string {
  if (loading[scene]) return '读取中...';
  return String(configForm[scene].text || '').trim() || META[scene].defaultText;
}
function showSceneImage(scene: ConfigScene): boolean {
  const imageUrl = sceneImageUrl(scene);
  return Boolean(imageUrl) && !thumbLoadFailed[scene];
}
function sceneImageMeta(scene: ConfigScene): string {
  if (loading[scene]) return '图片读取中...';
  const imageUrl = sceneImageUrl(scene);
  if (!imageUrl) return '未配置图片';
  return thumbLoadFailed[scene] ? '图片链接无效' : '已配置预览图';
}

async function loadConfig(scene: ConfigScene) {
  loading[scene] = true; thumbLoadFailed[scene] = false;
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

async function loadAppUpdateConfig() {
  loadingAppUpdate.value = true
  try {
    const payload = await api.get<OpsAppUpdatePayload>(APP_UPDATE_META.loadPath)
    const normalized = normalizeAppUpdatePayload(payload)
    appUpdateState.text = normalized.text
    appUpdateState.download_url = normalized.download_url
  } catch (e) {
    flashPage(e instanceof Error ? e.message : APP_UPDATE_META.loadError, false)
  } finally {
    loadingAppUpdate.value = false
  }
}

async function refreshAll() {
  pageMessage.value = ''
  await Promise.all([...SCENES.map((scene) => loadConfig(scene)), loadAppUpdateConfig()])
}

function openEditor(scene: ConfigScene) {
  editor.scene = scene; editor.visible = true; editor.saving = false; editor.message = ''; editor.ok = true;
  editor.draft = normalizePayload(configForm[scene])
}
function closeEditor() { if (editor.saving) return; editor.visible = false; }

function openAppUpdateEditor() {
  appUpdateEditor.visible = true; appUpdateEditor.saving = false; appUpdateEditor.message = ''; appUpdateEditor.ok = true;
  appUpdateEditor.draft = normalizeAppUpdatePayload(appUpdateState)
}
function closeAppUpdateEditor() { if (appUpdateEditor.saving) return; appUpdateEditor.visible = false; }

async function saveEditor() {
  const scene = editor.scene
  const payloadToSave = normalizePayload(editor.draft)
  editor.saving = true; editor.message = '';
  try {
    const payload = await api.post<OpsConfigPayload>(META[scene].savePath, payloadToSave)
    const normalized = normalizePayload(payload, payloadToSave)
    configForm[scene].text = normalized.text
    configForm[scene].image_url = normalized.image_url
    thumbLoadFailed[scene] = false
    flashPage(META[scene].saveSuccess, true)
    closeEditor()
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
    appUpdateState.text = normalized.text
    appUpdateState.download_url = normalized.download_url
    flashPage(APP_UPDATE_META.saveSuccess, true)
    closeAppUpdateEditor()
  } catch (e) {
    appUpdateEditor.message = e instanceof Error ? e.message : APP_UPDATE_META.saveError
    appUpdateEditor.ok = false
  } finally {
    appUpdateEditor.saving = false
  }
}

async function onLogout() {
  await store.logout()
  await router.push('/admin/login')
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
.user-avatar { width: 44px; height: 44px; border-radius: 50%; flex-shrink: 0; }
.user-details { display: flex; flex-direction: column; align-items: flex-start; }
.user-details h4 { font-size: 16px; font-weight: 800; margin: 0; padding: 0; color: #000; line-height: 1; }
.user-details p { font-size: 12px; color: #999; font-weight: 500; margin: 4px 0 0 0; padding: 0; line-height: 1; }
.logout-btn { width: 34px; height: 34px; border-radius: 10px; border: 1px solid #e2e2e2; background: transparent; color: #888; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.logout-btn:hover { background: #2d2d2d; color: #fff; border-color: #444; transform: translateX(2px); }

/* Main Content */
.main-content { flex: 1; padding: 40px 50px; overflow-y: auto; height: 100vh; background: #fafafa; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 35px; }
.header-title h1 { font-size: 32px; font-weight: 800; margin-bottom: 6px; color: #000; letter-spacing: -0.8px; }

.add-btn { height: 46px; padding: 0 22px; background: #000; color: white; border: none; border-radius: 12px; font-weight: 700; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 10px; font-size: 14.5px; }
.add-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2); }
.add-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.msg-tip { margin-bottom: 25px; font-weight: 700; font-size: 14.5px; }
.up { color: #10b981; }
.down { color: #ef4444; }

/* Grid Layout */
.config-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 20px; }

.config-card { background: white; border-radius: 20px; border: 1px solid #f0f0f0; overflow: hidden; display: flex; flex-direction: column; transition: all 0.3s ease; }
.config-card:hover { transform: translateY(-4px); box-shadow: 0 15px 35px rgba(0,0,0,0.06); }

.card-body { padding: 24px; flex: 1; display: flex; gap: 20px; }
.info-side { flex: 1; min-width: 0; }
.card-title { font-size: 18px; font-weight: 800; color: #000; margin: 0 0 10px 0; }
.card-preview { font-size: 14px; color: #666; line-height: 1.6; margin: 0 0 12px 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; font-weight: 500; }
.card-meta { font-size: 11px; font-weight: 800; background: #f5f5f5; color: #999; padding: 3px 10px; border-radius: 6px; text-transform: uppercase; }
.card-meta.is-error { background: #fff1f0; color: #f5222d; }

.thumb-side { flex-shrink: 0; }
.thumb-box { width: 84px; height: 84px; border-radius: 12px; background: #fafafa; border: 1px solid #eee; overflow: hidden; display: flex; align-items: center; justify-content: center; }
.thumb-box img { width: 100%; height: 100%; object-fit: cover; }
.thumb-empty { font-size: 12px; color: #ccc; font-weight: 700; }

.card-footer { padding: 18px 24px; background: #fcfcfc; border-top: 1px solid #f7f7f7; }
.action-btn { width: 100%; height: 40px; border-radius: 10px; border: 1px solid #eee; background: white; color: #333; font-weight: 700; font-size: 13px; cursor: pointer; transition: all 0.2s; }
.action-btn:hover:not(:disabled) { border-color: #000; background: #000; color: #fff; }

/* Update Card Special */
.update-card { grid-column: span 1; }
.update-preview { -webkit-line-clamp: 3; }
.url-line { display: flex; align-items: center; gap: 8px; margin-top: 10px; padding: 8px 12px; background: #f8f8f8; border-radius: 8px; border: 1px solid #eee; }
.url-icon { font-size: 14px; }
.url-text { font-size: 11px; font-weight: 700; color: #666; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.url-line.is-error { border-color: #ffa39e; background: #fff1f0; }

@media (max-width: 900px) {
  .sidebar { display: none; }
  .config-grid { grid-template-columns: 1fr; }
}
</style>
