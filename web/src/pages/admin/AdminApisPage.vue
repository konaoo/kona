<template>
  <LegacyAdminShell title="接口策略" subtitle="接口测试">
    <section class="panel block">
      <div class="block-head">
        <div>
          <h3>接口测试</h3>
        </div>
      </div>

      <table class="table provider-table">
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
              <button class="btn" :disabled="isTesting(provider.key)" @click="openTestModal(provider.key)">
                {{ isTesting(provider.key) ? '测试中...' : '测试' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <div v-if="modal.visible && currentProvider" class="detail-mask" @click.self="closeModal">
      <section class="panel detail-panel">
        <div class="detail-head">
          <h3>{{ currentProvider.title }} - 测试</h3>
          <div class="detail-actions">
            <button
              class="btn"
              :disabled="isTesting(currentProvider.key)"
              @click="runProviderTest(currentProvider.key)"
            >
              {{ isTesting(currentProvider.key) ? '测试中...' : '重新测试' }}
            </button>
            <button class="btn ghost" :disabled="isTesting(currentProvider.key)" @click="closeModal">关闭</button>
          </div>
        </div>

        <p v-if="testErrors[currentProvider.key]" class="down">{{ testErrors[currentProvider.key] }}</p>

        <div v-if="testResults[currentProvider.key]" class="table-wrap">
          <table class="table compact" v-if="currentProvider.kind === 'quote'">
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
          </table>

          <table class="table compact" v-else>
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
          </table>
        </div>

        <p v-else class="muted">{{ isTesting(currentProvider.key) ? '测试中...' : '暂无测试结果' }}</p>
      </section>
    </div>
  </LegacyAdminShell>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
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
</script>

<style scoped>
.block {
  padding: 16px;
  margin-bottom: 16px;
}

.block-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.block-head h3 {
  margin: 0;
  color: #264d73;
}

.provider-table td:last-child,
.provider-table th:last-child {
  width: 140px;
}

.table-wrap {
  max-height: 480px;
  overflow: auto;
  border: 1px solid #e1eaf5;
  border-radius: 10px;
}

.table.compact th,
.table.compact td {
  font-size: 12px;
  padding: 8px;
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
  color: #24496e;
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.btn.ghost {
  background: transparent;
  color: #35557d;
  border: 1px solid #c8d6e7;
  box-shadow: none;
}

.muted {
  margin: 0;
  color: #55708f;
  font-size: 13px;
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
  }

  .detail-actions .btn {
    width: 100%;
  }
}
</style>
