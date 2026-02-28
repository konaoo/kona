<template>
  <LegacyAdminShell title="接口策略" subtitle="运营测试台 + 策略开关">
    <section class="panel block">
      <div class="block-head">
        <div>
          <h3>快速测试</h3>
          <p class="muted">点一下就能验证数据源是否正常，适合日常巡检。</p>
        </div>
        <div class="toolbar">
          <button class="btn primary" :disabled="anyTesting" @click="runAllTests">
            {{ anyTesting ? '测试中...' : '全部测试' }}
          </button>
          <button class="btn" @click="load(true)">刷新策略</button>
        </div>
      </div>

      <div class="health-row">
        <span class="pill" :class="health.status === 'ok' ? 'ok' : 'bad'">
          总状态：{{ health.status || '-' }}
        </span>
        <span class="pill" :class="health.db?.ok ? 'ok' : 'bad'">
          数据库：{{ health.db?.ok ? '正常' : '异常' }}
        </span>
        <span class="pill" :class="upstreamOk ? 'ok' : 'bad'">
          上游：{{ upstreamOk ? '正常' : '部分异常' }}
        </span>
      </div>

      <div class="cards">
        <article class="card" v-for="provider in providers" :key="provider.key">
          <div class="card-head">
            <div>
              <h4>{{ provider.title }}</h4>
              <p class="muted">{{ provider.desc }}</p>
            </div>
            <button class="btn test-btn" :disabled="isTesting(provider.key)" @click="runProviderTest(provider.key)">
              {{ isTesting(provider.key) ? '测试中...' : '测试' }}
            </button>
          </div>

          <div class="chips">
            <span class="chip" v-for="sample in provider.samples" :key="sample">{{ sample }}</span>
          </div>

          <p class="meta" v-if="testResults[provider.key]">
            最近测试：{{ shortDateTime(testResults[provider.key]?.tested_at_utc) }} ·
            <b :class="testResults[provider.key]?.status === 'ok' ? 'up' : 'down'">
              {{ testResults[provider.key]?.status === 'ok' ? '通过' : '部分失败' }}
            </b>
          </p>
          <p class="down" v-if="testErrors[provider.key]">{{ testErrors[provider.key] }}</p>

          <div class="table-wrap" v-if="testResults[provider.key]">
            <table class="table compact" v-if="provider.kind === 'quote'">
              <thead>
                <tr>
                  <th>标的</th>
                  <th>代码</th>
                  <th>状态</th>
                  <th>最新价</th>
                  <th>涨跌幅</th>
                  <th>耗时(ms)</th>
                  <th>说明</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in testResults[provider.key]?.items || []" :key="`${provider.key}-${item.code}`">
                  <td>{{ item.name }}</td>
                  <td>{{ item.code }}</td>
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
                  <th>项目</th>
                  <th>值</th>
                  <th>状态</th>
                  <th>耗时(ms)</th>
                  <th>说明</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in testResults[provider.key]?.items || []" :key="`${provider.key}-${item.code}`">
                  <td>{{ item.name }}</td>
                  <td>{{ formatRate(item.rate) }}</td>
                  <td :class="item.ok ? 'up' : 'down'">{{ item.ok ? '成功' : '失败' }}</td>
                  <td>{{ item.latency_ms }}</td>
                  <td>{{ item.detail || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </div>
    </section>

    <section class="panel block">
      <div class="block-head">
        <div>
          <h3>策略开关</h3>
          <p class="muted">这里控制接口组和上游通道是否可用。</p>
        </div>
      </div>

      <table class="table">
        <thead>
          <tr>
            <th>策略</th>
            <th>类型</th>
            <th>状态</th>
            <th>限流(次/分钟)</th>
            <th>影响</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in policies.items || []" :key="item.scope_key">
            <td>{{ item.display_name || item.scope_key }}</td>
            <td>{{ item.scope_type_label || item.scope_type || '-' }}</td>
            <td :class="item.enabled ? 'up' : 'down'">{{ item.enabled ? '启用' : '停用' }}</td>
            <td>{{ item.limit_per_min }}</td>
            <td>{{ item.impact || '-' }}</td>
            <td>
              <button class="btn" @click="toggle(item)">{{ item.enabled ? '停用' : '启用' }}</button>
            </td>
          </tr>
          <tr v-if="!(policies.items || []).length">
            <td colspan="6" class="empty">暂无策略</td>
          </tr>
        </tbody>
      </table>
    </section>
  </LegacyAdminShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
import { api } from '../../shared/http'
import { shortDateTime } from '../../shared/format'

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

const providers: Array<{ key: ProviderKey; title: string; desc: string; kind: 'quote' | 'rate'; samples: string[] }> = [
  {
    key: 'sina_quote',
    title: '新浪行情',
    desc: '测试新浪行情通道是否可用（A股/港股/美股/基金样例）。',
    kind: 'quote',
    samples: ['腾讯 hk00700', '阿里巴巴 gb_baba', '特斯拉 gb_tsla', '宁德时代 sz300750', '场内ETF sh510300', '场外基金 f_161725'],
  },
  {
    key: 'tencent_quote',
    title: '腾讯行情',
    desc: '测试腾讯行情通道是否可用（同一批热门标的）。',
    kind: 'quote',
    samples: ['腾讯 hk00700', '阿里巴巴 gb_baba', '特斯拉 gb_tsla', '宁德时代 sz300750', '场内ETF sh510300', '场外基金 f_161725'],
  },
  {
    key: 'eastmoney_quote',
    title: '东方财富行情',
    desc: '测试东方财富通道是否可用（股票 + 基金）。',
    kind: 'quote',
    samples: ['腾讯 hk00700', '阿里巴巴 gb_baba', '特斯拉 gb_tsla', '宁德时代 sz300750', '场内ETF sh510300', '场外基金 f_161725'],
  },
  {
    key: 'forex_rate',
    title: '汇率',
    desc: '测试汇率接口，直接查看 USD/HKD/CNY。',
    kind: 'rate',
    samples: ['USD/CNY', 'HKD/CNY', 'CNY/CNY'],
  },
]

const health = reactive<Record<string, any>>({})
const policies = reactive<Record<string, any>>({ items: [] })
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

const anyTesting = computed(() => Object.values(testLoading).some(Boolean))
const upstreamOk = computed(() => {
  const upstream = health.upstream || {}
  const values = Object.values(upstream) as Array<Record<string, any>>
  if (!values.length) return true
  return values.every((item) => Boolean(item?.ok))
})

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

async function load(force = false) {
  const healthForcePart = force ? '?force=1' : ''
  const policyForcePart = force ? '&force=1' : ''
  Object.assign(health, await api.get(`/api/admin/apis/health${healthForcePart}`))
  Object.assign(policies, await api.get(`/api/admin/apis/policies?scope_type=all${policyForcePart}`))
}

async function toggle(item: Record<string, any>) {
  await api.post('/api/admin/apis/policies/update', {
    scope_key: item.scope_key,
    enabled: !item.enabled,
    limit_per_min: item.limit_per_min,
  })
  await load(true)
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

async function runAllTests() {
  for (const provider of providers) {
    await runProviderTest(provider.key)
  }
}

onMounted(() => {
  void load()
})
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
}

.block-head h3 {
  margin: 0;
  color: #264d73;
}

.muted {
  margin: 4px 0 0;
  color: #55708f;
  font-size: 13px;
}

.toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
}

.health-row {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid transparent;
}

.pill.ok {
  background: #ecfdf3;
  color: #067647;
  border-color: #9be1c0;
}

.pill.bad {
  background: #fff1f2;
  color: #b42318;
  border-color: #f4b4bd;
}

.cards {
  margin-top: 14px;
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.card {
  border: 1px solid #dbe7f4;
  border-radius: 12px;
  background: #fbfdff;
  padding: 12px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.card-head h4 {
  margin: 0;
  color: #21496f;
}

.test-btn {
  min-width: 84px;
}

.chips {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  font-size: 12px;
  line-height: 1;
  padding: 6px 8px;
  border-radius: 999px;
  color: #32597d;
  background: #eef5ff;
  border: 1px solid #d4e2f2;
}

.meta {
  margin: 10px 0 8px;
  color: #3d5f86;
  font-size: 12px;
}

.table-wrap {
  max-height: 280px;
  overflow: auto;
  border: 1px solid #e1eaf5;
  border-radius: 10px;
}

.table.compact th,
.table.compact td {
  font-size: 12px;
  padding: 8px;
}

.empty {
  text-align: center;
  color: #55708f;
  font-weight: 600;
}

@media (max-width: 1200px) {
  .cards {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .block-head {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
