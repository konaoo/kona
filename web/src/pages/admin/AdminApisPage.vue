<template>
  <div class="container admin-apis">
    <AdminConsoleNav />

    <div class="main-content">
      <div class="page-header">
        <h1>接口管理</h1>
      </div>

      <div class="card-grid">
        <section class="entry-card entry-probe">
          <div class="entry-head">
            <div class="entry-icon">🧪</div>
            <div class="entry-copy">
              <h2>股价异常排查</h2>
            </div>
          </div>
          <div class="entry-summary">
            <span>支持股票、ETF、基金</span>
          </div>
          <div class="entry-probe-form">
            <input
              v-model.trim="priceProbe.code"
              type="text"
              class="probe-input"
              placeholder=""
              @keyup.enter="openProbeModal"
            />
            <button class="primary-btn" :disabled="priceProbe.loading" @click="openProbeModal">
              {{ priceProbe.loading ? '查询中...' : '查询' }}
            </button>
          </div>
          <p v-if="priceProbe.error" class="down msg-tip">{{ priceProbe.error }}</p>
        </section>

        <button class="entry-card entry-provider" @click="openProviderModal">
          <div class="entry-head">
            <div class="entry-icon">🏥</div>
            <div class="entry-copy">
              <h2>股价行情测试</h2>
            </div>
          </div>
          <p class="entry-desc">批量检测行情源连通性和响应时间</p>
          <div class="entry-summary entry-provider-summary">
            <span class="summary-pill" :class="providerStatusBadgeClass">{{ providerStatusBadgeLabel }}</span>
            <span>最近测试 {{ providerLatestTestLabel }}</span>
          </div>
        </button>

        <button class="entry-card entry-alert" @click="openAlertModal(false)">
          <div class="entry-head">
            <div class="entry-icon">⚠️</div>
            <div class="entry-copy">
              <h2>股价异常测试</h2>
            </div>
          </div>
          <p class="entry-desc">扫描资产价格异常，发现潜在数据问题</p>
          <div class="entry-summary">
            <template v-if="priceAlerts.data">
              <span>最近巡检 {{ priceAlerts.data.report_date || '暂无' }}</span>
              <span>风险 {{ (priceAlerts.data.summary?.critical || 0) + (priceAlerts.data.summary?.warning || 0) }} 条</span>
            </template>
            <template v-else>
              <span>支持查看最近结果</span>
              <span>也可手动强制重跑</span>
            </template>
          </div>
        </button>

        <button class="entry-card entry-snapshot" @click="openSnapshotModal">
          <div class="entry-head">
            <div class="entry-icon">📋</div>
            <div class="entry-copy">
              <h2>快照任务检测</h2>
            </div>
          </div>
          <p class="entry-desc">监控每日快照任务的覆盖率和延迟情况</p>
          <div class="entry-summary">
            <template v-if="snapshotHealth.data">
              <span>今日覆盖 {{ snapshotHealth.data.today_snapshot_users }} / {{ snapshotHealth.data.total_users }}</span>
              <span>最大延迟 {{ snapshotHealth.data.max_gap_days }} 天</span>
            </template>
            <template v-else>
              <span>查看任务覆盖率</span>
              <span>点击后看明细</span>
            </template>
          </div>
        </button>
      </div>
    </div>

    <div v-if="modal.visible" class="modal-mask" @click.self="closeModal">
      <div class="modal-panel">
        <div class="modal-head">
          <div class="head-info">
            <h3>{{ modalTitle }}</h3>
            <p v-if="modalSubtitle">{{ modalSubtitle }}</p>
          </div>
          <button class="close-btn" @click="closeModal">✕</button>
        </div>

        <div class="modal-body">
          <div v-if="modal.kind === 'provider' && currentProvider">
            <div class="provider-toolbar">
              <div class="provider-tabs">
                <button
                  v-for="provider in providers"
                  :key="provider.key"
                  class="provider-tab"
                  :class="{ active: modal.providerKey === provider.key }"
                  @click="switchProvider(provider.key)"
                >
                  {{ providerTabLabel(provider.key) }}
                </button>
              </div>
              <button class="btn btn-primary" :disabled="providerBatchLoading" @click="runAllProviderTests">
                {{ providerBatchLoading ? '测试中...' : '测试' }}
              </button>
            </div>

            <div v-if="testResults[currentProvider.key]" class="table-container compact-table">
              <table class="data-table">
                <thead v-if="currentProvider.kind === 'quote'">
                  <tr>
                    <th>代码</th>
                    <th>名称</th>
                    <th>状态</th>
                    <th class="text-right">价格</th>
                    <th class="text-right">涨跌</th>
                    <th>测试时间</th>
                    <th>延迟</th>
                  </tr>
                </thead>
                <thead v-else>
                  <tr>
                    <th>代码</th>
                    <th>名称</th>
                    <th>状态</th>
                    <th class="text-right">汇率</th>
                    <th>测试时间</th>
                    <th>延迟</th>
                  </tr>
                </thead>
                <tbody v-if="currentProvider.kind === 'quote'">
                  <tr v-for="item in testResults[currentProvider.key]?.items" :key="item.code">
                    <td><code class="code-text">{{ item.code }}</code></td>
                    <td><strong>{{ item.name }}</strong></td>
                    <td><span class="dot-status" :class="providerStatusClass(item)"></span> {{ providerStatusLabel(item) }}</td>
                    <td class="text-right">{{ item.ok ? formatPrice(item.price) : '-' }}</td>
                    <td class="text-right" :class="changeClass(item.change_pct ?? 0)">{{ item.ok ? formatPct(item.change_pct ?? 0) : '-' }}</td>
                    <td><small>{{ formatProviderTestTime(testResults[currentProvider.key]?.tested_at_utc) }}</small></td>
                    <td><small>{{ item.latency_ms }}ms</small></td>
                  </tr>
                </tbody>
                <tbody v-else>
                  <tr v-for="item in testResults[currentProvider.key]?.items" :key="item.code">
                    <td><code class="code-text">{{ item.code }}</code></td>
                    <td><strong>{{ item.name }}</strong></td>
                    <td><span class="dot-status" :class="providerStatusClass(item)"></span> {{ providerStatusLabel(item) }}</td>
                    <td class="text-right">{{ formatRate(item.rate) }}</td>
                    <td><small>{{ formatProviderTestTime(testResults[currentProvider.key]?.tested_at_utc) }}</small></td>
                    <td><small>{{ item.latency_ms }}ms</small></td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else-if="providerBatchLoading || isTesting(currentProvider.key)" class="modal-loading">
              <div class="spinner"></div>
              <p>正在发起接口请求...</p>
            </div>
            <div v-else class="modal-empty">
              <p>暂未测试</p>
            </div>
            <p v-if="testErrors[currentProvider.key]" class="down msg-tip">{{ testErrors[currentProvider.key] }}</p>
          </div>

          <div v-else-if="modal.kind === 'probe'">
            <div v-if="priceProbe.loading" class="modal-loading">
              <div class="spinner"></div>
              <p>正在排查这只资产的主价和多源结果...</p>
            </div>
            <template v-else-if="priceProbe.data">
              <div class="probe-overview">
                <div class="overview-card">
                  <span class="mini-label">资产类型</span>
                  <strong>{{ priceProbe.data.asset_type_label }}</strong>
                </div>
                <div class="overview-card">
                  <span class="mini-label">系统主价</span>
                  <strong>{{ formatPrice(priceProbe.data.current.price) }}</strong>
                </div>
                <div class="overview-card">
                  <span class="mini-label">主价来源</span>
                  <strong>{{ priceProbe.data.current.source_hint || '暂未识别' }}</strong>
                </div>
                <div class="overview-card">
                  <span class="mini-label">诊断结果</span>
                  <strong :class="probeStatusClass(priceProbe.data.diagnosis.status)">
                    {{ probeStatusLabel(priceProbe.data.diagnosis.status) }}
                  </strong>
                </div>
              </div>

              <div class="diagnosis-card" :class="`diag-${priceProbe.data.diagnosis.status}`">
                <div class="diagnosis-title">系统判断</div>
                <div class="diagnosis-text">{{ priceProbe.data.diagnosis.summary }}</div>
                <div class="diagnosis-extra">
                  <span>代码：{{ priceProbe.data.code }}</span>
                  <span>昨收：{{ formatPrice(priceProbe.data.current.yclose) }}</span>
                  <span>涨跌幅：{{ formatPct(priceProbe.data.current.chg) }}</span>
                </div>
              </div>

              <div class="table-container">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>来源</th>
                      <th>状态</th>
                      <th class="text-right">价格</th>
                      <th class="text-right">涨跌幅</th>
                      <th class="text-right">偏差</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="source in priceProbe.data.sources" :key="source.source_key">
                      <td><strong>{{ source.source_label }}</strong></td>
                      <td><span class="dot-status" :class="{ ok: source.ok }"></span> {{ source.ok ? '成功' : '失败' }}</td>
                      <td class="text-right">{{ source.ok ? formatPrice(source.price) : '-' }}</td>
                      <td class="text-right" :class="changeClass(source.chg)">{{ source.ok ? formatPct(source.chg) : '-' }}</td>
                      <td class="text-right" :class="{ down: Number(source.delta_pct || 0) >= 0.5 }">
                        {{ source.ok ? formatDeltaPct(source.delta_pct) : '-' }}
                      </td>
                    </tr>
                    <tr v-if="!priceProbe.data.sources.length">
                      <td colspan="5" class="empty">当前没有可用的多源对比结果。</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>
            <p v-if="priceProbe.error" class="down msg-tip">{{ priceProbe.error }}</p>
          </div>

          <div v-else-if="modal.kind === 'snapshot'">
            <div v-if="snapshotHealth.loading" class="modal-loading">
              <div class="spinner"></div>
              <p>正在诊断今天的快照覆盖率...</p>
            </div>
            <template v-else-if="snapshotHealth.data">
              <div class="health-card">
                <div class="status-row">
                  <span class="health-badge" :class="`badge-${snapshotHealth.data.status}`">
                    {{ snapshotStatusLabel(snapshotHealth.data.status) }}
                  </span>
                  <span class="server-time">监测时间：{{ snapshotHealth.data.server_time }}</span>
                </div>
                <div class="stat-summary">
                  <div class="stat-item">
                    <label>今日覆盖</label>
                    <div class="val">{{ snapshotHealth.data.today_snapshot_users }} / {{ snapshotHealth.data.total_users }}</div>
                  </div>
                  <div class="stat-item">
                    <label>最大延迟</label>
                    <div class="val" :class="{ down: snapshotHealth.data.max_gap_days > 1 }">{{ snapshotHealth.data.max_gap_days }} 天</div>
                  </div>
                </div>
              </div>

              <div class="table-container compact-table">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>用户</th>
                      <th>状态</th>
                      <th>快照数</th>
                      <th>最近日期</th>
                      <th>延迟</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="u in snapshotHealth.data.users" :key="u.user_id">
                      <td><strong>{{ u.username || u.user_id.slice(0, 8) }}</strong></td>
                      <td>{{ u.status === 'ok' ? '✅ 正常' : u.status === 'recent' ? '🕐 近期正常' : '⚠️ 延迟' }}</td>
                      <td>{{ u.total_snapshots }}</td>
                      <td>{{ u.latest_date }}</td>
                      <td :class="{ down: u.gap_days > 1 }">{{ u.gap_days }}天</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>
            <p v-if="snapshotHealth.error" class="down msg-tip">{{ snapshotHealth.error }}</p>
          </div>

          <div v-else-if="modal.kind === 'alerts'">
            <div v-if="priceAlerts.loading" class="modal-loading">
              <div class="spinner"></div>
              <p>正在准备巡检结果...</p>
            </div>
            <template v-else-if="priceAlerts.data">
              <div class="alert-summary-grid">
                <div class="summary-card neutral">
                  <span>扫描资产</span>
                  <strong>{{ priceAlerts.data.total_assets }}</strong>
                </div>
                <div class="summary-card danger">
                  <span>严重异常</span>
                  <strong>{{ priceAlerts.data.summary?.critical || 0 }}</strong>
                </div>
                <div class="summary-card warning">
                  <span>潜在风险</span>
                  <strong>{{ priceAlerts.data.summary?.warning || 0 }}</strong>
                </div>
                <div class="summary-card success">
                  <span>缓存状态</span>
                  <strong>{{ priceAlertCacheLabel }}</strong>
                </div>
              </div>

              <div class="alert-meta">
                <span>最近巡检：{{ priceAlerts.data.report_date || '暂无' }}</span>
                <span>来源时间：{{ priceAlerts.data.tested_at_utc || '暂无' }}</span>
                <span>返回耗时：{{ priceAlerts.data.cache?.elapsed_ms ?? 0 }}ms</span>
              </div>

              <div class="table-container">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>代码</th>
                      <th>资产名称</th>
                      <th>异常类型</th>
                      <th class="text-right">当前价</th>
                      <th class="text-right">偏差</th>
                      <th>影响用户</th>
                      <th>建议处理</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in priceAlerts.data.items" :key="`${item.code}-${item.alert_type}`">
                      <td><code class="code-text">{{ item.code }}</code></td>
                      <td><strong>{{ item.name }}</strong></td>
                      <td>
                        <span class="alert-type-badge" :class="item.severity">
                          {{ alertTypeLabel(item.alert_type) }}
                        </span>
                      </td>
                      <td class="text-right">{{ formatPrice(item.current_price) }}</td>
                      <td class="text-right" :class="{ down: item.delta_pct >= 0.5 }">{{ formatDeltaPct(item.delta_pct) }}</td>
                      <td><span class="user-count">{{ item.user_count }} 人</span></td>
                      <td class="suggestion-cell">
                        <div class="reason">{{ item.reason }}</div>
                        <div class="suggestion">{{ item.suggestion }}</div>
                      </td>
                    </tr>
                    <tr v-if="!priceAlerts.data.items.length">
                      <td colspan="7" class="empty">未发现价格异常。</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>
            <p v-if="priceAlerts.error" class="down msg-tip">{{ priceAlerts.error }}</p>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">关闭</button>
          <button
            v-if="modal.kind === 'snapshot'"
            class="btn btn-primary"
            :disabled="snapshotHealth.loading"
            @click="openSnapshotModal"
          >
            {{ snapshotHealth.loading ? '诊断中...' : '重新诊断' }}
          </button>
          <button
            v-if="modal.kind === 'alerts'"
            class="btn btn-primary"
            :disabled="priceAlerts.loading"
            @click="openAlertModal(true)"
          >
            {{ priceAlerts.loading ? '巡检中...' : '强制重跑' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { api } from '../../shared/http'
import AdminConsoleNav from '../../components/admin/AdminConsoleNav.vue'

type ProviderKey = 'sina_quote' | 'tencent_quote' | 'eastmoney_quote' | 'forex_rate'
type ModalKind = 'provider' | 'probe' | 'snapshot' | 'alerts'

interface ProviderResultItem {
  code: string
  name: string
  ok: boolean
  status?: 'ok' | 'unsupported' | 'error'
  price?: number
  change_pct?: number
  rate?: number
  latency_ms: number
  detail?: string
}

interface ProviderTestResult {
  provider_key: ProviderKey
  provider_label: string
  status: 'ok' | 'degraded'
  tested_at_utc: string
  items: ProviderResultItem[]
}

interface ProviderBatchReport {
  tested_at_utc: string
  summary: {
    status: 'idle' | 'ok' | 'alert'
    label: string
    alert_keys: ProviderKey[]
  }
  providers: Partial<Record<ProviderKey, ProviderTestResult>>
}

interface ProbeSourceRow {
  source_key: string
  source_label: string
  price: number
  yclose: number
  amt: number
  chg: number
  ok: boolean
  delta_pct: number
}

interface PriceProbePayload {
  code: string
  asset_type: string
  asset_type_label: string
  current: {
    price: number
    yclose: number
    amt: number
    chg: number
    source_hint: string
  }
  sources: ProbeSourceRow[]
  diagnosis: {
    status: 'ok' | 'warning' | 'critical'
    summary: string
  }
}

const providers: Array<{ key: ProviderKey; title: string; kind: 'quote' | 'rate' }> = [
  { key: 'sina_quote', title: '新浪财经行情', kind: 'quote' },
  { key: 'eastmoney_quote', title: '东方财富行情', kind: 'quote' },
  { key: 'tencent_quote', title: '腾讯财经行情', kind: 'quote' },
  { key: 'forex_rate', title: '汇价实时汇率', kind: 'rate' },
]

const testResults = reactive<Record<ProviderKey, ProviderTestResult | null>>({
  sina_quote: null,
  tencent_quote: null,
  eastmoney_quote: null,
  forex_rate: null,
})
const testLoading = reactive<Record<ProviderKey, boolean>>({
  sina_quote: false,
  tencent_quote: false,
  eastmoney_quote: false,
  forex_rate: false,
})
const testErrors = reactive<Record<ProviderKey, string>>({
  sina_quote: '',
  tencent_quote: '',
  eastmoney_quote: '',
  forex_rate: '',
})
const providerBatchState = reactive({ loading: false })
const providerReport = reactive<{ loading: boolean; error: string; data: ProviderBatchReport | null }>({
  loading: false,
  error: '',
  data: null,
})

const modal = reactive<{ visible: boolean; kind: ModalKind; providerKey: ProviderKey }>({
  visible: false,
  kind: 'provider',
  providerKey: 'sina_quote',
})

const snapshotHealth = reactive<any>({ loading: false, error: '', data: null })
const priceAlerts = reactive<any>({ loading: false, error: '', data: null })
const priceProbe = reactive<{ code: string; loading: boolean; error: string; data: PriceProbePayload | null }>({
  code: '',
  loading: false,
  error: '',
  data: null,
})

const currentProvider = computed(
  () => providers.find((p) => p.key === modal.providerKey) || null,
)

const priceAlertCacheLabel = computed(() => {
  const state = String(priceAlerts.data?.cache?.state || '').toLowerCase()
  if (!state) return '未加载'
  if (state === 'snapshot') return '快照秒开'
  if (state === 'hit') return '缓存命中'
  if (state === 'miss') return '实时生成'
  if (state === 'bypass') return '强制重跑'
  return state
})

const providerLatestTestLabel = computed(() => {
  const raw = String(providerReport.data?.tested_at_utc || '').trim()
  if (!raw) return '暂无'
  const latest = new Date(raw)
  if (Number.isNaN(latest.getTime())) return '暂无'
  return formatMonthDayMinute(latest)
})

const providerStatusBadgeLabel = computed(() => {
  const label = String(providerReport.data?.summary?.label || '').trim()
  return label || '未测试'
})

const providerStatusBadgeClass = computed(() => {
  const status = String(providerReport.data?.summary?.status || '').trim().toLowerCase()
  if (status === 'ok') return 'ok'
  if (status === 'alert') return 'alert'
  return 'idle'
})

const modalTitle = computed(() => {
  if (modal.kind === 'provider') return '股价行情测试'
  if (modal.kind === 'probe') return '单资产价格排查'
  if (modal.kind === 'snapshot') return '快照任务监测'
  return '价格异常巡检'
})

const modalSubtitle = computed(() => {
  if (modal.kind === 'provider') return ''
  if (modal.kind === 'probe') return '这里看系统主价、主价来源和多源对比。'
  if (modal.kind === 'snapshot') return '这里看今天的快照覆盖和延迟明细。'
  return '这里看最近一次巡检结果，或强制重跑后的结果。'
})

const providerBatchLoading = computed(() => providerBatchState.loading || providers.some((provider) => testLoading[provider.key]))

function isTesting(key: ProviderKey): boolean {
  return Boolean(testLoading[key])
}

function formatPrice(value: unknown): string {
  const n = Number(value)
  if (!Number.isFinite(n) || n <= 0) return '-'
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 4 })
}

function formatPct(value: unknown): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return '-'
  const fixed = `${Math.abs(n).toFixed(2)}%`
  return n >= 0 ? `+${fixed}` : `-${fixed}`
}

function formatRate(value: unknown): string {
  const n = Number(value)
  if (!Number.isFinite(n) || n <= 0) return '-'
  return n.toFixed(4)
}

function formatDeltaPct(value: unknown): string {
  const n = Number(value)
  return Number.isFinite(n) ? `${n.toFixed(2)}%` : '-'
}

function formatMonthDayMinute(value: Date): string {
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  const hours = String(value.getHours()).padStart(2, '0')
  const minutes = String(value.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hours}:${minutes}`
}

function formatProviderTestTime(value: unknown): string {
  const raw = String(value || '').trim()
  if (!raw) return '-'
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) return '-'
  return formatMonthDayMinute(date)
}

function applyProviderReport(report: ProviderBatchReport | null) {
  providerReport.data = report
  const providerMap = report?.providers || {}
  for (const provider of providers) {
    testResults[provider.key] = providerMap[provider.key] || null
    testErrors[provider.key] = ''
  }
}

function changeClass(value: unknown) {
  const n = Number(value)
  if (!Number.isFinite(n)) return ''
  return n >= 0 ? 'up' : 'down'
}

function providerStatusLabel(item: ProviderResultItem) {
  const status = String(item.status || '').toLowerCase()
  if (status === 'unsupported') return '未支持'
  return item.ok ? '连通' : '异常'
}

function providerStatusClass(item: ProviderResultItem) {
  const status = String(item.status || '').toLowerCase()
  if (status === 'unsupported') return 'muted'
  return item.ok ? 'ok' : 'error'
}

function probeStatusLabel(status: string) {
  const labels: Record<string, string> = {
    ok: '基本正常',
    warning: '需要留意',
    critical: '优先排查',
  }
  return labels[status] || status
}

function probeStatusClass(status: string) {
  if (status === 'critical') return 'down'
  if (status === 'warning') return 'warning-text'
  return 'up'
}

function snapshotStatusLabel(status: string) {
  const labels: Record<string, string> = {
    healthy: '✅ 运行正常',
    recent: '🕐 近期正常',
    warning: '⚠️ 分钟级延迟',
    critical: '🔴 本日缺失',
  }
  return labels[status] || status
}

function alertTypeLabel(alertType: string) {
  const labels: Record<string, string> = {
    normalization: '分类异常',
    price_mismatch: '价格偏差',
    missing_price: '主价缺失',
  }
  return labels[alertType] || alertType
}

function closeModal() {
  modal.visible = false
}

function providerTabLabel(key: ProviderKey) {
  if (key === 'sina_quote') return '新浪'
  if (key === 'eastmoney_quote') return '东财'
  if (key === 'tencent_quote') return '腾讯'
  return '汇率'
}

function openProviderModal() {
  modal.visible = true
  modal.kind = 'provider'
  modal.providerKey = 'sina_quote'
}

function switchProvider(providerKey: ProviderKey) {
  modal.providerKey = providerKey
}

async function loadLatestProviderReport() {
  if (providerReport.loading) return
  providerReport.loading = true
  providerReport.error = ''
  try {
    const report = await api.get<ProviderBatchReport>('/api/admin/apis/provider_tests/latest')
    applyProviderReport(report)
  } catch (e) {
    providerReport.error = e instanceof Error ? e.message : '加载失败'
  } finally {
    providerReport.loading = false
  }
}

async function runAllProviderTests() {
  if (providerBatchLoading.value) return
  providerBatchState.loading = true
  for (const provider of providers) {
    testLoading[provider.key] = true
    testErrors[provider.key] = ''
  }
  try {
    const report = await api.post<ProviderBatchReport>('/api/admin/apis/provider_tests/run', {})
    applyProviderReport(report)
  } catch (e) {
    const message = e instanceof Error ? e.message : '测试失败'
    for (const provider of providers) {
      testErrors[provider.key] = message
    }
  } finally {
    for (const provider of providers) {
      testLoading[provider.key] = false
    }
    providerBatchState.loading = false
  }
}

async function runSnapshotHealthCheck() {
  if (snapshotHealth.loading) return
  snapshotHealth.loading = true
  snapshotHealth.error = ''
  try {
    snapshotHealth.data = await api.get('/api/admin/data/snapshot/health')
  } catch (e) {
    snapshotHealth.error = e instanceof Error ? e.message : '检测失败'
  } finally {
    snapshotHealth.loading = false
  }
}

async function openSnapshotModal() {
  modal.visible = true
  modal.kind = 'snapshot'
  if (!snapshotHealth.data) {
    await runSnapshotHealthCheck()
  } else {
    void runSnapshotHealthCheck()
  }
}

async function runPriceAlertCheck(force = false) {
  if (priceAlerts.loading) return
  priceAlerts.loading = true
  priceAlerts.error = ''
  try {
    const suffix = force ? '?force=1' : ''
    priceAlerts.data = await api.get(`/api/admin/apis/price_alerts${suffix}`)
  } catch (e) {
    priceAlerts.error = e instanceof Error ? e.message : '巡检失败'
  } finally {
    priceAlerts.loading = false
  }
}

async function openAlertModal(force = false) {
  modal.visible = true
  modal.kind = 'alerts'
  await runPriceAlertCheck(force)
}

async function runPriceProbe() {
  if (priceProbe.loading) return
  if (!priceProbe.code.trim()) {
    priceProbe.error = '请输入资产代码'
    return
  }
  priceProbe.loading = true
  priceProbe.error = ''
  try {
    priceProbe.data = await api.post<PriceProbePayload>('/api/admin/apis/price_probe', {
      code: priceProbe.code.trim(),
    })
  } catch (e) {
    priceProbe.error = e instanceof Error ? e.message : '排查失败'
  } finally {
    priceProbe.loading = false
  }
}

async function openProbeModal() {
  modal.visible = true
  modal.kind = 'probe'
  await runPriceProbe()
}

onMounted(() => {
  void loadLatestProviderReport()
  void runPriceAlertCheck(false)
  void runSnapshotHealthCheck()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.container {
  width: 100vw;
  height: 100vh;
  display: flex;
  overflow: hidden;
  background: #f5f7fb;
  color: #111827;
  font-family: 'Inter', sans-serif;
}

.sidebar {
  width: 260px;
  background: #fff;
  border-right: 1px solid #e8ecf4;
  display: flex;
  flex-direction: column;
  padding-top: 28px;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 24px;
  margin-bottom: 34px;
  color: #111827;
  font-size: 18px;
  font-weight: 800;
}

.logo-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: #111827;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 18px;
  margin: 0 12px 6px;
  border-radius: 14px;
  color: #667085;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: #f4f6fb;
  color: #111827;
}

.nav-item.active {
  background: #111827;
  color: #fff;
}

.user-profile {
  margin-top: auto;
  padding: 24px;
  border-top: 1px solid #eef2f7;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
}

.user-avatar-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: 800;
}

.user-details h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
}

.user-details p {
  margin: 4px 0 0;
  color: #98a2b3;
  font-size: 12px;
  font-weight: 600;
}

.logout-btn {
  width: 34px;
  height: 34px;
  border: 1px solid #e4e7ec;
  border-radius: 10px;
  background: #fff;
  color: #667085;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-btn:hover {
  background: #111827;
  color: #fff;
  border-color: #111827;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 22px;
}

.page-header {
  margin-bottom: 14px;
}

.page-header h1 {
  margin: 0;
  color: #111827;
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.summary-card span,
.mini-label,
.mini-stat span,
.stat-item label {
  display: block;
  color: #98a2b3;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 6px;
}

.summary-card strong,
.overview-card strong,
.mini-stat strong {
  color: #111827;
  font-size: 18px;
  font-weight: 800;
}

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

.entry-head {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
}

button.entry-card {
  width: 100%;
  cursor: pointer;
}

.entry-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 22px 48px rgba(15, 23, 42, 0.08);
  border-color: #d8dfeb;
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
}

.entry-provider .entry-icon {
  background: linear-gradient(135deg, #35d399 0%, #36a7f2 100%);
}

.entry-snapshot .entry-icon {
  background: linear-gradient(135deg, #ff9f1c 0%, #ff5d8f 100%);
}

.entry-alert .entry-icon {
  background: linear-gradient(135deg, #6f63ff 0%, #b55cff 100%);
}

.entry-probe .entry-icon {
  background: linear-gradient(135deg, #1d74e8 0%, #4f67f5 100%);
}

.entry-copy {
  min-width: 0;
  flex: 1;
}

.entry-copy h2 {
  margin: 0 0 4px;
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

.entry-copy p {
  margin: 0;
  color: #8a93a5;
  font-size: 12px;
  line-height: 1.45;
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

.summary-pill.ok {
  background: #ecfdf3;
  color: #027a48;
}

.summary-pill.alert {
  background: #fef2f2;
  color: #b42318;
}

.summary-pill.idle {
  background: #f4f7fb;
  color: #667085;
}

.entry-probe-form {
  width: 100%;
  display: flex;
  gap: 8px;
  align-items: center;
}

.probe-input {
  flex: 1;
  height: 38px;
  padding: 0 12px;
  border: 1px solid #dbe2ee;
  border-radius: 12px;
  background: #fbfcff;
  color: #111827;
  font-size: 12px;
  font-weight: 600;
  outline: none;
  transition: all 0.2s ease;
}

.probe-input::placeholder {
  color: transparent;
}

.probe-input:focus {
  border-color: #111827;
  box-shadow: 0 0 0 4px rgba(17, 24, 39, 0.06);
}

.primary-btn,
.secondary-btn,
.btn {
  border: none;
  cursor: pointer;
  font-weight: 800;
  transition: all 0.2s ease;
}

.primary-btn,
.secondary-btn {
  height: 38px;
  padding: 0 12px;
  border-radius: 12px;
  white-space: nowrap;
  font-size: 12px;
}

.primary-btn {
  background: #111827;
  color: #fff;
}

.secondary-btn {
  background: #f2f4f7;
  color: #344054;
}

.primary-btn:disabled,
.secondary-btn:disabled,
.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.alert-summary-grid,
.probe-overview,
.stat-summary {
  display: grid;
  gap: 12px;
}

.alert-summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 18px;
}

.probe-overview {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 16px;
}

.stat-summary {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 16px;
}

.summary-card.neutral {
  background: #fbfcff;
}

.summary-card.danger {
  background: #fef2f2;
}

.summary-card.warning {
  background: #fffbeb;
}

.summary-card.success {
  background: #f0fdf4;
}

.alert-meta,
.status-row,
.diagnosis-extra {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.alert-meta {
  margin-top: 14px;
  color: #98a2b3;
  font-size: 12px;
  font-weight: 700;
}

.health-card {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid #e9edf5;
  background: #fbfcff;
}

.health-badge,
.alert-type-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}

.badge-healthy {
  background: #ecfdf3;
  color: #027a48;
}

.badge-recent {
  background: #fffaeb;
  color: #b54708;
}

.badge-warning {
  background: #fff7ed;
  color: #ea580c;
}

.badge-critical {
  background: #fef2f2;
  color: #b42318;
}

.stat-item .val {
  color: #111827;
  font-size: 24px;
  font-weight: 800;
}

.diagnosis-card {
  padding: 16px 18px;
  border-radius: 18px;
  margin-bottom: 16px;
  border: 1px solid transparent;
}

.diag-ok {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.diag-warning {
  background: #fffbeb;
  border-color: #fde68a;
}

.diag-critical {
  background: #fef2f2;
  border-color: #fecaca;
}

.diagnosis-title {
  margin-bottom: 6px;
  color: #111827;
  font-size: 13px;
  font-weight: 800;
}

.diagnosis-text {
  color: #344054;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.7;
}

.table-container {
  margin-top: 14px;
  overflow: hidden;
  border: 1px solid #e8ecf4;
  border-radius: 18px;
  background: #fff;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: #f8fafc;
}

.data-table th {
  padding: 14px 18px;
  text-align: left;
  border-bottom: 1px solid #e8ecf4;
  color: #667085;
  font-size: 12px;
  font-weight: 800;
}

.data-table td {
  padding: 16px 18px;
  border-bottom: 1px solid #f1f5f9;
  color: #344054;
  font-size: 14px;
  vertical-align: top;
}

.compact-table .data-table td,
.compact-table .data-table th {
  padding: 12px 16px;
}

.text-right {
  text-align: right !important;
}

.code-text {
  padding: 4px 8px;
  border-radius: 8px;
  background: #f2f4f7;
  color: #111827;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  font-weight: 700;
}

.alert-type-badge.critical {
  background: #fee4e2;
  color: #b42318;
}

.alert-type-badge.warning {
  background: #fef0c7;
  color: #b54708;
}

.alert-type-badge.info {
  background: #dbeafe;
  color: #1d4ed8;
}

.dot-status {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 6px;
  border-radius: 50%;
  background: #ef4444;
}

.dot-status.ok {
  background: #22c55e;
}

.dot-status.error {
  background: #ef4444;
}

.dot-status.muted {
  background: #cbd5e1;
}

.user-count,
.suggestion {
  color: #667085;
  font-size: 13px;
  font-weight: 700;
}

.reason {
  margin-bottom: 4px;
  color: #111827;
  font-size: 13px;
  font-weight: 800;
}

.suggestion-cell {
  max-width: 360px;
}

.modal-mask {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(4px);
}

.modal-panel {
  width: min(1120px, 100%);
  max-height: 88vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 30px 80px rgba(15, 23, 42, 0.2);
}

.modal-head,
.modal-footer {
  padding: 22px 28px;
}

.modal-head {
  border-bottom: 1px solid #eef2f7;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.head-info h3 {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 800;
  color: #111827;
}

.head-info p {
  margin: 0;
  color: #98a2b3;
  font-size: 12px;
  font-weight: 700;
}

.close-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: none;
  background: #f2f4f7;
  color: #475467;
  cursor: pointer;
}

.close-btn:hover {
  background: #111827;
  color: #fff;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
}

.provider-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.provider-tabs {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  border-radius: 16px;
  background: #f4f6fb;
}

.provider-tab {
  height: 38px;
  padding: 0 18px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: #667085;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
}

.provider-tab.active {
  background: #111827;
  color: #fff;
}

.provider-tab:hover:not(.active) {
  background: #e8edf5;
  color: #111827;
}

.modal-loading {
  padding: 60px 0;
  text-align: center;
  color: #98a2b3;
}

.modal-empty {
  padding: 72px 0;
  text-align: center;
  color: #98a2b3;
  font-size: 16px;
  font-weight: 700;
}

.spinner {
  width: 30px;
  height: 30px;
  margin: 0 auto 14px;
  border: 3px solid #e5e7eb;
  border-top-color: #111827;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background: #fbfcff;
  border-top: 1px solid #eef2f7;
}

.btn {
  height: 44px;
  padding: 0 18px;
  border-radius: 14px;
}

.btn-primary {
  background: #111827;
  color: #fff;
}

.btn-secondary {
  background: #f2f4f7;
  color: #475467;
}

.up {
  color: #12b76a;
}

.down {
  color: #f04438;
}

.warning-text {
  color: #f79009;
}

.msg-tip {
  margin-top: 12px;
  font-size: 13px;
  font-weight: 700;
}

.empty {
  padding: 28px !important;
  text-align: center;
  color: #98a2b3 !important;
  font-weight: 700;
}

@media (max-width: 1200px) {
  .card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .probe-overview,
  .alert-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 920px) {
  .sidebar {
    display: none;
  }

  .main-content {
    padding: 18px 18px calc(112px + env(safe-area-inset-bottom));
  }

  .page-header {
    margin-bottom: 12px;
  }

  .page-header h1 {
    font-size: 28px;
  }

  .card-grid {
    grid-template-columns: 1fr;
  }

  .provider-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .provider-tabs {
    width: 100%;
    overflow-x: auto;
  }

  .entry-card {
    min-height: 0;
    padding: 20px;
    border-radius: 20px;
    gap: 14px;
  }

  .entry-head {
    align-items: flex-start;
  }

  .entry-icon {
    width: 64px;
    height: 64px;
    border-radius: 16px;
    font-size: 28px;
  }

  .entry-copy h2 {
    font-size: 20px;
  }

  .entry-copy p {
    font-size: 13px;
  }

  .entry-probe-form {
    flex-direction: column;
    align-items: stretch;
  }

  .probe-overview,
  .alert-summary-grid,
  .stat-summary {
    grid-template-columns: 1fr;
  }
}
</style>
