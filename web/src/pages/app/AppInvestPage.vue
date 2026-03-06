<template>
  <LegacyAppShell>
    <div id="capture-area-invest" class="kk-invest" :class="{ 'kk-light-v1': theme === 'light' }">
    <div class="home-action-row" aria-label="投资页工具栏">
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
      <div class="index-grid">
        <article v-for="idx in indexCards" :key="idx.id" class="idx-card">
          <div class="idx-header">
            <div class="idx-name">{{ idx.name }}</div>
          </div>
          <div class="idx-content">
            <div class="idx-value">{{ formatIndexPrice(idx.price) }}</div>
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
              <td class="qty-cell td-qty">{{ formatHoldingQty(row.qty, row) }}</td>
              <td class="td-price">
                <div class="price-cell">
                  <span class="price-line cost">{{ formatMoney(row.displayCostPrice ?? row.costPrice, rowCurrency(row)) }}</span>
                  <span class="price-line current">{{ formatMoney(row.currentPrice, rowCurrency(row)) }}</span>
                </div>
              </td>
              <td class="holding-cell td-holding">{{ formatMoneyInt(toNumber(row.value), rowCurrency(row)) }}</td>
              <td class="td-day-pnl">
                <div
                  class="pnl-cell"
                  :class="row.navUpdatePending ? '' : valueClass(toNumber(row.dayPnlDisplay))"
                >
                  <template v-if="row.navUpdatePending">
                    <span class="table-pnl-amount">待净值更新</span>
                    <span class="table-pnl-rate"></span>
                  </template>
                  <template v-else>
                    <span class="table-pnl-amount">{{ formatSignedMoneyOrDash(row.dayPnlDisplay, rowCurrency(row)) }}</span>
                    <span class="table-pnl-rate">{{ formatPctOrDash(row.dayPnlRateDisplay) }}</span>
                  </template>
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
          <div v-if="showFundInputMode" class="input-group">
            <label class="input-label">基金买入方式</label>
            <div class="fund-mode-switch">
              <button type="button" class="fund-mode-btn" :class="{ active: form.fundInputMode === 'qty' }" @click="form.fundInputMode = 'qty'">按份额</button>
              <button type="button" class="fund-mode-btn" :class="{ active: form.fundInputMode === 'amount' }" @click="form.fundInputMode = 'amount'">按金额</button>
            </div>
            <div v-if="isFundAmountMode && form.navLoading" class="fund-mode-hint">正在获取最新净值…</div>
            <div v-if="isFundAmountMode && form.navError" class="fund-mode-error">{{ form.navError }}</div>
          </div>
          <div class="input-group">
            <label class="input-label">{{ modal.type === 'edit' ? '平均成本' : (isFundAmountMode ? '净值' : '成交价格') }}</label>
            <input v-model.number="form.price" type="number" step="0.0001" class="modal-input" required />
          </div>
          <div class="input-group" v-if="showCashAccountSelector">
            <label class="input-label">资金账户</label>
            <select v-model.number="form.cashAssetId" class="modal-input" :disabled="cashAccountsLoading || !cashAccountOptions.length">
              <option v-if="!cashAccountOptions.length" :value="-1">暂无可用账户</option>
              <option v-for="account in cashAccountOptions" :key="account.id" :value="account.id">
                {{ account.label }}
              </option>
            </select>
            <div v-if="cashAccountsLoading" class="fund-mode-hint">正在加载资金账户…</div>
            <div v-else-if="cashAccountError" class="fund-mode-error">{{ cashAccountError }}</div>
            <div v-else-if="modal.type === 'sell' && !hasMatchingCashAccount" class="fund-mode-error">
              未找到 {{ targetTradeCurrency }} 现金账户，请先添加对应账户。
            </div>
          </div>
          <div v-if="isFundAmountMode" class="input-group">
            <label class="input-label">买入金额</label>
            <input v-model.number="form.amount" type="number" min="0" step="0.01" class="modal-input" required />
            <div class="fund-mode-hint">预计份额：{{ derivedFundQty() > 0 ? formatFundQty(derivedFundQty()) : '--' }}</div>
          </div>
          <div v-if="!isFundAmountMode" class="input-group">
            <label class="input-label">{{ modal.type === 'edit' ? '数量' : '交易数量' }}</label>
            <input
              v-model.number="form.qty"
              type="number"
              :min="showFundInputMode ? 0.0001 : 1"
              :step="showFundInputMode ? 0.0001 : 1"
              class="modal-input"
              required
            />
          </div>
          <div class="input-group" v-if="modal.type === 'edit'">
            <label class="input-label">累计盈亏校准 (调整值)</label>
            <input v-model.number="form.adjustment" type="number" step="0.01" class="modal-input" />
          </div>
          <button class="btn-primary full" type="submit">确认</button>
        </form>
      </div>
    </div>
    </div>
  </LegacyAppShell>
</template>

<script setup lang="ts">
import html2canvas from 'html2canvas'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import LegacyAppShell from '../../layouts/LegacyAppShell.vue'
import { marketDisplayCurrency, toNumber } from '../../shared/format'
import { api } from '../../shared/http'
import type { ApiError } from '../../shared/http'
import { readPageCache, writePageCache } from '../../shared/pageCache'
import { usePrivacyMode } from '../../shared/privacyMode'
import { useKonaStore } from '../../shared/store'
import { useWebTheme } from '../../shared/webTheme'

type TabKey = 'all' | 'a' | 'fund' | 'us' | 'hk'
type ModalType = 'add' | 'buy' | 'sell' | 'edit'
type ActionMenuState = { openCode: string | null }
type IndexCard = { id: string; name: string; price: number; chg: number }
type CashAsset = { id: number; name: string; amount?: number; curr?: string }
type CashAccountOption = { id: number; label: string }
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
const INVEST_PAGE_REFRESH_INTERVAL_MS = 120_000
const EXTERNAL_CASH_ASSET_ID = -999

const store = useKonaStore()
const { theme } = useWebTheme()
const { isPrivacyMode, togglePrivacy, maskValue } = usePrivacyMode()
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

const form = reactive<{
  code: string
  name: string
  qty: number
  price: number
  amount: number
  curr: string
  market: string
  fundInputMode: 'qty' | 'amount'
  navLoading: boolean
  navError: string
  adjustment: number
  cashAssetId: number | null
}>({
  code: '',
  name: '',
  qty: 0,
  price: 0,
  amount: 0,
  curr: 'CNY',
  market: 'a',
  fundInputMode: 'qty',
  navLoading: false,
  navError: '',
  adjustment: 0,
  cashAssetId: null,
})
const cashAccounts = ref<CashAsset[]>([])
const cashAccountsLoading = ref(false)
const cashAccountsLoaded = ref(false)
const cashAccountError = ref('')
let refreshInflight: Promise<void> | null = null
let staticRefreshTimer: number | null = null
let navPrefillTimer: number | null = null
let navFetchSeq = 0

function normalizeCurrency(curr: unknown): string {
  const text = String(curr || 'CNY').trim().toUpperCase()
  if (text === 'USD' || text === 'HKD' || text === 'CNY') return text
  return 'CNY'
}

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

function maskAmount(text: string): string {
  return maskValue(text)
}

function formatMoney(value: unknown, curr: string): string {
  const n = toNumber(value)
  const text = `${currencySymbol(curr)}${n.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
  return maskAmount(text)
}

function formatMoneyInt(value: unknown, curr: string): string {
  const n = Math.round(toNumber(value))
  const text = `${currencySymbol(curr)}${Math.abs(n).toLocaleString('zh-CN')}`
  return maskAmount(text)
}

function formatSignedMoney(value: number, curr: string): string {
  const sign = value >= 0 ? '+' : '-'
  const n = Math.abs(toNumber(value))
  const text = `${sign}${currencySymbol(curr)}${n.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
  return maskAmount(text)
}

function formatSignedMoneyInt(value: number, curr: string): string {
  const sign = value >= 0 ? '+' : '-'
  const n = Math.abs(Math.round(toNumber(value)))
  const text = `${sign}${currencySymbol(curr)}${n.toLocaleString('zh-CN')}`
  return maskAmount(text)
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
  return maskAmount(`¥ ${Math.round(value).toLocaleString('zh-CN')}`)
}

function formatSignedCny(value: number): string {
  const sign = value >= 0 ? '+' : '-'
  return maskAmount(`${sign}¥ ${Math.abs(Math.round(value)).toLocaleString('zh-CN')}`)
}

function formatPct(value: number): string {
  return `${value >= 0 ? '+' : ''}${toNumber(value).toFixed(2)}%`
}

function formatIndexPrice(value: number): string {
  if (!Number.isFinite(value) || value <= 0) return '--'
  return maskAmount(value.toFixed(2))
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

function isFundCode(code: unknown): boolean {
  const text = String(code || '').trim().toLowerCase()
  if (!text) return false
  if (text.startsWith('f_') || text.startsWith('ft_')) return true
  if (/^\d+$/.test(text) && text.startsWith('11')) return true
  return false
}

function inferMarketType(row?: Record<string, unknown>): 'a' | 'hk' | 'us' | 'fund' {
  const market = String(row?.market || row?.asset_type || '').trim().toLowerCase()
  if (market === 'a' || market === 'hk' || market === 'us' || market === 'fund') {
    return market
  }
  return isFundCode(row?.code) ? 'fund' : 'a'
}

function normalizeCodeForSubmit(rawCode: string): string {
  const input = String(rawCode || '').trim()
  if (!input) return ''
  if (/^\d+$/.test(input)) {
    if (input.startsWith('11')) return `f_${input}`
    if (input.startsWith('6') || input.startsWith('5') || input.startsWith('9')) return `sh${input}`
    if (input.startsWith('0') || input.startsWith('3') || input.startsWith('1') || input.startsWith('2')) return `sz${input}`
    if (input.startsWith('4') || input.startsWith('8')) return `bj${input}`
  }
  if (input.toUpperCase().endsWith('.HK')) return input.toUpperCase()
  if (/^[a-zA-Z]+$/.test(input)) return `gb_${input.toLowerCase()}`
  return input
}

function normalizeCodeForCompare(rawCode: unknown): string {
  return String(rawCode || '').trim().toLowerCase()
}

function clonePortfolioSnapshot(): Record<string, unknown>[] {
  return (store.state.portfolio as Record<string, unknown>[]).map((item) => ({ ...item }))
}

function restorePortfolioSnapshot(snapshot: Record<string, unknown>[]) {
  store.state.portfolio = snapshot as typeof store.state.portfolio
}

function findPortfolioIndexByCode(code: string): number {
  const target = normalizeCodeForCompare(code)
  if (!target) return -1
  return (store.state.portfolio as Record<string, unknown>[]).findIndex(
    (item) => normalizeCodeForCompare(item.code) === target,
  )
}

function holdingQtyByCode(code: string): number {
  const idx = findPortfolioIndexByCode(code)
  if (idx < 0) return 0
  return toNumber((store.state.portfolio as Record<string, unknown>[])[idx]?.qty, 0)
}

function applyOptimisticPortfolioChange(params: {
  mode: ModalType
  code: string
  name: string
  qty: number
  price: number
  adjustment: number
  curr: string
  assetType: string
}) {
  const { mode, code, name, qty, price, adjustment, curr, assetType } = params
  const list = [...(store.state.portfolio as Record<string, unknown>[])]
  const idx = findPortfolioIndexByCode(code)

  if (mode === 'add') {
    if (idx >= 0) {
      const existing = list[idx]
      if (!existing) return
      const oldQty = toNumber(existing.qty, 0)
      const oldPrice = toNumber(existing.price, 0)
      const nextQty = oldQty + qty
      const nextPrice = nextQty > 0 ? ((oldQty * oldPrice + qty * price) / nextQty) : oldPrice
      list[idx] = {
        ...existing,
        qty: nextQty,
        price: Number(nextPrice.toFixed(6)),
      }
    } else {
      list.push({
        code,
        name: name || code,
        qty,
        price,
        curr,
        asset_type: assetType,
        adjustment: 0,
      })
    }
    store.state.portfolio = list as typeof store.state.portfolio
    return
  }

  if (mode === 'buy') {
    if (idx < 0) return
    const existing = list[idx]
    if (!existing) return
    const oldQty = toNumber(existing.qty, 0)
    const oldPrice = toNumber(existing.price, 0)
    const nextQty = oldQty + qty
    const nextPrice = nextQty > 0 ? ((oldQty * oldPrice + qty * price) / nextQty) : oldPrice
    list[idx] = {
      ...existing,
      qty: nextQty,
      price: Number(nextPrice.toFixed(6)),
    }
    store.state.portfolio = list as typeof store.state.portfolio
    return
  }

  if (mode === 'sell') {
    if (idx < 0) return
    const existing = list[idx]
    if (!existing) return
    const oldQty = toNumber(existing.qty, 0)
    const nextQty = oldQty - qty
    if (nextQty <= 1e-6) {
      list.splice(idx, 1)
    } else {
      list[idx] = {
        ...existing,
        qty: nextQty,
      }
    }
    store.state.portfolio = list as typeof store.state.portfolio
    return
  }

  if (mode === 'edit') {
    if (idx < 0) return
    list[idx] = {
      ...list[idx],
      qty,
      price,
      adjustment,
    }
    store.state.portfolio = list as typeof store.state.portfolio
  }
}

const showFundInputMode = computed(() => {
  if (modal.type !== 'add' && modal.type !== 'buy') return false
  if (modal.type === 'buy') {
    return form.market === 'fund' || isFundCode(modal.code)
  }
  return form.market === 'fund' || isFundCode(form.code)
})

const isFundAmountMode = computed(() => showFundInputMode.value && form.fundInputMode === 'amount')
const showCashAccountSelector = computed(() => modal.type === 'buy' || modal.type === 'sell')
const targetTradeCurrency = computed(() => normalizeCurrency(form.curr))
const matchingCashAccounts = computed(() =>
  cashAccounts.value.filter((asset) => normalizeCurrency(asset.curr) === targetTradeCurrency.value),
)
const hasMatchingCashAccount = computed(() => matchingCashAccounts.value.length > 0)
const cashAccountOptions = computed<CashAccountOption[]>(() => {
  const options: CashAccountOption[] = []
  if (modal.type === 'buy') {
    options.push({
      id: EXTERNAL_CASH_ASSET_ID,
      label: `外部资金/初始转入 (${targetTradeCurrency.value})`,
    })
  }
  for (const asset of matchingCashAccounts.value) {
    options.push({
      id: Number(asset.id),
      label: `${asset.name} · ${normalizeCurrency(asset.curr)}`,
    })
  }
  return options
})

function applyDefaultCashSelection() {
  if (!showCashAccountSelector.value) {
    form.cashAssetId = null
    return
  }
  const optionIds = new Set(cashAccountOptions.value.map((item) => item.id))
  if (modal.type === 'buy') {
    if (form.cashAssetId != null && optionIds.has(form.cashAssetId)) return
    form.cashAssetId = EXTERNAL_CASH_ASSET_ID
    return
  }
  if (form.cashAssetId != null && optionIds.has(form.cashAssetId)) return
  form.cashAssetId = cashAccountOptions.value[0]?.id ?? null
}

function isNotFoundError(error: unknown): boolean {
  return Number((error as ApiError | undefined)?.status) === 404
}

async function ensureCashAccountsLoaded(force = false) {
  if (cashAccountsLoading.value) return
  if (cashAccountsLoaded.value && !force) return
  cashAccountsLoading.value = true
  cashAccountError.value = ''
  try {
    const list = await api.get<CashAsset[]>('/api/cash_assets')
    cashAccounts.value = Array.isArray(list) ? list : []
    cashAccountsLoaded.value = true
  } catch (error) {
    cashAccountError.value = (error as Error)?.message || '资金账户加载失败'
  } finally {
    cashAccountsLoading.value = false
    applyDefaultCashSelection()
  }
}

function derivedFundQty(): number {
  const amount = toNumber(form.amount)
  const nav = toNumber(form.price)
  if (amount <= 0 || nav <= 0) return 0
  const rawQty = amount / nav
  return Math.floor(rawQty * 10000) / 10000
}

function formatFundQty(value: number): string {
  const text = value.toFixed(4)
  return text.replace(/\.?0+$/, '')
}

function formatHoldingQty(qty: unknown, row?: Record<string, unknown>): string {
  const n = Math.abs(toNumber(qty))
  if (!Number.isFinite(n)) return '0'
  const market = String(row?.market || row?.asset_type || '').toLowerCase()
  if (market === 'fund' || isFundCode(row?.code)) {
    return formatFundQty(n)
  }
  return Math.round(n).toLocaleString('zh-CN')
}

function validatePositiveIntegerQty(qty: number): boolean {
  return Number.isInteger(qty) && qty > 0
}

function validatePositiveFundQty(qty: number): boolean {
  if (!Number.isFinite(qty) || qty <= 0) return false
  const scaled = Math.round(qty * 10000)
  return Math.abs(scaled - qty * 10000) < 1e-6
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
    cost += Math.abs(rowCost)
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
    floatRate: Math.abs(cost) > 0 ? (floatPnl / Math.abs(cost)) * 100 : 0,
    totalRate: Math.abs(cost) > 0 ? (totalPnl / Math.abs(cost)) * 100 : 0,
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
  form.price = toNumber(row?.rawCostPrice ?? row?.costPrice ?? row?.price, 0)
  form.amount = 0
  form.curr = String(row?.curr || 'CNY')
  form.market = inferMarketType(row)
  form.fundInputMode = 'qty'
  form.navLoading = false
  form.navError = ''
  form.adjustment = toNumber(row?.adjustment, 0)
  form.cashAssetId = null
  if (type === 'buy' || type === 'sell') {
    form.qty = 0
    form.price = toNumber(row?.currentPrice ?? row?.price, 0)
    applyDefaultCashSelection()
    void ensureCashAccountsLoaded()
  }
  if ((type === 'add' || type === 'buy') && showFundInputMode.value) {
    form.fundInputMode = 'amount'
    scheduleFundNavPrefill()
  }
}

function openAction(type: Exclude<ModalType, 'add'>, row: Record<string, unknown>) {
  openModal(type, row)
}

function closeModal() {
  modal.visible = false
  navFetchSeq += 1
  if (navPrefillTimer !== null) {
    window.clearTimeout(navPrefillTimer)
    navPrefillTimer = null
  }
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
  if (isFundAmountMode.value) return true
  const qty = toNumber(form.qty)
  if (showFundInputMode.value) {
    if (validatePositiveFundQty(qty)) return true
    alert('基金份额必须大于 0，且最多 4 位小数')
    return false
  }
  if (validatePositiveIntegerQty(toNumber(form.qty))) return true
  alert('数量必须是正整数')
  return false
}

function ensureValidPriceByMode(): boolean {
  const price = Number(form.price)
  if (!Number.isFinite(price)) {
    alert('价格必须是有效数字')
    return false
  }
  if (modal.type !== 'edit' && price <= 0) {
    alert('成交价格必须大于 0')
    return false
  }
  return true
}

function scheduleFundNavPrefill() {
  if (navPrefillTimer !== null) {
    window.clearTimeout(navPrefillTimer)
    navPrefillTimer = null
  }
  if (!modal.visible || !isFundAmountMode.value) return
  navPrefillTimer = window.setTimeout(() => {
    navPrefillTimer = null
    void prefillFundNav()
  }, 300)
}

async function prefillFundNav() {
  if (!modal.visible || !isFundAmountMode.value) return
  const code = modal.type === 'add' ? normalizeCodeForSubmit(form.code) : normalizeCodeForSubmit(modal.code || form.code)
  if (!code) return
  const apiCode = code.startsWith('gb_') ? code.slice(3) : code
  const seq = ++navFetchSeq
  form.navLoading = true
  form.navError = ''
  try {
    const prices = await api.post<Record<string, { price?: number; yclose?: number }>>('/api/prices/batch', { codes: [apiCode] })
    if (seq !== navFetchSeq) return
    const quote = prices[apiCode] || {}
    const nav = toNumber(quote.price, 0) > 0 ? toNumber(quote.price, 0) : toNumber(quote.yclose, 0)
    if (nav > 0) {
      form.price = Number(nav.toFixed(4))
      form.navError = ''
    } else {
      form.navError = '净值获取失败，可手动输入'
    }
  } catch {
    if (seq !== navFetchSeq) return
    form.navError = '净值获取失败，可手动输入'
  } finally {
    if (seq === navFetchSeq) {
      form.navLoading = false
    }
  }
}

async function submitModal() {
  if (!ensureValidQty()) return
  if (!ensureValidPriceByMode()) return

  const submitCode = normalizeCodeForSubmit(modal.type === 'add' ? form.code : modal.code)
  const submitQty = isFundAmountMode.value ? derivedFundQty() : toNumber(form.qty)
  if (!submitCode) {
    alert('资产代码无效')
    return
  }
  if (isFundAmountMode.value) {
    if (toNumber(form.amount) <= 0) {
      alert('买入金额必须大于 0')
      return
    }
    if (submitQty <= 0) {
      alert('金额过小，按当前净值不足以买入最小份额（0.0001）')
      return
    }
  }
  if (modal.type === 'sell') {
    const holdingQty = holdingQtyByCode(submitCode)
    if (submitQty > holdingQty + 1e-6) {
      alert(`卖出数量超过持仓：当前持仓 ${formatHoldingQty(holdingQty)}`)
      return
    }
  }

  const snapshot = clonePortfolioSnapshot()
  try {
    applyOptimisticPortfolioChange({
      mode: modal.type,
      code: submitCode,
      name: form.name || modal.code || submitCode,
      qty: modal.type === 'edit' ? toNumber(form.qty, 0) : submitQty,
      price: toNumber(form.price, 0),
      adjustment: toNumber(form.adjustment, 0),
      curr: form.curr || 'CNY',
      assetType: form.market || 'a',
    })

    if (modal.type === 'add') {
      await api.post('/api/portfolio/add', {
        code: submitCode,
        name: form.name || submitCode,
        qty: submitQty,
        price: form.price,
        curr: form.curr || 'CNY',
      })
    } else if (modal.type === 'buy') {
      const selectedCashAssetId = Number(form.cashAssetId)
      if (!Number.isFinite(selectedCashAssetId)) {
        restorePortfolioSnapshot(snapshot)
        alert('请选择资金账户')
        return
      }
      if (selectedCashAssetId === EXTERNAL_CASH_ASSET_ID) {
        await api.post('/api/portfolio/buy', { code: submitCode, qty: submitQty, price: form.price })
      } else {
        try {
          await api.post('/api/portfolio/buy_with_cash', {
            code: submitCode,
            name: form.name || modal.code || submitCode,
            qty: submitQty,
            price: form.price,
            cash_asset_id: selectedCashAssetId,
            curr: form.curr || 'CNY',
            asset_type: form.market || 'a',
          })
        } catch (error) {
          if (!isNotFoundError(error)) throw error
          await api.post('/api/portfolio/buy', { code: submitCode, qty: submitQty, price: form.price })
        }
      }
    } else if (modal.type === 'sell') {
      const selectedCashAssetId = Number(form.cashAssetId)
      if (!Number.isFinite(selectedCashAssetId) || selectedCashAssetId <= 0) {
        restorePortfolioSnapshot(snapshot)
        alert(`请先选择 ${targetTradeCurrency.value} 回款账户`)
        return
      }
      try {
        await api.post('/api/portfolio/sell_to_cash', {
          code: submitCode,
          qty: submitQty,
          price: form.price,
          cash_asset_id: selectedCashAssetId,
        })
      } catch (error) {
        if (!isNotFoundError(error)) throw error
        await api.post('/api/portfolio/sell', { code: submitCode, qty: submitQty, price: form.price })
      }
    } else {
      await api.post('/api/portfolio/modify', {
        code: submitCode,
        qty: form.qty,
        price: form.price,
        adjustment: form.adjustment,
      })
    }
  } catch (error) {
    restorePortfolioSnapshot(snapshot)
    alert((error as Error)?.message || '保存失败，请稍后重试')
    return
  }
  closeModal()
  await refresh('force')
}

watch(
  () => [modal.visible, modal.type, form.code, form.fundInputMode, form.market] as const,
  () => {
    if (showFundInputMode.value && isFundAmountMode.value) {
      scheduleFundNavPrefill()
    }
  },
)

watch(
  () => [modal.visible, modal.type, form.curr, cashAccounts.value.length] as const,
  ([visible, type]) => {
    if (!visible) return
    if (type === 'buy' || type === 'sell') {
      applyDefaultCashSelection()
      void ensureCashAccountsLoaded()
    }
  },
)

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

async function saveAsImage() {
  const target = document.getElementById('capture-area-invest')
  if (!target) return
  const canvas = await html2canvas(target, {
    backgroundColor: theme.value === 'light' ? '#f7fbff' : '#0a0e27',
    scale: 2,
    useCORS: true,
  })
  const link = document.createElement('a')
  link.download = `kaka-invest-${Date.now()}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
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
  try {
    await refresh(restored ? 'light' : 'force')
  } finally {
    store.startAutoRefresh()
    startStaticRefresh()
  }
})

onBeforeUnmount(() => {
  if (staticRefreshTimer) {
    window.clearInterval(staticRefreshTimer)
    staticRefreshTimer = null
  }
  if (navPrefillTimer !== null) {
    window.clearTimeout(navPrefillTimer)
    navPrefillTimer = null
  }
  store.stopAutoRefresh()
  document.removeEventListener('click', handleDocumentClick)
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
  color: var(--legacy-text-secondary);
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
  border: 1px solid var(--legacy-action-btn-border);
  background: var(--legacy-action-btn-bg);
  color: var(--legacy-text-primary);
  font-size: var(--inv-fs-sub);
  font-weight: 600;
  cursor: pointer;
}

.action-trigger:hover {
  background: var(--legacy-action-btn-hover-bg);
}

.action-dropdown {
  position: absolute;
  top: calc(32px * var(--legacy-density-space-scale));
  left: 50%;
  transform: translateX(-50%);
  width: calc(102px * var(--legacy-density-card-minh));
  background: var(--legacy-dropdown-bg);
  border: 1px solid var(--legacy-border);
  border-radius: 10px;
  padding: calc(5px * var(--legacy-density-space-scale));
  display: flex;
  flex-direction: column;
  gap: calc(3px * var(--legacy-density-space-scale));
  box-shadow: var(--legacy-dropdown-shadow);
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
  color: var(--legacy-action-danger-text);
}

.menu-item.danger:hover {
  background: var(--legacy-action-danger-hover-bg);
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
  margin-bottom: calc(15px * var(--legacy-density-space-scale));
}

.close-btn {
  width: calc(34px * var(--legacy-density-space-scale));
  height: calc(34px * var(--legacy-density-space-scale));
  border-radius: 50%;
  border: none;
  background: var(--legacy-bg-tertiary);
  color: var(--legacy-text-primary);
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
  background: var(--legacy-input-bg);
  border: 1px solid var(--legacy-border);
  border-radius: 12px;
  color: var(--legacy-input-text);
  padding: calc(10px * var(--legacy-density-space-scale));
}

.fund-mode-switch {
  display: flex;
  gap: 8px;
}

.fund-mode-btn {
  flex: 1;
  border: 1px solid var(--legacy-border);
  border-radius: 10px;
  background: var(--legacy-input-bg);
  color: var(--legacy-text-primary);
  padding: 8px 10px;
  cursor: pointer;
  font-weight: 600;
}

.fund-mode-btn.active {
  background: var(--legacy-accent, #3b82f6);
  color: #fff;
  border-color: var(--legacy-accent, #3b82f6);
}

.fund-mode-hint {
  margin-top: 6px;
  color: var(--legacy-text-secondary);
  font-size: 12px;
}

.fund-mode-error {
  margin-top: 6px;
  color: #ef4444;
  font-size: 12px;
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

/* 浅色主题：投资页 1:1 风格覆盖（仅本页） */
.kk-invest.kk-light-v1 {
  color: #0f172a;
}

.kk-invest.kk-light-v1 .legacy-section {
  background: var(--legacy-bg-secondary);
  border: 1px solid var(--legacy-border);
  box-shadow: var(--legacy-shadow);
  border-radius: var(--legacy-radius);
}

.kk-invest.kk-light-v1 .index-grid {
  gap: 12px;
}

.kk-invest.kk-light-v1 .idx-card {
  background: var(--legacy-bg-tertiary);
  border: 1px solid var(--legacy-border);
  border-radius: 18px;
  padding: 14px;
  box-shadow: var(--legacy-shadow);
}

.kk-invest.kk-light-v1 .idx-name,
.kk-invest.kk-light-v1 .total-mv-label,
.kk-invest.kk-light-v1 .pnl-label,
.kk-invest.kk-light-v1 .table-legacy th,
.kk-invest.kk-light-v1 .name-secondary,
.kk-invest.kk-light-v1 .pnl-hint,
.kk-invest.kk-light-v1 .input-label,
.kk-invest.kk-light-v1 .empty {
  color: rgba(15, 23, 42, 0.55);
  font-weight: 900;
}

.kk-invest.kk-light-v1 .idx-value {
  color: rgba(15, 23, 42, 0.9);
}

.kk-invest.kk-light-v1 .up {
  color: #ef4444;
}

.kk-invest.kk-light-v1 .down {
  color: #10b981;
}

.kk-invest.kk-light-v1 .assets-header {
  gap: 22px;
}

.kk-invest.kk-light-v1 .main-mv {
  font-weight: 900;
  letter-spacing: -1px;
  background: linear-gradient(135deg, #ff4d8d 0%, #6366f1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.kk-invest.kk-light-v1 .pnl-stats {
  gap: 10px;
  flex-wrap: wrap;
}

.kk-invest.kk-light-v1 .pnl-stat-item {
  background: var(--legacy-bg-tertiary);
  border: 1px solid var(--legacy-border);
  border-radius: 18px;
  padding: 12px 14px;
  min-width: 160px;
  box-shadow: var(--legacy-shadow);
}

.kk-invest.kk-light-v1 .pnl-value {
  font-weight: 900;
}

.kk-invest.kk-light-v1 .pnl-rate {
  font-weight: 900;
}

.kk-invest.kk-light-v1 .table-header {
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.1);
}

.kk-invest.kk-light-v1 .table-header h2 {
  font-size: 20px;
  font-weight: 900;
  letter-spacing: -0.2px;
}

.kk-invest.kk-light-v1 .legacy-btn-primary {
  border: 0;
  border-radius: 999px;
  padding: 0 14px;
  font-size: 12px;
  font-weight: 900;
  color: #fff;
  background: linear-gradient(135deg, #ff4d8d 0%, #6366f1 100%);
  box-shadow: 0 16px 40px rgba(99, 102, 241, 0.22);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.kk-invest.kk-light-v1 .legacy-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 22px 55px rgba(99, 102, 241, 0.28);
}

.kk-invest.kk-light-v1 .category-tabs {
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 18px;
  padding: 4px;
}

.kk-invest.kk-light-v1 .tab-item {
  color: rgba(15, 23, 42, 0.55);
  font-size: 13px;
  font-weight: 900;
}

.kk-invest.kk-light-v1 .tab-item.active {
  color: var(--legacy-text-primary);
  background: rgba(59, 130, 246, 0.14);
  border: 1px solid rgba(59, 130, 246, 0.24);
}

.kk-invest.kk-light-v1 .table-legacy th {
  background: rgba(255, 255, 255, 0.45);
  border-bottom: none;
}

.kk-invest.kk-light-v1 .table-legacy td {
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
}

.kk-invest.kk-light-v1 .name-primary,
.kk-invest.kk-light-v1 .qty-cell,
.kk-invest.kk-light-v1 .holding-cell,
.kk-invest.kk-light-v1 .price-line.current,
.kk-invest.kk-light-v1 .table-pnl-amount {
  color: rgba(15, 23, 42, 0.9);
}

.kk-invest.kk-light-v1 .price-line.cost,
.kk-invest.kk-light-v1 .table-pnl-rate {
  color: rgba(15, 23, 42, 0.55);
}

.kk-invest.kk-light-v1 .td-day-pnl .pnl-cell,
.kk-invest.kk-light-v1 .td-total-pnl .pnl-cell {
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
  padding: 0;
}

.kk-invest.kk-light-v1 .action-trigger {
  border: 1px solid var(--legacy-action-btn-border);
  background: var(--legacy-action-btn-bg);
  color: var(--legacy-text-primary);
}

.kk-invest.kk-light-v1 .action-trigger:hover {
  background: var(--legacy-action-btn-hover-bg);
}

.kk-invest.kk-light-v1 .action-dropdown {
  background: var(--legacy-dropdown-bg);
  border: 1px solid var(--legacy-border);
  box-shadow: var(--legacy-dropdown-shadow);
}

.kk-invest.kk-light-v1 .menu-item {
  color: rgba(15, 23, 42, 0.85);
}

.kk-invest.kk-light-v1 .menu-item:hover {
  background: rgba(99, 102, 241, 0.12);
}

.kk-invest.kk-light-v1 .menu-item.danger {
  color: rgba(239, 68, 68, 0.95);
}

.kk-invest.kk-light-v1 .menu-item.danger:hover {
  background: rgba(239, 68, 68, 0.1);
}

.kk-invest.kk-light-v1 .overlay {
  background: rgba(15, 23, 42, 0.2);
  backdrop-filter: blur(10px);
}

.kk-invest.kk-light-v1 .modal {
  background: rgba(255, 255, 255, 0.78);
  border-radius: 26px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  box-shadow: 0 30px 80px rgba(15, 23, 42, 0.18);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}

.kk-invest.kk-light-v1 .modal-header h3,
.kk-invest.kk-light-v1 .close-btn {
  color: rgba(15, 23, 42, 0.9);
}

.kk-invest.kk-light-v1 .close-btn {
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: rgba(255, 255, 255, 0.8);
}

.kk-invest.kk-light-v1 .modal-input {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(15, 23, 42, 0.1);
  color: rgba(15, 23, 42, 0.9);
}

.kk-invest.kk-light-v1 .modal-input:focus {
  border-color: rgba(99, 102, 241, 0.35);
  box-shadow: 0 0 0 6px rgba(99, 102, 241, 0.14);
}

.kk-invest.kk-light-v1 .btn-primary.full {
  background: linear-gradient(135deg, #ff4d8d 0%, #6366f1 100%);
  box-shadow: 0 16px 40px rgba(99, 102, 241, 0.22);
}

</style>
