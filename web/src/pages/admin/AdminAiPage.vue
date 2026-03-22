<template>
  <div class="container admin-ai">
    <AdminConsoleNav />

    <div class="main-content">
      <div class="page-header">
        <h1>AI 助手配置</h1>
        <p class="page-desc">配置 AI 供应商，用于小咔智能助手和截图识别</p>
      </div>

      <p v-if="pageMessage" :class="pageOk ? 'up' : 'down'" class="msg-tip">{{ pageMessage }}</p>

      <div class="toolbar">
        <button class="add-btn" @click="openEditor()">
          <span class="add-icon">+</span>
          添加供应商
        </button>
      </div>

      <div class="ocr-config-card">
        <div class="ocr-config-header">
          <h2>截图识别配置</h2>
          <p>这里单独指定截图识别使用的供应商和模型，不再跟聊天助手共用。</p>
        </div>

        <div class="ocr-config-grid">
          <div class="ocr-field">
            <label class="field-label">截图识别供应商</label>
            <select v-model="ocrConfig.provider_id" class="field-input" @change="onOcrProviderChange">
              <option value="">跟随当前激活供应商</option>
              <option v-for="p in providers" :key="p.id" :value="p.id">
                {{ p.name }}（{{ presetLabel(p.type) }}）
              </option>
            </select>
          </div>

          <div class="ocr-field">
            <label class="field-label">截图识别模型</label>
            <div class="model-field">
              <select v-if="ocrModels.length > 0" v-model="ocrConfig.model" class="field-input mono">
                <option value="">跟随供应商默认模型</option>
                <option v-for="m in ocrModels" :key="m.id" :value="m.id">{{ m.name || m.id }}</option>
                <option
                  v-if="ocrConfig.model && !ocrModels.some(m => m.id === ocrConfig.model)"
                  :value="ocrConfig.model"
                >
                  {{ ocrConfig.model }}（当前）
                </option>
              </select>
              <input
                v-else
                v-model="ocrConfig.model"
                class="field-input mono"
                placeholder="留空时跟随供应商默认模型"
                maxlength="100"
              />
              <button
                class="fetch-models-btn"
                :disabled="ocrFetchingModels || !ocrConfig.provider_id"
                @click="fetchOcrModels"
                title="获取模型列表"
              >
                <template v-if="ocrFetchingModels">⏳</template>
                <template v-else>🔄</template>
              </button>
            </div>
          </div>
        </div>

        <div class="ocr-config-footer">
          <p class="ocr-config-meta">
            <template v-if="ocrConfig.provider_id">
              当前截图识别：{{ ocrConfig.provider_name || '未命名供应商' }} / {{ ocrConfig.resolved_model || '未指定模型' }}
            </template>
            <template v-else>
              当前截图识别：跟随当前激活供应商
            </template>
          </p>
          <button class="footer-btn save-btn" :disabled="ocrSaving" @click="saveOcrConfig">
            {{ ocrSaving ? '保存中…' : '保存截图识别配置' }}
          </button>
        </div>

        <p v-if="ocrMessage" class="modal-msg" :class="ocrOk ? 'up' : 'down'">{{ ocrMessage }}</p>
      </div>

      <div v-if="loading" class="loading-text">加载中…</div>

      <div v-else-if="providers.length === 0" class="empty-text">
        暂未配置 AI 供应商，点击上方按钮添加
      </div>

      <div v-else class="provider-list">
        <div v-for="p in providers" :key="p.id" class="provider-card" :class="{ active: p.active }">
          <div class="card-header">
            <div class="card-status">
              <span class="status-dot" :class="p.active ? 'dot-active' : 'dot-inactive'"></span>
              <span class="card-name">{{ p.name }}</span>
            </div>
            <span v-if="p.active" class="active-badge">激活中</span>
          </div>

          <div class="card-info">
            <div class="info-row">
              <span class="info-label">类型</span>
              <span class="info-value">{{ presetLabel(p.type) }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">模型</span>
              <span class="info-value mono">{{ p.model || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">API</span>
              <span class="info-value mono truncate">{{ p.base_url || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Key</span>
              <span class="info-value mono">{{ p.api_key_masked }}</span>
            </div>
          </div>

          <div class="card-actions">
            <button class="action-btn test-btn" :disabled="testing === p.id" @click="testProvider(p)">
              <template v-if="testing === p.id">测试中…</template>
              <template v-else>测试连通</template>
            </button>
            <button class="action-btn" @click="openEditor(p)">编辑</button>
            <button v-if="!p.active" class="action-btn activate-btn" @click="activateProvider(p.id)">设为激活</button>
            <button class="action-btn delete-btn" @click="deleteProvider(p)">删除</button>
          </div>

          <p v-if="testResults[p.id]" class="test-result" :class="testResults[p.id]?.ok ? 'up' : 'down'">
            {{ testResults[p.id]?.message }}
          </p>
        </div>
      </div>
    </div>

    <!-- 编辑 Modal -->
    <Teleport to="body">
      <div v-if="editor.visible" class="modal-overlay" @click.self="closeEditor()">
        <div class="modal-box">
          <div class="modal-header">
            <h2>{{ editor.id ? '编辑供应商' : '添加供应商' }}</h2>
            <button class="modal-close" @click="closeEditor()">&times;</button>
          </div>

          <div class="modal-body">
            <label class="field-label">供应商类型</label>
            <select v-model="editor.type" class="field-input" @change="onTypeChange">
              <option v-for="(preset, key) in presets" :key="key" :value="key">{{ preset.label }}</option>
            </select>

            <label class="field-label">显示名称</label>
            <input v-model="editor.name" class="field-input" placeholder="自定义名称" maxlength="50" />

            <label class="field-label">API 地址</label>
            <input v-model="editor.base_url" class="field-input mono" placeholder="https://api.example.com" maxlength="512" />

            <label class="field-label">API Key</label>
            <input v-model="editor.api_key" type="password" class="field-input mono" placeholder="sk-..." maxlength="256" />

            <label class="field-label">模型名称</label>
            <div class="model-field">
              <select v-if="editorModels.length > 0" v-model="editor.model" class="field-input mono">
                <option v-for="m in editorModels" :key="m.id" :value="m.id">{{ m.name || m.id }}</option>
                <option v-if="editor.model && !editorModels.some(m => m.id === editor.model)" :value="editor.model">{{ editor.model }}（当前）</option>
              </select>
              <input v-else v-model="editor.model" class="field-input mono" placeholder="模型 ID（测试连通后可选择）" maxlength="100" />
              <button class="fetch-models-btn" :disabled="fetchingModels" @click="fetchEditorModels" title="获取模型列表">
                <template v-if="fetchingModels">⏳</template>
                <template v-else>🔄</template>
              </button>
            </div>

            <p v-if="editor.message" class="modal-msg" :class="editor.ok ? 'up' : 'down'">{{ editor.message }}</p>
          </div>

          <div class="modal-footer">
            <button class="footer-btn test-footer-btn" :disabled="editor.saving || editorTesting" @click="testEditorProvider">
              {{ editorTesting ? '测试中…' : '测试连通' }}
            </button>
            <div class="footer-right">
              <button class="footer-btn cancel-btn" :disabled="editor.saving" @click="closeEditor()">取消</button>
              <button class="footer-btn save-btn" :disabled="editor.saving" @click="saveEditor">
                {{ editor.saving ? '保存中…' : '保存' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api } from '../../shared/http'
import AdminConsoleNav from '../../components/admin/AdminConsoleNav.vue'

interface ProviderItem {
  id: string
  type: string
  name: string
  base_url: string
  api_key_masked: string
  model: string
  active: boolean
  protocol: string
}

interface ProviderPreset {
  label: string
  default_base_url: string
  default_model: string
  protocol: string
}

interface OcrConfig {
  provider_id: string
  provider_name: string
  model: string
  resolved_model: string
  enabled: boolean
}

const providers = ref<ProviderItem[]>([])
const presets: Record<string, ProviderPreset> = {
  deepseek: { label: 'DeepSeek', default_base_url: 'https://api.deepseek.com', default_model: 'deepseek-chat', protocol: 'openai' },
  openai: { label: 'OpenAI', default_base_url: 'https://api.openai.com/v1', default_model: 'gpt-4o', protocol: 'openai' },
  anthropic: { label: 'Anthropic Claude', default_base_url: 'https://api.anthropic.com', default_model: 'claude-sonnet-4-20250514', protocol: 'anthropic' },
  gemini: { label: 'Google Gemini', default_base_url: 'https://generativelanguage.googleapis.com/v1beta/openai', default_model: 'gemini-2.0-flash', protocol: 'openai' },
  zhipu: { label: '智谱 GLM', default_base_url: 'https://open.bigmodel.cn/api/paas/v4', default_model: 'glm-4-flash', protocol: 'openai' },
  custom: { label: '自定义供应商', default_base_url: '', default_model: '', protocol: 'openai' },
}
const loading = ref(true)
const pageMessage = ref('')
const pageOk = ref(true)
const ocrMessage = ref('')
const ocrOk = ref(true)
const ocrSaving = ref(false)
const testing = ref('')
const testResults = reactive<Record<string, { ok: boolean; message: string }>>({})
const editorTesting = ref(false)
const editorModels = ref<{ id: string; name: string }[]>([])
const fetchingModels = ref(false)
const ocrModels = ref<{ id: string; name: string }[]>([])
const ocrFetchingModels = ref(false)

const ocrConfig = reactive<OcrConfig>({
  provider_id: '',
  provider_name: '',
  model: '',
  resolved_model: '',
  enabled: false,
})

const editor = reactive({
  visible: false,
  id: '',
  type: 'deepseek',
  name: '',
  base_url: '',
  api_key: '',
  model: '',
  saving: false,
  message: '',
  ok: true,
})

function presetLabel(type: string): string {
  return presets[type]?.label || type
}

function flash(msg: string, ok: boolean) {
  pageMessage.value = msg
  pageOk.value = ok
}

function applyOcrConfig(config?: Partial<OcrConfig>) {
  ocrConfig.provider_id = config?.provider_id || ''
  ocrConfig.provider_name = config?.provider_name || ''
  ocrConfig.model = config?.model || config?.resolved_model || ''
  ocrConfig.resolved_model = config?.resolved_model || config?.model || ''
  ocrConfig.enabled = Boolean(config?.enabled)
}

function onTypeChange() {
  const preset = presets[editor.type]
  if (preset) {
    if (!editor.name || Object.values(presets).some(p => p.label === editor.name)) {
      editor.name = preset.label
    }
    editor.base_url = preset.default_base_url
    editor.model = preset.default_model
  }
}

function openEditor(p?: ProviderItem) {
  editor.message = ''
  editor.ok = true
  editor.saving = false
  editorModels.value = []
  if (p) {
    editor.id = p.id
    editor.type = p.type
    editor.name = p.name
    editor.base_url = p.base_url
    editor.api_key = ''  // 不回填真实 key
    editor.model = p.model
  } else {
    editor.id = ''
    editor.type = 'deepseek'
    const preset = presets['deepseek']
    editor.name = preset?.label || 'DeepSeek'
    editor.base_url = preset?.default_base_url || ''
    editor.api_key = ''
    editor.model = preset?.default_model || ''
  }
  editor.visible = true
}

function closeEditor() {
  if (editor.saving) return
  editor.visible = false
}

async function loadAll() {
  loading.value = true
  try {
    const resp = await api.get<{ providers: ProviderItem[]; ocr_config?: OcrConfig }>('/api/admin/ai/providers')
    providers.value = resp.providers || []
    applyOcrConfig(resp.ocr_config)
  } catch (e) {
    flash(e instanceof Error ? e.message : '加载失败', false)
  } finally {
    loading.value = false
  }
}

function onOcrProviderChange() {
  const provider = providers.value.find(p => p.id === ocrConfig.provider_id)
  ocrModels.value = []
  ocrMessage.value = ''
  if (!provider) {
    ocrConfig.provider_name = ''
    ocrConfig.model = ''
    ocrConfig.resolved_model = ''
    return
  }
  ocrConfig.provider_name = provider.name
  if (!ocrConfig.model) {
    ocrConfig.model = provider.model || ''
  }
  ocrConfig.resolved_model = ocrConfig.model || provider.model || ''
}

async function fetchOcrModels() {
  if (!ocrConfig.provider_id) return
  ocrFetchingModels.value = true
  ocrMessage.value = ''
  try {
    const resp = await api.post<{ models: { id: string; name: string }[] }>('/api/admin/ai/providers/models', {
      id: ocrConfig.provider_id,
    })
    ocrModels.value = resp.models || []
    ocrMessage.value = ocrModels.value.length > 0 ? `已获取 ${ocrModels.value.length} 个模型` : '未获取到模型列表'
    ocrOk.value = ocrModels.value.length > 0
  } catch (e) {
    ocrMessage.value = e instanceof Error ? e.message : '获取模型列表失败'
    ocrOk.value = false
  } finally {
    ocrFetchingModels.value = false
  }
}

async function saveOcrConfig() {
  ocrSaving.value = true
  ocrMessage.value = ''
  try {
    const resp = await api.post<{ ocr_config: OcrConfig }>('/api/admin/ai/ocr/save', {
      provider_id: ocrConfig.provider_id,
      model: ocrConfig.model,
    })
    applyOcrConfig(resp.ocr_config)
    ocrMessage.value = ocrConfig.provider_id ? '截图识别配置已保存' : '截图识别已改为跟随当前激活供应商'
    ocrOk.value = true
  } catch (e) {
    ocrMessage.value = e instanceof Error ? e.message : '保存失败'
    ocrOk.value = false
  } finally {
    ocrSaving.value = false
  }
}

async function saveEditor() {
  editor.saving = true
  editor.message = ''
  try {
    const payload: Record<string, string> = {
      type: editor.type,
      name: editor.name,
      base_url: editor.base_url,
      model: editor.model,
    }
    if (editor.id) payload.id = editor.id
    if (editor.api_key) payload.api_key = editor.api_key

    const resp = await api.post<{ providers: ProviderItem[] }>('/api/admin/ai/providers/save', payload)
    providers.value = resp.providers || []
    await loadAll()
    flash(editor.id ? '供应商已更新' : '供应商已添加', true)
    editor.visible = false
  } catch (e) {
    editor.message = e instanceof Error ? e.message : '保存失败'
    editor.ok = false
  } finally {
    editor.saving = false
  }
}

async function deleteProvider(p: ProviderItem) {
  if (!confirm(`确认删除「${p.name}」？`)) return
  try {
    const resp = await api.post<{ providers: ProviderItem[] }>('/api/admin/ai/providers/delete', { id: p.id })
    providers.value = resp.providers || []
    await loadAll()
    flash('已删除', true)
  } catch (e) {
    flash(e instanceof Error ? e.message : '删除失败', false)
  }
}

async function activateProvider(id: string) {
  try {
    const resp = await api.post<{ providers: ProviderItem[] }>('/api/admin/ai/providers/activate', { id })
    providers.value = resp.providers || []
    await loadAll()
    flash('已切换激活供应商', true)
  } catch (e) {
    flash(e instanceof Error ? e.message : '操作失败', false)
  }
}

async function testProvider(p: ProviderItem) {
  testing.value = p.id
  delete testResults[p.id]
  try {
    const resp = await api.post<{ message?: string; error?: string }>('/api/admin/ai/providers/test', {
      id: p.id,
      type: p.type,
      base_url: p.base_url,
      model: p.model,
    })
    testResults[p.id] = { ok: true, message: resp.message || '连接成功' }
  } catch (e) {
    testResults[p.id] = { ok: false, message: e instanceof Error ? e.message : '测试失败' }
  } finally {
    testing.value = ''
  }
}

async function testEditorProvider() {
  editorTesting.value = true
  editor.message = ''
  try {
    const payload: Record<string, string> = {
      type: editor.type,
      base_url: editor.base_url,
      model: editor.model,
      api_key: editor.api_key,
    }
    if (editor.id) payload.id = editor.id

    const resp = await api.post<{ message?: string; models?: { id: string; name: string }[] }>('/api/admin/ai/providers/test', payload)
    editor.message = resp.message || '连接成功'
    editor.ok = true
    // 测试成功后更新模型列表
    if (resp.models && resp.models.length > 0) {
      editorModels.value = resp.models
    }
  } catch (e) {
    editor.message = e instanceof Error ? e.message : '测试失败'
    editor.ok = false
  } finally {
    editorTesting.value = false
  }
}

async function fetchEditorModels() {
  fetchingModels.value = true
  try {
    const payload: Record<string, string> = {
      type: editor.type,
      base_url: editor.base_url,
      api_key: editor.api_key,
    }
    if (editor.id) payload.id = editor.id

    const resp = await api.post<{ models: { id: string; name: string }[] }>('/api/admin/ai/providers/models', payload)
    if (resp.models && resp.models.length > 0) {
      editorModels.value = resp.models
      editor.message = `已获取 ${resp.models.length} 个模型`
      editor.ok = true
    } else {
      editor.message = '未获取到模型列表'
      editor.ok = false
    }
  } catch (e) {
    editor.message = e instanceof Error ? e.message : '获取模型列表失败'
    editor.ok = false
  } finally {
    fetchingModels.value = false
  }
}

onMounted(() => {
  void loadAll()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.container { width: 100vw; height: 100vh; background: white; overflow: hidden; display: flex; font-family: 'Inter', sans-serif; color: #333; }
.main-content { flex: 1; overflow-y: auto; padding: 22px; background: #f5f7fb; }

.page-header { margin-bottom: 6px; }
.page-header h1 { margin: 0; color: #111827; font-size: 32px; font-weight: 800; letter-spacing: -0.04em; }
.page-desc { margin: 6px 0 0; color: #8a93a5; font-size: 13px; }

.msg-tip { margin: 10px 0; font-weight: 700; font-size: 14px; }
.up { color: #12b76a; }
.down { color: #ef4444; }

.toolbar { margin: 18px 0 16px; }
.add-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 20px; border: none; border-radius: 12px;
  background: #111827; color: #fff; font-weight: 700; font-size: 14px;
  cursor: pointer; transition: all 0.2s;
}
.add-btn:hover { background: #1f2937; transform: translateY(-1px); }
.add-icon { font-size: 18px; font-weight: 300; }

.loading-text, .empty-text { color: #8a93a5; font-size: 14px; padding: 40px 0; text-align: center; }

.ocr-config-card {
  margin-bottom: 18px;
  padding: 18px 20px;
  border: 1px solid #e7ebf3;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}
.ocr-config-header h2 { margin: 0; font-size: 18px; font-weight: 800; color: #111827; }
.ocr-config-header p { margin: 6px 0 0; color: #8a93a5; font-size: 13px; }
.ocr-config-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(280px, 1.2fr);
  gap: 16px;
}
.ocr-field { min-width: 0; }
.ocr-config-footer {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.ocr-config-meta { margin: 0; color: #6b7280; font-size: 13px; }

/* Provider Cards */
.provider-list { display: flex; flex-direction: column; gap: 14px; }

.provider-card {
  padding: 20px;
  border: 1px solid #e7ebf3;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
  transition: all 0.2s;
}
.provider-card.active { border-color: #5b8def; box-shadow: 0 8px 24px rgba(91, 141, 239, 0.1); }
.provider-card:hover { transform: translateY(-1px); box-shadow: 0 12px 32px rgba(15, 23, 42, 0.07); }

.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.card-status { display: flex; align-items: center; gap: 10px; }
.status-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.dot-active { background: #12b76a; box-shadow: 0 0 8px rgba(18, 183, 106, 0.4); }
.dot-inactive { background: #d1d5db; }
.card-name { font-size: 17px; font-weight: 800; color: #111827; letter-spacing: -0.02em; }
.active-badge {
  padding: 4px 12px; border-radius: 999px;
  background: #ecfdf3; color: #027a48;
  font-size: 12px; font-weight: 700;
}

.card-info { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 20px; margin-bottom: 16px; }
.info-row { display: flex; align-items: baseline; gap: 8px; }
.info-label { color: #8a93a5; font-size: 12px; font-weight: 600; min-width: 32px; }
.info-value { color: #344054; font-size: 13px; font-weight: 600; }
.info-value.mono { font-family: 'JetBrains Mono', 'SF Mono', monospace; font-size: 12px; }
.info-value.truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 300px; }

.card-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.action-btn {
  padding: 7px 14px; border: 1px solid #e2e2e2; border-radius: 10px;
  background: #fff; color: #444; font-size: 12px; font-weight: 700;
  cursor: pointer; transition: all 0.2s;
}
.action-btn:hover { background: #f8f9fa; border-color: #ccc; }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.test-btn:hover { border-color: #5b8def; color: #5b8def; }
.activate-btn:hover { border-color: #12b76a; color: #12b76a; }
.delete-btn:hover { border-color: #ef4444; color: #ef4444; }

.test-result { margin: 10px 0 0; font-size: 13px; font-weight: 600; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(0, 0, 0, 0.5); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
}
.modal-box {
  width: 480px; max-width: 92vw; max-height: 90vh;
  background: #fff; border-radius: 20px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.2);
  display: flex; flex-direction: column;
  overflow: hidden;
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px; border-bottom: 1px solid #f0f0f0;
}
.modal-header h2 { margin: 0; font-size: 18px; font-weight: 800; color: #111827; }
.modal-close {
  width: 32px; height: 32px; border: none; background: #f3f4f6; border-radius: 8px;
  font-size: 20px; color: #6b7280; cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.modal-close:hover { background: #e5e7eb; }

.modal-body {
  padding: 20px 24px; overflow-y: auto; flex: 1;
}
.field-label { display: block; margin: 0 0 6px; font-size: 13px; font-weight: 700; color: #344054; }
.field-label:not(:first-child) { margin-top: 16px; }
.field-input {
  display: block; width: 100%; padding: 10px 14px;
  border: 1px solid #d0d5dd; border-radius: 10px;
  font-size: 14px; color: #111827; background: #fff;
  outline: none; transition: border-color 0.2s;
  box-sizing: border-box;
}
.field-input:focus { border-color: #5b8def; }
.field-input.mono { font-family: 'JetBrains Mono', 'SF Mono', monospace; font-size: 13px; }
select.field-input { cursor: pointer; }

.model-field { display: flex; gap: 8px; align-items: center; }
.model-field .field-input { flex: 1; }
.fetch-models-btn {
  width: 38px; height: 38px; flex-shrink: 0;
  border: 1px solid #d0d5dd; border-radius: 10px;
  background: #fff; cursor: pointer; font-size: 16px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.fetch-models-btn:hover { background: #f3f4f6; border-color: #5b8def; }
.fetch-models-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.modal-msg { margin: 14px 0 0; font-size: 13px; font-weight: 600; }

.modal-footer {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 24px; border-top: 1px solid #f0f0f0;
}
.footer-right { display: flex; gap: 8px; }
.footer-btn {
  padding: 9px 18px; border: 1px solid #d0d5dd; border-radius: 10px;
  font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s;
  background: #fff; color: #344054;
}
.footer-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.test-footer-btn:hover { border-color: #5b8def; color: #5b8def; }
.cancel-btn:hover { background: #f3f4f6; }
.save-btn { background: #111827; color: #fff; border-color: #111827; }
.save-btn:hover { background: #1f2937; }

@media (max-width: 900px) {
  .main-content { padding: 18px 18px calc(112px + env(safe-area-inset-bottom)); }
  .page-header h1 { font-size: 28px; }
  .ocr-config-grid { grid-template-columns: 1fr; }
  .ocr-config-footer { flex-direction: column; align-items: flex-start; }
  .card-info { grid-template-columns: 1fr; }
  .info-value.truncate { max-width: 200px; }
}
</style>
