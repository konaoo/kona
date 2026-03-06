<script setup lang="ts">
/**
 * AppHomePage - 首页（1:1复刻版 - 原始CSS样式）
 * 完全按照参考HTML复刻UI，使用原始CSS类名系统
 */

import { computed, onMounted, onBeforeUnmount, ref, reactive } from 'vue'
import html2canvas from 'html2canvas'
import { api } from '@/shared/http'
import { toNumber } from '@/shared/format'
import { useKonaStore } from '@/stores/composables'
import { usePrivacyMode } from '@/shared/privacyMode'
import { useWebTheme } from '@/shared/webTheme'


// Types
type AssetType = 'cash' | 'other' | 'liability'
type SimpleAsset = { id: number; icon?: string; name: string; amount: number; curr?: string }

// Stores & Composables
const store = useKonaStore()
const { theme, toggleTheme } = useWebTheme()
const { isPrivacyMode, togglePrivacy, maskValue } = usePrivacyMode()

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

const rates = computed(() => (store?.state as any)?.rates || {})

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
      icon: '📈',
      name: String(row.name || ''),
      amount: Number(row.value || 0),
      curr: String(row.curr || 'CNY'),
      type: 'invest' as const,
      code: String(row.code || '')
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

// Derived asset value based on selected currency
const displayTotalAssets = computed(() => {
  const cny = totalAssetsCny.value
  if (currentCurrency.value === 'USD') return cny / rateToCny('USD')
  if (currentCurrency.value === 'HKD') return cny / rateToCny('HKD')
  return cny
})

// Current currency formatting config
const currMeta = computed(() => {
  if (currentCurrency.value === 'USD') return { sym: '$ ', label: '美元' }
  if (currentCurrency.value === 'HKD') return { sym: 'HK$ ', label: '港币' }
  return { sym: '¥ ', label: '人民币' }
})

// 持仓筛选
const filteredRows = computed(() => {
  const validRows = (rows.value || []).filter(row => row && typeof row === 'object')
  if (selectedTab.value === 'all') return validRows
  return validRows.filter(row => row?.market === selectedTab.value)
})

// Helpers
function formatCny(value: number): string {
  return `¥ ${Math.round(value).toLocaleString('zh-CN')}`
}

function formatSignedCny(value: number): string {
  const sign = value >= 0 ? '+' : '-'
  return `${sign}¥ ${Math.abs(Math.round(value)).toLocaleString('zh-CN')}`
}

function formatPct(value: number | undefined): string {
  if (typeof value !== 'number' || isNaN(value)) return '0.00%'
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function valueClass(value: number | undefined): 'up' | 'dn' | 'neutral' {
  if (typeof value !== 'number' || isNaN(value)) return 'neutral'
  return value >= 0 ? 'up' : 'dn'
}

function masked(text: string): string {
  return maskValue(text)
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
      loadLists(),
      loadMarketIndices()
    ])
  } catch (e) {
    console.error('Failed to refresh:', e)
  }
}

function saveAsImage() {
  const target = document.getElementById('capture-area')
  if (!target) return
  html2canvas(target, {
    backgroundColor: theme.value === 'light' ? '#f7fbff' : '#0a0e27',
    scale: 2,
    useCORS: true,
  }).then(canvas => {
    const link = document.createElement('a')
    link.download = `kaka-assets-${Date.now()}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
  })
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

function openModal(type: AssetType) {
  modalType.value = type
  modalVisible.value = true
  isFormModalVisible.value = false
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
  <div class="layout" :data-theme="theme" style="width: 100vw;">
    <aside class="sidebar">
      <a class="sidebar-logo">
        <div class="s-logo-icon">
          <svg width="16" height="12" viewBox="0 0 18 14" fill="none"><polyline points="1,13 5,5 9,9 13,3 17,7" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <div>
          <div class="s-logo-name">咔咔记账</div>
          <div class="s-logo-tag">GLOBAL ASSET DESK</div>
        </div>
      </a>
      <nav class="sidebar-nav">
        <div class="nav-item active" @click="$router.push('/app/home')">
          <span class="nav-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></span>首页
        </div>
        <div class="nav-item" @click="$router.push('/app/invest')">
          <span class="nav-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg></span>投资
        </div>
        <div class="nav-item">
          <span class="nav-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></span>分析
        </div>
        <div class="nav-item">
          <span class="nav-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg></span>快讯
        </div>
        <div class="nav-item">
          <span class="nav-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></span>我的
        </div>
      </nav>
      <div class="sidebar-bottom">
        <button class="sidebar-add-btn" @click="openModal('cash')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          添加资产
        </button>
      </div>
    </aside>

    <div class="main">
      <div class="topbar">
        <div class="topbar-title">首页</div>
        <div class="topbar-actions">
          <button @click="toggleTheme" class="icon-btn" :style="theme==='dark'?'':'background:rgba(0,0,0,0.04)'">
            {{ theme === 'dark' ? '🌙' : '☀️' }}
          </button>
          <button @click="togglePrivacy" class="icon-btn" :style="theme==='dark'?'':'background:rgba(0,0,0,0.04)'">
            {{ isPrivacyMode ? '🙈' : '👁️' }}
          </button>
          <button @click="saveAsImage" class="icon-btn" :style="theme==='dark'?'':'background:rgba(0,0,0,0.04)'">
            📸
          </button>
        </div>
      </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="page active" style="display:flex;align-items:center;justify-content:center;height:100%">
      <div style="text-align:center">
        <div style="font-size:48px;margin-bottom:16px">⏳</div>
        <div class="text-sub">加载中...</div>
      </div>
    </div>

    <!-- Content -->
    <div v-else id="capture-area" class="page active">

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
                <div v-show="currencyOpen" style="position:absolute;top:24px;left:0;background:var(--s2);border:1px solid var(--border-b);border-radius:10px;padding:4px;min-width:110px;z-index:100;box-shadow:0 12px 32px rgba(0,0,0,0.4);animation:modalIn .18s ease">
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
            <div class="c3-total">{{ masked(currMeta.sym + Math.round(displayTotalAssets).toLocaleString('zh-CN')) }}</div>
            <div class="c3-stats">
              <span class="badge" :class="valueClass(investTotal?.dayPnl||0)" style="font-size:12px;padding:4px 10px">今日 {{ masked(formatSignedCny(toNumber(investTotal?.dayPnl))) }}</span>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px">
            <div style="font-size:10px;color:var(--muted)">近30天走势</div>
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
            <div class="c3-segment-val">{{ masked(formatCny(investTotal?.mv||0)) }}</div>
            <div class="c3-segment-change" :class="valueClass(investTotal?.dayPnl||0)">今日 {{ formatPct(investTotal?.dayRate||0) }}</div>
          </div>
          <div class="c3-segment" :class="{ active: activeSegment === 'cash' }" @click="toggleSegment('cash')">
            <div class="c3-active-bar" :style="{ background: activeSegment === 'cash' ? 'var(--blue)' : '' }"></div>
            <div class="c3-segment-label">现金资产</div>
            <div class="c3-segment-val">{{ masked(formatCny(cashTotal)) }}</div>
            <div class="c3-segment-change text-muted">{{ cashAssets.length }}个账户</div>
          </div>
          <div class="c3-segment" :class="{ active: activeSegment === 'other' }" @click="toggleSegment('other')">
            <div class="c3-active-bar" :style="{ background: activeSegment === 'other' ? 'var(--gold)' : '' }"></div>
            <div class="c3-segment-label">其他资产</div>
            <div class="c3-segment-val">{{ masked(formatCny(otherTotal)) }}</div>
            <div class="c3-segment-change text-muted">{{ otherAssets.length }}条记录</div>
          </div>
          <div class="c3-segment" :class="{ active: activeSegment === 'liability' }" @click="toggleSegment('liability')">
            <div class="c3-active-bar" :style="{ background: activeSegment === 'liability' ? 'var(--red)' : '' }"></div>
            <div class="c3-segment-label">我的负债</div>
            <div class="c3-segment-val" style="color:var(--red)">{{ masked(formatCny(-(liabilityTotal||0))) }}</div>
            <div class="c3-segment-change text-red">{{ liabilities.length }}条负债</div>
          </div>
        </div>

        <!-- Expandable Drawer -->
        <div class="c3-drawer" :class="{ open: !!activeSegment }">
          <div class="c3-drawer-inner">
            <div v-for="item in activeDrawerData" :key="item.id" class="c5-detail-pill" @click="item.code ? $router.push(`/app/asset/${item.code}`) : openFormModal(item)">
              <span class="c5-pill-icon">{{ item.icon }}</span>
              <div>
                <div class="c5-pill-name">{{ item.name }}</div>
                <div class="c5-pill-amt" :style="{ color: item.type === 'liability' ? 'var(--red)' : 'var(--sub)' }">
                  {{ masked(formatCny(toCny(item.amount, item.curr))) }}
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
          <div class="section-label" style="margin-bottom: 10px">持仓概览</div>
          <div class="tabs" style="width: fit-content; margin-bottom: 12px">
            <button v-for="tab in ['all','hk','us','a','fund']" :key="tab" @click="selectedTab=tab" class="tab" :class="{active:selectedTab===tab}">{{ tab==='all'?'全部':tab==='hk'?'港股':tab==='us'?'美股':tab==='a'?'A股':'基金' }}</button>
          </div>

        <div v-if="!filteredRows || filteredRows.length === 0" class="holding-list" style="align-items:center;justify-content:center;padding:40px">
          <div style="font-size:48px;margin-bottom:12px">📭</div>
          <div class="text-muted fs13">暂无持仓数据</div>
        </div>

        <div v-else class="holding-list">
          <div v-for="(row, idx) in filteredRows" :key="row?.code||`holding-${idx}`" @click="row?.code && $router.push(`/app/asset/${row.code}`)" class="holding-row">
            <div class="h-icon" :class="row?.market==='us'?'blue':row?.market==='hk'?'orange':row?.market==='a'?'green':'gold'">
              {{ row?.code?.substring(0,4).toUpperCase() || '??' }}
            </div>
            <div class="h-meta">
              <div class="h-name">{{ row?.name || '未知标的' }}</div>
              <div class="flex-row gap-8 mt-4">
                <span class="tag" :class="row?.market==='us'?'us':row?.market==='hk'?'hk':row?.market==='a'?'a':'fund'">{{ row?.market==='us'?'NASDAQ·US':row?.market==='hk'?'港交所·HK':row?.market==='a'?'沪深·A':'基金' }}</span>
                <span class="mono text-muted fs11">{{ Number(row?.qty||0).toLocaleString() }}股</span>
              </div>
              <div v-if="row?.totalPnl && Math.abs(row.totalPnl) > 0" class="mt-8">
                <div class="progress-wrap">
                  <div class="progress-center"></div>
                  <div class="progress-fill" :class="(row?.totalPnl||0)>=0?'up':'dn'" :style="{left:(row?.totalPnl||0)>=0?'50%':undefined,right:(row?.totalPnl||0)<0?'50%':undefined,width:Math.min(Math.abs((row?.totalPnl||0)/(Math.max(Number(row?.value)||1,1)))*100,50)+'%'}"></div>
                </div>
              </div>
            </div>
            <div class="h-right">
              <div class="h-val">{{ masked(formatCny(toCny(row?.value||0, String(row?.curr)))) }}</div>
              <div class="badge" :class="valueClass(toNumber(row?.totalPnlRate))" style="margin-top:4px">{{ formatPct(toNumber(row?.totalPnlRate)) }}</div>
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
      </div>
    </div>
  </div>
</template>

<style>
@import '@/styles/homepage-original.css';
/* 使用全局样式以确保 :root 和 布局类生效 */
</style>
