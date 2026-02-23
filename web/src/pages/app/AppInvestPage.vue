<template>
  <LegacyAppShell>
    <section class="legacy-section">
      <div class="index-grid">
        <article v-for="idx in indexCards" :key="idx.id" class="idx-card">
          <div class="idx-header">
            <div class="idx-name">{{ idx.name }}</div>
          </div>
          <div class="idx-content">
            <div class="idx-value">{{ idx.price ? idx.price.toFixed(2) : '--' }}</div>
            <div class="idx-change" :class="idx.chg >= 0 ? 'up' : 'down'">{{ formatPct(idx.chg || 0) }}</div>
          </div>
        </article>
      </div>
    </section>

    <section class="legacy-section">
      <div class="assets-header">
        <div class="total-assets-section">
          <div class="total-mv-label">总持有市值 (CNY)</div>
          <div class="main-mv">{{ formatCny(investStats.mv) }}</div>
        </div>
        <div class="pnl-stats">
          <article class="pnl-stat-item">
            <div class="pnl-label">今日盈亏</div>
            <div class="pnl-value" :class="valueClass(investStats.dayPnl)">{{ formatSignedCny(investStats.dayPnl) }}</div>
            <div class="pnl-rate" :class="valueClass(investStats.dayRate)">{{ formatPct(investStats.dayRate) }}</div>
          </article>
          <article class="pnl-stat-item">
            <div class="pnl-label">持仓盈亏</div>
            <div class="pnl-value" :class="valueClass(investStats.floatPnl)">{{ formatSignedCny(investStats.floatPnl) }}</div>
            <div class="pnl-rate" :class="valueClass(investStats.floatRate)">{{ formatPct(investStats.floatRate) }}</div>
          </article>
          <article class="pnl-stat-item">
            <div class="pnl-label">累计盈亏</div>
            <div class="pnl-value" :class="valueClass(investStats.totalPnl)">{{ formatSignedCny(investStats.totalPnl) }}</div>
            <div class="pnl-rate" :class="valueClass(investStats.totalRate)">{{ formatPct(investStats.totalRate) }}</div>
          </article>
        </div>
      </div>
    </section>

    <section class="legacy-section">
      <div class="table-header">
        <h2>持仓明细</h2>
        <button class="legacy-btn-primary" @click="openModal('add')">+ 添加资产</button>
      </div>
      <div class="category-tabs">
        <button
          v-for="item in tabs"
          :key="item.key"
          class="tab-item"
          :class="{ active: currentCategory === item.key }"
          @click="currentCategory = item.key"
        >
          {{ item.label }}
        </button>
      </div>

      <div class="table-container">
        <table class="table-legacy">
          <colgroup>
            <col class="col-name" />
            <col class="col-qty" />
            <col class="col-price" />
            <col class="col-holding" />
            <col class="col-day" />
            <col class="col-total" />
            <col class="col-action" />
          </colgroup>
          <thead>
            <tr>
              <th class="th-name">资产名称</th>
              <th class="th-qty">持有数量</th>
              <th class="th-price">成本/现价</th>
              <th class="th-holding">持有金额</th>
              <th class="th-day-pnl">当日盈亏</th>
              <th class="th-total-pnl">累计盈亏</th>
              <th class="th-action">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredRows" :key="String(row.code)">
              <td class="name-code-cell td-name">
                <div class="name-primary" :title="String(row.name || '-')">{{ truncateAssetName(row.name) }}</div>
                <div class="name-secondary">{{ displayCode(String(row.code || '')) }}</div>
              </td>
              <td class="qty-cell td-qty">{{ formatHoldingQty(row.qty) }}</td>
              <td class="td-price">
                <div class="price-cell">
                  <span class="price-line cost">{{ formatMoney(row.costPrice, rowCurrency(row)) }}</span>
                  <span class="price-line current">{{ formatMoney(row.currentPrice, rowCurrency(row)) }}</span>
                </div>
              </td>
              <td class="holding-cell td-holding">{{ formatMoneyInt(toNumber(row.value), rowCurrency(row)) }}</td>
              <td class="td-day-pnl">
                <div class="pnl-cell" :class="valueClass(toNumber(row.dayPnlDisplay))">
                  <span class="table-pnl-amount">{{ formatSignedMoneyOrDash(row.dayPnlDisplay, rowCurrency(row)) }}</span>
                  <span class="table-pnl-rate">{{ formatPctOrDash(row.dayPnlRateDisplay) }}</span>
                  <span v-if="showClosedHint(row)" class="pnl-hint">休市</span>
                </div>
              </td>
              <td class="td-total-pnl">
                <div class="pnl-cell" :class="valueClass(toNumber(row.totalPnl))">
                  <span class="table-pnl-amount">{{ formatSignedMoneyIntOrDash(row.totalPnl, rowCurrency(row)) }}</span>
                  <span class="table-pnl-rate">{{ formatPctOrDash(row.totalPnlRate) }}</span>
                </div>
              </td>
              <td class="actions td-action">
                <div class="action-menu" @click.stop>
                  <button class="action-trigger" @click.stop="toggleActionMenu(String(row.code || ''))">操作 ▾</button>
                  <div v-if="isActionMenuOpen(String(row.code || ''))" class="action-dropdown">
                    <button class="menu-item" @click="openAction('buy', row)">买入</button>
                    <button class="menu-item" @click="openAction('sell', row)">卖出</button>
                    <button class="menu-item" @click="openAction('edit', row)">调整</button>
                    <button class="menu-item danger" @click="remove(String(row.code || ''))">删除</button>
                  </div>
                </div>
              </td>
            </tr>
            <tr v-if="!filteredRows.length">
              <td colspan="7" class="empty">暂无持仓</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="modal.visible" class="overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ modalTitle }}</h3>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="input-group" v-if="modal.type === 'add'">
            <label class="input-label">资产代码</label>
            <input v-model.trim="form.code" class="modal-input" placeholder="如 sh600000 / hk00700 / gb_aapl" required />
          </div>
          <div class="input-group" v-if="modal.type === 'add'">
            <label class="input-label">资产名称</label>
            <input v-model.trim="form.name" class="modal-input" placeholder="资产名称（可留空）" />
          </div>
          <div class="input-group">
            <label class="input-label">{{ modal.type === 'edit' ? '数量' : '交易数量' }}</label>
            <input v-model.number="form.qty" type="number" min="1" step="1" class="modal-input" required />
          </div>
          <div class="input-group">
            <label class="input-label">{{ modal.type === 'edit' ? '平均成本' : '成交价格' }}</label>
            <input v-model.number="form.price" type="number" step="0.0001" class="modal-input" required />
          </div>
          <div class="input-group" v-if="modal.type === 'edit'">
            <label class="input-label">累计盈亏校准 (调整值)</label>
            <input v-model.number="form.adjustment" type="number" step="0.01" class="modal-input" />
          </div>
          <button class="btn-primary full" type="submit">确认</button>
        </form>
      </div>
    </div>
  </LegacyAppShell>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import LegacyAppShell from '../../layouts/LegacyAppShell.vue'
import { marketDisplayCurrency, toNumber } from '../../shared/format'
import { api } from '../../shared/http'
import { readPageCache, writePageCache } from '../../shared/pageCache'
import { useKonaStore } from '../../shared/store'

type TabKey = 'all' | 'a' | 'fund' | 'us' | 'hk'
type ModalType = 'add' | 'buy' | 'sell' | 'edit'
type ActionMenuState = { openCode: string | null }
type IndexCard = { id: string; name: string; price: number; chg: number }
type InvestCachePayload = {
  indexCards: IndexCard[]
  currentCategory: TabKey
  portfolio: unknown[]
  quotes: Record<string, unknown>
  rates: Record<string, number>
  marketStatus: Record<string, unknown>
  allClosed: boolean
}

const INVEST_CACHE_DOMAIN = 'invest'
const INVEST_CACHE_KEY = 'page'
const INVEST_CACHE_TTL_MS = 15 * 60_000
const INVEST_PAGE_REFRESH_INTERVAL_MS = 60_000

const store = useKonaStore()
const rows = computed(() => store.rows.value)
const rates = computed(() => store.state.rates)

const currentCategory = ref<TabKey>('all')
const indexCards = ref([
  { id: 's_sh000001', name: '上证指数', price: 0, chg: 0 },
  { id: 'rt_hkHSTECH', name: '恒生科技', price: 0, chg: 0 },
  { id: 'gb_ixic', name: '纳斯达克', price: 0, chg: 0 },
])

const tabs = [
  { key: 'all', label: '全部' },
  { key: 'a', label: 'A股' },
  { key: 'fund', label: '基金' },
  { key: 'us', label: '美股' },
  { key: 'hk', label: '港股' },
] as const

const modal = reactive<{ visible: boolean; type: ModalType; code: string }>({
  visible: false,
  type: 'add',
  code: '',
})

const actionMenu = reactive<ActionMenuState>({
  openCode: null,
})

const form = reactive({
  code: '',
  name: '',
  qty: 0,
  price: 0,
  curr: 'CNY',
  adjustment: 0,
})
let refreshInflight: Promise<void> | null = null
let staticRefreshTimer: number | null = null

function cacheUserId(): string {
  return String(store.state.user?.id || 'guest')
}

function persistInvestCache() {
  writePageCache<InvestCachePayload>(
    INVEST_CACHE_DOMAIN,
    INVEST_CACHE_KEY,
    cacheUserId(),
    {
      indexCards: indexCards.value,
      currentCategory: currentCategory.value,
      portfolio: store.state.portfolio as unknown[],
      quotes: store.state.quotes as Record<string, unknown>,
      rates: store.state.rates,
      marketStatus: store.state.marketStatus as Record<string, unknown>,
      allClosed: Boolean(store.state.allClosed),
    },
    INVEST_CACHE_TTL_MS,
  )
}

function restoreInvestCache(): boolean {
  const cached = readPageCache<InvestCachePayload>(
    INVEST_CACHE_DOMAIN,
    INVEST_CACHE_KEY,
    cacheUserId(),
    INVEST_CACHE_TTL_MS,
  )
  if (!cached) return false
  if (Array.isArray(cached.indexCards) && cached.indexCards.length) {
    indexCards.value = cached.indexCards
  }
  if (['all', 'a', 'fund', 'us', 'hk'].includes(String(cached.currentCategory))) {
    currentCategory.value = cached.currentCategory
  }
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

function rateToCny(curr?: string): number {
  const code = String(curr || 'CNY').toUpperCase()
  return toNumber(rates.value[code], 1) || 1
}

function formatMoney(value: unknown, curr: string): string {
  const n = toNumber(value)
  return `${currencySymbol(curr)}${n.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

function formatMoneyInt(value: unknown, curr: string): string {
  const n = Math.round(toNumber(value))
  return `${currencySymbol(curr)}${Math.abs(n).toLocaleString('zh-CN')}`
}

function formatSignedMoney(value: number, curr: string): string {
  const sign = value >= 0 ? '+' : '-'
  const n = Math.abs(toNumber(value))
  return `${sign}${currencySymbol(curr)}${n.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

function formatSignedMoneyInt(value: number, curr: string): string {
  const sign = value >= 0 ? '+' : '-'
  const n = Math.abs(Math.round(toNumber(value)))
  return `${sign}${currencySymbol(curr)}${n.toLocaleString('zh-CN')}`
}

function formatSignedMoneyOrDash(value: unknown, curr: string): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return '--'
  return formatSignedMoney(n, curr)
}

function formatSignedMoneyIntOrDash(value: unknown, curr: string): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return '--'
  return formatSignedMoneyInt(n, curr)
}

function currencySymbol(curr: string): string {
  const code = String(curr || 'CNY').toUpperCase()
  if (code === 'USD') return '$'
  if (code === 'HKD') return 'HK$'
  return '¥'
}

function formatCny(value: number): string {
  return `¥ ${Math.round(value).toLocaleString('zh-CN')}`
}

function formatSignedCny(value: number): string {
  const sign = value >= 0 ? '+' : '-'
  return `${sign}¥ ${Math.abs(Math.round(value)).toLocaleString('zh-CN')}`
}

function formatPct(value: number): string {
  return `${value >= 0 ? '+' : ''}${toNumber(value).toFixed(2)}%`
}

function formatPctOrDash(value: unknown): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return '--'
  return formatPct(n)
}

function valueClass(value: number): 'up' | 'down' | 'neutral' {
  if (!Number.isFinite(value)) return 'neutral'
  return value >= 0 ? 'up' : 'down'
}

function displayCode(code: string): string {
  const lower = String(code || '').toLowerCase()
  if (lower.startsWith('sh') || lower.startsWith('sz') || lower.startsWith('bj')) return code.slice(2)
  if (lower.startsWith('gb_')) return code.slice(3).toUpperCase()
  if (lower.startsWith('f_')) return code.slice(2)
  if (lower.startsWith('ft_')) return code.slice(3)
  return code.toUpperCase()
}

function truncateAssetName(name: unknown): string {
  const text = String(name || '-')
  if (text === '-') return text
  const chars = [...text]
  const maxChars = 10
  return chars.length > maxChars ? `${chars.slice(0, maxChars).join('')}...` : text
}

function rowCurrency(row: Record<string, unknown>): 'CNY' | 'HKD' | 'USD' {
  return marketDisplayCurrency(row.market, row.curr)
}

function formatHoldingQty(qty: unknown): string {
  const n = Math.abs(Math.round(toNumber(qty)))
  return n.toLocaleString('zh-CN')
}

function validatePositiveIntegerQty(qty: number): boolean {
  return Number.isInteger(qty) && qty > 0
}

function showClosedHint(row: Record<string, unknown>): boolean {
  const marketTradingDay = row.marketTradingDay
  if (marketTradingDay === true || marketTradingDay === 1 || marketTradingDay === '1') return false
  if (String(marketTradingDay ?? '').toLowerCase() === 'true') return false
  // 仅在“非交易日”提示休市；交易日中的午休/收盘后不显示该提示，避免误导。
  return marketTradingDay === false || marketTradingDay === 0 || marketTradingDay === '0'
}

const filteredRows = computed(() => {
  if (currentCategory.value === 'all') return rows.value
  return rows.value.filter((row) => {
    if (currentCategory.value === 'a') return row.market === 'a'
    if (currentCategory.value === 'fund') return row.market === 'fund'
    if (currentCategory.value === 'us') return row.market === 'us'
    if (currentCategory.value === 'hk') return row.market === 'hk'
    return true
  })
})

const investStats = computed(() => {
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
    dayPnl,
    floatPnl,
    totalPnl,
    dayRate: mv - dayPnl > 0 ? (dayPnl / (mv - dayPnl)) * 100 : 0,
    floatRate: cost > 0 ? (floatPnl / cost) * 100 : 0,
    totalRate: cost > 0 ? (totalPnl / cost) * 100 : 0,
  }
})

const modalTitle = computed(() => {
  if (modal.type === 'add') return '添加资产'
  if (modal.type === 'buy') return `买入 ${modal.code}`
  if (modal.type === 'sell') return `卖出 ${modal.code}`
  return `调整 ${modal.code}`
})

function openModal(type: ModalType, row?: Record<string, unknown>) {
  closeActionMenu()
  modal.visible = true
  modal.type = type
  modal.code = String(row?.code || '')
  form.code = String(row?.code || '')
  form.name = String(row?.name || '')
  form.qty = toNumber(row?.qty, 0)
  form.price = toNumber(row?.costPrice ?? row?.price, 0)
  form.curr = String(row?.curr || 'CNY')
  form.adjustment = toNumber(row?.adjustment, 0)
  if (type === 'buy' || type === 'sell') {
    form.qty = 0
    form.price = toNumber(row?.currentPrice ?? row?.price, 0)
  }
}

function openAction(type: Exclude<ModalType, 'add'>, row: Record<string, unknown>) {
  openModal(type, row)
}

function closeModal() {
  modal.visible = false
}

function toggleActionMenu(code: string) {
  actionMenu.openCode = actionMenu.openCode === code ? null : code
}

function isActionMenuOpen(code: string): boolean {
  return actionMenu.openCode === code
}

function closeActionMenu() {
  actionMenu.openCode = null
}

function ensureValidQty(): boolean {
  if (validatePositiveIntegerQty(toNumber(form.qty))) return true
  alert('数量必须是正整数')
  return false
}

async function submitModal() {
  if (!ensureValidQty()) return

  if (modal.type === 'add') {
    await api.post('/api/portfolio/add', {
      code: form.code,
      name: form.name || form.code,
      qty: form.qty,
      price: form.price,
      curr: form.curr || 'CNY',
    })
  } else if (modal.type === 'buy') {
    await api.post('/api/portfolio/buy', { code: modal.code, qty: form.qty, price: form.price })
  } else if (modal.type === 'sell') {
    await api.post('/api/portfolio/sell', { code: modal.code, qty: form.qty, price: form.price })
  } else {
    await api.post('/api/portfolio/update', { code: modal.code, field: 'qty', val: form.qty })
    await api.post('/api/portfolio/update', { code: modal.code, field: 'price', val: form.price })
    await api.post('/api/portfolio/update', { code: modal.code, field: 'adjustment', val: form.adjustment })
  }
  closeModal()
  await refresh('force')
}

async function remove(code: string) {
  closeActionMenu()
  if (!confirm(`确认删除 ${code} ？`)) return
  await api.post('/api/portfolio/delete', { code })
  await refresh('force')
}

async function loadIndexes() {
  try {
    const result = await api.post<Record<string, { price?: number; yclose?: number; chg?: number }>>('/api/prices/batch', {
      codes: indexCards.value.map((item) => item.id),
    })
    indexCards.value = indexCards.value.map((item) => {
      const quote = result[item.id] || {}
      return {
        ...item,
        price: toNumber(quote.price, toNumber(quote.yclose, 0)),
        chg: toNumber(quote.chg, 0),
      }
    })
  } catch {
    // ignore index failures
  }
}

async function refresh(mode: 'light' | 'force' = 'light') {
  if (refreshInflight) {
    return refreshInflight
  }
  refreshInflight = (async () => {
    const refreshStore = mode === 'force' ? store.refreshAll() : store.refreshStaticOnly()
    await Promise.all([refreshStore, loadIndexes()])
    persistInvestCache()
  })()
  try {
    await refreshInflight
  } finally {
    refreshInflight = null
  }
}

function handleDocumentClick() {
  closeActionMenu()
}

function startStaticRefresh() {
  if (staticRefreshTimer) {
    window.clearInterval(staticRefreshTimer)
  }
  staticRefreshTimer = window.setInterval(() => {
    void refresh('light')
  }, INVEST_PAGE_REFRESH_INTERVAL_MS)
}

onMounted(async () => {
  document.addEventListener('click', handleDocumentClick)
  const restored = restoreInvestCache()
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
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<style scoped>
.index-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.idx-card {
  background: var(--legacy-bg-tertiary);
  border-radius: var(--legacy-radius-sm);
  padding: 20px;
  border: 2px solid var(--legacy-border);
}

.idx-header {
  margin-bottom: 10px;
}

.idx-name {
  font-size: calc(13px * var(--legacy-density-font-scale));
  color: var(--legacy-text-secondary);
}

.idx-value {
  font-size: calc(26px * var(--legacy-density-font-scale));
  font-weight: 700;
}

.idx-change {
  font-size: calc(12px * var(--legacy-density-font-scale));
  margin-top: calc(3px * var(--legacy-density-space-scale));
}

.up { color: var(--legacy-red); }
.down { color: var(--legacy-green); }

.assets-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: calc(20px * var(--legacy-density-space-scale));
}

.total-mv-label {
  font-size: calc(13px * var(--legacy-density-font-scale));
  color: var(--legacy-text-secondary);
  margin-bottom: calc(10px * var(--legacy-density-space-scale));
}

.main-mv {
  font-size: clamp(34px, calc(48px * var(--legacy-density-font-scale)), 52px);
  font-weight: 700;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.pnl-stats {
  display: flex;
  gap: calc(10px * var(--legacy-density-space-scale));
}

.pnl-stat-item {
  background: var(--legacy-bg-tertiary);
  border-radius: var(--legacy-radius-sm);
  padding: calc(12px * var(--legacy-density-space-scale)) calc(14px * var(--legacy-density-space-scale));
  border: 2px solid var(--legacy-border);
  min-width: calc(150px * var(--legacy-density-card-minh));
}

.pnl-label {
  font-size: calc(11px * var(--legacy-density-font-scale));
  color: var(--legacy-text-secondary);
}

.pnl-value {
  margin-top: calc(6px * var(--legacy-density-space-scale));
  font-size: calc(16px * var(--legacy-density-font-scale));
  font-weight: 700;
}

.pnl-rate {
  margin-top: calc(3px * var(--legacy-density-space-scale));
  font-size: calc(12px * var(--legacy-density-font-scale));
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: calc(14px * var(--legacy-density-space-scale));
  padding-bottom: calc(14px * var(--legacy-density-space-scale));
  border-bottom: 1px solid var(--legacy-border);
}

.table-header h2 {
  font-size: calc(18px * var(--legacy-density-font-scale));
  font-weight: 700;
  line-height: 1.25;
  margin: 0;
}

.category-tabs {
  display: flex;
  gap: calc(6px * var(--legacy-density-space-scale));
  margin-bottom: calc(14px * var(--legacy-density-space-scale));
  padding: calc(3px * var(--legacy-density-space-scale));
  background: var(--legacy-bg-tertiary);
  border-radius: 12px;
  border: 1px solid var(--legacy-border);
}

.tab-item {
  padding: calc(7px * var(--legacy-density-space-scale)) calc(14px * var(--legacy-density-space-scale));
  border-radius: 8px;
  cursor: pointer;
  font-size: calc(12px * var(--legacy-density-font-scale));
  color: var(--legacy-text-secondary);
  background: transparent;
  border: 0;
}

.tab-item.active {
  color: var(--legacy-text-primary);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2));
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.table-container {
  overflow-x: auto;
  --inv-fs-head: calc(12px * var(--legacy-density-font-scale));
  --inv-fs-name: calc(16px * var(--legacy-density-font-scale));
  --inv-fs-main: calc(16px * var(--legacy-density-font-scale));
  --inv-fs-sub: calc(13px * var(--legacy-density-font-scale));
  --inv-fs-hint: calc(11px * var(--legacy-density-font-scale));
  --inv-lh-main: 1.25;
  --inv-lh-sub: 1.2;
  --inv-cell-py: calc(9px * var(--legacy-density-space-scale));
  --inv-cell-px: calc(10px * var(--legacy-density-space-scale));
  --inv-col-gap: calc(16px * var(--legacy-density-space-scale));
}

.table-legacy {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
}

.col-name,
.col-qty,
.col-price,
.col-holding,
.col-day,
.col-total,
.col-action {
  width: calc(100% / 7);
}

.table-legacy th,
.table-legacy td {
  font-variant-numeric: tabular-nums;
}

.table-legacy th {
  vertical-align: middle;
  font-size: var(--inv-fs-head);
  font-weight: 600;
  line-height: var(--inv-lh-sub);
  color: var(--legacy-text-secondary);
  padding: var(--inv-cell-py) calc(var(--inv-cell-px) + var(--inv-col-gap) * 0.5);
  text-align: center;
  border-bottom: none;
  background: var(--legacy-bg-tertiary);
}

.table-legacy td {
  vertical-align: top;
  padding: var(--inv-cell-py) calc(var(--inv-cell-px) + var(--inv-col-gap) * 0.5);
  line-height: var(--inv-lh-main);
  text-align: center;
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
}

.table-legacy th + th,
.table-legacy td + td {
  border-left: none;
}

.table-legacy tbody tr:last-child td {
  border-bottom: none;
}

.name-code-cell {
  min-width: 0;
}

.name-primary {
  color: var(--legacy-text-primary);
  font-size: var(--inv-fs-name);
  font-weight: 700;
  line-height: var(--inv-lh-main);
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.name-secondary {
  margin-top: calc(3px * var(--legacy-density-space-scale));
  color: var(--legacy-text-secondary);
  font-size: var(--inv-fs-sub);
  font-weight: 500;
  line-height: var(--inv-lh-sub);
  text-align: left;
}

.qty-cell {
  font-size: var(--inv-fs-main);
  font-weight: 700;
  text-align: center;
  white-space: nowrap;
}

.price-cell,
.pnl-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  gap: 2px;
  line-height: var(--inv-lh-sub);
}

.price-line {
  font-size: calc(15px * var(--legacy-density-font-scale));
  font-weight: 600;
  line-height: 1.25;
  white-space: nowrap;
}

.price-line.cost {
  color: var(--legacy-text-secondary);
}

.price-line.current {
  color: var(--legacy-text-primary);
  font-weight: 600;
}

.holding-cell {
  font-size: var(--inv-fs-main);
  font-weight: 700;
  white-space: nowrap;
  text-align: right;
}

.table-pnl-amount,
.table-pnl-rate {
  white-space: nowrap;
}

.table-pnl-amount {
  font-size: var(--inv-fs-main);
  font-weight: 700;
  line-height: var(--inv-lh-main);
}

.table-pnl-rate {
  font-size: var(--inv-fs-sub);
  font-weight: 500;
  line-height: var(--inv-lh-sub);
}

.table-legacy th.th-name,
.table-legacy td.td-name {
  text-align: left;
}

.table-legacy th.th-price,
.table-legacy td.td-price {
  text-align: right;
}

.table-legacy th.th-holding,
.table-legacy td.td-holding {
  text-align: right;
}

.table-legacy th.th-day-pnl,
.table-legacy th.th-total-pnl,
.table-legacy td.td-day-pnl,
.table-legacy td.td-total-pnl {
  text-align: right;
}

.td-price .price-cell {
  align-items: flex-end;
  justify-content: flex-start;
  gap: calc(3px * var(--legacy-density-space-scale));
}

.td-price .price-line.cost,
.td-price .price-line.current {
  font-weight: 600;
}

.td-day-pnl .pnl-cell,
.td-total-pnl .pnl-cell {
  align-items: flex-end;
  justify-content: flex-start;
  min-height: calc(54px * var(--legacy-density-space-scale));
}

.pnl-hint {
  color: rgba(148, 163, 184, 0.85);
  font-size: var(--inv-fs-hint);
  font-weight: 500;
  line-height: var(--inv-lh-sub);
}

.actions {
  white-space: nowrap;
}

.action-menu {
  position: relative;
  display: inline-flex;
  justify-content: center;
}

.action-trigger {
  min-width: calc(68px * var(--legacy-density-card-minh));
  height: calc(28px * var(--legacy-density-space-scale));
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(15, 23, 42, 0.8);
  color: var(--legacy-text-primary);
  font-size: var(--inv-fs-sub);
  font-weight: 600;
  cursor: pointer;
}

.action-trigger:hover {
  background: rgba(30, 41, 59, 0.9);
}

.action-dropdown {
  position: absolute;
  top: calc(32px * var(--legacy-density-space-scale));
  left: 50%;
  transform: translateX(-50%);
  width: calc(102px * var(--legacy-density-card-minh));
  background: #0f172a;
  border: 1px solid var(--legacy-border);
  border-radius: 10px;
  padding: calc(5px * var(--legacy-density-space-scale));
  display: flex;
  flex-direction: column;
  gap: calc(3px * var(--legacy-density-space-scale));
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
  z-index: 10;
}

.menu-item {
  border: none;
  background: transparent;
  color: var(--legacy-text-primary);
  border-radius: 8px;
  padding: calc(5px * var(--legacy-density-space-scale)) calc(7px * var(--legacy-density-space-scale));
  font-size: var(--inv-fs-sub);
  line-height: var(--inv-lh-sub);
  text-align: left;
  cursor: pointer;
}

.menu-item:hover {
  background: rgba(59, 130, 246, 0.15);
}

.menu-item.danger {
  color: #ffb4b4;
}

.menu-item.danger:hover {
  background: rgba(239, 68, 68, 0.18);
}

.neutral {
  color: var(--legacy-text-secondary);
}

.empty {
  text-align: center;
  color: var(--legacy-text-secondary);
}

.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
  z-index: 6000;
}

.modal {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #1e293b;
  border-radius: 20px;
  padding: calc(24px * var(--legacy-density-space-scale));
  width: min(420px, 92vw);
  border: 1px solid var(--legacy-border);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: calc(15px * var(--legacy-density-space-scale));
}

.close-btn {
  width: calc(34px * var(--legacy-density-space-scale));
  height: calc(34px * var(--legacy-density-space-scale));
  border-radius: 50%;
  border: none;
  background: var(--legacy-bg-tertiary);
  color: #fff;
  cursor: pointer;
  font-size: calc(20px * var(--legacy-density-font-scale));
}

.input-group { margin-bottom: calc(12px * var(--legacy-density-space-scale)); }
.input-label {
  display: block;
  color: var(--legacy-text-secondary);
  font-size: calc(12px * var(--legacy-density-font-scale));
  margin-bottom: calc(6px * var(--legacy-density-space-scale));
}
.modal-input {
  width: 100%;
  background: #0f172a;
  border: 1px solid var(--legacy-border);
  border-radius: 12px;
  color: #fff;
  padding: calc(10px * var(--legacy-density-space-scale));
}
.btn-primary.full {
  width: 100%;
  height: calc(40px * var(--legacy-density-space-scale));
  border: 0;
  border-radius: 12px;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
}

@media (max-width: 1200px) {
  .index-grid {
    grid-template-columns: 1fr;
  }

  .assets-header {
    flex-direction: column;
  }

  .pnl-stats {
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .main-mv {
    font-size: 40px;
  }

  .category-tabs {
    overflow-x: auto;
  }

  .modal {
    width: 90%;
    padding: 20px;
  }
}

@media (max-width: 1280px) {
  .table-legacy {
    min-width: 1040px;
  }
}

</style>
