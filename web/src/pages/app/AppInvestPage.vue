<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePrivacyMode } from '@/shared/privacyMode'
import { toNumber } from '@/shared/format'
import { useKonaStore } from '@/stores/composables'
import { useMarketStore } from '@/stores/market'
import { useRealtimeTodayStore } from '@/stores/realtimeToday'
import { buildMarketSummaries, buildPortfolioSummary } from '@/stores/portfolioMetrics'
import {
  formatLatestNavDateText,
  isDateToday,
  isFundAsset,
  readLatestNavDate,
  shouldShowFundNavMeta
} from '@/shared/assetDisplay'
import { buildInvestHoldingRows } from '@/stores/investHoldingRows'
import { InvestTradeModal, LedgerManageModal } from '@/components'
import InvestHoldingList from '@/components/business/InvestHoldingList.vue'
import InvestLedgerSelector from '@/components/business/InvestLedgerSelector.vue'
import InvestMarketGrid from '@/components/business/InvestMarketGrid.vue'
import InvestSummaryCards from '@/components/business/InvestSummaryCards.vue'
import AppShell from '@/layouts/AppShell.vue'
import { useLedgerScopeStore } from '@/stores/ledgerScope'
import type { PositionRow } from '@/stores/types'
import { useInvestReadState } from './useInvestReadState'

// Stores & Composables
const store = useKonaStore()
const marketStore = useMarketStore()
const realtimeTodayStore = useRealtimeTodayStore()
const ledgerStore = useLedgerScopeStore()
const router = useRouter()
const { maskValue } = usePrivacyMode()
function masked(text: string): string {
  return maskValue(text)
}

// State
const selectedTab = ref('all')
const holdingsView = ref<'card' | 'row'>('card')

// Computed for rates and conversions
const rates = computed(() => marketStore.rates)

function rateToCny(curr?: string): number {
  const c = String(curr || 'CNY').toUpperCase()
  return toNumber(rates.value?.[c], 1) || 1
}

// Current currency formatting config (Follow Homepage)
const currentCurrency = ref<'CNY' | 'USD' | 'HKD'>('CNY')
const currMeta = computed(() => {
  if (currentCurrency.value === 'USD') return { sym: '$ ', label: '美元' }
  if (currentCurrency.value === 'HKD') return { sym: 'HK$ ', label: '港币' }
  return { sym: '¥ ', label: '人民币' }
})

function toDisplay(cnyVal: number): number {
  if (currentCurrency.value === 'USD') return cnyVal / rateToCny('USD')
  if (currentCurrency.value === 'HKD') return cnyVal / rateToCny('HKD')
  return cnyVal
}

function formatCurrency(cnyValue: number, signed = false, integerOnly = false): string {
  const val = toDisplay(cnyValue)
  const sym = currMeta.value.sym
  const sign = signed && cnyValue >= 0 ? '+' : signed && cnyValue < 0 ? '-' : ''
  const absVal = Math.abs(val)
  const formatted = integerOnly
    ? Math.round(absVal).toLocaleString('zh-CN')
    : absVal >= 1000
      ? Math.round(absVal).toLocaleString('zh-CN')
      : absVal.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
  return `${sign}${sym}${formatted}`
}

function formatHoldingCurrency(cnyValue: number): string {
  const val = Math.round(Math.abs(toDisplay(cnyValue)))
  return `${currMeta.value.sym}${val.toLocaleString('zh-CN')}`
}

// Utility

// Data Processing
const rows = computed<PositionRow[]>(() => (store?.rows as any)?.value || [])
const {
  trendMap,
  loadAssetTrends,
  refreshInvestReadState,
  startInvestAutoRefresh,
  stopInvestAutoRefresh
} = useInvestReadState(rows)

const investTotal = computed(() => {
  const summary = buildPortfolioSummary(rows.value || [])
  const totals = realtimeTodayStore.payload?.totals || {}
  return {
    mv: Number(totals.total_asset ?? summary.totalValue),
    cost: summary.totalCostAbs,
    marketValue: Number(totals.total_market_value ?? summary.totalValue),
    dayPnl: Number(totals.day_pnl ?? summary.todayPnl),
    floatPnl: summary.floatPnl,
    totalPnl: Number(totals.total_pnl ?? summary.totalPnl),
    dayRate: Number(totals.day_pnl_rate ?? summary.dayRate),
    floatRate: summary.floatRate,
    totalRate: Number(totals.total_pnl_rate ?? summary.totalRate)
  }
})

// Market breakdowns
const marketCards = computed(() => buildMarketSummaries(rows.value || []))

// Distribution Donut Chart
const distributionData = computed(() => {
  const activeSectors = marketCards.value.filter(m => m.mv > 0)
  const localTotal = activeSectors.reduce((sum, m) => sum + m.mv, 0) || 1

  return activeSectors
    .map(m => ({
      name: m.name,
      percent: (m.mv / localTotal) * 100,
      value: m.mv,
      color:
        m.name === '美股'
          ? '#5B8DEF'
          : m.name === 'A股'
            ? '#F05A55'
            : m.name === '港股'
              ? '#3ECF82'
              : '#F2C94C'
    }))
    .sort((a, b) => b.value - a.value)
})

// Helpers for SVG Chart
const slices = computed(() => {
  let currentPercent = 0
  return distributionData.value.map(d => {
    const start = currentPercent
    currentPercent += d.percent
    return { ...d, start, end: currentPercent }
  })
})

function describeArc(x: number, y: number, radius: number, startAngle: number, endAngle: number) {
  const start = polarToCartesian(x, y, radius, endAngle)
  const end = polarToCartesian(x, y, radius, startAngle)
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1'
  return ['M', start.x, start.y, 'A', radius, radius, 0, largeArcFlag, 0, end.x, end.y].join(' ')
}

function polarToCartesian(
  centerX: number,
  centerY: number,
  radius: number,
  angleInDegrees: number
) {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0
  return {
    x: centerX + radius * Math.cos(angleInRadians),
    y: centerY + radius * Math.sin(angleInRadians)
  }
}

// Holdings filtering
// Utility

const filteredRows = computed(() =>
  buildInvestHoldingRows({
    rows: rows.value || [],
    selectedTab: selectedTab.value,
    totalMarketValue: investTotal.value.mv,
    trendMap: trendMap.value
  })
)

function quoteLabel(row: any): string {
  if (isFundAsset(row)) {
    const value = toNumber(row?.price)
    return value > 0 ? `${getCurrencySymbol(row?.curr)}${formatAssetPrice(value)}` : '--'
  }
  if (row?.quotePending) return '更新中'
  const value = toNumber(row?.price)
  return value > 0 ? `${getCurrencySymbol(row?.curr)}${formatAssetPrice(value)}` : '--'
}

function dayPnlRateLabel(row: any): string {
  const latestNavDate = readLatestNavDate(row)
  const shouldHoldFundDayPnl =
    isFundAsset(row) && latestNavDate != null && !isDateToday(latestNavDate)
  if (
    shouldHoldFundDayPnl ||
    row?.navUpdatePending ||
    row?.quotePending ||
    row?.dayPnlVisible === false
  )
    return '--'
  return formatPct(toNumber(row?.dayPnlRate))
}

function formatPnlOriginal(value: number, curr?: string): string {
  if (value === 0) return '--'
  const sign = value > 0 ? '+' : '-'
  const sym = getCurrencySymbol(curr)
  const formatted = Math.round(Math.abs(value)).toLocaleString('zh-CN')
  return `${sign}${sym}${formatted}`
}

function dayPnlAmountLabel(row: any): string {
  if (row?.dayPnlVisible === false) return '--'
  return masked(formatPnlOriginal(toNumber(row?.dayPnlRaw), row?.curr))
}

function quoteMetaLabel(row: any): string {
  if (!shouldShowFundNavMeta(row)) return ''
  const dateText = formatLatestNavDateText(readLatestNavDate(row))
  return dateText ? `最新净值 (${dateText})` : '最新净值'
}

// Utility
function formatPct(v: number): string {
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`
}
function valueClass(v: number): string {
  return v >= 0 ? 'up' : 'dn'
}
function getMarketName(m: string) {
  if (m === 'us') return '美股'
  if (m === 'hk') return '港股'
  if (m === 'a') return 'A股'
  return '基金'
}
function formatLocal(v: any) {
  return Number(v || 0).toLocaleString()
}

function formatAssetPrice(value: unknown): string {
  const amount = toNumber(value)
  if (!Number.isFinite(amount) || amount === 0) return '0.00'

  const absAmount = Math.abs(amount)
  if (absAmount >= 1000) {
    return absAmount.toLocaleString('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })
  }

  return absAmount.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4
  })
}

function getCurrencySymbol(curr?: string) {
  if (curr === 'USD') return '$'
  if (curr === 'HKD') return 'HK$'
  return '¥'
}

function getQtyFontSize(val: string | number) {
  const s = String(val)
  if (s.length > 12) return '9px'
  if (s.length > 9) return '10px'
  return '11px'
}

watch(
  () => (rows.value || []).map((row: any) => `${row?.code || ''}:${row?.name || ''}`).join('|'),
  () => {
    void loadAssetTrends()
  }
)

onMounted(async () => {
  await ledgerStore.loadLedgers()
  await refreshInvestReadState()
  startInvestAutoRefresh()
})

onBeforeUnmount(() => {
  stopInvestAutoRefresh()
})

// Ledger state
const showLedgerManageModal = ref(false)

function selectLedger(ledgerId: number) {
  ledgerStore.switchLedger(ledgerId)
}

function openLedgerManage() {
  showLedgerManageModal.value = true
}

watch(
  () => ledgerStore.currentLedgerId,
  () => {
    void refreshInvestReadState()
  }
)

// Modal states
const showTradeModal = ref(false)
const tradeModalAsset = ref<any>(null)

function openAddTradeModal() {
  tradeModalAsset.value = null
  showTradeModal.value = true
}

async function openAssetDetail(row: any) {
  const code = String(row?.code || '').trim()
  if (!code) return
  await router.push(`/app/asset/${encodeURIComponent(code)}`)
  await refreshInvestReadState()
}

const handleTradeSuccess = async () => {
  await refreshInvestReadState()
}
</script>

<template>
  <AppShell title="投资分析">
    <div class="kk-page invest-page">
      <div class="modern-shell">
        <InvestLedgerSelector
          :ledgers="ledgerStore.ledgers"
          :current-ledger-id="ledgerStore.currentLedgerId"
          :current-ledger-name="ledgerStore.currentLedgerName"
          :is-default-ledger="ledgerStore.isDefault"
          @select-ledger="selectLedger"
          @manage="openLedgerManage"
        />

        <InvestSummaryCards
          :current-currency="currentCurrency"
          :invest-total="investTotal"
          :distribution-data="distributionData"
          :slices="slices"
          :masked="masked"
          :format-currency="formatCurrency"
          :value-class="valueClass"
          :format-pct="formatPct"
          :describe-arc="describeArc"
        />

        <InvestMarketGrid
          :market-cards="marketCards"
          :masked="masked"
          :format-currency="formatCurrency"
          :value-class="valueClass"
          :format-pct="formatPct"
        />

        <InvestHoldingList
          v-model:selected-tab="selectedTab"
          v-model:holdings-view="holdingsView"
          :rows="filteredRows"
          :masked="masked"
          :format-holding-currency="formatHoldingCurrency"
          :get-market-name="getMarketName"
          :get-qty-font-size="getQtyFontSize"
          :format-local="formatLocal"
          :quote-label="quoteLabel"
          :quote-meta-label="quoteMetaLabel"
          :value-class="valueClass"
          :day-pnl-rate-label="dayPnlRateLabel"
          :day-pnl-amount-label="dayPnlAmountLabel"
          :format-pnl-original="formatPnlOriginal"
          :get-currency-symbol="getCurrencySymbol"
          :format-asset-price="formatAssetPrice"
          :format-pct="formatPct"
          @add-asset="openAddTradeModal"
          @open-asset="openAssetDetail"
        />
      </div>
    </div>

    <!-- Add Asset Modal -->
    <InvestTradeModal
      v-model:show="showTradeModal"
      :asset="tradeModalAsset"
      mode="add"
      @success="handleTradeSuccess"
    />

    <!-- Ledger Management Modal -->
    <LedgerManageModal v-model:show="showLedgerManageModal" />
  </AppShell>
</template>

<style scoped>
@import '@/styles/homepage-original.css';

.invest-page {
  padding: 0 0 120px;
  min-height: auto;
  background: transparent;
  color: var(--text);
  font-family:
    'DM Sans',
    -apple-system,
    BlinkMacSystemFont,
    sans-serif;
}

.modern-shell {
  width: 100%;
}

[data-theme='light'] .invest-page {
  background:
    radial-gradient(
      circle at top left,
      color-mix(in srgb, var(--blue) 10%, transparent),
      transparent 28%
    ),
    var(--bg);
}
</style>
