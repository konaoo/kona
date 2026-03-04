<template>
  <LegacyAdminShell title="接口管理" subtitle="接口测试">
    <AdminCard class="block" variant="surface">
      <AdminSectionHeader title="接口测试" subtitle="逐个接口测试，结果在弹窗里查看明细" />
      <AdminTable>
        <thead>
          <tr>
            <th>接口名称</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="provider in providers" :key="provider.key">
            <td>{{ provider.title }}</td>
            <td>
              <AdminButton :disabled="isTesting(provider.key)" pill @click="openTestModal(provider.key)">
                {{ isTesting(provider.key) ? '测试中...' : '测试' }}
              </AdminButton>
            </td>
          </tr>
        </tbody>
      </AdminTable>
    </AdminCard>

    <!-- 快照定时任务健康检查 -->
    <AdminCard class="block" variant="surface">
      <AdminSectionHeader title="快照定时任务" subtitle="检测 cron 定时快照是否正常运行" />
      <div class="snapshot-actions">
        <AdminButton :disabled="snapshotHealth.loading" pill @click="runSnapshotHealthCheck">
          {{ snapshotHealth.loading ? '检测中...' : '检测' }}
        </AdminButton>
        <span v-if="snapshotHealth.data" :class="['snapshot-badge', `badge-${snapshotHealth.data.status}`]">
          {{ snapshotStatusLabel(snapshotHealth.data.status) }}
        </span>
      </div>
      <p v-if="snapshotHealth.error" class="down" style="margin-top:8px">{{ snapshotHealth.error }}</p>
      <div v-if="snapshotHealth.data" class="snapshot-result">
        <div class="snapshot-summary">
          <div class="summary-item">
            <span class="summary-label">服务器时间</span>
            <span class="summary-value">{{ snapshotHealth.data.server_time }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">今日快照覆盖</span>
            <span class="summary-value">{{ snapshotHealth.data.today_snapshot_users }} / {{ snapshotHealth.data.total_users }} 用户</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">最大间隔天数</span>
            <span class="summary-value" :class="snapshotHealth.data.max_gap_days > 1 ? 'down' : ''">{{ snapshotHealth.data.max_gap_days }} 天</span>
          </div>
        </div>
        <AdminButton v-if="snapshotHealth.data.users.length" variant="secondary" soft pill style="margin:12px 0 8px" @click="snapshotHealth.showUsers = !snapshotHealth.showUsers">
          {{ snapshotHealth.showUsers ? '收起用户明细' : '展开用户明细' }} ({{ snapshotHealth.data.users.length }})
        </AdminButton>
        <AdminTable v-if="snapshotHealth.showUsers" compact>
          <thead>
            <tr>
              <th>用户名</th>
              <th>状态</th>
              <th>快照总数</th>
              <th>最早日期</th>
              <th>最新日期</th>
              <th>间隔(天)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in snapshotHealth.data.users" :key="u.user_id">
              <td>{{ u.username || u.user_id.slice(0, 8) }}</td>
              <td :class="u.status === 'ok' ? 'up' : u.status === 'recent' ? '' : 'down'">
                {{ u.status === 'ok' ? '✅ 正常' : u.status === 'recent' ? '🕐 近期' : '⚠️ 过期' }}
              </td>
              <td>{{ u.total_snapshots }}</td>
              <td>{{ u.earliest_date }}</td>
              <td>{{ u.latest_date }}</td>
              <td :class="u.gap_days > 1 ? 'down' : ''">{{ u.gap_days }}</td>
            </tr>
          </tbody>
        </AdminTable>
      </div>
    </AdminCard>

    <div v-if="modal.visible && currentProvider" class="detail-mask" @click.self="closeModal">
      <AdminCard class="detail-panel" variant="surface">
        <div class="detail-head">
          <h3>{{ currentProvider.title }} - 测试</h3>
          <div class="detail-actions">
            <AdminButton
              :disabled="isTesting(currentProvider.key)"
              pill
              @click="runProviderTest(currentProvider.key)"
            >
              {{ isTesting(currentProvider.key) ? '测试中...' : '重新测试' }}
            </AdminButton>
            <AdminButton variant="secondary" soft pill :disabled="isTesting(currentProvider.key)" @click="closeModal">
              关闭
            </AdminButton>
          </div>
        </div>

        <p v-if="testErrors[currentProvider.key]" class="down">{{ testErrors[currentProvider.key] }}</p>

        <div v-if="testResults[currentProvider.key]">
          <AdminTable compact v-if="currentProvider.kind === 'quote'">
            <thead>
              <tr>
                <th>代码</th>
                <th>名称</th>
                <th>状态</th>
                <th>最新价</th>
                <th>涨跌幅</th>
                <th>耗时(ms)</th>
                <th>说明</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in testResults[currentProvider.key]?.items || []" :key="`${currentProvider.key}-${item.code}`">
                <td>{{ item.code }}</td>
                <td>{{ item.name }}</td>
                <td :class="item.ok ? 'up' : 'down'">{{ item.ok ? '成功' : '失败' }}</td>
                <td>{{ item.ok ? formatPrice(item.price) : '-' }}</td>
                <td :class="Number(item.change_pct ?? 0) >= 0 ? 'up' : 'down'">
                  {{ item.ok ? formatPct(item.change_pct ?? 0) : '-' }}
                </td>
                <td>{{ item.latency_ms }}</td>
                <td>{{ item.detail || '-' }}</td>
              </tr>
            </tbody>
          </AdminTable>

          <AdminTable compact v-else>
            <thead>
              <tr>
                <th>代码</th>
                <th>名称</th>
                <th>状态</th>
                <th>最新价</th>
                <th>耗时(ms)</th>
                <th>说明</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in testResults[currentProvider.key]?.items || []" :key="`${currentProvider.key}-${item.code}`">
                <td>{{ item.code }}</td>
                <td>{{ item.name }}</td>
                <td :class="item.ok ? 'up' : 'down'">{{ item.ok ? '成功' : '失败' }}</td>
                <td>{{ formatRate(item.rate) }}</td>
                <td>{{ item.latency_ms }}</td>
                <td>{{ item.detail || '-' }}</td>
              </tr>
            </tbody>
          </AdminTable>
        </div>

        <p v-else class="muted">{{ isTesting(currentProvider.key) ? '测试中...' : '暂无测试结果' }}</p>
      </AdminCard>
    </div>
  </LegacyAdminShell>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
import AdminCard from '../../components/admin/ui/AdminCard.vue'
import AdminButton from '../../components/admin/ui/AdminButton.vue'
import AdminTable from '../../components/admin/ui/AdminTable.vue'
import AdminSectionHeader from '../../components/admin/ui/AdminSectionHeader.vue'
import { api } from '../../shared/http'

type ProviderKey = 'sina_quote' | 'tencent_quote' | 'eastmoney_quote' | 'forex_rate'

interface ProviderResultItem {
  code: string
  name: string
  ok: boolean
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

const providers: Array<{ key: ProviderKey; title: string; kind: 'quote' | 'rate' }> = [
  { key: 'sina_quote', title: '新浪财经行情', kind: 'quote' },
  { key: 'tencent_quote', title: '腾讯财经行情', kind: 'quote' },
  { key: 'eastmoney_quote', title: '东方财富行情', kind: 'quote' },
  { key: 'forex_rate', title: '汇率', kind: 'rate' },
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

const modal = reactive<{ visible: boolean; providerKey: ProviderKey }>({
  visible: false,
  providerKey: 'sina_quote',
})

const currentProvider = computed(
  () => providers.find((provider) => provider.key === modal.providerKey) || null,
)

function isTesting(key: ProviderKey): boolean {
  return Boolean(testLoading[key])
}

function formatPrice(value: unknown): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return '-'
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
  if (!Number.isFinite(n)) return '-'
  return n.toFixed(6)
}

async function runProviderTest(providerKey: ProviderKey) {
  if (testLoading[providerKey]) return
  testLoading[providerKey] = true
  testErrors[providerKey] = ''
  try {
    testResults[providerKey] = await api.post<ProviderTestResult>('/api/admin/apis/provider_test', {
      provider_key: providerKey,
    })
  } catch (e) {
    testErrors[providerKey] = e instanceof Error ? e.message : '测试失败'
  } finally {
    testLoading[providerKey] = false
  }
}

function openTestModal(providerKey: ProviderKey) {
  modal.visible = true
  modal.providerKey = providerKey
  if (!testResults[providerKey]) {
    void runProviderTest(providerKey)
  }
}

function closeModal() {
  modal.visible = false
}

// --- 快照健康检查 ---
interface SnapshotUserHealth {
  user_id: string
  username: string
  total_snapshots: number
  earliest_date: string
  latest_date: string
  last_updated_at: string
  gap_days: number
  has_today: boolean
  status: 'ok' | 'recent' | 'stale'
}

interface SnapshotHealthData {
  status: 'healthy' | 'recent' | 'warning' | 'critical'
  server_time: string
  today: string
  today_snapshot_users: number
  total_users: number
  max_gap_days: number
  users: SnapshotUserHealth[]
}

const snapshotHealth = reactive<{
  loading: boolean
  error: string
  data: SnapshotHealthData | null
  showUsers: boolean
}>({
  loading: false,
  error: '',
  data: null,
  showUsers: false,
})

function snapshotStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    healthy: '✅ 正常运行',
    recent: '🕐 近期正常',
    warning: '⚠️ 有延迟',
    critical: '🔴 异常',
  }
  return labels[status] || status
}

async function runSnapshotHealthCheck() {
  if (snapshotHealth.loading) return
  snapshotHealth.loading = true
  snapshotHealth.error = ''
  try {
    snapshotHealth.data = await api.get<SnapshotHealthData>('/api/admin/data/snapshot/health')
  } catch (e) {
    snapshotHealth.error = e instanceof Error ? e.message : '检测失败'
  } finally {
    snapshotHealth.loading = false
  }
}
</script>

<style scoped>
.block {
  padding: 16px;
  margin-bottom: 16px;
}

.detail-mask {
  position: fixed;
  inset: 0;
  background: rgba(7, 18, 33, 0.58);
  display: grid;
  place-items: center;
  z-index: 90;
  padding: 16px;
}

.detail-panel {
  width: min(1200px, 100%);
  max-height: min(86vh, 860px);
  overflow: auto;
  padding: 14px;
}

.detail-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.detail-head h3 {
  margin: 0;
  color: #1f252b;
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.muted {
  margin: 0;
  color: #8a939c;
  font-size: 13px;
}

.snapshot-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}

.snapshot-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.badge-healthy { background: #e6f9ee; color: #0d7a3e; }
.badge-recent  { background: #e8f4fd; color: #1a6fb5; }
.badge-warning { background: #fff8e1; color: #b5850a; }
.badge-critical { background: #fde8e8; color: #c0392b; }

.snapshot-result {
  margin-top: 12px;
}

.snapshot-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 8px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 140px;
}

.summary-label {
  font-size: 12px;
  color: #8a939c;
}

.summary-value {
  font-size: 14px;
  font-weight: 500;
  color: #1f252b;
}

.up {
  color: var(--success);
}

.down {
  color: var(--danger);
}

@media (max-width: 900px) {
  .detail-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .detail-actions {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
