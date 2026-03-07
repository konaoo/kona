<script setup lang="ts">
/**
 * AppInvestPage - 投资分析与明细 (Refactored Modern Style)
 */
import { computed, onMounted, ref } from 'vue'
import { toNumber } from '@/shared/format'
import { useKonaStore } from '@/stores/composables'
import { usePrivacyMode } from '@/shared/privacyMode'
import { useMarketStore } from '@/stores/market'

// Stores
const store = useKonaStore()
const { maskValue } = usePrivacyMode()
const marketStore = useMarketStore()

// State
const selectedTab = ref('all')
const holdingsView = ref<'card'|'row'>('card')

// Computed for rates and conversions
const rates = computed(() => marketStore.rates)

function rateToCny(curr?: string): number {
  const c = String(curr || 'CNY').toUpperCase()
  return toNumber(rates.value?.[c], 1) || 1
}



// Current currency formatting config (Follow Homepage)
const currentCurrency = ref<'CNY'|'USD'|'HKD'>('CNY')
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

function formatCurrency(cnyValue: number, signed = false): string {
  const val = toDisplay(cnyValue)
  const sym = currMeta.value.sym
  const sign = signed && cnyValue >= 0 ? '+' : signed && cnyValue < 0 ? '-' : ''
  const absVal = Math.abs(val)
  const formatted = absVal >= 1000 ? Math.round(absVal).toLocaleString('zh-CN') : absVal.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
  return `${sign}${sym}${formatted}`
}

// Utility

// Data Processing
const rows = computed(() => store?.rows?.value || [])

const investTotal = computed(() => {
  let mv = 0
  let cost = 0
  let dayPnl = 0
  let totalPnl = 0
  const rowsData = rows.value || []
  for (const row of rowsData) {
    const rate = rateToCny(String(row.curr))
    const rowMv = (Number(row.value) || 0) * rate
    const rowCost = (Number(row.cost) || Number(row.costPrice) * Number(row.qty) || 0) * rate
    mv += rowMv
    cost += Math.abs(rowCost)
    dayPnl += (Number(row.dayPnlAggregate) || 0) * rate
    totalPnl += (Number(row.totalPnl) || 0) * rate
  }
  const floatPnl = mv - cost
  return {
    mv,
    dayPnl,
    floatPnl,
    totalPnl,
    dayRate: (mv - dayPnl) > 0 ? (dayPnl / (mv - dayPnl)) * 100 : 0,
    floatRate: cost > 0 ? (floatPnl / cost) * 100 : 0,
    totalRate: cost > 0 ? (totalPnl / cost) * 100 : 0
  }
})

// Market breakdowns
const marketCards = computed(() => {
  const result: Record<string, any> = {
    a: { name: 'A股', dayPnl: 0, totalPnl: 0, mv: 0, cost: 0, icon: '🇨🇳' },
    hk: { name: '港股', dayPnl: 0, totalPnl: 0, mv: 0, cost: 0, icon: '🇭🇰' },
    us: { name: '美股', dayPnl: 0, totalPnl: 0, mv: 0, cost: 0, icon: '🇺🇸' },
    fund: { name: '基金', dayPnl: 0, totalPnl: 0, mv: 0, cost: 0, icon: '📈' }
  }
  
  rows.value.forEach(row => {
    const m = row.market as string
    if (result[m]) {
      const rate = rateToCny(String(row.curr))
      const rowMv = (Number(row.value) || 0) * rate
      const rowCost = (Number(row.cost) || Number(row.costPrice) * Number(row.qty) || 0) * rate
      result[m].mv += rowMv
      result[m].cost += Math.abs(rowCost)
      result[m].dayPnl += (Number(row.dayPnlAggregate) || 0) * rate
      result[m].totalPnl += (Number(row.totalPnl) || 0) * rate
    }
  })
  
  return Object.values(result).map(m => ({
    ...m,
    dayRate: (m.mv - m.dayPnl) > 0 ? (m.dayPnl / (m.mv - m.dayPnl)) * 100 : 0,
    totalRate: m.cost > 0 ? (m.totalPnl / m.cost) * 100 : 0
  }))
})

// Distribution Donut Chart
const distributionData = computed(() => {
  const total = investTotal.value.mv || 1
  return marketCards.value.map(m => ({
    name: m.name,
    percent: (m.mv / total) * 100,
    value: m.mv,
    color: m.name === '美股' ? '#5B8DEF' : m.name === 'A股' ? '#F05A55' : m.name === '港股' ? '#3ECF82' : '#F2C94C'
  })).filter(d => d.value > 0).sort((a, b) => b.value - a.value)
})

// Helpers for SVG Chart
const slices = computed(() => {
    let currentPercent = 0;
    return distributionData.value.map(d => {
        const start = currentPercent;
        currentPercent += d.percent;
        return { ...d, start, end: currentPercent };
    });
})

function describeArc(x: number, y: number, radius: number, startAngle: number, endAngle: number) {
    const start = polarToCartesian(x, y, radius, endAngle);
    const end = polarToCartesian(x, y, radius, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
    return ["M", start.x, start.y, "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y].join(" ");
}

function polarToCartesian(centerX: number, centerY: number, radius: number, angleInDegrees: number) {
    const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
    return {
        x: centerX + (radius * Math.cos(angleInRadians)),
        y: centerY + (radius * Math.sin(angleInRadians))
    };
}

// Holdings filtering
// Utility

const filteredRows = computed(() => {
  const s = selectedTab.value
  let base = rows.value || []
  if (s !== 'all') {
    base = base.filter(r => r.market === s)
  }
  return base.map(row => {
    const qty = Number(row.qty) || 0
    const last = Number(row.last) || 0
    const costPrice = Number(row.costPrice) || 0
    const cost = Math.abs(Number(row.cost) || costPrice * qty)
    const mv = Number(row.value) || (qty * last)
    
    // Percentages
    const dayPnl = Number(row.dayPnlAggregate) || 0
    const totalPnl = Number(row.totalPnl) || (mv - cost)
    
    const dayPnlRate = (mv - dayPnl) > 0 ? (dayPnl / (mv - dayPnl)) * 100 : 0
    const totalPnlRate = cost > 0 ? (totalPnl / cost) * 100 : 0
    const totalMarketMv = investTotal.value.mv || 1
    const pct = mv / totalMarketMv

    return {
      ...row,
      qty,
      last,
      costPrice,
      mv,
      dayPnl,
      totalPnl,
      dayPnlRate,
      totalPnlRate,
      cost,
      pct,
      price: last,
      curr: String(row.curr || 'CNY'),
      market: row.market,
      unit: row.unit || (row.market === 'fund' ? '份' : '股'),
      spark: row.spark || 'M0,30 L20,26 L40,28 L60,18 L80,14 L100,8 L120,5' // Default mock spark
    }
  })
})

// Utility
function masked(text: string): string { return maskValue(text) }
function formatPct(v: number): string { return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%` }
function valueClass(v: number): string { return v >= 0 ? 'up' : 'dn' }
function getMarketCls(m: string) {
  if (m === 'us') return 'blue'
  if (m === 'hk') return 'orange'
  if (m === 'a') return 'green'
  return 'gold'
}
function getMarketName(m: string) {
  if (m === 'us') return 'NASDAQ·US'
  if (m === 'hk') return '港交所·HK'
  if (m === 'a') return '沪深·A'
  return '基金'
}
function formatLocal(v: any, cur?: string) {
  return Number(v || 0).toLocaleString()
}

onMounted(async () => {
    try {
        await store.refreshAll()
        await marketStore.loadRates()
    } catch (e) {
        console.error('Failed to load invest data', e)
    }
})

</script>

<template>
  <div class="kk-page invest-page">
    <div class="modern-shell">
      <!-- Top Title -->
      <div class="page-header">
        <div class="title-group">
          <h1>投资资产分析</h1>
          <div class="subtitle">Investment Analysis & Portfolio</div>
        </div>
        <div class="ccy-tag" @click="currentCurrency = (currentCurrency === 'CNY' ? 'USD' : currentCurrency === 'USD' ? 'HKD' : 'CNY')">
          {{ currentCurrency }} 汇率折算
        </div>
      </div>

      <!-- Main Statistics Grid -->
      <div class="stats-grid">
        <!-- Hero Card: Total MV -->
        <div class="hero-card">
          <div class="card-label">投资总资产 ({{ currentCurrency }})</div>
          <div class="main-val">{{ masked(formatCurrency(investTotal.mv)) }}</div>
          <div class="stats-row">
            <div class="stat-item">
              <span class="sl">今日盈亏</span>
              <div class="sv-group" :class="valueClass(investTotal.dayPnl)">
                <span class="sv-amt">{{ formatCurrency(investTotal.dayPnl, true) }}</span>
                <span class="sv-pct">{{ formatPct(investTotal.dayRate) }}</span>
              </div>
            </div>
            <div class="stat-item">
              <span class="sl">持仓收益</span>
              <div class="sv-group" :class="valueClass(investTotal.floatPnl)">
                <span class="sv-amt">{{ formatCurrency(investTotal.floatPnl, true) }}</span>
                <span class="sv-pct">{{ formatPct(investTotal.floatRate) }}</span>
              </div>
            </div>
            <div class="stat-item">
              <span class="sl">累计收益</span>
              <div class="sv-group" :class="valueClass(investTotal.totalPnl)">
                <span class="sv-amt">{{ formatCurrency(investTotal.totalPnl, true) }}</span>
                <span class="sv-pct">{{ formatPct(investTotal.totalRate) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Donut Distribution Card -->
        <div class="dist-card">
           <div class="card-title">资产分布</div>
           <div class="dist-content">
              <div class="chart-container">
                  <svg viewBox="0 0 100 100" class="donut-svg">
                      <circle cx="50" cy="50" r="35" fill="transparent" stroke="rgba(255,255,255,0.05)" stroke-width="12" />
                      <g v-for="(slice, i) in slices" :key="i">
                          <path 
                            :d="describeArc(50, 50, 35, slice.start * 3.6, slice.end * 3.6)" 
                            :stroke="slice.color" 
                            stroke-width="12" 
                            fill="none"
                            stroke-linecap="round"
                            class="donut-slice"
                          />
                      </g>
                      <text x="50" y="47" text-anchor="middle" class="chart-center-val">{{ distributionData.length }}</text>
                      <text x="50" y="62" text-anchor="middle" class="chart-center-lbl">资产</text>
                  </svg>
              </div>
              <div class="legend-list">
                  <div v-for="item in distributionData" :key="item.name" class="legend-item">
                      <span class="dot" :style="{ background: item.color }"></span>
                      <span class="ln">{{ item.name }}</span>
                      <span class="lp">{{ item.percent.toFixed(1) }}%</span>
                  </div>
              </div>
           </div>
        </div>
      </div>

      <!-- Market Breakdown PnL Grid -->
      <div class="market-grid">
         <div v-for="m in marketCards" :key="m.name" class="market-card">
            <div class="m-header">
                <div class="m-title">
                    <span class="m-icon">{{ m.icon }}</span>
                    <span class="m-name">{{ m.name }}</span>
                </div>
                <div class="m-mv">{{ formatCurrency(m.mv) }}</div>
            </div>
            <div class="m-stats">
                <div class="ms-item">
                    <div class="ms-lbl">今日</div>
                    <div class="ms-val-group" :class="valueClass(m.dayPnl)">
                        <div class="ms-amt">{{ formatCurrency(m.dayPnl, true) }}</div>
                        <div class="ms-pct">{{ formatPct(m.dayRate) }}</div>
                    </div>
                </div>
                <div class="ms-item">
                    <div class="ms-lbl">累计</div>
                    <div class="ms-val-group" :class="valueClass(m.totalPnl)">
                        <div class="ms-amt">{{ formatCurrency(m.totalPnl, true) }}</div>
                        <div class="ms-pct">{{ formatPct(m.totalRate) }}</div>
                    </div>
                </div>
            </div>
         </div>
      </div>

      <!-- Holdings 1:1 Replica from Homepage -->
      <div class="holdings-section">
          <div class="h-header">
              <div class="h-title-group">
                <div class="section-label">持仓明细</div>
                <div class="tabs">
                    <button v-for="tab in ['all','hk','us','a','fund']" :key="tab" @click="selectedTab=tab" class="tab" :class="{active:selectedTab===tab}">{{ tab==='all'?'全部':tab==='hk'?'港股':tab==='us'?'美股':tab==='a'?'A股':'基金' }}</button>
                </div>
              </div>
              <div class="view-toggle">
                  <button @click="holdingsView='card'" :class="{active: holdingsView==='card'}">
                    <svg width="13" height="13" viewBox="0 0 16 16" fill="none"><rect x="0" y="0" width="7" height="7" rx="1.5" fill="currentColor"/><rect x="9" y="0" width="7" height="7" rx="1.5" fill="currentColor"/><rect x="0" y="9" width="7" height="7" rx="1.5" fill="currentColor"/><rect x="9" y="9" width="7" height="7" rx="1.5" fill="currentColor"/></svg>
                  </button>
                  <button @click="holdingsView='row'" :class="{active: holdingsView==='row'}">
                    <svg width="13" height="13" viewBox="0 0 16 16" fill="none"><rect x="0" y="1" width="16" height="2.5" rx="1.2" fill="currentColor"/><rect x="0" y="6.5" width="16" height="2.5" rx="1.2" fill="currentColor"/><rect x="0" y="12" width="16" height="2.5" rx="1.2" fill="currentColor"/></svg>
                  </button>
              </div>
          </div>

          <div v-if="!filteredRows || filteredRows.length === 0" class="empty-state">
              <div class="empty-icon">📭</div>
              <div class="empty-text">暂无持仓数据</div>
          </div>

          <div v-else>
              <!-- Card View -->
              <div v-if="holdingsView === 'card'" class="card-view-grid">
                <div v-for="(row, idx) in filteredRows" :key="row?.code||`card-${idx}`" @click="row?.code && $router.push(`/app/asset/${row.code}`)" class="hcard">
                  <!-- Top Accent Bar -->
                  <div 
                    class="hcard-accent-top" 
                    :style="{ background: `linear-gradient(90deg, transparent, ${toNumber(row.dayPnl) >= 0 ? 'var(--red)' : 'var(--green)'} 40%, transparent)` }"
                  ></div>
                  
                  <div class="h-icon" :class="[getMarketCls(row.market)]" style="width:38px;height:38px;font-size:9px;margin-bottom:10px">
                    {{ row.code?.substring(0, 4).toUpperCase() || '??' }}
                  </div>
                  
                  <div class="h-name" style="font-size:13px;font-weight:700;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:3px">
                    {{ row.name }}
                  </div>
                  
                  <div style="display:flex;align-items:center;gap:5px;margin-bottom:10px">
                    <span class="tag" :class="[row.market]">{{ getMarketName(row.market) }}</span>
                    <span style="font-size:10px;color:var(--muted)">{{ formatLocal(row.amount, '') }}{{ row.unit }}</span>
                  </div>

                  <!-- Sparkline -->
                  <div style="height:38px;margin-bottom:10px;opacity:.85">
                    <svg viewBox="0 0 120 40" width="100%" height="100%" preserveAspectRatio="none" fill="none">
                      <path 
                        :d="row.spark" 
                        :stroke="toNumber(row.dayPnl) >= 0 ? 'var(--red)' : 'var(--green)'" 
                        stroke-width="1.6" 
                        fill="none"
                      />
                    </svg>
                  </div>

                  <div style="font-family: 'JetBrains Mono', monospace; font-size:16px; font-weight:600; color:var(--text); margin-bottom:5px">
                    {{ formatCurrency(row.mv) }}
                  </div>
                  
                  <div 
                    class="badge" 
                    :class="[toNumber(row.dayPnlRate) >= 0 ? 'up' : 'dn']"
                    style="display:inline-flex;font-size:10px;font-weight:700;padding:2px 8px;border-radius:6px;margin-bottom:10px"
                  >
                    {{ formatPct(row.dayPnlRate) }}
                  </div>

                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.05)">
                    <div>
                      <div style="font-size:9px;color:var(--muted);margin-bottom:2px">今日盈亏</div>
                      <div :class="[toNumber(row.dayPnl) >= 0 ? 'text-up' : 'text-dn']" style="font-family: 'JetBrains Mono', monospace; font-size:11px; font-weight:600">
                        {{ formatCurrency(row.dayPnl, true) }}
                      </div>
                    </div>
                    <div>
                      <div style="font-size:9px;color:var(--muted);margin-bottom:2px">累计盈亏</div>
                      <div :class="[toNumber(row.totalPnlRate) >= 0 ? 'text-up' : 'text-dn']" style="font-family: 'JetBrains Mono', monospace; font-size:11px; font-weight:600">
                        {{ formatPct(row.totalPnlRate) }}
                      </div>
                    </div>
                    <div>
                      <div style="font-size:9px;color:var(--muted);margin-bottom:2px">成本价</div>
                      <div style="font-family: 'JetBrains Mono', monospace; font-size:11px; font-weight:500; color:var(--sub)">
                        {{ row.cost }}
                      </div>
                    </div>
                    <div>
                      <div style="font-size:9px;color:var(--muted);margin-bottom:4px;display:flex;justify-content:space-between">
                        仓位 <span style="color:var(--blue)">{{ formatPct(row.pct).replace('%','') }}%</span>
                      </div>
                      <div style="height:3px;background:rgba(255,255,255,0.07);border-radius:2px;overflow:hidden">
                        <div 
                          style="height:100%;background:rgba(91,141,239,0.7);border-radius:2px"
                          :style="{ width: `${Math.min(toNumber(row.pct) * 100, 100)}%` }"
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Row View -->
              <div v-else class="row-view-list">
                <div v-for="(row, idx) in filteredRows" :key="row?.code||`row-${idx}`" @click="row?.code && $router.push(`/app/asset/${row.code}`)" class="hrow">
                  <div style="display:flex;align-items:center;gap:11px">
                    <div class="h-icon" :class="[getMarketCls(row.market)]" style="width:38px;height:38px;font-size:9px;flex-shrink:0">
                      {{ row.code?.substring(0,4).toUpperCase() || '??' }}
                    </div>
                    <div>
                      <div style="font-size:13px;font-weight:700;color:var(--text)">{{ row.name }}</div>
                      <div style="display:flex;gap:5px;margin-top:3px">
                        <span class="tag" :class="[row.market]">{{ getMarketName(row.market) }}</span>
                        <span style="font-size:10px;color:var(--muted)">{{ formatLocal(row.amount, '') }}{{ row.unit }}</span>
                      </div>
                    </div>
                  </div>

                  <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1.2fr 1.2fr 1fr;align-items:center;gap:0">
                    <div style="padding:0 12px;border-right:1px solid rgba(255,255,255,0.05)">
                      <div style="font-size:9px;color:var(--muted);margin-bottom:3px">现价</div>
                      <div style="font-family: 'JetBrains Mono', monospace; font-size:12px; font-weight:600; color:var(--text)">
                        {{ row.price }}
                      </div>
                    </div>
                    <div style="padding:0 12px;border-right:1px solid rgba(255,255,255,0.05)">
                      <div style="font-size:9px;color:var(--muted);margin-bottom:3px">成本价</div>
                      <div style="font-family: 'JetBrains Mono', monospace; font-size:12px; font-weight:500; color:var(--muted)">
                        {{ row.cost }}
                      </div>
                    </div>
                    <div style="padding:0 12px;border-right:1px solid rgba(255,255,255,0.05)">
                      <div style="font-size:9px;color:var(--muted);margin-bottom:3px">市值</div>
                      <div style="font-family: 'JetBrains Mono', monospace; font-size:12px; font-weight:600; color:var(--text)">
                        {{ formatCurrency(row.mv) }}
                      </div>
                    </div>
                    <div style="padding:0 12px;border-right:1px solid rgba(255,255,255,0.05)">
                      <div style="font-size:9px;color:var(--muted);margin-bottom:3px">今日盈亏</div>
                      <div :class="[toNumber(row.dayPnl) >= 0 ? 'text-up' : 'text-dn']" style="font-family: 'JetBrains Mono', monospace; font-size:12px; font-weight:600">
                        {{ formatCurrency(row.dayPnl, true) }}
                      </div>
                      <div style="font-size:10px;margin-top:1px" :class="[toNumber(row.dayPnl) >= 0 ? 'text-up' : 'text-dn']">
                        {{ formatPct(row.dayPnlRate) }}
                      </div>
                    </div>
                    <div style="padding:0 12px;border-right:1px solid rgba(255,255,255,0.05)">
                      <div style="font-size:9px;color:var(--muted);margin-bottom:3px">累计盈亏</div>
                      <div :class="[toNumber(row.totalPnl) >= 0 ? 'text-up' : 'text-dn']" style="font-family: 'JetBrains Mono', monospace; font-size:12px; font-weight:600">
                        {{ formatCurrency(row.totalPnl, true) }}
                      </div>
                      <div style="font-size:10px;margin-top:1px" :class="[toNumber(row.totalPnl) >= 0 ? 'text-up' : 'text-dn']">
                        {{ formatPct(row.totalPnlRate) }}
                      </div>
                    </div>
                    <div style="padding:0 0 0 12px">
                      <div style="font-size:9px;color:var(--muted);margin-bottom:4px;display:flex;justify-content:space-between">
                        仓位 <span style="color:var(--blue)">{{ formatPct(row.pct).replace('%','') }}%</span>
                      </div>
                      <div style="height:4px;background:rgba(255,255,255,0.07);border-radius:3px;overflow:hidden">
                        <div 
                          style="height:100%;background:linear-gradient(90deg,rgba(91,141,239,0.5),rgba(91,141,239,0.9));border-radius:3px"
                          :style="{ width: `${Math.min(toNumber(row.pct) * 100, 100)}%` }"
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
          </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import '@/styles/homepage-original.css';

.invest-page {
  padding: 24px;
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family: 'DM Sans',-apple-system,BlinkMacSystemFont,sans-serif;
}

.modern-shell {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 32px;
}
.page-header h1 { font-size: 28px; font-weight: 800; margin: 0; color: var(--text); }
.subtitle { font-size: 13px; color: var(--sub); margin-top: 4px; font-family: 'JetBrains Mono', monospace; }
.ccy-tag {
  padding: 8px 16px;
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all .2s;
}
.ccy-tag:hover { background: rgba(255,255,255,0.08); border-color: var(--blue); }

.stats-grid {
  display: grid;
  grid-template-columns: 1.8fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.hero-card {
  background: linear-gradient(135deg, rgba(91,141,239,0.1), rgba(74,123,224,0.05));
  border: 1px solid rgba(91,141,239,0.2);
  border-radius: 28px;
  padding: 32px;
  display: flex;
  flex-direction: column;
}
.card-label { font-size: 13px; color: var(--sub); margin-bottom: 12px; font-weight: 600; }
.main-val { font-family: 'JetBrains Mono', monospace; font-size: 42px; font-weight: 800; margin-bottom: 24px; letter-spacing: -1px; }
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; padding: 4px 0; }
.stat-item { display: flex; flex-direction: column; gap: 8px; }
.sl { font-size: 11px; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.sv-group { display: flex; flex-direction: column; gap: 4px; }
.sv-amt { font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 800; white-space: nowrap; letter-spacing: -0.5px; }
.sv-pct { font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; opacity: 0.9; }
.sv-group.up { color: var(--red); }
.sv-group.dn { color: var(--green); }

.dist-card {
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: 28px;
  padding: 20px;
}
.card-title { font-size: 14px; font-weight: 700; margin-bottom: 16px; color: var(--text); }
.dist-content { display: flex; align-items: center; gap: 20px; }
.chart-container { position: relative; width: 100px; height: 100px; flex-shrink: 0; }
.donut-svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.chart-center-val { fill: var(--text); font-size: 18px; font-weight: 800; font-family: 'JetBrains Mono', monospace; transform: rotate(90deg); transform-origin: center; }
.chart-center-lbl { fill: var(--sub); font-size: 8px; font-weight: 600; transform: rotate(90deg); transform-origin: center; }
.donut-slice { transition: stroke-dasharray 0.5s var(--easing-out); }

.legend-list { flex: 1; display: flex; flex-direction: column; gap: 6px; }
.legend-item { display: flex; align-items: center; gap: 8px; font-size: 11px; }
.legend-item .dot { width: 6px; height: 6px; border-radius: 50%; }
.legend-item .ln { color: var(--sub); flex: 1; }
.legend-item .lp { font-weight: 700; color: var(--text); font-family: 'JetBrains Mono', monospace; }

.market-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}
.market-card {
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 18px;
  transition: all .2s;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.market-card:hover { border-color: rgba(91,141,239,0.3); transform: translateY(-2px); background: rgba(255,255,255,0.01); }
.m-header { display: flex; justify-content: space-between; align-items: center; }
.m-title { display: flex; align-items: center; gap: 8px; }
.m-icon { font-size: 14px; }
.m-name { font-size: 13px; font-weight: 700; color: var(--text); opacity: 0.9; }
.m-mv { font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600; color: var(--muted); }

.m-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.ms-item { display: flex; flex-direction: column; gap: 6px; }
.ms-lbl { font-size: 10px; color: var(--muted); font-weight: 600; text-transform: uppercase; }
.ms-val-group { display: flex; flex-direction: column; gap: 2px; }
.ms-amt { font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; white-space: nowrap; }
.ms-pct { font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 600; opacity: 0.85; }
.ms-val-group.up { color: var(--red); }
.ms-val-group.dn { color: var(--green); }

.holdings-section { margin-top: 40px; }
.h-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; }
.h-title-group .section-label { margin: 0 0 12px; font-size: 16px; }
.view-toggle {
  display: flex; gap: 4px; background: rgba(255,255,255,0.04); border: 1px solid var(--border); border-radius: 9px; padding: 3px;
}
.view-toggle button {
  width: 32px; height: 28px; border-radius: 6px; border: none; background: transparent; color: var(--muted); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all .2s;
}
.view-toggle button.active { background: rgba(255,255,255,0.08); color: var(--text); }

/* Holdings 1:1 Styles */
.card-view-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 14px; }
.hcard {
  position: relative;
  background: var(--s2);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px;
  cursor: pointer;
  transition: all .2s;
  overflow: hidden;
}
.hcard:hover { 
  background: rgba(255,255,255,0.05); 
  transform: translateY(-2px); 
  box-shadow: 0 8px 24px rgba(0,0,0,0.3); 
  border-color: var(--border-b); 
}
.hcard-accent-top { 
  position: absolute; 
  top: 0; 
  left: 0; 
  right: 0; 
  height: 2px; 
}
.h-icon { 
  width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; 
  font-size: 10px; font-weight: 800; color: #fff; margin-bottom: 12px; 
}
.h-icon.blue { background: #007AFF; }
.h-icon.orange { background: #FF9500; }
.h-icon.green { background: #34C759; }
.h-icon.gold { background: #FFCC00; }

.tag { font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
.tag.us { background: rgba(0,122,255,0.1); color: #007AFF; }
.tag.hk { background: rgba(255,149,0,0.1); color: #FF9500; }
.tag.a { background: rgba(52,199,89,0.1); color: #34C759; }
.tag.fund { background: rgba(255,204,0,0.1); color: #FFCC00; }

.row-view-list { display: flex; flex-direction: column; gap: 8px; }
.hrow { 
  display: flex; justify-content: space-between; align-items: center; 
  background: var(--s2); border: 1px solid var(--border); border-radius: 18px; 
  padding: 14px 20px; cursor: pointer; transition: all .2s; 
}
.hrow:hover { background: rgba(255,255,255,0.03); border-color: var(--blue); }

.badge.up { background: rgba(240,90,85,0.12); color: var(--red); }
.badge.dn { background: rgba(62,207,130,0.12); color: var(--green); }

.text-up { color: var(--red) !important; }
.text-dn { color: var(--green) !important; }

@media (max-width: 900px) {
  .stats-grid { grid-template-columns: 1fr; }
  .market-grid { grid-template-columns: 1fr 1fr; }
  .row-view-list > .hrow > div:nth-child(2) { display: none; }
}

.empty-state { padding: 80px 0; text-align: center; background: rgba(255,255,255,0.01); border: 1px dashed var(--border); border-radius: 32px; }
.empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.5; }
.empty-text { font-size: 14px; color: var(--muted); }

/* Color overrides for consistent palette */
.up { color: #F05A55 !important; }
.dn { color: #3ECF82 !important; }
</style>
