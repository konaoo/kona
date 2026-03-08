<template>
  <div class="container admin-apis">
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
          <h1>接口管理</h1>
        </div>
      </div>

      <div class="api-grid">
        <!-- API Test List -->
        <div class="config-section">
          <div class="section-top">
            <div class="top-info">
              <h2>行情与汇率接口测试</h2>
              <p>检测第三方数据源接口是否连通</p>
            </div>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>接口提供商</th>
                  <th class="text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="provider in providers" :key="provider.key">
                  <td><strong>{{ provider.title }}</strong></td>
                  <td class="text-right">
                    <button class="test-btn" :disabled="isTesting(provider.key)" @click="openTestModal(provider.key)">
                      {{ isTesting(provider.key) ? '测试中...' : '立即测试' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Snapshot Health Check -->
        <div class="config-section">
          <div class="section-top">
            <div class="top-info">
              <h2>快照任务监测</h2>
              <p>监测 Cron 定时快照覆盖率及延迟</p>
            </div>
            <button class="run-btn" :disabled="snapshotHealth.loading" @click="runSnapshotHealthCheck">
              {{ snapshotHealth.loading ? '正在诊断...' : '快照健康诊断' }}
            </button>
          </div>
          
          <div v-if="snapshotHealth.data" class="health-card">
            <div class="status-row">
               <span class="health-badge" :class="`badge-${snapshotHealth.data.status}`">
                 {{ snapshotStatusLabel(snapshotHealth.data.status) }}
               </span>
               <span class="server-time">监测时间: {{ snapshotHealth.data.server_time }}</span>
            </div>
            <div class="stat-summary">
               <div class="stat-item">
                 <label>今日快照覆盖</label>
                 <div class="val">{{ snapshotHealth.data.today_snapshot_users }} / {{ snapshotHealth.data.total_users }} <small>用户</small></div>
               </div>
               <div class="stat-item">
                 <label>最大延迟天数</label>
                 <div class="val" :class="{ 'down': snapshotHealth.data.max_gap_days > 1 }">{{ snapshotHealth.data.max_gap_days }} <small>天</small></div>
               </div>
            </div>
            <button class="detail-toggle" @click="snapshotHealth.showUsers = !snapshotHealth.showUsers">
              {{ snapshotHealth.showUsers ? '收起用户列表 ▲' : `查看 ${snapshotHealth.data.users.length} 名用户明细 ▼` }}
            </button>
          </div>

          <div v-if="snapshotHealth.showUsers" class="table-container compact-table">
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
                  <td>
                    <span class="status-indicator" :class="u.status">
                      {{ u.status === 'ok' ? '✅' : u.status === 'recent' ? '🕐' : '⚠️' }}
                    </span>
                  </td>
                  <td>{{ u.total_snapshots }}</td>
                  <td>{{ u.latest_date }}</td>
                  <td :class="{ 'down': u.gap_days > 1 }">{{ u.gap_days }}天</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="snapshotHealth.error" class="down msg-tip">{{ snapshotHealth.error }}</p>
        </div>
      </div>

      <!-- Price Alerts Section -->
      <div class="price-alert-section">
         <div class="section-top">
            <div class="top-info">
              <h2>价格异常巡检</h2>
              <p>全局扫描持仓价格偏差、主价缺失、或是分类错误的资产</p>
            </div>
            <button class="run-btn alert-run" :disabled="priceAlerts.loading" @click="runPriceAlertCheck(true)">
              {{ priceAlerts.loading ? '正在扫描...' : '运行全局巡检' }}
            </button>
          </div>

          <div v-if="priceAlerts.data" class="alert-dashboard">
             <div class="alert-summary">
                <div class="summary-pill total">
                   <span class="label">扫描资产</span>
                   <span class="value">{{ priceAlerts.data.total_assets }}</span>
                </div>
                <div class="summary-pill critical" v-if="priceAlerts.data.summary.critical">
                   <span class="label">严重异常</span>
                   <span class="value">{{ priceAlerts.data.summary.critical }}</span>
                </div>
                <div class="summary-pill warning" v-if="priceAlerts.data.summary.warning">
                   <span class="label">潜在风险</span>
                   <span class="value">{{ priceAlerts.data.summary.warning }}</span>
                </div>
                <div class="summary-pill healthy" v-if="!priceAlerts.data.alert_count">
                   <span class="label">巡检状态</span>
                   <span class="value">未发现问题</span>
                </div>
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
                     <td class="text-right" :class="{ 'down': item.delta_pct >= 0.5 }">{{ formatDeltaPct(item.delta_pct) }}</td>
                     <td><span class="user-count">{{ item.user_count }} 人</span></td>
                     <td class="suggestion-cell">
                       <div class="reason">{{ item.reason }}</div>
                       <div class="suggestion">{{ item.suggestion }}</div>
                     </td>
                   </tr>
                   <tr v-if="!priceAlerts.data.items.length">
                     <td colspan="7" class="empty">🎉 全球资产价格暂无异常。</td>
                   </tr>
                 </tbody>
               </table>
             </div>
          </div>
          <p v-if="priceAlerts.error" class="down msg-tip">{{ priceAlerts.error }}</p>
      </div>
    </div>

    <!-- Test Result Modal -->
    <div v-if="modal.visible && currentProvider" class="modal-mask" @click.self="closeModal">
      <div class="modal-panel">
        <div class="modal-head">
          <div class="head-info">
             <h3>{{ currentProvider.title }} 测试</h3>
             <p v-if="testResults[currentProvider.key]">测得 {{ testResults[currentProvider.key]?.items.length }} 条样本</p>
          </div>
          <button class="close-btn" @click="closeModal">✕</button>
        </div>

        <div class="modal-body">
           <div v-if="testResults[currentProvider.key]">
              <div class="table-container compact-table">
                <table class="data-table">
                   <thead v-if="currentProvider.kind === 'quote'">
                    <tr>
                      <th>代码</th>
                      <th>名称</th>
                      <th>状态</th>
                      <th class="text-right">价格</th>
                      <th class="text-right">涨跌</th>
                      <th>延迟</th>
                    </tr>
                  </thead>
                  <thead v-else>
                    <tr>
                      <th>代码</th>
                      <th>名称</th>
                      <th>状态</th>
                      <th class="text-right">汇率</th>
                      <th>延迟</th>
                    </tr>
                  </thead>
                  
                  <tbody v-if="currentProvider.kind === 'quote'">
                    <tr v-for="item in testResults[currentProvider.key]?.items" :key="item.code">
                      <td><code class="code-text">{{ item.code }}</code></td>
                      <td><strong>{{ item.name }}</strong></td>
                      <td><span class="dot-status" :class="{ 'ok': item.ok }"></span> {{ item.ok ? '连通' : '异常' }}</td>
                      <td class="text-right">{{ item.ok ? formatPrice(item.price) : '-' }}</td>
                      <td class="text-right" :class="Number(item.change_pct ?? 0) >= 0 ? 'up' : 'down'">
                        {{ item.ok ? formatPct(item.change_pct ?? 0) : '-' }}
                      </td>
                      <td><small>{{ item.latency_ms }}ms</small></td>
                    </tr>
                  </tbody>
                  <tbody v-else>
                    <tr v-for="item in testResults[currentProvider.key]?.items" :key="item.code">
                      <td><code class="code-text">{{ item.code }}</code></td>
                      <td><strong>{{ item.name }}</strong></td>
                      <td><span class="dot-status" :class="{ 'ok': item.ok }"></span> {{ item.ok ? '连通' : '异常' }}</td>
                      <td class="text-right">{{ formatRate(item.rate) }}</td>
                      <td><small>{{ item.latency_ms }}ms</small></td>
                    </tr>
                  </tbody>
                </table>
              </div>
           </div>
           <div v-else class="modal-loading">
              <div class="spinner"></div>
              <p>{{ isTesting(currentProvider.key) ? '正在发起接口请求...' : '暂无数据' }}</p>
           </div>
           <p v-if="testErrors[currentProvider.key]" class="down msg-tip">{{ testErrors[currentProvider.key] }}</p>
        </div>

        <div class="modal-footer">
           <button class="btn btn-secondary" @click="closeModal">关闭</button>
           <button class="btn btn-primary" :disabled="isTesting(currentProvider.key)" @click="runProviderTest(currentProvider.key)">
             {{ isTesting(currentProvider.key) ? '测试中...' : '重新发起测试' }}
           </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../shared/http'
import { useKonaStore } from '../../stores/composables'

const router = useRouter()
const store = useKonaStore()

type ProviderKey = 'sina_quote' | 'tencent_quote' | 'eastmoney_quote' | 'forex_rate'

interface ProviderResultItem {
  code: string; name: string; ok: boolean; price?: number; change_pct?: number; rate?: number; latency_ms: number; detail?: string
}

interface ProviderTestResult {
  provider_key: ProviderKey; provider_label: string; status: 'ok' | 'degraded'; tested_at_utc: string; items: ProviderResultItem[]
}

const providers: Array<{ key: ProviderKey; title: string; kind: 'quote' | 'rate' }> = [
  { key: 'sina_quote', title: '新浪财经行情', kind: 'quote' },
  { key: 'tencent_quote', title: '腾讯财经行情', kind: 'quote' },
  { key: 'eastmoney_quote', title: '东方财富行情', kind: 'quote' },
  { key: 'forex_rate', title: '汇价实时汇率', kind: 'rate' },
]

const testResults = reactive<Record<ProviderKey, ProviderTestResult | null>>({
  sina_quote: null, tencent_quote: null, eastmoney_quote: null, forex_rate: null,
})
const testLoading = reactive<Record<ProviderKey, boolean>>({
  sina_quote: false, tencent_quote: false, eastmoney_quote: false, forex_rate: false,
})
const testErrors = reactive<Record<ProviderKey, string>>({
  sina_quote: '', tencent_quote: '', eastmoney_quote: '', forex_rate: '',
})

const modal = reactive<{ visible: boolean; providerKey: ProviderKey }>({
  visible: false, providerKey: 'sina_quote',
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

const currentProvider = computed(
  () => providers.find((p) => p.key === modal.providerKey) || null,
)

function isTesting(key: ProviderKey): boolean { return Boolean(testLoading[key]); }

function formatPrice(value: unknown): string {
  const n = Number(value); if (!Number.isFinite(n)) return '-';
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
}

function formatPct(value: unknown): string {
  const n = Number(value); if (!Number.isFinite(n)) return '-';
  const fixed = `${Math.abs(n).toFixed(2)}%`; return n >= 0 ? `+${fixed}` : `-${fixed}`;
}

function formatRate(value: unknown): string {
  const n = Number(value); if (!Number.isFinite(n)) return '-';
  return n.toFixed(4);
}

async function runProviderTest(providerKey: ProviderKey) {
  if (testLoading[providerKey]) return;
  testLoading[providerKey] = true; testErrors[providerKey] = '';
  try {
    testResults[providerKey] = await api.post<ProviderTestResult>('/api/admin/apis/provider_test', { provider_key: providerKey })
  } catch (e) {
    testErrors[providerKey] = e instanceof Error ? e.message : '测试失败'
  } finally {
    testLoading[providerKey] = false
  }
}

function openTestModal(providerKey: ProviderKey) {
  modal.visible = true; modal.providerKey = providerKey;
  if (!testResults[providerKey]) { void runProviderTest(providerKey); }
}

function closeModal() { modal.visible = false; }

// --- Health Check ---
const snapshotHealth = reactive<any>({ loading: false, error: '', data: null, showUsers: false })
const priceAlerts = reactive<any>({ loading: false, error: '', data: null })

function snapshotStatusLabel(status: string) {
  const labels: any = { healthy: '✅ 运行正常', recent: '🕐 近期正常', warning: '⚠️ 分钟级延迟', critical: '🔴 本日缺失' }
  return labels[status] || status
}

async function runSnapshotHealthCheck() {
  if (snapshotHealth.loading) return; snapshotHealth.loading = true; snapshotHealth.error = '';
  try {
    snapshotHealth.data = await api.get('/api/admin/data/snapshot/health')
  } catch (e) {
    snapshotHealth.error = e instanceof Error ? e.message : '检测失败'
  } finally {
    snapshotHealth.loading = false
  }
}

function alertTypeLabel(alertType: string) {
  const labels: any = { normalization: '分类异常', price_mismatch: '价格偏差', missing_price: '主价缺失' }
  return labels[alertType] || alertType
}

function formatDeltaPct(value: unknown) {
  const n = Number(value); return Number.isFinite(n) ? `${n.toFixed(2)}%` : '-'
}

async function runPriceAlertCheck(force = false) {
  if (priceAlerts.loading) return; priceAlerts.loading = true; priceAlerts.error = '';
  try {
    const suffix = force ? '?force=1' : '';
    priceAlerts.data = await api.get(`/api/admin/apis/price_alerts${suffix}`)
  } catch (e) {
    priceAlerts.error = e instanceof Error ? e.message : '巡检失败'
  } finally {
    priceAlerts.loading = false
  }
}

async function onLogout() { await store.logout(); await router.push('/admin/login'); }

onMounted(() => { void runPriceAlertCheck(false); })
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
.header { margin-bottom: 35px; }
.header-title h1 { font-size: 32px; font-weight: 800; margin-bottom: 6px; color: #000; letter-spacing: -0.8px; }

.api-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
.config-section { background: white; border-radius: 20px; border: 1px solid #f0f0f0; padding: 24px; }
.section-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 16px; }
.top-info h2 { font-size: 19px; font-weight: 800; color: #000; margin: 0 0 6px 0; }
.top-info p { font-size: 13.5px; color: #888; margin: 0; }

.run-btn { height: 40px; padding: 0 16px; background: #000; color: #fff; border: none; border-radius: 10px; font-weight: 700; cursor: pointer; font-size: 13.5px; white-space: nowrap; }
.run-btn:disabled { opacity: 0.5; }

.test-btn { height: 34px; padding: 0 14px; background: #f5f5f5; border: 1px solid #eee; border-radius: 8px; color: #666; font-weight: 700; font-size: 12px; cursor: pointer; }
.test-btn:hover:not(:disabled) { background: #000; color: #fff; border-color: #000; }

/* Status Cards & Badges */
.health-card { background: #fdfdfd; border: 1px solid #f0f0f0; border-radius: 14px; padding: 16px; margin-bottom: 12px; }
.status-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.health-badge { font-size: 12px; font-weight: 800; padding: 4px 12px; border-radius: 10px; }
.badge-healthy { background: #e6f9ee; color: #10b981; }
.badge-recent { background: #fdf6ec; color: #e6a23c; }
.badge-warning { background: #fff1f0; color: #f5222d; }
.badge-critical { background: #000; color: #fff; }
.server-time { font-size: 11px; color: #aaa; font-weight: 600; }

.stat-summary { display: flex; gap: 24px; margin-bottom: 15px; }
.stat-item label { display: block; font-size: 11px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 4px; }
.stat-item .val { font-size: 20px; font-weight: 800; color: #000; }
.stat-item .val small { font-size: 12px; color: #aaa; margin-left: 2px; }

.detail-toggle { width: 100%; height: 34px; border: 1px dashed #eee; background: transparent; border-radius: 8px; color: #999; font-weight: 700; font-size: 12px; cursor: pointer; }
.detail-toggle:hover { color: #000; border-color: #ddd; }

/* Price Alert Section */
.price-alert-section { background: white; border-radius: 20px; border: 1px solid #f0f0f0; padding: 24px; }
.alert-dashboard { margin-top: 10px; }
.alert-summary { display: flex; gap: 12px; margin-bottom: 20px; overflow-x: auto; padding-bottom: 5px; }
.summary-pill { padding: 10px 18px; border-radius: 12px; display: flex; flex-direction: column; gap: 2px; min-width: 100px; }
.summary-pill.total { background: #f8f9fa; border: 1px solid #f0f0f0; }
.summary-pill.critical { background: #fff1f0; border: 1px solid #ffa39e; }
.summary-pill.critical .value { color: #f5222d; }
.summary-pill.warning { background: #fffbe6; border: 1px solid #ffe58f; }
.summary-pill.healthy { background: #f6ffed; border: 1px solid #b7eb8f; }
.summary-pill.healthy .value { color: #52c41a; }
.summary-pill .label { font-size: 10px; font-weight: 800; color: #999; text-transform: uppercase; }
.summary-pill .value { font-size: 19px; font-weight: 800; color: #000; }

/* Table Sync */
.table-container { border: 1px solid #edeef1; border-radius: 16px; overflow: hidden; margin-bottom: 12px; }
.compact-table .data-table td { padding: 12px 20px; font-size: 13.5px; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table thead { background: #fbfbfc; }
.data-table th { padding: 14px 22px; text-align: left; font-weight: 700; font-size: 12px; color: #888; border-bottom: 1px solid #f0f0f2; text-transform: uppercase; letter-spacing: 0.5px; }
.data-table tbody tr { border-bottom: 1px solid #f8f8fb; }
.data-table td { padding: 16px 22px; font-size: 14px; color: #444; }
.text-right { text-align: right !important; }

.alert-type-badge { font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 6px; }
.alert-type-badge.critical { background: #f5222d; color: #fff; }
.alert-type-badge.warning { background: #faad14; color: #fff; }
.alert-type-badge.info { background: #1890ff; color: #fff; }

.suggestion-cell { max-width: 300px; }
.reason { font-weight: 700; color: #333; margin-bottom: 4px; font-size: 13.5px; }
.suggestion { font-size: 12px; color: #999; font-weight: 500; }

.code-text { font-family: 'Courier New', monospace; background: #f4f4f4; padding: 3px 6px; border-radius: 4px; font-weight: 700; color: #000; }

/* Modal Sync */
.modal-mask { position: fixed; inset: 0; z-index: 1000; background: rgba(0,0,0,0.4); backdrop-filter: blur(5px); display: flex; align-items: center; justify-content: center; padding: 20px; }
.modal-panel { width: min(1000px, 100%); max-height: 88vh; background: white; border-radius: 24px; box-shadow: 0 30px 60px -12px rgba(0,0,0,0.3); display: flex; flex-direction: column; overflow: hidden; }
.modal-head { padding: 24px 30px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; }
.head-info h3 { margin: 0 0 4px 0; font-size: 20px; font-weight: 800; color: #000; }
.head-info p { margin: 0; font-size: 12px; color: #999; font-weight: 700; }
.close-btn { width: 34px; height: 34px; border-radius: 50%; border: none; background: #f4f4f4; cursor: pointer; transition: all 0.2s; }
.close-btn:hover { background: #000; color: #fff; }

.modal-body { flex: 1; overflow-y: auto; padding: 24px 30px; }
.dot-status { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #ef4444; margin-right: 6px; }
.dot-status.ok { background: #10b981; box-shadow: 0 0 10px rgba(16, 185, 129, 0.4); }

.modal-loading { text-align: center; padding: 60px 0; color: #aaa; }
.spinner { width: 30px; height: 30px; border: 3px solid #f0f0f0; border-top-color: #000; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 15px; }
@keyframes spin { to { transform: rotate(360deg); } }

.modal-footer { padding: 20px 30px; background: #fdfdfd; border-top: 1px solid #f0f0f0; display: flex; justify-content: flex-end; gap: 12px; }
.btn { height: 44px; padding: 0 24px; border-radius: 12px; font-size: 14px; font-weight: 700; border: none; cursor: pointer; transition: all 0.2s; }
.btn-primary { background: #000; color: #fff; }
.btn-secondary { background: #f0f0f0; color: #666; }

.msg-tip { margin-top: 15px; font-weight: 700; }
.up { color: #10b981; }
.down { color: #ef4444; }
.empty { text-align: center; padding: 40px; color: #999; font-weight: 600; }

@media (max-width: 1000px) {
  .sidebar { display: none; }
  .api-grid { grid-template-columns: 1fr; }
  .main-content { padding: 25px; }
}
</style>
