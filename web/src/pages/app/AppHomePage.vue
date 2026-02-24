<template>
  <LegacyAppShell>
    <div id="capture-area" class="kk-assets" :class="{ 'kk-light-v1': theme === 'light' }">
      <div class="home-action-row" aria-label="首页工具栏">
        <button
          class="home-action-btn"
          type="button"
          :title="theme === 'dark' ? '切换浅色主题' : '切换深色主题'"
          :aria-label="theme === 'dark' ? '切换浅色主题' : '切换深色主题'"
          @click="toggleTheme"
        >{{ theme === 'dark' ? '🌙' : '☀️' }}</button>
        <button
          class="home-action-btn"
          type="button"
          :title="isPrivacyMode ? '关闭隐私模式' : '开启隐私模式'"
          :aria-label="isPrivacyMode ? '关闭隐私模式' : '开启隐私模式'"
          @click="togglePrivacy"
        >{{ isPrivacyMode ? '🙈' : '👁️' }}</button>
        <button
          class="home-action-btn"
          type="button"
          title="保存截图"
          aria-label="保存截图"
          @click="saveAsImage"
        >📸</button>
      </div>

      <section class="legacy-section">
        <div class="assets-header">
          <div class="total-assets-section">
            <div class="total-mv-label">总资产 (CNY)</div>
            <div class="main-mv">{{ masked(formatCny(totalAssets)) }}</div>
          </div>
          <div class="asset-breakdown">
            <article class="asset-card">
              <div class="asset-card-label">现金资产</div>
              <div class="asset-card-value cash">{{ masked(formatCny(cashTotal)) }}</div>
            </article>
            <article class="asset-card">
              <div class="asset-card-label">投资资产</div>
              <div class="asset-card-value invest">{{ masked(formatCny(investTotal.mv)) }}</div>
            </article>
            <article class="asset-card">
              <div class="asset-card-label">其他资产</div>
              <div class="asset-card-value other">{{ masked(formatCny(otherTotal)) }}</div>
            </article>
          </div>
        </div>
      </section>

      <section class="legacy-section">
        <div class="section-header">
          <div class="section-title">投资资产</div>
          <RouterLink to="/app/invest" class="goto-link">查看详情 →</RouterLink>
        </div>

        <div class="invest-header">
          <div class="invest-total">
            <div class="invest-total-label">持有总市值 (CNY)</div>
            <div class="invest-total-value">{{ masked(formatCny(investTotal.mv)) }}</div>
          </div>
          <div class="pnl-stats">
            <article class="pnl-stat-item">
              <div class="pnl-label">今日盈亏</div>
              <div class="pnl-value" :class="valueClass(investTotal.dayPnl)">
                {{ masked(formatSignedCny(investTotal.dayPnl)) }}
              </div>
              <div class="pnl-rate" :class="valueClass(investTotal.dayRate)">{{ formatPct(investTotal.dayRate) }}</div>
            </article>
            <article class="pnl-stat-item">
              <div class="pnl-label">持仓盈亏</div>
              <div class="pnl-value" :class="valueClass(investTotal.floatPnl)">
                {{ masked(formatSignedCny(investTotal.floatPnl)) }}
              </div>
              <div class="pnl-rate" :class="valueClass(investTotal.floatRate)">{{ formatPct(investTotal.floatRate) }}</div>
            </article>
            <article class="pnl-stat-item">
              <div class="pnl-label">累计盈亏</div>
              <div class="pnl-value" :class="valueClass(investTotal.totalPnl)">
                {{ masked(formatSignedCny(investTotal.totalPnl)) }}
              </div>
              <div class="pnl-rate" :class="valueClass(investTotal.totalRate)">{{ formatPct(investTotal.totalRate) }}</div>
            </article>
          </div>
        </div>

        <div class="category-grid">
          <article v-for="market in marketCards" :key="market.key" class="category-card">
            <div class="category-header">
              <span class="category-icon">{{ market.icon }}</span>
              <span class="category-name">{{ market.name }}</span>
            </div>
            <div class="category-mv" :class="market.key">{{ masked(formatCny(market.mv)) }}</div>
            <div class="category-pnl">
              <div class="category-pnl-row">
                <span class="category-pnl-label">今日盈亏</span>
                <span class="category-pnl-value" :class="valueClass(market.dayPnl)">
                  {{ masked(formatSignedCny(market.dayPnl)) }} ({{ formatPct(market.dayRate) }})
                </span>
              </div>
              <div class="category-pnl-row">
                <span class="category-pnl-label">持仓盈亏</span>
                <span class="category-pnl-value" :class="valueClass(market.floatPnl)">
                  {{ masked(formatSignedCny(market.floatPnl)) }} ({{ formatPct(market.floatRate) }})
                </span>
              </div>
              <div class="category-pnl-row">
                <span class="category-pnl-label">累计盈亏</span>
                <span class="category-pnl-value" :class="valueClass(market.totalPnl)">
                  {{ masked(formatSignedCny(market.totalPnl)) }} ({{ formatPct(market.totalRate) }})
                </span>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section class="legacy-section">
        <div class="section-header">
          <div class="section-title">现金资产</div>
          <button class="legacy-btn-primary section-add-btn" @click="openModal('cash')">+ 添加</button>
        </div>
        <div class="invest-total-label">现金总额 (CNY)</div>
        <div class="invest-total-value cash">{{ masked(formatCny(cashTotal)) }}</div>
        <div class="asset-card-grid">
          <article v-for="item in cashAssets" :key="`cash-${item.id}`" class="asset-card-item">
            <div class="asset-card-item-header">
              <div class="asset-card-item-name">{{ item.name }}</div>
              <div class="row-actions">
                <button class="action-btn" @click="openModal('cash', item)">编辑</button>
                <button class="action-btn danger" @click="removeAsset('cash', item.id)">删除</button>
              </div>
            </div>
            <div class="asset-card-item-value cash">{{ masked(formatCny(toCny(item.amount, item.curr))) }}</div>
          </article>
          <div v-if="!cashAssets.length" class="empty-state">暂无现金资产</div>
        </div>
      </section>

      <section class="legacy-section">
        <div class="section-header">
          <div class="section-title">其他资产</div>
          <button class="legacy-btn-primary section-add-btn" @click="openModal('other')">+ 添加</button>
        </div>
        <div class="invest-total-label">其他资产总额 (CNY)</div>
        <div class="invest-total-value other">{{ masked(formatCny(otherTotal)) }}</div>
        <div class="asset-card-grid">
          <article v-for="item in otherAssets" :key="`other-${item.id}`" class="asset-card-item">
            <div class="asset-card-item-header">
              <div class="asset-card-item-name">{{ item.name }}</div>
              <div class="row-actions">
                <button class="action-btn" @click="openModal('other', item)">编辑</button>
                <button class="action-btn danger" @click="removeAsset('other', item.id)">删除</button>
              </div>
            </div>
            <div class="asset-card-item-value other">{{ masked(formatCny(toCny(item.amount, item.curr))) }}</div>
          </article>
          <div v-if="!otherAssets.length" class="empty-state">暂无其他资产</div>
        </div>
      </section>

      <section class="legacy-section">
        <div class="section-header">
          <div class="section-title">我的负债</div>
          <button class="legacy-btn-primary section-add-btn" @click="openModal('liability')">+ 添加</button>
        </div>
        <div class="invest-total-label">负债总额 (CNY)</div>
        <div class="invest-total-value liability">{{ masked(formatCny(liabilityTotal)) }}</div>
        <div class="asset-card-grid">
          <article v-for="item in liabilities" :key="`liability-${item.id}`" class="asset-card-item">
            <div class="asset-card-item-header">
              <div class="asset-card-item-name">{{ item.name }}</div>
              <div class="row-actions">
                <button class="action-btn" @click="openModal('liability', item)">编辑</button>
                <button class="action-btn danger" @click="removeAsset('liability', item.id)">删除</button>
              </div>
            </div>
            <div class="asset-card-item-value liability">{{ masked(formatCny(toCny(item.amount, item.curr))) }}</div>
          </article>
          <div v-if="!liabilities.length" class="empty-state">暂无负债记录</div>
        </div>
      </section>
    </div>

    <div v-if="modalVisible" class="overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ modalMode === 'add' ? '添加资产' : '编辑资产' }}</h3>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="input-group">
            <label class="input-label">资产名称</label>
            <input v-model.trim="form.name" class="modal-input" required />
          </div>
          <div class="input-group">
            <label class="input-label">金额 (CNY)</label>
            <input v-model.number="form.amount" class="modal-input" type="number" min="0.01" step="0.01" required />
          </div>
          <button class="btn-primary full" type="submit">{{ modalMode === 'add' ? '确认保存' : '保存修改' }}</button>
        </form>
      </div>
    </div>
  </LegacyAppShell>
</template>

<script setup lang="ts">
import html2canvas from 'html2canvas'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import LegacyAppShell from '../../layouts/LegacyAppShell.vue'
import { api } from '../../shared/http'
import { toNumber } from '../../shared/format'
import { readPageCache, writePageCache } from '../../shared/pageCache'
import { useKonaStore } from '../../shared/store'
import { useWebTheme } from '../../shared/webTheme'

type AssetType = 'cash' | 'other' | 'liability'
type SimpleAsset = { id: number; name: string; amount: number; curr?: string }
type HomeCachePayload = {
  cashAssets: SimpleAsset[]
  otherAssets: SimpleAsset[]
  liabilities: SimpleAsset[]
  portfolio: unknown[]
  quotes: Record<string, unknown>
  rates: Record<string, number>
  marketStatus: Record<string, unknown>
  allClosed: boolean
}

const HOME_CACHE_DOMAIN = 'home'
const HOME_CACHE_KEY = 'assets'
const HOME_CACHE_TTL_MS = 1000 * 60 * 60 * 12
const STATIC_REFRESH_INTERVAL_MS = 5 * 60_000

const store = useKonaStore()
const { theme, toggleTheme } = useWebTheme()
const rows = computed(() => store.rows.value)
const rates = computed(() => store.state.rates)

const cashAssets = ref<SimpleAsset[]>([])
const otherAssets = ref<SimpleAsset[]>([])
const liabilities = ref<SimpleAsset[]>([])
const isPrivacyMode = ref(localStorage.getItem('privacy_mode') === 'true')
let staticRefreshTimer: number | null = null
let refreshInflight: Promise<void> | null = null

const modalVisible = ref(false)
const modalType = ref<AssetType>('cash')
const modalMode = ref<'add' | 'edit'>('add')
const form = reactive<{ id: number | null; name: string; amount: number; curr: string }>({
  id: null,
  name: '',
  amount: 0,
  curr: 'CNY',
})

const marketMeta = {
  a: { name: 'A股', icon: '🇨🇳' },
  us: { name: '美股', icon: '🇺🇸' },
  hk: { name: '港股', icon: '🇭🇰' },
  fund: { name: '基金', icon: '📊' },
} as const

function rateToCny(curr?: string): number {
  const c = String(curr || 'CNY').toUpperCase()
  return toNumber(rates.value[c], 1) || 1
}

function toCny(amount: unknown, curr?: string): number {
  return toNumber(amount) * rateToCny(curr)
}

function formatCny(value: number): string {
  return `¥ ${Math.round(value).toLocaleString('zh-CN')}`
}

function formatSignedCny(value: number): string {
  const sign = value >= 0 ? '+' : '-'
  return `${sign}¥ ${Math.abs(Math.round(value)).toLocaleString('zh-CN')}`
}

function formatPct(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function valueClass(value: number): 'up' | 'down' {
  return value >= 0 ? 'up' : 'down'
}

function masked(text: string): string {
  return isPrivacyMode.value ? '****' : text
}

const investTotal = computed(() => {
  let mv = 0
  let cost = 0
  let dayPnl = 0
  let floatPnl = 0
  let totalPnl = 0
  for (const row of rows.value) {
    const rate = rateToCny(row.curr)
    const rowMv = toNumber(row.value) * rate
    const rowCost = toNumber(row.costPrice) * toNumber(row.qty) * rate
    mv += rowMv
    cost += rowCost
    dayPnl += toNumber(row.dayPnlAggregate) * rate
    floatPnl += (toNumber(row.value) - toNumber(row.costPrice) * toNumber(row.qty)) * rate
    totalPnl += toNumber(row.totalPnl) * rate
  }
  return {
    mv,
    cost,
    dayPnl,
    floatPnl,
    totalPnl,
    dayRate: mv - dayPnl > 0 ? (dayPnl / (mv - dayPnl)) * 100 : 0,
    floatRate: cost > 0 ? (floatPnl / cost) * 100 : 0,
    totalRate: cost > 0 ? (totalPnl / cost) * 100 : 0,
  }
})

const marketCards = computed(() => {
  const marketStats = {
    a: { mv: 0, cost: 0, dayPnl: 0, floatPnl: 0, totalPnl: 0 },
    us: { mv: 0, cost: 0, dayPnl: 0, floatPnl: 0, totalPnl: 0 },
    hk: { mv: 0, cost: 0, dayPnl: 0, floatPnl: 0, totalPnl: 0 },
    fund: { mv: 0, cost: 0, dayPnl: 0, floatPnl: 0, totalPnl: 0 },
  }

  for (const row of rows.value) {
    const key = String(row.market || 'a') as keyof typeof marketStats
    const stats = marketStats[key]
    const rate = rateToCny(row.curr)
    const mv = toNumber(row.value) * rate
    const cost = toNumber(row.costPrice) * toNumber(row.qty) * rate
    stats.mv += mv
    stats.cost += cost
    stats.dayPnl += toNumber(row.dayPnlAggregate) * rate
    stats.floatPnl += (toNumber(row.value) - toNumber(row.costPrice) * toNumber(row.qty)) * rate
    stats.totalPnl += toNumber(row.totalPnl) * rate
  }

  return (Object.keys(marketMeta) as Array<keyof typeof marketMeta>).map((key) => {
    const stats = marketStats[key]
    return {
      key,
      name: marketMeta[key].name,
      icon: marketMeta[key].icon,
      ...stats,
      dayRate: stats.mv - stats.dayPnl > 0 ? (stats.dayPnl / (stats.mv - stats.dayPnl)) * 100 : 0,
      floatRate: stats.cost > 0 ? (stats.floatPnl / stats.cost) * 100 : 0,
      totalRate: stats.cost > 0 ? (stats.totalPnl / stats.cost) * 100 : 0,
    }
  })
})

const cashTotal = computed(() => cashAssets.value.reduce((sum, item) => sum + toCny(item.amount, item.curr), 0))
const otherTotal = computed(() => otherAssets.value.reduce((sum, item) => sum + toCny(item.amount, item.curr), 0))
const liabilityTotal = computed(() => liabilities.value.reduce((sum, item) => sum + toCny(item.amount, item.curr), 0))
const totalAssets = computed(() => investTotal.value.mv + cashTotal.value + otherTotal.value - liabilityTotal.value)

function cacheUserId(): string {
  return String(store.state.user?.id || 'guest')
}

function persistHomeCache() {
  writePageCache<HomeCachePayload>(
    HOME_CACHE_DOMAIN,
    HOME_CACHE_KEY,
    cacheUserId(),
    {
      cashAssets: cashAssets.value,
      otherAssets: otherAssets.value,
      liabilities: liabilities.value,
      portfolio: store.state.portfolio as unknown[],
      quotes: store.state.quotes as Record<string, unknown>,
      rates: store.state.rates,
      marketStatus: store.state.marketStatus as Record<string, unknown>,
      allClosed: Boolean(store.state.allClosed),
    },
    HOME_CACHE_TTL_MS,
  )
}

function restoreHomeCache(): boolean {
  const cached = readPageCache<HomeCachePayload>(
    HOME_CACHE_DOMAIN,
    HOME_CACHE_KEY,
    cacheUserId(),
    HOME_CACHE_TTL_MS,
  )
  if (!cached) return false
  cashAssets.value = Array.isArray(cached.cashAssets) ? cached.cashAssets : []
  otherAssets.value = Array.isArray(cached.otherAssets) ? cached.otherAssets : []
  liabilities.value = Array.isArray(cached.liabilities) ? cached.liabilities : []
  if (Array.isArray(cached.portfolio)) {
    store.state.portfolio = cached.portfolio as typeof store.state.portfolio
  }
  if (cached.quotes && typeof cached.quotes === 'object') {
    store.state.quotes = cached.quotes as typeof store.state.quotes
  }
  if (cached.rates && typeof cached.rates === 'object') {
    store.state.rates = cached.rates
  }
  if (cached.marketStatus && typeof cached.marketStatus === 'object') {
    store.state.marketStatus = cached.marketStatus as typeof store.state.marketStatus
  }
  store.state.allClosed = Boolean(cached.allClosed)
  return true
}

async function loadLists() {
  const [cash, other, debt] = await Promise.all([
    api.get<SimpleAsset[]>('/api/cash_assets'),
    api.get<SimpleAsset[]>('/api/other_assets'),
    api.get<SimpleAsset[]>('/api/liabilities'),
  ])
  cashAssets.value = Array.isArray(cash) ? cash : []
  otherAssets.value = Array.isArray(other) ? other : []
  liabilities.value = Array.isArray(debt) ? debt : []
  persistHomeCache()
}

async function refresh(mode: 'light' | 'force' = 'light') {
  if (refreshInflight) {
    return refreshInflight
  }
  refreshInflight = (async () => {
    const refreshStore = mode === 'force' ? store.refreshAll() : store.refreshStaticOnly()
    await Promise.all([refreshStore, loadLists()])
    persistHomeCache()
  })()
  try {
    await refreshInflight
  } finally {
    refreshInflight = null
  }
}

function togglePrivacy() {
  isPrivacyMode.value = !isPrivacyMode.value
  localStorage.setItem('privacy_mode', String(isPrivacyMode.value))
}

async function saveAsImage() {
  const target = document.getElementById('capture-area')
  if (!target) return
  const canvas = await html2canvas(target, {
    backgroundColor: theme.value === 'light' ? '#f7fbff' : '#0a0e27',
    scale: 2,
    useCORS: true,
  })
  const link = document.createElement('a')
  link.download = `kaka-assets-${Date.now()}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}

function openModal(type: AssetType, item?: SimpleAsset) {
  modalType.value = type
  modalMode.value = item ? 'edit' : 'add'
  form.id = item?.id ?? null
  form.name = item?.name ?? ''
  form.amount = toNumber(item?.amount, 0)
  form.curr = item?.curr || 'CNY'
  modalVisible.value = true
}

function closeModal() {
  modalVisible.value = false
}

async function submitModal() {
  const payload = { id: form.id, name: form.name, amount: form.amount, curr: form.curr }
  const map = {
    cash: {
      add: '/api/cash_assets/add',
      update: '/api/cash_assets/update',
    },
    other: {
      add: '/api/other_assets/add',
      update: '/api/other_assets/update',
    },
    liability: {
      add: '/api/liabilities/add',
      update: '/api/liabilities/update',
    },
  } as const
  const route = modalMode.value === 'add' ? map[modalType.value].add : map[modalType.value].update
  await api.post(route, payload)
  closeModal()
  await refresh('light')
}

async function removeAsset(type: AssetType, id: number) {
  const ok = confirm('确认删除该资产？')
  if (!ok) return
  const map = {
    cash: '/api/cash_assets/delete',
    other: '/api/other_assets/delete',
    liability: '/api/liabilities/delete',
  } as const
  await api.post(map[type], { id })
  await refresh('light')
}

function startStaticRefresh() {
  if (staticRefreshTimer) {
    window.clearInterval(staticRefreshTimer)
  }
  staticRefreshTimer = window.setInterval(() => {
    void refresh('light')
  }, STATIC_REFRESH_INTERVAL_MS)
}

onMounted(async () => {
  const restored = restoreHomeCache()
  void refresh(restored ? 'light' : 'force')
  store.startAutoRefresh()
  startStaticRefresh()
})

onBeforeUnmount(() => {
  if (staticRefreshTimer) {
    window.clearInterval(staticRefreshTimer)
    staticRefreshTimer = null
  }
  store.stopAutoRefresh()
})
</script>

<style scoped>
.home-action-row {
  display: flex;
  justify-content: flex-end;
  gap: calc(12px * var(--legacy-density-space-scale));
  margin-bottom: calc(14px * var(--legacy-density-space-scale));
}

.home-action-btn {
  width: calc(46px * var(--legacy-density-card-minh));
  height: calc(46px * var(--legacy-density-card-minh));
  border-radius: 999px;
  border: 1px solid var(--legacy-action-btn-border);
  background: var(--legacy-action-btn-bg);
  color: var(--legacy-text-primary);
  box-shadow: var(--legacy-shadow);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: calc(20px * var(--legacy-density-font-scale));
  cursor: pointer;
  transition: transform 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}

.home-action-btn:hover {
  transform: translateY(-1px);
  background: var(--legacy-action-btn-hover-bg);
  box-shadow: var(--legacy-shadow-hover);
}

.assets-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 28px;
}

.total-assets-section {
  display: flex;
  flex-direction: column;
}

.total-mv-label {
  font-size: calc(14px * var(--legacy-density-font-scale));
  color: var(--legacy-text-secondary);
  margin-bottom: calc(12px * var(--legacy-density-space-scale));
}

.main-mv {
  font-size: clamp(36px, calc(52px * var(--legacy-density-font-scale)), 52px);
  font-weight: 700;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  user-select: none;
}

.asset-breakdown {
  display: flex;
  gap: calc(12px * var(--legacy-density-space-scale));
}

.asset-card {
  background: var(--legacy-bg-tertiary);
  border: 2px solid var(--legacy-border);
  border-radius: var(--legacy-radius-sm);
  padding: calc(12px * var(--legacy-density-space-scale)) calc(14px * var(--legacy-density-space-scale));
  min-width: calc(150px * var(--legacy-density-card-minh));
}

.asset-card-label {
  font-size: calc(12px * var(--legacy-density-font-scale));
  color: var(--legacy-text-secondary);
  margin-bottom: 8px;
}

.asset-card-value {
  font-size: calc(22px * var(--legacy-density-font-scale));
  font-weight: 800;
}

.asset-card-value.cash { color: var(--legacy-green); }
.asset-card-value.invest { color: var(--legacy-blue); }
.asset-card-value.other { color: var(--legacy-orange); }

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: calc(14px * var(--legacy-density-space-scale));
  padding-bottom: calc(12px * var(--legacy-density-space-scale));
  border-bottom: 1px solid var(--legacy-border);
}

.section-title {
  font-size: calc(26px * var(--legacy-density-font-scale));
  font-weight: 700;
  margin: 0;
}

.goto-link {
  color: var(--legacy-text-secondary);
  text-decoration: none;
  font-size: calc(12px * var(--legacy-density-font-scale));
}

.section-add-btn {
  min-width: calc(84px * var(--legacy-density-card-minh));
  height: calc(34px * var(--legacy-density-space-scale));
  border-radius: 999px;
  padding: 0 calc(14px * var(--legacy-density-space-scale));
  font-size: calc(12px * var(--legacy-density-font-scale));
  font-weight: 700;
  background: linear-gradient(135deg, #4d7dff 0%, #6b6cff 100%);
  box-shadow: 0 8px 20px rgba(77, 125, 255, 0.32);
}

.section-add-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(77, 125, 255, 0.4);
}

.invest-header {
  display: flex;
  justify-content: space-between;
  gap: calc(18px * var(--legacy-density-space-scale));
  margin-bottom: calc(20px * var(--legacy-density-space-scale));
}

.invest-total-label {
  color: var(--legacy-text-secondary);
  margin-bottom: calc(6px * var(--legacy-density-space-scale));
  font-size: calc(13px * var(--legacy-density-font-scale));
}

.invest-total-value {
  font-size: clamp(28px, calc(38px * var(--legacy-density-font-scale)), 40px);
  font-weight: 700;
}

.invest-total-value.cash { color: var(--legacy-green); }
.invest-total-value.other { color: var(--legacy-orange); }
.invest-total-value.liability { color: var(--legacy-red); }

.pnl-stats {
  display: flex;
  gap: calc(10px * var(--legacy-density-space-scale));
}

.pnl-stat-item {
  background: var(--legacy-bg-tertiary);
  border: 2px solid var(--legacy-border);
  border-radius: var(--legacy-radius-sm);
  padding: calc(12px * var(--legacy-density-space-scale)) calc(14px * var(--legacy-density-space-scale));
  min-width: calc(148px * var(--legacy-density-card-minh));
}

.pnl-label {
  font-size: calc(11px * var(--legacy-density-font-scale));
  color: var(--legacy-text-secondary);
  margin-bottom: calc(6px * var(--legacy-density-space-scale));
}

.pnl-value {
  font-size: calc(16px * var(--legacy-density-font-scale));
  font-weight: 700;
}

.pnl-rate {
  margin-top: calc(3px * var(--legacy-density-space-scale));
  font-size: calc(12px * var(--legacy-density-font-scale));
}

.up { color: var(--legacy-red); }
.down { color: var(--legacy-green); }

.category-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: calc(10px * var(--legacy-density-space-scale));
}

.category-card {
  background: var(--legacy-bg-tertiary);
  border: 2px solid var(--legacy-border);
  border-radius: var(--legacy-radius-sm);
  padding: calc(12px * var(--legacy-density-space-scale)) calc(14px * var(--legacy-density-space-scale));
}

.category-header {
  display: flex;
  gap: calc(6px * var(--legacy-density-space-scale));
  align-items: center;
  margin-bottom: calc(8px * var(--legacy-density-space-scale));
}

.category-name {
  font-size: calc(18px * var(--legacy-density-font-scale));
  font-weight: 700;
}

.category-mv {
  font-size: calc(24px * var(--legacy-density-font-scale));
  font-weight: 700;
  margin-bottom: calc(6px * var(--legacy-density-space-scale));
}

.category-mv.a { color: var(--legacy-blue); }
.category-mv.us { color: var(--legacy-purple); }
.category-mv.hk { color: var(--legacy-orange); }
.category-mv.fund { color: var(--legacy-green); }

.category-pnl-row {
  display: flex;
  justify-content: space-between;
  gap: calc(6px * var(--legacy-density-space-scale));
  margin-top: calc(4px * var(--legacy-density-space-scale));
  font-size: calc(13px * var(--legacy-density-font-scale));
}

.category-pnl-label {
  color: var(--legacy-text-secondary);
}

.asset-card-grid {
  margin-top: calc(12px * var(--legacy-density-space-scale));
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(calc(176px * var(--legacy-density-card-minh)), 1fr));
  gap: calc(10px * var(--legacy-density-space-scale));
}

.asset-card-item {
  background: var(--legacy-bg-tertiary);
  border: 2px solid var(--legacy-border);
  border-radius: 12px;
  padding: calc(12px * var(--legacy-density-space-scale));
  min-height: calc(96px * var(--legacy-density-card-minh));
  position: relative;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.asset-card-item:hover {
  background: var(--legacy-card-hover-bg);
  border-color: var(--legacy-card-hover-border);
}

.asset-card-item-header {
  display: block;
  min-height: calc(20px * var(--legacy-density-card-minh));
}

.asset-card-item-name {
  color: var(--legacy-text-secondary);
  font-size: calc(13px * var(--legacy-density-font-scale));
  padding-right: calc(84px * var(--legacy-density-card-minh));
}

.asset-card-item-value {
  margin-top: calc(12px * var(--legacy-density-space-scale));
  font-size: calc(22px * var(--legacy-density-font-scale));
  font-weight: 700;
}

.asset-card-item-value.cash { color: var(--legacy-green); }
.asset-card-item-value.other { color: var(--legacy-orange); }
.asset-card-item-value.liability { color: var(--legacy-red); }

.row-actions {
  position: absolute;
  top: calc(8px * var(--legacy-density-space-scale));
  right: calc(8px * var(--legacy-density-space-scale));
  display: flex;
  gap: 4px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
}

.asset-card-item:hover .row-actions {
  opacity: 1;
  pointer-events: auto;
}

.action-btn {
  height: calc(24px * var(--legacy-density-space-scale));
  border: 1px solid var(--legacy-action-btn-border);
  border-radius: 8px;
  background: var(--legacy-action-btn-bg);
  color: var(--legacy-text-secondary);
  font-size: calc(11px * var(--legacy-density-font-scale));
  padding: 0 calc(6px * var(--legacy-density-space-scale));
  cursor: pointer;
}

.action-btn:hover {
  color: var(--legacy-text-primary);
  background: var(--legacy-action-btn-hover-bg);
}

.action-btn.danger:hover {
  color: var(--legacy-action-danger-text);
  background: var(--legacy-action-danger-hover-bg);
}

.empty-state {
  padding: calc(20px * var(--legacy-density-space-scale));
  color: var(--legacy-text-secondary);
}

.overlay {
  position: fixed;
  inset: 0;
  background: var(--legacy-overlay-bg);
  backdrop-filter: blur(10px);
  z-index: 6000;
}

.modal {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--legacy-modal-bg);
  border-radius: 20px;
  padding: calc(24px * var(--legacy-density-space-scale));
  width: min(420px, 92vw);
  border: 1px solid var(--legacy-border);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: calc(16px * var(--legacy-density-space-scale));
}

.close-btn {
  width: calc(34px * var(--legacy-density-space-scale));
  height: calc(34px * var(--legacy-density-space-scale));
  border-radius: 50%;
  border: 0;
  cursor: pointer;
  background: var(--legacy-bg-tertiary);
  color: var(--legacy-text-primary);
  font-size: calc(20px * var(--legacy-density-font-scale));
}

.input-group { margin-bottom: calc(14px * var(--legacy-density-space-scale)); }
.input-label {
  display: block;
  margin-bottom: calc(6px * var(--legacy-density-space-scale));
  color: var(--legacy-text-secondary);
  font-size: calc(12px * var(--legacy-density-font-scale));
}
.modal-input {
  width: 100%;
  background: var(--legacy-input-bg);
  border: 1px solid var(--legacy-border);
  border-radius: 12px;
  color: var(--legacy-input-text);
  padding: calc(10px * var(--legacy-density-space-scale));
}
.btn-primary.full {
  width: 100%;
  border: 0;
  border-radius: 12px;
  height: calc(40px * var(--legacy-density-space-scale));
  cursor: pointer;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: #fff;
  font-weight: 700;
}

@media (max-width: 1400px) {
  .asset-card-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  }

  .category-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1024px) {
  .assets-header,
  .invest-header {
    flex-direction: column;
  }

  .asset-breakdown,
  .pnl-stats {
    flex-wrap: wrap;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .main-mv { font-size: 38px; }
  .section-title { font-size: 30px; }
  .asset-card-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .category-grid { grid-template-columns: 1fr; }
  .modal { width: 90%; padding: 20px; }
}

@media (hover: none) {
  .row-actions {
    opacity: 1;
    pointer-events: auto;
  }
}

/* 浅色主题 1:1 视觉稿（仅首页） */
.kk-light-v1 {
  color: #0f172a;
}

.kk-light-v1 .home-action-row {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 14px;
}

.kk-light-v1 .home-action-btn {
  width: 44px;
  height: 44px;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.1);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  cursor: pointer;
  transition: transform 0.22s ease, box-shadow 0.22s ease, background 0.22s ease;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.kk-light-v1 .home-action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 24px 55px rgba(15, 23, 42, 0.14);
  background: rgba(255, 255, 255, 0.88);
}

.kk-light-v1 .legacy-section {
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(255, 255, 255, 0.72);
  box-shadow: 0 26px 70px rgba(15, 23, 42, 0.14);
  border-radius: 26px;
  padding: 18px;
  margin-bottom: 16px;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  position: relative;
  overflow: hidden;
}

.kk-light-v1 .legacy-section::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(15, 23, 42, 0.06) 1px, transparent 1px);
  background-size: 18px 18px;
  mask-image: radial-gradient(circle at 40% 10%, #000 0%, transparent 60%);
  opacity: 0.55;
  pointer-events: none;
  z-index: 0;
}

.kk-light-v1 .legacy-section > * {
  position: relative;
  z-index: 1;
}

.kk-light-v1 .assets-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 22px;
}

.kk-light-v1 .total-mv-label {
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 1.2px;
  color: rgba(15, 23, 42, 0.55);
  margin-bottom: 10px;
}

.kk-light-v1 .main-mv {
  font-size: clamp(38px, 4vw, 56px);
  font-weight: 900;
  letter-spacing: -1px;
  line-height: 1.05;
  background: linear-gradient(135deg, #ff4d8d 0%, #6366f1 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.kk-light-v1 .asset-breakdown {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.kk-light-v1 .asset-card {
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 18px;
  padding: 12px 14px;
  min-width: 168px;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.1);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.kk-light-v1 .asset-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 24px 55px rgba(15, 23, 42, 0.14);
  border-color: rgba(99, 102, 241, 0.22);
}

.kk-light-v1 .asset-card-label {
  font-size: 12px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.55);
  margin-bottom: 8px;
}

.kk-light-v1 .asset-card-value {
  font-size: 20px;
  font-weight: 900;
  letter-spacing: -0.2px;
}

.kk-light-v1 .asset-card-value.cash {
  color: rgba(16, 185, 129, 0.95);
}

.kk-light-v1 .asset-card-value.invest {
  color: rgba(99, 102, 241, 0.95);
}

.kk-light-v1 .asset-card-value.other {
  color: rgba(255, 77, 141, 0.95);
}

.kk-light-v1 .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.1);
}

.kk-light-v1 .section-title {
  margin: 0;
  font-size: 20px;
  font-weight: 900;
  letter-spacing: -0.2px;
}

.kk-light-v1 .goto-link {
  color: rgba(15, 23, 42, 0.55);
  text-decoration: none;
  font-size: 12px;
  font-weight: 900;
}

.kk-light-v1 .goto-link:hover {
  text-decoration: underline;
}

.kk-light-v1 .section-add-btn {
  border: 0;
  cursor: pointer;
  height: 34px;
  border-radius: 999px;
  padding: 0 14px;
  font-size: 12px;
  font-weight: 900;
  color: #fff;
  background: linear-gradient(135deg, #ff4d8d 0%, #6366f1 100%);
  box-shadow: 0 16px 40px rgba(99, 102, 241, 0.22);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.kk-light-v1 .section-add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 22px 55px rgba(99, 102, 241, 0.28);
}

.kk-light-v1 .invest-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.kk-light-v1 .invest-total-label {
  color: rgba(15, 23, 42, 0.55);
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 1.2px;
}

.kk-light-v1 .invest-total-value {
  font-size: clamp(26px, 2.6vw, 40px);
  font-weight: 900;
  letter-spacing: -0.6px;
}

.kk-light-v1 .invest-total-value.cash {
  color: rgba(16, 185, 129, 0.95);
}

.kk-light-v1 .invest-total-value.other {
  color: rgba(255, 77, 141, 0.95);
}

.kk-light-v1 .invest-total-value.liability {
  color: rgba(239, 68, 68, 0.95);
}

.kk-light-v1 .pnl-stats {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.kk-light-v1 .pnl-stat-item {
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 18px;
  padding: 12px 14px;
  min-width: 160px;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.1);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.kk-light-v1 .pnl-label {
  font-size: 11px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.55);
  margin-bottom: 6px;
}

.kk-light-v1 .pnl-value {
  font-size: 16px;
  font-weight: 900;
  letter-spacing: -0.2px;
}

.kk-light-v1 .pnl-rate {
  margin-top: 4px;
  font-size: 12px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.55);
}

/* 1:1 视觉稿颜色 */
.kk-light-v1 .up {
  color: rgba(255, 77, 141, 0.95);
  font-weight: 900;
}

.kk-light-v1 .down {
  color: rgba(99, 102, 241, 0.95);
  font-weight: 900;
}

.kk-light-v1 .category-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.kk-light-v1 .category-card {
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 18px;
  padding: 12px 14px;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.1);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.kk-light-v1 .category-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 24px 55px rgba(15, 23, 42, 0.14);
  border-color: rgba(99, 102, 241, 0.22);
}

.kk-light-v1 .category-header {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-bottom: 8px;
}

.kk-light-v1 .category-name {
  font-size: 16px;
  font-weight: 900;
}

.kk-light-v1 .category-mv {
  font-size: 22px;
  font-weight: 900;
  letter-spacing: -0.3px;
  margin-bottom: 6px;
}

.kk-light-v1 .category-mv.a {
  color: rgba(99, 102, 241, 0.95);
}

.kk-light-v1 .category-mv.us {
  color: rgba(168, 85, 247, 0.95);
}

.kk-light-v1 .category-mv.hk {
  color: rgba(255, 77, 141, 0.95);
}

.kk-light-v1 .category-mv.fund {
  color: rgba(16, 185, 129, 0.95);
}

.kk-light-v1 .category-pnl-row {
  display: flex;
  justify-content: space-between;
  gap: 6px;
  margin-top: 4px;
  font-size: 12px;
  font-weight: 850;
}

.kk-light-v1 .category-pnl-label {
  color: rgba(15, 23, 42, 0.55);
}

.kk-light-v1 .asset-card-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 10px;
}

.kk-light-v1 .asset-card-item {
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 18px;
  padding: 12px;
  min-height: 96px;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.1);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.kk-light-v1 .asset-card-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 24px 55px rgba(15, 23, 42, 0.14);
  border-color: rgba(99, 102, 241, 0.22);
}

.kk-light-v1 .asset-card-item-name {
  color: rgba(15, 23, 42, 0.55);
  font-size: 12px;
  font-weight: 900;
}

.kk-light-v1 .asset-card-item-value {
  margin-top: 12px;
  font-size: 20px;
  font-weight: 900;
  letter-spacing: -0.2px;
}

.kk-light-v1 .asset-card-item-value.cash {
  color: rgba(16, 185, 129, 0.95);
}

.kk-light-v1 .asset-card-item-value.other {
  color: rgba(255, 77, 141, 0.95);
}

.kk-light-v1 .asset-card-item-value.liability {
  color: rgba(239, 68, 68, 0.95);
}

.kk-light-v1 .action-btn {
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: rgba(255, 255, 255, 0.8);
  color: rgba(15, 23, 42, 0.7);
}

.kk-light-v1 .action-btn:hover {
  background: rgba(255, 255, 255, 0.95);
  color: rgba(15, 23, 42, 0.9);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.1);
}

@media (max-width: 1200px) {
  .kk-light-v1 .category-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .kk-light-v1 .assets-header,
  .kk-light-v1 .invest-header {
    flex-direction: column;
  }

  .kk-light-v1 .main-mv {
    font-size: 44px;
  }
}

@media (max-width: 520px) {
  .kk-light-v1 .asset-card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .kk-light-v1 .category-grid {
    grid-template-columns: 1fr;
  }
}
</style>
