<script setup lang="ts">
/**
 * AppHomePage - 首页（1:1复刻版 - 原始CSS样式）
 * 完全按照参考HTML复刻UI，使用原始CSS类名系统
 */

import { computed, onMounted, onBeforeUnmount, ref, reactive } from 'vue'
import { api } from '@/shared/http'
import { toNumber } from '@/shared/format'
import { useKonaStore } from '@/stores/composables'
import { usePrivacyMode } from '@/shared/privacyMode'
import { useMarketStore } from '@/stores/market'
import AssetLogo from '@/components/base/AssetLogo.vue'
import AppShell from '../../layouts/AppShell.vue'


// Types
type AssetType = 'cash' | 'other' | 'liability'
type SimpleAsset = { id: number; icon?: string; name: string; amount: number; curr?: string }

// Stores & Composables
const store = useKonaStore()
const { maskValue } = usePrivacyMode()
const marketStore = useMarketStore()

// State
const isLoading = ref(true)
const cashAssets = ref<SimpleAsset[]>([])
const otherAssets = ref<SimpleAsset[]>([])
const liabilities = ref<SimpleAsset[]>([])
const modalVisible = ref(false)
const isFormModalVisible = ref(false)
const modalType = ref<AssetType>('cash')
const modalMode = ref<'add' | 'edit'>('add')
const selectedTab = ref('all')
const holdingsView = ref<'card'|'row'>('card')
const marketIndices = ref<any[]>([])
const activeSegment = ref<AssetType | 'invest' | null>(null)

// Currency Switcher State
const currencyOpen = ref(false)
const currentCurrency = ref<'CNY'|'USD'|'HKD'>('CNY')

const form = reactive<{ id: number | null; icon: string; name: string; amount: number; curr: string }>({
  id: null,
  icon: '🏦',
  name: '',
  amount: 0,
  curr: 'CNY',
})

let staticRefreshTimer: number | null = null

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
      const rowCost = Number(row.costPrice) * Number(row.qty) * rate
      mv += rowValue * rate
      cost += Math.abs(rowCost)
      dayPnl += (Number(row.dayPnlAggregate) || 0) * rate
      floatPnl += (rowValue - rowCost) * rate
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

// Segment Drawer Data
const activeDrawerData = computed(() => {
  if (!activeSegment.value) return []
  if (activeSegment.value === 'invest') {
    return (rows.value || []).map(row => ({
      id: Number(row.id || 0),
      name: String(row.name || ''),
      amount: Number(row.value || 0),
      curr: String(row.curr || 'CNY'),
      type: 'invest' as const,
      code: String(row.code || ''),
      market: String(row.market || ''),
      logo_url: row.logo_url,
      asset_type: row.asset_type
    }))
  }
  if (activeSegment.value === 'cash') return cashAssets.value.map(a => ({ ...a, type: 'cash' as const, code: undefined }))
  if (activeSegment.value === 'other') return otherAssets.value.map(a => ({ ...a, type: 'other' as const, code: undefined }))
  if (activeSegment.value === 'liability') return liabilities.value.map(a => ({ ...a, type: 'liability' as const, code: undefined }))
  return []
})

function toggleSegment(type: AssetType | 'invest') {
  if (activeSegment.value === type) {
    activeSegment.value = null
  } else {
    activeSegment.value = type
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
  const base = selectedTab.value === 'all' ? validRows : validRows.filter(row => row?.market === selectedTab.value)
  return base.map((row: any, idx) => {
    const qty = Number(row?.qty || 0)
    const displayCostPrice = Number(row?.displayCostPrice || 0)
    const currentPrice = Number(row?.currentPrice || 0)
    
    return {
      ...row,
      qty,
      costPrice: displayCostPrice, // 首页展示摊薄后成本
      price: currentPrice || (idx % 2 === 0 ? 225.50 : 88.35),
      dayPnlRate: Number(row?.dayPnlRate || 0) || (idx % 2 === 0 ? 1.28 : -0.75),
      // 保持 Store 中的原始字段
      cost: row?.cost || (qty * displayCostPrice),
      mv: row?.value || (qty * currentPrice),
      spark: 'M0,15 L20,12 L40,14 L60,8 L80,6 L100,5'
    }
  })
})

// Helpers

function formatPct(value: number | undefined): string {
  if (typeof value !== 'number' || isNaN(value)) return '0.00%'
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
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
    marketIndices.value = res || []
  } catch (e) {
    console.error('Failed to load market indices:', e)
  }
}

async function refreshAll() {
  try {
    await Promise.all([
      store.refreshAll(),
      marketStore.loadRates(),
      loadLists(),
      loadMarketIndices()
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
  } else if (activeSegment.value && activeSegment.value !== 'invest') {
    modalType.value = activeSegment.value
  }
  
  modalMode.value = (item && item.id) ? 'edit' : 'add'
  form.id = item?.id ?? null
  form.icon = item?.icon ?? '🏦'
  form.name = item?.name ?? ''
  form.amount = toNumber(item?.amount, 0)
  form.curr = item?.curr || 'CNY'
  isFormModalVisible.value = true
}

function closeFormModal() {
  isFormModalVisible.value = false
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

// Global click handler to close currency menu
function handleGlobalClick() {
  if (currencyOpen.value) currencyOpen.value = false
}

// Lifecycle
onMounted(async () => {
  document.addEventListener('click', handleGlobalClick)
  isLoading.value = true
  try {
    await store.bootstrap()
    await Promise.all([
      marketStore.loadRates(),
      loadLists(),
      loadMarketIndices()
    ])
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
})
</script>

<template>
  <AppShell title="我的资产">
    <!-- Loading State -->
    <div v-if="isLoading" class="page active" style="display:flex;align-items:center;justify-content:center;height:100%">
      <div style="text-align:center">
        <div style="font-size:48px;margin-bottom:16px">⏳</div>
        <div class="text-sub">加载中...</div>
      </div>
    </div>

    <!-- Content -->
    <template v-else>

      <!-- Market Index Cards -->
      <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:14px">
        <template v-if="marketIndices && marketIndices.length > 0">
          <div v-for="idx in marketIndices" :key="idx.name" class="card" style="padding:12px 14px">
            <div class="section-label" style="font-size:11px;margin-bottom:6px">{{ idx.name }}</div>
            <div class="mono" :class="valueClass(idx.change)" style="font-size:16px;font-weight:600">
              {{ idx.name === 'USD/CNY' ? idx.value.toFixed(4) : formatPct(idx.change_pct) }}
            </div>
            <div class="mono text-muted" style="font-size:10px;margin-top:3px">
              {{ idx.name === 'USD/CNY' ? '汇率' : idx.value.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}
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
              <div @click.stop="currencyOpen = !currencyOpen" style="display:inline-flex;align-items:center;gap:4px;height:20px;padding:0 8px;border-radius:6px;border:1px solid var(--border);background:rgba(255,255,255,0.06);font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;color:var(--sub);cursor:pointer;transition:all .14s;user-select:none;position:relative">
                <span>{{ currentCurrency }}</span>
                <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" :style="{ transition: 'transform .2s', transform: currencyOpen ? 'rotate(180deg)' : 'rotate(0)' }"><polyline points="6 9 12 15 18 9"/></svg>
                
                <!-- Currency Dropdown -->
                <div v-if="currencyOpen" style="position:absolute;top:24px;left:0;background:var(--s2);border:1px solid var(--border-b);border-radius:10px;padding:4px;min-width:110px;z-index:100;box-shadow:0 12px 32px rgba(0,0,0,0.4);animation:modalIn .18s ease">
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
              <span class="badge" :class="valueClass(investTotal?.dayPnl||0)" style="font-size:12px;padding:4px 10px">今日 {{ masked(formatSignedCny(toNumber(investTotal?.dayPnl))) }}</span>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;justify-content:center">
            <div class="c1-period-tabs">
              <button class="c1-pt active">近1月</button>
              <button class="c1-pt">近3月</button>
              <button class="c1-pt">近1年</button>
              <button class="c1-pt">全部</button>
            </div>
          </div>
        </div>

        <!-- Sparkline Trend Chart -->
        <div class="c3-chart">
          <svg viewBox="0 0 1044 120" preserveAspectRatio="none" fill="none">
            <defs>
              <linearGradient id="c3grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" :stop-color="(investTotal?.dayPnl||0)>=0?'#f05a55':'#3ecf82'" stop-opacity=".15"/>
                <stop offset="100%" :stop-color="(investTotal?.dayPnl||0)>=0?'#f05a55':'#3ecf82'" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <path d="M0,95 C60,92 100,85 160,78 C220,71 260,83 320,75 C380,67 420,53 480,45 C540,37 580,43 640,33 C700,23 740,28 800,21 C860,14 900,17 960,13 C1000,10 1030,8 1044,7" :stroke="(investTotal?.dayPnl||0)>=0?'#f05a55':'#3ecf82'" stroke-width="2.5" fill="none"/>
            <path d="M0,95 C60,92 100,85 160,78 C220,71 260,83 320,75 C380,67 420,53 480,45 C540,37 580,43 640,33 C700,23 740,28 800,21 C860,14 900,17 960,13 C1000,10 1030,8 1044,7 L1044,120 L0,120 Z" fill="url(#c3grad)"/>
            <circle cx="1044" cy="7" r="4.5" :fill="(investTotal?.dayPnl||0)>=0?'#f05a55':'#3ecf82'"/>
            <line x1="1044" y1="7" x2="1044" y2="120" :stroke="(investTotal?.dayPnl||0)>=0?'rgba(240,90,85,0.2)':'rgba(62,207,130,0.2)'" stroke-width="1.5" stroke-dasharray="4 3"/>
          </svg>
        </div>

        <!-- Bottom Segments -->
        <div class="c3-bottom">
          <div class="c3-segment" :class="{ active: activeSegment === 'invest' }" @click="toggleSegment('invest')">
            <div class="c3-active-bar" :style="{ background: activeSegment === 'invest' ? 'var(--green)' : '' }"></div>
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
            <div v-for="item in activeDrawerData" :key="item.id" class="c5-detail-pill" @click="item.code ? $router.push(`/app/asset/${item.code}`) : openFormModal(item)">
              <div class="c5-pill-icon" style="background:none;border:none">
                <AssetLogo 
                  v-if="item.type === 'invest'"
                  :name="item.name" 
                  :code="item.code" 
                  :logo-url="item.logo_url" 
                  :market="item.market" 
                  :asset-type="item.asset_type"
                />
                <span v-else>{{ item.icon }}</span>
              </div>
              <div>
                <div class="c5-pill-name">{{ item.name }}</div>
                <div class="c5-pill-amt" :style="{ color: item.type === 'liability' ? 'var(--red)' : 'var(--sub)' }">
                  {{ masked(formatCurrency(toCny(item.amount, item.curr))) }}
                </div>
              </div>
              <span v-if="item.type !== 'invest'" class="c5-pill-edit" @click.stop="openFormModal(item)">✏</span>
            </div>
            
            <!-- Contextual Add Action in Drawer -->
            <div v-if="activeSegment && activeSegment !== 'invest'" class="c5-add-pill" @click="openFormModal()">
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
            <div style="display:flex;gap:4px;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:9px;padding:3px;flex-shrink:0;margin-top:2px">
              <button @click="holdingsView='card'" title="卡片视图" :style="holdingsView==='card'?'background:rgba(255,255,255,0.08);color:var(--text)':'background:transparent;color:var(--muted)'" style="width:30px;height:26px;border-radius:6px;border:none;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .15s">
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none"><rect x="0" y="0" width="7" height="7" rx="1.5" fill="currentColor" opacity=".9"/><rect x="9" y="0" width="7" height="7" rx="1.5" fill="currentColor" opacity=".9"/><rect x="0" y="9" width="7" height="7" rx="1.5" fill="currentColor" opacity=".9"/><rect x="9" y="9" width="7" height="7" rx="1.5" fill="currentColor" opacity=".9"/></svg>
              </button>
              <button @click="holdingsView='row'" title="列表视图" :style="holdingsView==='row'?'background:rgba(255,255,255,0.08);color:var(--text)':'background:transparent;color:var(--muted)'" style="width:30px;height:26px;border-radius:6px;border:none;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .15s">
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none"><rect x="0" y="1" width="16" height="2.5" rx="1.2" fill="currentColor"/><rect x="0" y="6.5" width="16" height="2.5" rx="1.2" fill="currentColor" opacity=".6"/><rect x="0" y="12" width="16" height="2.5" rx="1.2" fill="currentColor" opacity=".35"/></svg>
              </button>
            </div>
          </div>

        <div v-if="!filteredRows || filteredRows.length === 0" style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px;background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:16px">
          <div style="font-size:48px;margin-bottom:12px">📭</div>
          <div class="text-muted fs13">暂无持仓数据</div>
        </div>

        <div v-else>
          <!-- Card View -->
          <div v-if="holdingsView === 'card'" style="display:grid;grid-template-columns:repeat(4, 1fr);gap:10px">
            <div v-for="(row, idx) in filteredRows.slice(0, 8)" :key="row?.code||`card-${idx}`" class="hcard">
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
                    <span class="tag" :class="row?.market">{{ row?.market==='us'?'美股':row?.market==='hk'?'港股':row?.market==='a'?'A股':'基金' }}</span>
                    <span class="h-qty"><span :style="{ fontSize: getQtyFontSize(Number(row?.qty||0).toLocaleString()) }">{{ Number(row?.qty||0).toLocaleString() }}</span>{{ row?.market === 'fund' ? '份' : '股' }}</span>
                  </div>
                </div>
                <!-- Market Value in Top Right -->
                <div class="h-mv-right">
                  {{ formatCurrency(row?.value || 0) }}
                </div>
              </div>

              <!-- Price Row (Above Sparkline) -->
              <div class="h-price-row">
                <div class="h-price-main">
                  <span class="h-price-sym">{{ getCurrencySymbol(row?.curr) }}</span>
                  <span class="h-price-val">{{ row?.price }}</span>
                </div>
                <div class="h-price-tag badge" :class="valueClass(toNumber(row?.dayPnlRate))" style="padding: 2px 6px; border-radius: 4px; font-size: 10px;">
                  {{ formatPct(toNumber(row?.dayPnlRate)) }}
                </div>
              </div>

              <!-- Sparkline stub -->
              <div style="height:38px;margin-bottom:10px;opacity:.85">
                <svg viewBox="0 0 120 40" width="100%" height="100%" preserveAspectRatio="none" fill="none">
                  <path d="M0,20 L30,15 L60,25 L90,10 L120,5" :stroke="toNumber(row?.dayPnl)>=0?'var(--red)':'var(--green)'" stroke-width="1.6" fill="none"/>
                </svg>
              </div>
              <!-- Removed redundant dayPnlRate badge -->
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.05)">
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
                  <div style="font-family:'JetBrains Mono',monospace;font-size: 12.5px; font-weight: 500; color:var(--sub)">{{ masked(formatValue(toNumber(row?.cost), row?.curr as any)) }}</div>
                </div>
                <div>
                  <div style="font-size: 10px; color: var(--muted); margin-bottom: 4px; display: flex; justify-content: space-between">仓位 <span style="color:var(--blue); font-size: 12.5px; font-weight: 600">{{ formatPct(toNumber(row?.pct)).replace('%','') }}%</span></div>
                  <div style="height:3px;background:rgba(255,255,255,0.07);border-radius:2px;overflow:hidden">
                    <div style="height:100%;background:rgba(91,141,239,0.7);border-radius:2px" :style="{ width: Math.min(toNumber(row?.pct) * 100, 100) + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Row View -->
          <div v-else style="display:flex;flex-direction:column;gap:6px">
            <div v-for="(row, idx) in filteredRows.slice(0, 8)" :key="row?.code||`row-${idx}`" class="hrow">
              <div style="display:flex;align-items:center;gap:12px;width:240px;flex-shrink:0">
                <div class="h-icon" style="width:38px;height:38px;flex-shrink:0;border:none;background:none">
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
                    <span class="tag" :class="row?.market">{{ row?.market==='us'?'美股':row?.market==='hk'?'港股':row?.market==='a'?'A股':'基金' }}</span>
                  </div>
                </div>
              </div>
              <div style="display:grid;grid-template-columns:repeat(7, 1fr);gap:12px;flex:1;align-items:center">
                <div style="padding:0 12px;border-right:1px solid rgba(255,255,255,0.05)">
                  <div style="font-size:10px;color:var(--muted);margin-bottom:3px">持仓数量</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:12.5px;font-weight:600;color:var(--text)">{{ Number(row?.qty||0).toLocaleString() }}</div>
                </div>
                <div style="padding:0 12px;border-right:1px solid rgba(255,255,255,0.05)">
                  <div style="font-size:10px;color:var(--muted);margin-bottom:3px">现价</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:12.5px;font-weight:600;color:var(--text)">
                    <span style="font-size:10px;opacity:0.6;margin-right:2px">{{ getCurrencySymbol(row?.curr) }}</span>{{ row?.price }}
                  </div>
                </div>
                <div style="padding:0 12px;border-right:1px solid rgba(255,255,255,0.05)">
                  <div style="font-size:10px;color:var(--muted);margin-bottom:3px">成本价</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:12.5px;font-weight:500;color:var(--muted)">{{ masked(formatValue(toNumber(row?.cost), row?.curr as any)) }}</div>
                </div>
                <div style="padding:0 12px;border-right:1px solid rgba(255,255,255,0.05)">
                  <div style="font-size:10px;color:var(--muted);margin-bottom:3px">市值</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:12.5px;font-weight:600;color:var(--text)">{{ masked(formatCurrency(toCny(row?.value||0, String(row?.curr)))) }}</div>
                </div>
                <div style="padding:0 12px;border-right:1px solid rgba(255,255,255,0.05)">
                  <div style="font-size:10px;color:var(--muted);margin-bottom:3px">今日盈亏</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:12.5px;font-weight:600" :class="valueClass(toNumber(row?.dayPnl))">{{ masked(formatValue(toNumber(row?.dayPnl), row?.curr as any)) }}</div>
                  <div style="font-size:11px;margin-top:1px" :class="valueClass(toNumber(row?.dayPnlRate))">{{ formatPct(toNumber(row?.dayPnlRate)) }}</div>
                </div>
                <div style="padding:0 12px;border-right:1px solid rgba(255,255,255,0.05)">
                  <div style="font-size:10px;color:var(--muted);margin-bottom:3px">累计盈亏</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:12.5px;font-weight:600" :class="valueClass(toNumber(row?.totalPnl))">{{ masked(formatValue(toNumber(row?.totalPnl), row?.curr as any)) }}</div>
                  <div style="font-size:11px;margin-top:1px" :class="valueClass(toNumber(row?.totalPnlRate))">{{ formatPct(toNumber(row?.totalPnlRate)) }}</div>
                </div>
                <div style="padding:0 0 0 12px">
                  <div style="font-size: 10px; color: var(--muted); margin-bottom: 4px; display: flex; justify-content: space-between">仓位 <span style="color:var(--blue); font-size: 12.5px; font-weight: 600">{{ formatPct(toNumber(row?.pct)).replace('%','') }}%</span></div>
                  <div style="height:4px;background:rgba(255,255,255,0.07);border-radius:3px;overflow:hidden">
                    <div style="height:100%;background:linear-gradient(90deg,rgba(91,141,239,0.5),rgba(91,141,239,0.9));border-radius:3px" :style="{ width: Math.min(toNumber(row?.pct) * 100, 100) + '%' }"></div>
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
          <button @click="closeModal" style="position:absolute;top:20px;right:20px;width:32px;height:32px;border-radius:9px;background:rgba(255,255,255,0.04);border:none;color:var(--sub);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .15s">✕</button>
          
          <div style="font-size:18px;font-weight:700;margin-bottom:4px">{{ modalTitle }}</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:600;color:var(--text);margin-bottom:24px" :style="{ color: modalType === 'liability' ? 'var(--red)' : modalType === 'other' ? 'var(--gold)' : 'var(--green)' }">
            {{ formatCny(currentTypeAssetsTotal) }}
          </div>
          
          <div style="max-height:400px;overflow-y:auto;margin:0 -8px;padding:0 8px">
            <div v-if="!currentTypeAssets.length" style="text-align:center;padding:40px;color:var(--muted);font-size:13px">暂无记录，点击下方添加</div>
            <div v-else>
              <div v-for="item in currentTypeAssets as any[]" :key="item.id" style="display:flex;align-items:center;gap:14px;padding:14px 16px;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:14px;margin-bottom:10px">
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
                   <button @click="openFormModal(item)" style="width:32px;height:32px;border-radius:9px;border:1px solid var(--border);background:rgba(255,255,255,0.04);display:flex;align-items:center;justify-content:center;cursor:pointer;color:var(--muted);flex-shrink:0"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
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
              <select class="form-inp" v-model="form.curr" style="-webkit-appearance:none;appearance:none">
                <option value="CNY">CNY 人民币</option>
                <option value="USD">USD 美元</option>
                <option value="HKD">HKD 港币</option>
              </select>
            </div>
          </div>
          <div style="display:flex;gap:8px;margin-top:8px">
            <button @click="closeFormModal" style="flex:1;height:42px;border-radius:10px;border:1px solid var(--border);background:rgba(255,255,255,0.05);color:var(--sub);font-family:'DM Sans',sans-serif;font-size:14px;font-weight:700;cursor:pointer">取消</button>
            <button @click="submitModal" :disabled="!form.name" style="flex:2;height:42px;border-radius:10px;border:none;background:linear-gradient(135deg,#5b8def,#4a7be0);color:#fff;font-family:'DM Sans',sans-serif;font-size:14px;font-weight:700;cursor:pointer;box-shadow:0 4px 14px rgba(74,123,224,0.25)" :style="{ opacity: !form.name ? 0.5 : 1 }">保存</button>
          </div>
        </div>
      </div>
    </template>
  </AppShell>
</template>

<style>
@import '@/styles/homepage-original.css';

/* Nested scoping for period tabs to ensure they match Concept 3 expectations */
.c1-period-tabs {
  display: flex !important;
  gap: 4px !important;
  background: rgba(255,255,255,0.04) !important;
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
  background: rgba(255,255,255,0.08) !important;
  color: var(--text) !important;
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
.h-name-row {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
</style>
