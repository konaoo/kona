<script setup lang="ts">
/**
 * AppHomePage - 首页（1:1复刻版 - 原始CSS样式）
 * 完全按照参考HTML复刻UI，使用原始CSS类名系统
 */

import { computed, onMounted, onBeforeUnmount, ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/shared/http'
import { toNumber } from '@/shared/format'
import { buildTrendSparklinePath, type TrendItem } from '@/shared/assetTrend'
import { useKonaStore } from '@/stores/composables'
import { usePrivacyMode } from '@/shared/privacyMode'
import { useMarketStore } from '@/stores/market'
import { InvestTradeModal } from '@/components'
import AssetLogo from '@/components/base/AssetLogo.vue'
import AppShell from '../../layouts/AppShell.vue'


// Types
type AssetType = 'cash' | 'other' | 'liability'
type SimpleAsset = { id: number; icon?: string; name: string; amount: number; curr?: string }
type ChartPeriod = '1m' | '3m' | '6m' | '1y' | 'all'
type SnapshotPoint = { date: string; total_asset: number; day_pnl?: number }

// Stores & Composables
const store = useKonaStore()
const router = useRouter()
const { maskValue } = usePrivacyMode()
const marketStore = useMarketStore()

// State
const isLoading = ref(true)
const cashAssets = ref<SimpleAsset[]>([])
const otherAssets = ref<SimpleAsset[]>([])
const liabilities = ref<SimpleAsset[]>([])
const modalVisible = ref(false)
const isFormModalVisible = ref(false)
const isDeleteConfirmVisible = ref(false)
const modalType = ref<AssetType>('cash')
const modalMode = ref<'add' | 'edit'>('add')
const showTradeModal = ref(false)
const tradeModalAsset = ref<any>(null)
const tradeModalMode = ref<'add' | 'buy' | 'sell' | 'adjust'>('add')
const chartPeriod = ref<ChartPeriod>('1m')
const chartHoverIndex = ref<number | null>(null)
const chartSwitchAnimating = ref(false)
const selectedTab = ref('all')
const holdingsView = ref<'card'|'row'>('card')
const marketIndices = ref<any[]>([])
const activeSegment = ref<AssetType | null>(null)
const historyPoints = ref<SnapshotPoint[]>([])
const chartLoading = ref(false)
const chartError = ref('')
const trendMap = ref<Record<string, TrendItem>>({})
const marketIndicesCacheKey = 'kaka:web:market-indices'
const chartContainer = ref<HTMLElement | null>(null)

const chartPeriodOptions: Array<{ label: string; value: ChartPeriod }> = [
  { label: '近1月', value: '1m' },
  { label: '近3月', value: '3m' },
  { label: '近6月', value: '6m' },
  { label: '近1年', value: '1y' },
  { label: '全部', value: 'all' },
]

// Currency Switcher State
const currencyOpen = ref(false)
const currentCurrency = ref<'CNY'|'USD'|'HKD'>('CNY')
const assetCurrencyOpen = ref(false)

const form = reactive<{ id: number | null; icon: string; name: string; amount: number; curr: string }>({
  id: null,
  icon: '🏦',
  name: '',
  amount: 0,
  curr: 'CNY',
})

function defaultAssetIcon(type: AssetType): string {
  if (type === 'cash') return '🏦'
  if (type === 'other') return '📦'
  return '💳'
}

let staticRefreshTimer: number | null = null
let chartSwitchTimer: number | null = null

// Computed
const rows = computed(() => {
  const data = store?.rows?.value || []
  return Array.isArray(data) ? data : []
})

const rates = computed(() => marketStore.rates)

function rateToCny(curr?: string): number {
  const c = String(curr || 'CNY').toUpperCase()
  return toNumber(rates.value?.[c], 1) || 1
}

function toCny(amount: unknown, curr?: string): number {
  return toNumber(amount || 0) * rateToCny(curr)
}

// 投资资产总计
const investTotal = computed(() => {
  let mv = 0
  let cost = 0
  let dayPnl = 0
  let floatPnl = 0
  let totalPnl = 0

  const rowsData = rows.value || []
  for (const row of rowsData) {
    if (!row || typeof row !== 'object') continue
    try {
      const rate = rateToCny(String(row.curr))
      const rowValue = Number(row.value) || 0
      const rowCost = (Number(row.cost) || 0) * rate
      mv += rowValue * rate
      cost += Math.abs(rowCost)
      dayPnl += (Number(row.dayPnlAggregate) || 0) * rate
      floatPnl += ((rowValue * rate) - rowCost)
      totalPnl += (Number(row.totalPnl) || 0) * rate
    } catch (e) {
      console.error('Error processing row:', e)
    }
  }

  return {
    mv,
    cost,
    dayPnl,
    floatPnl,
    totalPnl,
    dayRate: mv > 0 && (mv - dayPnl) > 0 ? (dayPnl / (mv - dayPnl)) * 100 : 0,
    floatRate: cost > 0 ? (floatPnl / cost) * 100 : 0,
    totalRate: cost > 0 ? (totalPnl / cost) * 100 : 0,
  }
})

// 各类资产总计
const cashTotal = computed(() => (cashAssets.value || []).reduce((sum, item) => sum + toCny(item.amount, item.curr), 0))
const otherTotal = computed(() => (otherAssets.value || []).reduce((sum, item) => sum + toCny(item.amount, item.curr), 0))
const liabilityTotal = computed(() => (liabilities.value || []).reduce((sum, item) => sum + toCny(item.amount, item.curr), 0))
const totalAssetsCny = computed(() => (investTotal.value?.mv || 0) + cashTotal.value + otherTotal.value - liabilityTotal.value)

// Modal Data Getters
const currentTypeAssets = computed(() => {
  if (modalType.value === 'cash') return cashAssets.value
  if (modalType.value === 'other') return otherAssets.value
  return liabilities.value
})

const currentTypeAssetsTotal = computed(() => {
  if (modalType.value === 'cash') return cashTotal.value
  if (modalType.value === 'other') return otherTotal.value
  return liabilityTotal.value
})

const modalTitle = computed(() => {
  if (modalType.value === 'cash') return '现金资产'
  if (modalType.value === 'other') return '其他资产'
  return '我的负债'
})

const modalAddLabel = computed(() => {
  if (modalType.value === 'cash') return '添加现金账户'
  if (modalType.value === 'other') return '添加其他资产'
  return '添加负债记录'
})

const allHistoryPoints = computed(() => {
  return [...historyPoints.value]
    .filter((item) => item && item.date)
    .sort((a, b) => String(a.date).localeCompare(String(b.date)))
})

const filteredHistoryPoints = computed(() => {
  const sorted = allHistoryPoints.value

  if (chartPeriod.value === 'all') return sorted

  const limitMap: Record<Exclude<ChartPeriod, 'all'>, number> = {
    '1m': 30,
    '3m': 90,
    '6m': 180,
    '1y': 365,
  }

  return sorted.slice(-limitMap[chartPeriod.value])
})

const chartRangeLabel = computed(() => {
  const first = filteredHistoryPoints.value[0]
  const last = filteredHistoryPoints.value[filteredHistoryPoints.value.length - 1]
  if (!first || !last) return '资产趋势会在积累几天后显示在这里'
  return `${formatChartDate(first.date)} - ${formatChartDate(last.date)}`
})

const chartSeries = computed(() => {
  return filteredHistoryPoints.value
    .map((item) => ({
      date: String(item.date || ''),
      value: toDisplay(toNumber(item.total_asset, 0)),
    }))
    .filter((item) => item.date && Number.isFinite(item.value))
})

const chartStrokeColor = computed(() => {
  const series = chartSeries.value
  const first = series[0]
  const last = series[series.length - 1]
  if (first && last && series.length >= 2) {
    return last.value >= first.value
      ? '#f05a55'
      : '#3ecf82'
  }
  return (investTotal.value?.dayPnl || 0) >= 0 ? '#f05a55' : '#3ecf82'
})

const chartHeadlineChange = computed(() => {
  const points = filteredHistoryPoints.value
  const first = points[0]
  const last = points[points.length - 1]
  if (first && last) {
    return toNumber(last.total_asset, 0) - toNumber(first.total_asset, 0)
  }
  return 0
})

const chartHeadlineLabel = computed(() => {
  if (chartPeriod.value === '1m') return '近1月'
  if (chartPeriod.value === '3m') return '近3月'
  if (chartPeriod.value === '6m') return '近6月'
  if (chartPeriod.value === '1y') return '近1年'
  return '累计'
})

const chartGeometry = computed(() => {
  const width = 1044
  const top = 10
  const bottom = 96
  const values = chartSeries.value

  if (!values.length) {
    return {
      linePath: '',
      areaPath: '',
      lastX: width,
      lastY: bottom,
      guideX: width,
      color: chartStrokeColor.value,
      points: [] as Array<{ x: number; y: number }>,
      hasData: false,
    }
  }

  const firstValue = values[0]
  const source = values.length === 1 && firstValue
    ? [firstValue, { ...firstValue, date: `${firstValue.date}-end` }]
    : values

  if (source.length < 2) {
    return {
      linePath: '',
      areaPath: '',
      lastX: width,
      lastY: bottom,
      guideX: width,
      color: chartStrokeColor.value,
      points: [] as Array<{ x: number; y: number }>,
      hasData: false,
    }
  }

  const onlyValues = source.map((item) => item.value)
  const minVal = Math.min(...onlyValues)
  const maxVal = Math.max(...onlyValues)
  const range = Math.max(maxVal - minVal, 1)
  const points = source.map((item, index) => {
    const x = (width / (source.length - 1)) * index
    const ratio = (item.value - minVal) / range
    const y = maxVal === minVal
      ? (top + bottom) / 2
      : bottom - ratio * (bottom - top)
    return { x, y }
  })

  const firstPoint = points[0]
  const secondPoint = points[1]
  const lastPoint = points[points.length - 1]
  const lastControl = points[points.length - 2]

  if (!firstPoint || !secondPoint || !lastPoint || !lastControl) {
    return {
      linePath: '',
      areaPath: '',
      lastX: width,
      lastY: bottom,
      guideX: width,
      color: chartStrokeColor.value,
      points: [] as Array<{ x: number; y: number }>,
      hasData: false,
    }
  }

  let linePath = `M${firstPoint.x.toFixed(1)},${firstPoint.y.toFixed(1)}`
  if (points.length === 2) {
    linePath += ` L${secondPoint.x.toFixed(1)},${secondPoint.y.toFixed(1)}`
  } else {
    for (let i = 1; i < points.length - 1; i += 1) {
      const control = points[i]
      const next = points[i + 1]
      if (!control || !next) continue
      const midX = (control.x + next.x) / 2
      const midY = (control.y + next.y) / 2
      linePath += ` Q${control.x.toFixed(1)},${control.y.toFixed(1)} ${midX.toFixed(1)},${midY.toFixed(1)}`
    }
    linePath += ` Q${lastControl.x.toFixed(1)},${lastControl.y.toFixed(1)} ${lastPoint.x.toFixed(1)},${lastPoint.y.toFixed(1)}`
  }

  const areaPath = `${linePath} L${lastPoint.x.toFixed(1)},120 L${firstPoint.x.toFixed(1)},120 Z`

  return {
    linePath,
    areaPath,
    lastX: lastPoint.x,
    lastY: lastPoint.y,
    guideX: lastPoint.x,
    color: chartStrokeColor.value,
    points,
    hasData: true,
  }
})

const hoveredChartPoint = computed(() => {
  const hoverIndex = chartHoverIndex.value
  if (hoverIndex === null) return null
  const point = chartGeometry.value.points?.[hoverIndex]
  const series = chartSeries.value[hoverIndex]
  if (!point || !series) return null
  return {
    ...series,
    x: point.x,
    y: point.y,
  }
})

const chartTooltipStyle = computed(() => {
  const point = hoveredChartPoint.value
  if (!point) return {}
  const ratio = point.x / 1044
  if (ratio <= 0.14) {
    return {
      left: `${Math.max(ratio * 100, 2)}%`,
      top: '-72px',
      transform: 'translateX(0)',
    }
  }
  if (ratio >= 0.86) {
    return {
      left: `${Math.min(ratio * 100, 98)}%`,
      top: '-72px',
      transform: 'translateX(-100%)',
    }
  }
  return {
    left: `${ratio * 100}%`,
    top: '-72px',
    transform: 'translateX(-50%)',
  }
})

// Segment Drawer Data
const activeDrawerData = computed(() => {
  if (!activeSegment.value) return []
  if (activeSegment.value === 'cash') return cashAssets.value.map(a => ({ ...a, type: 'cash' as const, code: undefined }))
  if (activeSegment.value === 'other') return otherAssets.value.map(a => ({ ...a, type: 'other' as const, code: undefined }))
  if (activeSegment.value === 'liability') return liabilities.value.map(a => ({ ...a, type: 'liability' as const, code: undefined }))
  return []
})

function toggleSegment(type: AssetType) {
  if (activeSegment.value === type) {
    activeSegment.value = null
  } else {
    activeSegment.value = type
  }
}

async function goToInvestPage() {
  await router.push('/app/invest')
}

function openInvestTradeModal(item: any, mode: 'buy' | 'sell' | 'adjust' = 'buy') {
  tradeModalAsset.value = item
  tradeModalMode.value = mode
  showTradeModal.value = true
}

async function handleTradeSuccess() {
  try {
    await store.refreshStaticOnly()
    void store.refreshQuotesOnly()
  } catch (e) {
    console.error('Failed to reload home invest data', e)
  }
}


// Current currency formatting config
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

// Helpers
function formatCny(value: number): string {
  // We keep this for backward compatibility or rename to formatSelected
  return formatCurrency(value)
}

function formatSignedCny(value: number): string {
  return formatCurrency(value, true)
}

function formatCurrency(cnyValue: number, signed = false): string {
  const val = toDisplay(cnyValue)
  const sym = currMeta.value.sym
  const sign = signed && cnyValue >= 0 ? '+' : signed && cnyValue < 0 ? '-' : ''
  const absVal = Math.abs(val)
  
  // For non-CNY, we might want 2 decimals if it's small, 
  // but for the 1:1 look, round numbers are often used in headers.
  // However, for accuracy we should probably allow 2 decimals if needed.
  const formatted = absVal >= 1000 ? Math.round(absVal).toLocaleString('zh-CN') : absVal.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
  
  return `${sign}${sym}${formatted}`
}

const filteredRows = computed(() => {
  const validRows = (rows.value || []).filter(row => row && typeof row === 'object')
  const base = selectedTab.value === 'all'
    ? validRows
    : validRows.filter(row => (row?.category || row?.market) === selectedTab.value)
  const totalMarketMv = investTotal.value?.mv || 1;
  
  return base.map((row: any) => {
    const qty = Number(row?.qty || 0)
    const displayCostPrice = Number(row?.displayCostPrice || 0)
    const currentPrice = Number(row?.currentPrice || 0)
    
    const localMv = Number(row?.value) || (qty * currentPrice)
    const rate = rateToCny(String(row?.curr || 'CNY'))
    const cnyMv = localMv * rate
    const pct = (cnyMv / totalMarketMv) * 100

    return {
      ...row,
      qty,
      costPrice: displayCostPrice, // 首页展示摊薄后成本
      price: currentPrice || 0,
      dayPnlRate: Number(row?.dayPnlRate || 0),
      // 保持 Store 中的原始字段
      cost: Number(row?.cost) || (qty * displayCostPrice),
      mv: localMv,
      totalPnl: Number(row?.totalPnl) || 0,
      quoteReady: Boolean(row?.quoteReady),
      quotePending: Boolean(row?.quotePending),
      navUpdatePending: Boolean(row?.navUpdatePending),
      category: String(row?.category || row?.market || ''),
      pct,
      spark: buildTrendSparklinePath(trendMap.value[String(row?.code || '')]?.points || []),
      sparkReady: (trendMap.value[String(row?.code || '')]?.points || []).length >= 2,
    }
  })
})

// Helpers

function formatPct(value: number | undefined): string {
  if (typeof value !== 'number' || isNaN(value)) return '0.00%'
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function quoteLabel(row: any): string {
  if (row?.navUpdatePending) return '待净值更新'
  if (row?.quotePending) return '更新中'
  const value = toNumber(row?.price)
  return value > 0 ? `${getCurrencySymbol(row?.curr)}${value}` : '--'
}

function dayPnlRateLabel(row: any): string {
  if (row?.navUpdatePending || row?.quotePending) return '--'
  return formatPct(toNumber(row?.dayPnlRate))
}

function valueClass(value: number | undefined): 'up' | 'dn' | 'neutral' {
  if (value === undefined || value === 0) return 'neutral'
  return value >= 0 ? 'up' : 'dn'
}

function masked(text: string): string {
  return maskValue(text)
}

function formatValue(value: number, curr?: string): string {
  // If global currency is NOT CNY, we convert the item's value to the global display currency?
  // User said "切换汇率需要根据实时汇率进行不同币种的计算". 
  // Usually this means the WHOLE DASHBOARD should flip.
  
  if (currentCurrency.value !== 'CNY') {
    // Convert to CNY first then to Display
    return formatCurrency(toCny(value, curr))
  }

  const symbol = getCurrencySymbol(curr)
  const absVal = Math.abs(value)
  const formatted = absVal % 1 !== 0 ? absVal.toFixed(2) : absVal.toLocaleString('zh-CN')
  return `${symbol} ${formatted}`
}

function formatHoldingValue(value: number, curr?: string): string {
  if (currentCurrency.value !== 'CNY') {
    return formatCurrency(Math.round(Math.abs(toCny(value, curr))))
  }

  const symbol = getCurrencySymbol(curr)
  return `${symbol} ${Math.round(Math.abs(value)).toLocaleString('zh-CN')}`
}

function formatAssetOriginalAmount(value: number, curr?: string): string {
  const symbol = getCurrencySymbol(curr)
  const absVal = Math.abs(toNumber(value, 0))
  const formatted = absVal % 1 !== 0
    ? absVal.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
    : absVal.toLocaleString('zh-CN')
  return `${symbol} ${formatted}`
}

function formatChartDisplayValue(value: number): string {
  const sym = currMeta.value.sym
  const absVal = Math.abs(toNumber(value, 0))
  const formatted = absVal >= 1000
    ? Math.round(absVal).toLocaleString('zh-CN')
    : absVal.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
  return `${sym}${formatted}`
}

function formatChartDate(dateText: string): string {
  const [year = '', month = '', day = ''] = String(dateText || '').split('-')
  if (!year || !month || !day) return String(dateText || '')
  return `${year}.${month}.${day}`
}

function handleChartMouseMove(event: MouseEvent) {
  const container = chartContainer.value
  const points = chartGeometry.value.points || []
  if (!container || points.length === 0) return
  const rect = container.getBoundingClientRect()
  if (!rect.width) return
  const ratio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1)
  const index = Math.round(ratio * (points.length - 1))
  chartHoverIndex.value = Math.min(Math.max(index, 0), points.length - 1)
}

function handleChartMouseLeave() {
  chartHoverIndex.value = null
}

watch(chartPeriod, () => {
  chartSwitchAnimating.value = true
  if (chartSwitchTimer) window.clearTimeout(chartSwitchTimer)
  chartSwitchTimer = window.setTimeout(() => {
    chartSwitchAnimating.value = false
  }, 180)
})

watch(
  () => (rows.value || []).map((row: any) => `${row?.code || ''}:${row?.name || ''}`).join('|'),
  () => { void loadAssetTrends() },
)

const getQtyFontSize = (val: string | number) => {
  const s = String(val)
  if (s.length > 12) return '9px'
  if (s.length > 9) return '10px'
  return '11px'
}

// Methods
async function loadLists() {
  try {
    const [cashRes, otherRes, liabilityRes] = await Promise.all([
      api.get<SimpleAsset[]>('/api/cash_assets'),
      api.get<SimpleAsset[]>('/api/other_assets'),
      api.get<SimpleAsset[]>('/api/liabilities'),
    ])
    cashAssets.value = cashRes || []
    otherAssets.value = otherRes || []
    liabilities.value = liabilityRes || []
  } catch (e) {
    console.error('Failed to load asset lists:', e)
  }
}

async function loadMarketIndices() {
  try {
    const res = await api.get<any[]>('/api/market/indices')
    marketIndices.value = Array.isArray(res) ? res : []
    try {
      localStorage.setItem(marketIndicesCacheKey, JSON.stringify(marketIndices.value))
    } catch {}
  } catch (e) {
    console.error('Failed to load market indices:', e)
  }
}

async function loadHistory() {
  chartLoading.value = true
  chartError.value = ''
  try {
    const res = await api.get<SnapshotPoint[]>('/api/history?days=5000')
    historyPoints.value = Array.isArray(res)
      ? res.map((item) => ({
          date: String(item?.date || ''),
          total_asset: toNumber(item?.total_asset, 0),
          day_pnl: toNumber(item?.day_pnl, 0),
        }))
      : []
  } catch (e) {
    chartError.value = e instanceof Error ? e.message : '历史快照加载失败'
    historyPoints.value = []
    console.error('Failed to load history:', e)
  } finally {
    chartLoading.value = false
  }
}

async function loadAssetTrends() {
  const items = (rows.value || [])
    .filter((row: any) => row?.code)
    .map((row: any) => ({
      code: String(row.code || ''),
      name: String(row.name || ''),
      market: String(row.category || row.market || ''),
    }))

  if (!items.length) {
    trendMap.value = {}
    return
  }

  try {
    const payload = await api.post<{ items?: Record<string, TrendItem> }>('/api/asset/trends', {
      items,
      points: 20,
    })
    trendMap.value = payload?.items || {}
  } catch (e) {
    console.error('Failed to load asset trends:', e)
    trendMap.value = {}
  }
}

async function refreshAll() {
  try {
    await Promise.all([
      store.refreshStaticOnly(),
      loadLists(),
      loadHistory(),
    ])
    await loadAssetTrends()
    void Promise.all([
      store.refreshQuotesOnly(),
      loadMarketIndices(),
    ])
  } catch (e) {
    console.error('Failed to refresh:', e)
  }
}

function getCurrencySymbol(curr?: string) {
  if (curr === 'USD') return '$'
  if (curr === 'HKD') return 'HK$'
  return '¥'
}

function getCurrencyLabel(curr?: string) {
  if (curr === 'USD') return '美元'
  if (curr === 'HKD') return '港币'
  return '人民币'
}



function closeModal() {
  modalVisible.value = false
}

function openFormModal(item?: any) {
  if (item?.type && item.type !== 'invest') {
    modalType.value = item.type
  } else if (activeSegment.value) {
    modalType.value = activeSegment.value
  }
  
  modalMode.value = (item && item.id) ? 'edit' : 'add'
  form.id = item?.id ?? null
  form.icon = item?.icon ?? defaultAssetIcon(modalType.value)
  form.name = item?.name ?? ''
  form.amount = toNumber(item?.amount, 0)
  form.curr = item?.curr || 'CNY'
  isFormModalVisible.value = true
}

function closeFormModal() {
  isFormModalVisible.value = false
  isDeleteConfirmVisible.value = false
  assetCurrencyOpen.value = false
}

async function submitModal() {
  const payload = { id: form.id, icon: form.icon, name: form.name, amount: form.amount, curr: form.curr }
  const map = {
    cash: { add: '/api/cash_assets/add', update: '/api/cash_assets/update' },
    other: { add: '/api/other_assets/add', update: '/api/other_assets/update' },
    liability: { add: '/api/liabilities/add', update: '/api/liabilities/update' },
  } as const
  const route = modalMode.value === 'add' ? map[modalType.value].add : map[modalType.value].update

  await api.post(route, payload)
  closeFormModal()
  await loadLists()
}

async function removeAsset(type: AssetType, id: number) {
  const map = {
    cash: '/api/cash_assets/delete',
    other: '/api/other_assets/delete',
    liability: '/api/liabilities/delete',
  } as const
  await api.post(map[type], { id })
  await loadLists()
}

function openDeleteConfirm() {
  if (modalMode.value !== 'edit' || !form.id) return
  isDeleteConfirmVisible.value = true
}

function closeDeleteConfirm() {
  isDeleteConfirmVisible.value = false
}

async function removeAssetFromForm() {
  if (!form.id) return
  const assetId = form.id
  closeDeleteConfirm()
  closeFormModal()
  await removeAsset(modalType.value, assetId)
}

// Global click handler to close currency menu
function handleGlobalClick() {
  if (currencyOpen.value) currencyOpen.value = false
  if (assetCurrencyOpen.value) assetCurrencyOpen.value = false
}

// Lifecycle
onMounted(async () => {
  document.addEventListener('click', handleGlobalClick)
  isLoading.value = true
  try {
    try {
      const cached = localStorage.getItem(marketIndicesCacheKey)
      if (cached) {
        const parsed = JSON.parse(cached)
        if (Array.isArray(parsed) && parsed.length) {
          marketIndices.value = parsed
        }
      }
    } catch {}
    void store.bootstrap()
    await Promise.all([
      store.refreshStaticOnly(),
      loadLists(),
      loadHistory(),
    ])
    await loadAssetTrends()
    void loadMarketIndices()
    void store.refreshQuotesOnly()
    store.startAutoRefresh()
    staticRefreshTimer = window.setInterval(() => refreshAll(), 60000)
  } finally {
    isLoading.value = false
  }
})


onBeforeUnmount(() => {
  document.removeEventListener('click', handleGlobalClick)
  store.stopAutoRefresh()
  if (staticRefreshTimer) clearInterval(staticRefreshTimer)
  if (chartSwitchTimer) window.clearTimeout(chartSwitchTimer)
})
</script>

<template>
  <AppShell title="我的资产">
    <!-- Content -->

      <!-- Market Index Cards -->
      <!-- Market Index Cards -->
      <div class="market-strip">
        <template v-if="marketIndices && marketIndices.length > 0">
          <div v-for="idx in marketIndices" :key="idx.name" class="card" style="padding:14px 16px;background:var(--s1);border-radius:16px">
            <div class="section-label" style="font-size:11px;margin-bottom:6px">{{ idx.name }}</div>
            <div class="mono" :class="valueClass(idx.change)" style="font-size:16px;font-weight:600">
              {{ idx.name === 'USD/CNY' ? idx.value.toFixed(4) : formatPct(idx.change_pct) }}
            </div>
            <div class="mono text-muted" style="font-size:10px;margin-top:3px">
              {{ idx.name === 'USD/CNY' ? '实时汇率' : idx.value.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}
            </div>
          </div>
        </template>
        <template v-else>
          <!-- Fallback skeletons -->
          <div v-for="i in 6" :key="i" class="card" style="padding:12px 14px;opacity:0.6">
            <div class="section-label" style="font-size:11px;margin-bottom:6px">加载中...</div>
            <div class="mono text-muted" style="font-size:16px;font-weight:600">--%</div>
            <div class="mono text-muted" style="font-size:10px;margin-top:3px">0.00</div>
          </div>
        </template>
      </div>

      <!-- Scenario 3 Asset Overview -->
      <div class="c3-wrap">
        <div class="c3-top">
          <div class="c3-hero">
            <div style="font-size:11px;color:var(--sub);margin-bottom:4px;display:flex;align-items:center;gap:8px">
              总资产
              <div @click.stop="currencyOpen = !currencyOpen" style="display:inline-flex;align-items:center;gap:4px;height:20px;padding:0 8px;border-radius:6px;border:1px solid var(--border);background:var(--surface-soft);font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;color:var(--sub);cursor:pointer;transition:all .14s;user-select:none;position:relative">
                <span>{{ currentCurrency }}</span>
                <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" :style="{ transition: 'transform .2s', transform: currencyOpen ? 'rotate(180deg)' : 'rotate(0)' }"><polyline points="6 9 12 15 18 9"/></svg>
                
                <!-- Currency Dropdown -->
                <div v-if="currencyOpen" style="position:absolute;top:24px;left:0;background:var(--panel-elevated);border:1px solid var(--border-b);border-radius:10px;padding:4px;min-width:110px;z-index:100;box-shadow:var(--shadow-float);animation:modalIn .18s ease">
                  <div class="ccy-option" :class="{ active: currentCurrency === 'CNY' }" @click.stop="currentCurrency = 'CNY'; currencyOpen = false">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700">CNY</span>
                    <span style="font-size:9px;color:var(--muted)">人民币</span>
                  </div>
                  <div class="ccy-option" :class="{ active: currentCurrency === 'USD' }" @click.stop="currentCurrency = 'USD'; currencyOpen = false">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700">USD</span>
                    <span style="font-size:9px;color:var(--muted)">美元</span>
                  </div>
                  <div class="ccy-option" :class="{ active: currentCurrency === 'HKD' }" @click.stop="currentCurrency = 'HKD'; currencyOpen = false">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700">HKD</span>
                    <span style="font-size:9px;color:var(--muted)">港币</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="c3-total">{{ masked(formatCurrency(totalAssetsCny)) }}</div>
            <div class="c3-stats">
              <span class="badge" :class="valueClass(chartHeadlineChange)" style="font-size:12px;padding:4px 10px">{{ chartHeadlineLabel }} {{ masked(formatSignedCny(chartHeadlineChange)) }}</span>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;justify-content:center">
            <div class="c1-period-tabs">
              <button
                v-for="item in chartPeriodOptions"
                :key="item.value"
                class="c1-pt"
                :class="{ active: chartPeriod === item.value }"
                @click="chartPeriod = item.value"
              >
                {{ item.label }}
              </button>
            </div>
            <div class="home-chart-range">{{ chartRangeLabel }}</div>
          </div>
        </div>

        <!-- Sparkline Trend Chart -->
        <div
          ref="chartContainer"
          class="c3-chart"
          :class="{ 'chart-switching': chartSwitchAnimating }"
          @mousemove="handleChartMouseMove"
          @mouseleave="handleChartMouseLeave"
        >
          <svg viewBox="0 0 1044 120" preserveAspectRatio="none" fill="none">
            <defs>
              <linearGradient id="c3grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" :stop-color="chartGeometry.color" stop-opacity=".18"/>
                <stop offset="100%" :stop-color="chartGeometry.color" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <g class="home-chart-series">
              <path v-if="chartGeometry.hasData" :d="chartGeometry.linePath" :stroke="chartGeometry.color" stroke-width="2.5" fill="none"/>
              <path v-if="chartGeometry.hasData" :d="chartGeometry.areaPath" fill="url(#c3grad)"/>
              <circle v-if="hoveredChartPoint" :cx="hoveredChartPoint.x" :cy="hoveredChartPoint.y" r="4.5" :fill="chartGeometry.color"/>
              <line v-if="hoveredChartPoint" :x1="hoveredChartPoint.x" :y1="hoveredChartPoint.y" :x2="hoveredChartPoint.x" y2="120" :stroke="chartGeometry.color === '#f05a55' ? 'rgba(240,90,85,0.2)' : 'rgba(62,207,130,0.2)'" stroke-width="1.5" stroke-dasharray="4 3"/>
            </g>
          </svg>
          <div
            v-if="hoveredChartPoint && chartGeometry.hasData && !chartLoading"
            class="home-chart-tooltip"
            :style="chartTooltipStyle"
          >
            <div class="home-chart-tooltip-date">{{ formatChartDate(hoveredChartPoint.date) }}</div>
            <div class="home-chart-tooltip-value">{{ masked(formatChartDisplayValue(hoveredChartPoint.value)) }}</div>
          </div>
          <div v-if="chartGeometry.hasData && filteredHistoryPoints.length >= 2" class="home-chart-axis">
            <span>{{ formatChartDate(filteredHistoryPoints[0]?.date || '') }}</span>
            <span>{{ formatChartDate(filteredHistoryPoints[filteredHistoryPoints.length - 1]?.date || '') }}</span>
          </div>
          <div v-if="chartLoading" class="home-chart-empty">正在加载历史资产走势...</div>
          <div v-else-if="chartError" class="home-chart-empty">{{ chartError }}</div>
          <div v-else-if="!chartGeometry.hasData" class="home-chart-empty">继续使用几天后，这里会显示你的资产趋势</div>
        </div>

        <!-- Bottom Segments -->
        <div class="c3-bottom">
          <div class="c3-segment" @click="goToInvestPage">
            <div class="c3-active-bar"></div>
            <div class="c3-segment-label">投资资产</div>
            <div class="c3-segment-val">{{ masked(formatCurrency(investTotal?.mv||0)) }}</div>
            <div class="c3-segment-change" :class="valueClass(investTotal?.dayPnl||0)">今日 {{ formatPct(investTotal?.dayRate||0) }}</div>
          </div>
          <div class="c3-segment" :class="{ active: activeSegment === 'cash' }" @click="toggleSegment('cash')">
            <div class="c3-active-bar" :style="{ background: activeSegment === 'cash' ? 'var(--blue)' : '' }"></div>
            <div class="c3-segment-label">现金资产</div>
            <div class="c3-segment-val">{{ masked(formatCurrency(cashTotal)) }}</div>
            <div class="c3-segment-change text-muted">{{ cashAssets.length }}个账户</div>
          </div>
          <div class="c3-segment" :class="{ active: activeSegment === 'other' }" @click="toggleSegment('other')">
            <div class="c3-active-bar" :style="{ background: activeSegment === 'other' ? 'var(--gold)' : '' }"></div>
            <div class="c3-segment-label">其他资产</div>
            <div class="c3-segment-val">{{ masked(formatCurrency(otherTotal)) }}</div>
            <div class="c3-segment-change text-muted">{{ otherAssets.length }}条记录</div>
          </div>
          <div class="c3-segment" :class="{ active: activeSegment === 'liability' }" @click="toggleSegment('liability')">
            <div class="c3-active-bar" :style="{ background: activeSegment === 'liability' ? 'var(--red)' : '' }"></div>
            <div class="c3-segment-label">我的负债</div>
            <div class="c3-segment-val" style="color:var(--red)">{{ masked(formatCurrency(-(liabilityTotal||0))) }}</div>
            <div class="c3-segment-change text-red">{{ liabilities.length }}条负债</div>
          </div>
        </div>

        <!-- Expandable Drawer -->
        <div class="c3-drawer" :class="{ open: !!activeSegment }">
          <div class="c3-drawer-inner">
            <div v-for="item in activeDrawerData" :key="item.id" class="c5-detail-pill" @click="item.code ? openInvestTradeModal(item) : openFormModal(item)">
              <div class="c5-pill-icon" style="background:none;border:none">
                <span>{{ item.icon || defaultAssetIcon(item.type) }}</span>
              </div>
              <div>
                <div class="c5-pill-name">{{ item.name }}</div>
                <div class="c5-pill-amt" :style="{ color: item.type === 'liability' ? 'var(--red)' : 'var(--sub)' }">
                  {{ masked(formatAssetOriginalAmount(item.amount, item.curr)) }}
                </div>
              </div>
            </div>
            
            <!-- Contextual Add Action in Drawer -->
            <div v-if="activeSegment" class="c5-add-pill" @click="openFormModal()">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              添加{{ activeSegment === 'cash' ? '现金账户' : activeSegment === 'other' ? '其他资产' : '负债记录' }}
            </div>
          </div>
        </div>
      </div>

        <!-- Holdings -->
        <div style="margin-top: 16px">
          <!-- Holdings header -->
          <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:14px;gap:12px">
            <div>
              <div class="section-label" style="margin:0 0 10px">持仓概览</div>
              <div class="tabs" style="width:fit-content">
                <button v-for="tab in ['all','hk','us','a','fund']" :key="tab" @click="selectedTab=tab" class="tab" :class="{active:selectedTab===tab}">{{ tab==='all'?'全部':tab==='hk'?'港股':tab==='us'?'美股':tab==='a'?'A股':'基金' }}</button>
              </div>
            </div>
            <!-- View toggle -->
            <div style="display:flex;gap:4px;background:var(--surface-soft);border:1px solid var(--border);border-radius:9px;padding:3px;flex-shrink:0;margin-top:2px">
              <button @click="holdingsView='card'" title="卡片视图" :style="holdingsView==='card'?'background:var(--surface-strong);color:var(--text)':'background:transparent;color:var(--muted)'" style="width:30px;height:26px;border-radius:6px;border:none;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .15s">
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none"><rect x="0" y="0" width="7" height="7" rx="1.5" fill="currentColor" opacity=".9"/><rect x="9" y="0" width="7" height="7" rx="1.5" fill="currentColor" opacity=".9"/><rect x="0" y="9" width="7" height="7" rx="1.5" fill="currentColor" opacity=".9"/><rect x="9" y="9" width="7" height="7" rx="1.5" fill="currentColor" opacity=".9"/></svg>
              </button>
              <button @click="holdingsView='row'" title="列表视图" :style="holdingsView==='row'?'background:var(--surface-strong);color:var(--text)':'background:transparent;color:var(--muted)'" style="width:30px;height:26px;border-radius:6px;border:none;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .15s">
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none"><rect x="0" y="1" width="16" height="2.5" rx="1.2" fill="currentColor"/><rect x="0" y="6.5" width="16" height="2.5" rx="1.2" fill="currentColor" opacity=".6"/><rect x="0" y="12" width="16" height="2.5" rx="1.2" fill="currentColor" opacity=".35"/></svg>
              </button>
            </div>
          </div>

        <div v-if="!filteredRows || filteredRows.length === 0" style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px;background:var(--surface-faint);border:1px solid var(--border);border-radius:16px">
          <div style="font-size:48px;margin-bottom:12px">📭</div>
          <div class="text-muted fs13">暂无持仓数据</div>
        </div>

        <div v-else>
          <!-- Card View -->
          <div v-if="holdingsView === 'card'" style="display:grid;grid-template-columns:repeat(auto-fill, minmax(280px, 1fr));gap:10px">
            <div v-for="(row, idx) in filteredRows.slice(0, 8)" :key="row?.code||`card-${idx}`" class="hcard" @click="row?.code && openInvestTradeModal(row)">
              <div style="position:absolute;top:0;left:0;right:0;height:2px" :style="{ background: 'linear-gradient(90deg,transparent,' + (toNumber(row?.dayPnl)>=0?'var(--red)':'var(--green)') + ' 40%,transparent)' }"></div>
              <div class="hcard-header-row">
                <div class="h-icon-box">
                  <AssetLogo 
                    :name="row?.name" 
                    :code="row?.code" 
                    :logo-url="row?.logo_url" 
                    :market="row?.market" 
                    :asset-type="row?.asset_type"
                  />
                </div>
                <div class="h-info-group">
                  <div class="h-name-row">{{ row?.name || '未知标的' }}</div>
                  <div class="h-meta-row">
                    <span class="tag" :class="row?.category || row?.market">{{ (row?.category || row?.market)==='us'?'美股':(row?.category || row?.market)==='hk'?'港股':(row?.category || row?.market)==='a'?'A股':'基金' }}</span>
                    <span class="h-qty"><span :style="{ fontSize: getQtyFontSize(Number(row?.qty||0).toLocaleString()) }">{{ Number(row?.qty||0).toLocaleString() }}</span>{{ row?.market === 'fund' ? '份' : '股' }}</span>
                  </div>
                </div>
                <!-- Market Value in Top Right -->
                <div class="h-mv-right">
                  {{ formatHoldingValue(row?.mv || 0, String(row?.curr)) }}
                </div>
              </div>

              <!-- Price Row (Above Sparkline) -->
              <div class="h-price-row">
                <div class="h-price-main">
                  <span class="h-price-val">{{ quoteLabel(row) }}</span>
                </div>
                <div class="h-price-tag badge" :class="valueClass(toNumber(row?.dayPnlRate))" style="padding: 2px 6px; border-radius: 4px; font-size: 10px;">
                  {{ dayPnlRateLabel(row) }}
                </div>
              </div>

              <!-- Sparkline stub -->
              <div style="height:38px;margin-bottom:10px;opacity:.85">
                <svg v-if="row?.sparkReady" viewBox="0 0 120 40" width="100%" height="100%" preserveAspectRatio="none" fill="none">
                  <path :d="row?.spark" :stroke="toNumber(row?.dayPnl)>=0?'var(--red)':'var(--green)'" stroke-width="1.6" fill="none"/>
                </svg>
                <div v-else class="trend-empty">暂无趋势</div>
              </div>
              <!-- Removed redundant dayPnlRate badge -->
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;padding-top:10px;border-top:1px solid var(--surface-divider)">
                <div>
                  <div style="font-size: 10px; color: var(--muted); margin-bottom: 2px">今日盈亏</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size: 12.5px; font-weight: 600" :class="valueClass(toNumber(row?.dayPnl))">{{ masked(formatValue(toNumber(row?.dayPnl), row?.curr as any)) }}</div>
                </div>
                <div>
                  <div style="font-size: 10px; color: var(--muted); margin-bottom: 2px">累计盈亏</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size: 12.5px; font-weight: 600" :class="valueClass(toNumber(row?.totalPnlRate))">{{ formatPct(toNumber(row?.totalPnlRate)) }}</div>
                </div>
                <div>
                  <div style="font-size: 10px; color: var(--muted); margin-bottom: 2px">成本价</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size: 12.5px; font-weight: 500; color:var(--sub)">{{ masked(formatValue(toNumber(row?.costPrice), row?.curr as any)) }}</div>
                </div>
                <div>
                  <div style="font-size: 10px; color: var(--muted); margin-bottom: 4px; display: flex; justify-content: space-between">仓位 <span style="color:var(--blue); font-size: 12.5px; font-weight: 600">{{ formatPct(toNumber(row?.pct)).replace('%','') }}%</span></div>
                  <div style="height:3px;background:var(--surface-track);border-radius:2px;overflow:hidden">
                    <div style="height:100%;background:rgba(91,141,239,0.7);border-radius:2px" :style="{ width: Math.min(toNumber(row?.pct), 100) + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Row View -->
          <div v-else style="display:flex;flex-direction:column;gap:6px">
            <div v-for="(row, idx) in filteredRows.slice(0, 8)" :key="row?.code||`row-${idx}`" class="hrow" @click="row?.code && openInvestTradeModal(row)">
              <div style="display:flex;align-items:flex-start;gap:12px;width:320px;flex-shrink:0">
                <div class="h-icon" style="width:38px;height:38px;flex-shrink:0;border:none;background:none">
                  <AssetLogo 
                    :name="row?.name" 
                    :code="row?.code" 
                    :logo-url="row?.logo_url" 
                    :market="row?.market" 
                    :asset-type="row?.asset_type"
                  />
                </div>
                <div class="h-info-group h-info-group-row">
                  <div class="h-name-row h-name-row-wrap">{{ row?.name || '未知标的' }}</div>
                  <div class="h-meta-row">
                        <span class="tag" :class="row?.category || row?.market">{{ (row?.category || row?.market)==='us'?'美股':(row?.category || row?.market)==='hk'?'港股':(row?.category || row?.market)==='a'?'A股':'基金' }}</span>
                  </div>
                </div>
              </div>
              <div style="display:grid;grid-template-columns:repeat(7, 1fr);gap:12px;flex:1;align-items:center">
                <div style="padding:0 12px;border-right:1px solid var(--surface-divider)">
                  <div style="font-size:10px;color:var(--muted);margin-bottom:3px">持仓数量</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:12.5px;font-weight:600;color:var(--text)">{{ Number(row?.qty||0).toLocaleString() }}</div>
                </div>
                <div style="padding:0 12px;border-right:1px solid var(--surface-divider)">
                  <div style="font-size:10px;color:var(--muted);margin-bottom:3px">现价</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:12.5px;font-weight:600;color:var(--text)">
                    {{ quoteLabel(row) }}
                  </div>
                </div>
                <div style="padding:0 12px;border-right:1px solid var(--surface-divider)">
                  <div style="font-size:10px;color:var(--muted);margin-bottom:3px">成本价</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:12.5px;font-weight:500;color:var(--muted)">{{ masked(formatValue(toNumber(row?.costPrice), row?.curr as any)) }}</div>
                </div>
                <div style="padding:0 12px;border-right:1px solid var(--surface-divider)">
                  <div style="font-size:10px;color:var(--muted);margin-bottom:3px">市值</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:12.5px;font-weight:600;color:var(--text)">{{ masked(formatHoldingValue(toNumber(row?.mv), row?.curr as any)) }}</div>
                </div>
                <div style="padding:0 12px;border-right:1px solid var(--surface-divider)">
                  <div style="font-size:10px;color:var(--muted);margin-bottom:3px">今日盈亏</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:12.5px;font-weight:600" :class="valueClass(toNumber(row?.dayPnl))">{{ masked(formatValue(toNumber(row?.dayPnl), row?.curr as any)) }}</div>
                  <div style="font-size:11px;margin-top:1px" :class="valueClass(toNumber(row?.dayPnlRate))">{{ dayPnlRateLabel(row) }}</div>
                </div>
                <div style="padding:0 12px;border-right:1px solid var(--surface-divider)">
                  <div style="font-size:10px;color:var(--muted);margin-bottom:3px">累计盈亏</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:12.5px;font-weight:600" :class="valueClass(toNumber(row?.totalPnl))">{{ masked(formatValue(toNumber(row?.totalPnl), row?.curr as any)) }}</div>
                  <div style="font-size:11px;margin-top:1px" :class="valueClass(toNumber(row?.totalPnlRate))">{{ formatPct(toNumber(row?.totalPnlRate)) }}</div>
                </div>
                <div style="padding:0 0 0 12px">
                  <div style="font-size: 10px; color: var(--muted); margin-bottom: 4px; display: flex; justify-content: space-between">仓位 <span style="color:var(--blue); font-size: 12.5px; font-weight: 600">{{ formatPct(toNumber(row?.pct)).replace('%','') }}%</span></div>
                  <div style="height:4px;background:var(--surface-track);border-radius:3px;overflow:hidden">
                    <div style="height:100%;background:linear-gradient(90deg,rgba(91,141,239,0.5),rgba(91,141,239,0.9));border-radius:3px" :style="{ width: Math.min(toNumber(row?.pct), 100) + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 资产详情列表 Modal -->
      <div class="modal-overlay" :class="{ show: modalVisible && !isFormModalVisible }" @click.self="closeModal">
        <div style="width:100%;max-width:440px;background:var(--s1);border:1px solid var(--border);border-radius:24px;padding:24px;box-shadow:var(--shadow-xl);animation:modalIn .2s var(--easing-out);position:relative">
          <button @click="closeModal" style="position:absolute;top:20px;right:20px;width:32px;height:32px;border-radius:9px;background:var(--surface-soft);border:none;color:var(--sub);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .15s">✕</button>
          
          <div style="font-size:18px;font-weight:700;margin-bottom:4px">{{ modalTitle }}</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:600;color:var(--text);margin-bottom:24px" :style="{ color: modalType === 'liability' ? 'var(--red)' : modalType === 'other' ? 'var(--gold)' : 'var(--green)' }">
            {{ formatCny(currentTypeAssetsTotal) }}
          </div>
          
          <div style="max-height:400px;overflow-y:auto;margin:0 -8px;padding:0 8px">
            <div v-if="!currentTypeAssets.length" style="text-align:center;padding:40px;color:var(--muted);font-size:13px">暂无记录，点击下方添加</div>
            <div v-else>
              <div v-for="item in currentTypeAssets as any[]" :key="item.id" style="display:flex;align-items:center;gap:14px;padding:14px 16px;background:var(--surface-faint);border:1px solid var(--border);border-radius:14px;margin-bottom:10px">
                <div style="width:52px;height:52px;border-radius:14px;background:rgba(91,141,239,0.1);border:1px solid rgba(91,141,239,0.18);display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">{{ item.icon || '🏦' }}</div>
                <div style="flex:1;min-width:0">
                  <div style="font-size:15px;font-weight:700;color:var(--text);margin-bottom:4px">{{ item.name }}</div>
                  <div style="display:flex;align-items:baseline;gap:5px">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:600" :style="{ color: modalType === 'liability' ? 'var(--red)' : item.curr === 'HKD' ? 'var(--gold)' : item.curr === 'USD' ? 'var(--blue)' : 'var(--text)' }">
                      {{ getCurrencySymbol(item.curr) }} {{ Math.abs(item.amount).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 }) }}
                    </span>
                    <span style="font-size:11px;color:var(--muted)">{{ getCurrencyLabel(item.curr) }}</span>
                  </div>
                </div>
                <!-- 操作按钮组 -->
                <div style="display:flex;gap:6px">
                   <button @click="openFormModal(item)" style="width:32px;height:32px;border-radius:9px;border:1px solid var(--border);background:var(--surface-soft);display:flex;align-items:center;justify-content:center;cursor:pointer;color:var(--muted);flex-shrink:0"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
                   <button @click="removeAsset(modalType, item.id as number)" style="width:32px;height:32px;border-radius:9px;border:1px solid var(--border);background:rgba(240,90,85,0.1);display:flex;align-items:center;justify-content:center;cursor:pointer;color:var(--red);flex-shrink:0"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button>
                </div>
              </div>
            </div>
          </div>
          
          <button @click="openFormModal()" style="width:100%;height:46px;border-radius:12px;border:none;background:linear-gradient(135deg,rgba(91,141,239,0.15),rgba(74,123,224,0.05));border:1px solid rgba(91,141,239,0.25);color:var(--blue);font-family:'DM Sans',sans-serif;font-size:14px;font-weight:700;margin-top:20px;cursor:pointer;transition:all .2s">
            + {{ modalAddLabel }}
          </button>
        </div>
      </div>

      <!-- 添加/编辑 资产详情的二层表单 Modal -->
      <div class="modal-overlay" :class="{ show: isFormModalVisible }" @click.self="closeFormModal">
        <div style="width:100%;max-width:380px;background:var(--s1);border:1px solid var(--border);border-radius:24px;padding:24px;box-shadow:var(--shadow-xl);animation:modalIn .2s var(--easing-out);position:relative">
          <button
            v-if="modalMode === 'edit' && form.id"
            @click="openDeleteConfirm"
            style="position:absolute;top:20px;right:20px;width:32px;height:32px;border-radius:9px;border:1px solid rgba(240,90,85,0.22);background:rgba(240,90,85,0.1);display:flex;align-items:center;justify-content:center;cursor:pointer;color:var(--red);transition:all .15s"
            aria-label="删除资产"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
          </button>
          <div style="font-size:18px;font-weight:700;margin-bottom:20px">{{ modalMode === 'add' ? modalAddLabel : '编辑资产' }}</div>
          
          <div style="margin-bottom:16px">
            <div style="font-size:11px;font-weight:600;color:var(--sub);margin-bottom:8px">图标</div>
            <div style="display:flex;gap:8px">
              <div class="icon-pick" :class="{ active: form.icon === '🏦' }" @click="form.icon = '🏦'">🏦</div>
              <div class="icon-pick" :class="{ active: form.icon === '💳' }" @click="form.icon = '💳'">💳</div>
              <div class="icon-pick" :class="{ active: form.icon === '👛' }" @click="form.icon = '👛'">👛</div>
              <div class="icon-pick" :class="{ active: form.icon === '💵' }" @click="form.icon = '💵'">💵</div>
              <div class="icon-pick" :class="{ active: form.icon === '📦' }" @click="form.icon = '📦'">📦</div>
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">名称</label>
            <input class="form-inp" v-model="form.name" placeholder="如：中国银行储蓄卡">
          </div>
          
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div class="form-group">
              <label class="form-label">金额</label>
              <input class="form-inp" type="number" v-model="form.amount" placeholder="0.00">
            </div>
            <div class="form-group">
              <label class="form-label">货币</label>
              <div style="position:relative">
                <button
                  type="button"
                  class="form-inp"
                  @click.stop="assetCurrencyOpen = !assetCurrencyOpen"
                  style="display:flex;align-items:center;justify-content:space-between;text-align:left"
                >
                  <span>{{ form.curr }} {{ getCurrencyLabel(form.curr) }}</span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" :style="{ transition: 'transform .2s', transform: assetCurrencyOpen ? 'rotate(180deg)' : 'rotate(0)' }">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
                <div v-if="assetCurrencyOpen" class="asset-currency-menu">
                  <button type="button" class="asset-currency-option" :class="{ active: form.curr === 'CNY' }" @click.stop="form.curr = 'CNY'; assetCurrencyOpen = false">
                    <span class="asset-currency-code">CNY</span>
                    <span class="asset-currency-name">人民币</span>
                  </button>
                  <button type="button" class="asset-currency-option" :class="{ active: form.curr === 'USD' }" @click.stop="form.curr = 'USD'; assetCurrencyOpen = false">
                    <span class="asset-currency-code">USD</span>
                    <span class="asset-currency-name">美元</span>
                  </button>
                  <button type="button" class="asset-currency-option" :class="{ active: form.curr === 'HKD' }" @click.stop="form.curr = 'HKD'; assetCurrencyOpen = false">
                    <span class="asset-currency-code">HKD</span>
                    <span class="asset-currency-name">港币</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div style="display:flex;gap:8px;margin-top:8px">
            <button @click="closeFormModal" style="flex:1;height:42px;border-radius:10px;border:1px solid var(--border);background:var(--surface-soft);color:var(--sub);font-family:'DM Sans',sans-serif;font-size:14px;font-weight:700;cursor:pointer">取消</button>
            <button @click="submitModal" :disabled="!form.name" style="flex:2;height:42px;border-radius:10px;border:none;background:linear-gradient(135deg,#5b8def,#4a7be0);color:#fff;font-family:'DM Sans',sans-serif;font-size:14px;font-weight:700;cursor:pointer;box-shadow:0 4px 14px rgba(74,123,224,0.25)" :style="{ opacity: !form.name ? 0.5 : 1 }">保存</button>
          </div>
        </div>
      </div>

      <div class="modal-overlay" :class="{ show: isDeleteConfirmVisible }" @click.self="closeDeleteConfirm">
        <div style="width:100%;max-width:360px;background:var(--s1);border:1px solid rgba(240,90,85,0.18);border-radius:24px;padding:24px;box-shadow:var(--shadow-xl);animation:modalIn .2s var(--easing-out)">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
            <div style="width:40px;height:40px;border-radius:12px;background:rgba(240,90,85,0.12);border:1px solid rgba(240,90,85,0.18);display:flex;align-items:center;justify-content:center;color:var(--red);font-size:18px">🗑️</div>
            <div>
              <div style="font-size:18px;font-weight:700;color:var(--text)">确认删除</div>
              <div style="font-size:12px;color:var(--muted);margin-top:4px">删掉后就不会再出现在首页列表里。</div>
            </div>
          </div>
          <div style="font-size:14px;color:var(--sub);line-height:1.6;margin-bottom:20px">
            确定要删除“{{ form.name || '这条资产' }}”吗？这个动作不能撤回。
          </div>
          <div style="display:flex;gap:8px">
            <button @click="closeDeleteConfirm" style="flex:1;height:42px;border-radius:10px;border:1px solid var(--border);background:var(--surface-soft);color:var(--sub);font-family:'DM Sans',sans-serif;font-size:14px;font-weight:700;cursor:pointer">取消</button>
            <button @click="removeAssetFromForm" style="flex:1;height:42px;border-radius:10px;border:none;background:linear-gradient(135deg,#f05a55,#d84d48);color:#fff;font-family:'DM Sans',sans-serif;font-size:14px;font-weight:700;cursor:pointer;box-shadow:0 4px 14px rgba(240,90,85,0.22)">确认删除</button>
          </div>
        </div>
      </div>
      <InvestTradeModal
        v-model:show="showTradeModal"
        :asset="tradeModalAsset"
        :mode="tradeModalMode"
        @success="handleTradeSuccess"
      />
    </AppShell>
</template>

<style>
@import '@/styles/homepage-original.css';

/* Nested scoping for period tabs to ensure they match Concept 3 expectations */
.c1-period-tabs {
  display: flex !important;
  gap: 4px !important;
  background: var(--surface-soft) !important;
  border: 1px solid var(--border) !important;
  border-radius: 9px !important;
  padding: 3px !important;
  width: fit-content;
}
.c1-pt {
  padding: 5px 14px !important;
  border-radius: 6px !important;
  border: none !important;
  background: transparent !important;
  font-family: inherit !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  color: var(--muted) !important;
  cursor: pointer !important;
  transition: all .14s !important;
  white-space: nowrap !important;
  line-height: 1 !important;
}
.c1-pt.active {
  background: var(--surface-strong) !important;
  color: var(--text) !important;
}

.market-strip {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

@media (max-width: 1600px) {
  .market-strip {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }
}

@media (max-width: 1500px) {
  .market-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 980px) {
  .market-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .market-strip {
    grid-template-columns: 1fr;
  }
}
/* 使用全局样式以确保 :root 和 布局类生效 */
/* New Horizontal Layout */
.hcard-header-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.h-icon-box {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 10px;
  overflow: hidden;
}
.h-info-group {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.h-info-group-row {
  padding-top: 1px;
}
.h-name-row {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.h-name-row-wrap {
  white-space: normal;
  overflow: visible;
  text-overflow: unset;
  line-height: 1.28;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.h-meta-row {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: nowrap;
  overflow: hidden;
}
.h-qty {
  font-size: 11px;
  color: var(--muted);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: baseline;
  gap: 2px;
}
.h-qty span {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
}

/* Price Row Styles */
.h-price-row {
  display: flex;
  align-items: baseline;
  justify-content: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}
.h-price-main {
  display: flex;
  align-items: baseline;
  gap: 2px;
  color: var(--text);
}
.h-price-sym {
  font-size: 11px;
  font-weight: 700;
  opacity: 0.7;
}
.h-price-val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 700;
}
.h-price-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
}
.h-price-tag.dn { color: var(--green); background: rgba(62, 207, 130, 0.12); }

.h-mv-right {
  margin-left: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  text-align: right;
}

.home-chart-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: var(--muted);
  pointer-events: none;
}

.home-chart-range {
  margin-top: 8px;
  font-size: 11px;
  color: var(--muted);
}

.home-chart-tooltip {
  position: absolute;
  min-width: 120px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(8, 13, 24, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 16px 38px rgba(0, 0, 0, 0.28);
  pointer-events: none;
  z-index: 4;
  backdrop-filter: blur(12px);
  transition: left .14s ease, transform .14s ease, opacity .18s ease;
}

.home-chart-tooltip-date {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.62);
  margin-bottom: 4px;
}

.home-chart-tooltip-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 700;
  color: #f5f7fb;
}

.home-chart-axis {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 8px;
  display: flex;
  justify-content: space-between;
  padding: 0 18px;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.34);
  pointer-events: none;
}

.home-chart-series {
  transition: opacity .18s ease, transform .18s ease;
}

.c3-chart.chart-switching .home-chart-series,
.c3-chart.chart-switching .home-chart-tooltip,
.c3-chart.chart-switching .home-chart-axis {
  opacity: 0.42;
}

[data-theme='light'] .home-chart-range {
  color: rgba(23, 27, 35, 0.48);
}

[data-theme='light'] .home-chart-axis {
  color: rgba(23, 27, 35, 0.4);
}

.asset-currency-menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  padding: 6px;
  background: var(--panel-elevated);
  border: 1px solid var(--border-b);
  border-radius: 14px;
  box-shadow: var(--shadow-float);
  z-index: 120;
  animation: modalIn .18s ease;
}

.asset-currency-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 12px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--sub);
  cursor: pointer;
  transition: all .15s;
  text-align: left;
}

.asset-currency-option:hover {
  background: var(--surface-soft);
  color: var(--text);
}

.asset-currency-option.active {
  background: linear-gradient(135deg, rgba(91,141,239,0.22), rgba(74,123,224,0.12));
  color: var(--text);
}

.asset-currency-option.active::before {
  content: '✓';
  color: var(--blue);
  font-size: 14px;
  font-weight: 700;
}

.asset-currency-code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  min-width: 34px;
}

.asset-currency-name {
  font-size: 13px;
  font-weight: 600;
}

.trend-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed color-mix(in srgb, var(--border) 78%, transparent);
  border-radius: 10px;
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 0.02em;
  background: color-mix(in srgb, var(--surface-soft) 70%, transparent);
}
</style>
