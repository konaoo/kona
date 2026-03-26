<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/shared/http'
import { toNumber } from '@/shared/format'
import { useKonaStore } from '@/stores/composables'
import AppShell from '@/layouts/AppShell.vue'
import AssetLogo from '@/components/base/AssetLogo.vue'
import { InvestTradeModal } from '@/components'

type TradeMode = 'buy' | 'sell' | 'adjust'

const route = useRoute()
const router = useRouter()
const store = useKonaStore()

const loading = ref(false)
const txLoading = ref(false)
const pageError = ref('')
const txList = ref<Record<string, any>[]>([])

const showTradeModal = ref(false)
const tradeMode = ref<TradeMode>('buy')

const code = computed(() => {
  const raw = String(route.params.code || '').trim()
  if (!raw) return ''
  try {
    return decodeURIComponent(raw)
  } catch {
    return raw
  }
})

const row = computed(() => {
  const target = code.value.trim().toLowerCase()
  if (!target) return null
  return (
    store.rows.value.find((item) => String(item.code || '').trim().toLowerCase() === target) ||
    null
  )
})

const marketLabel = computed(() => {
  const market = String(row.value?.category || row.value?.market || '').toLowerCase()
  if (market === 'hk') return '港股'
  if (market === 'us') return '美股'
  if (market === 'fund') return '基金'
  return 'A股'
})

function isFundAsset(item: any): boolean {
  const market = String(item?.category || item?.market || '').toLowerCase()
  if (market === 'fund') return true
  const assetType = String(item?.asset_type || '').toLowerCase()
  if (assetType === 'fund') return true
  const codeText = String(item?.code || '').toLowerCase()
  return codeText.startsWith('f_') || codeText.startsWith('ft_')
}

function readLatestNavDate(item: any): string | null {
  const raw = String(item?.latest_nav_date ?? item?.latestNavDate ?? '').trim()
  return raw || null
}

function formatLatestNavDateText(value: string | null): string | null {
  const text = String(value || '').trim()
  if (!text) return null
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(text)
  if (!match) return text
  return `${match[2]}-${match[3]}`
}

function formatDisplayCode(raw: unknown): string {
  const codeText = String(raw || '').trim()
  if (!codeText) return '--'
  if (codeText === 'ft_LU1116320737') return 'BLK'
  if (codeText.toLowerCase().startsWith('gb_')) return codeText.slice(3).toUpperCase()
  if (codeText.toLowerCase().startsWith('f_')) return codeText.slice(2)
  if (codeText.toLowerCase().startsWith('ft_')) return codeText.slice(3)
  if (codeText.toLowerCase().startsWith('sh') || codeText.toLowerCase().startsWith('sz') || codeText.toLowerCase().startsWith('bj')) {
    return codeText.slice(2)
  }
  return codeText.toUpperCase()
}

function getCurrencySymbol(curr?: string): string {
  const codeText = String(curr || 'CNY').toUpperCase()
  if (codeText === 'USD') return '$'
  if (codeText === 'HKD') return 'HK$'
  return '¥'
}

function formatSignedMoney(value: unknown, curr?: string, integerOnly = true): string {
  const amount = toNumber(value)
  if (!Number.isFinite(amount)) return '--'
  const abs = Math.abs(amount)
  const formatted = integerOnly
    ? Math.round(abs).toLocaleString('zh-CN')
    : abs.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 4 })
  const sign = amount >= 0 ? '+' : '-'
  return `${sign}${getCurrencySymbol(curr)} ${formatted}`
}

function formatMoney(value: unknown, curr?: string): string {
  const amount = toNumber(value)
  if (!Number.isFinite(amount)) return '--'
  const abs = Math.abs(amount)
  return `${getCurrencySymbol(curr)} ${Math.round(abs).toLocaleString('zh-CN')}`
}

function formatPct(value: unknown): string {
  const amount = toNumber(value)
  if (!Number.isFinite(amount)) return '--'
  return `${amount >= 0 ? '+' : ''}${amount.toFixed(2)}%`
}

function valueClass(value: unknown): 'up' | 'dn' | 'flat' {
  const amount = toNumber(value)
  if (!Number.isFinite(amount) || amount === 0) return 'flat'
  return amount > 0 ? 'up' : 'dn'
}

function formatPrice(item: any): string {
  const value = toNumber(item?.price)
  if (!Number.isFinite(value) || value <= 0) return '--'
  const digits = isFundAsset(item) ? 4 : 2
  return `${getCurrencySymbol(item?.curr)}${value.toLocaleString('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  })}`
}

function formatDateTime(raw: unknown): string {
  const text = String(raw || '').trim()
  if (!text) return '-'
  const date = new Date(text)
  if (Number.isNaN(date.getTime())) return text
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${d} ${hh}:${mm}`
}

function tradeTypeLabel(item: Record<string, any>): string {
  const text = String(item.type || item.action || '').trim().toLowerCase()
  if (text === 'buy') return '买入'
  if (text === 'sell') return '卖出'
  if (text === 'modify') return '修正'
  if (text === 'dividend') return '分红'
  if (text === 'fee') return '手续费'
  return text || '-'
}

function tradeQtyLabel(item: Record<string, any>): string {
  const qty = toNumber(item.qty)
  if (!Number.isFinite(qty)) return '-'
  return qty.toLocaleString('zh-CN')
}

function tradePriceLabel(item: Record<string, any>): string {
  const price = toNumber(item.price)
  if (!Number.isFinite(price)) return '-'
  return price.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 4 })
}

async function loadTransactions() {
  txLoading.value = true
  try {
    const payload = await api.get<Record<string, any>[]>('/api/transactions?days=3650')
    const target = code.value.trim().toLowerCase()
    const list = (Array.isArray(payload) ? payload : [])
      .filter((item) => String(item.code || '').trim().toLowerCase() === target)
      .sort((a, b) => {
        const at = new Date(String(a.time || a.date || a.created_at || '')).getTime()
        const bt = new Date(String(b.time || b.date || b.created_at || '')).getTime()
        return bt - at
      })
    txList.value = list
  } catch (error) {
    console.error('Failed to load investment transactions', error)
    txList.value = []
  } finally {
    txLoading.value = false
  }
}

async function refreshDetail() {
  loading.value = true
  pageError.value = ''
  try {
    await store.refreshAll()
    await loadTransactions()
    void store.refreshQuotesOnly()
  } catch (error) {
    console.error('Failed to refresh asset detail', error)
    pageError.value = '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function openTrade(mode: TradeMode) {
  if (!row.value) return
  tradeMode.value = mode
  showTradeModal.value = true
}

async function onTradeSuccess() {
  await refreshDetail()
}

watch(code, () => {
  txList.value = []
  void refreshDetail()
})

onMounted(() => {
  void refreshDetail()
})
</script>

<template>
  <AppShell title="投资分析">
    <div class="asset-detail-page">
      <div class="detail-header-row">
        <button class="back-btn" type="button" @click="router.back()">返回</button>
        <button class="refresh-btn" type="button" @click="refreshDetail">刷新</button>
      </div>

      <div v-if="pageError" class="detail-error">{{ pageError }}</div>

      <div v-if="!row && !loading" class="detail-empty">
        未找到该资产持仓，可能已清仓或代码不存在。
      </div>

      <template v-else-if="row">
        <div class="detail-card">
          <div class="asset-head">
            <div class="asset-main">
              <div class="asset-logo-wrap">
                <AssetLogo
                  :name="row.name"
                  :code="row.code"
                  :logo-url="row.logo_url"
                  :market="row.market"
                  :asset-type="row.asset_type"
                />
              </div>
              <div class="asset-title-wrap">
                <div class="asset-name">{{ row.name || formatDisplayCode(row.code) }}</div>
                <div class="asset-meta">
                  <span class="asset-tag">{{ marketLabel }}</span>
                  <span>{{ formatDisplayCode(row.code) }}</span>
                  <span>{{ Number(row.qty || 0).toLocaleString('zh-CN') }}{{ row.unit || (isFundAsset(row) ? '份' : '股') }}</span>
                </div>
              </div>
            </div>
            <div class="asset-mv">{{ formatMoney(row.mv ?? row.value, row.curr) }}</div>
          </div>

          <div class="metric-grid">
            <div class="metric-item">
              <div class="metric-label">{{ isFundAsset(row) ? '最新净值' : '最新价格' }}</div>
              <div class="metric-value">{{ formatPrice(row) }}</div>
              <div v-if="isFundAsset(row)" class="metric-sub">
                {{ formatLatestNavDateText(readLatestNavDate(row)) ? `净值日期 ${formatLatestNavDateText(readLatestNavDate(row))}` : '净值日期 --' }}
              </div>
            </div>

            <div class="metric-item">
              <div class="metric-label">成本价</div>
              <div class="metric-value">{{ formatPrice({ ...row, price: row.costPrice }) }}</div>
            </div>

            <div class="metric-item">
              <div class="metric-label">今日盈亏</div>
              <div class="metric-value" :class="valueClass(row.dayPnl)">{{ formatSignedMoney(row.dayPnl, row.curr) }}</div>
              <div class="metric-sub" :class="valueClass(row.dayPnlRate)">{{ formatPct(row.dayPnlRate) }}</div>
            </div>

            <div class="metric-item">
              <div class="metric-label">累计盈亏</div>
              <div class="metric-value" :class="valueClass(row.totalPnl)">{{ formatSignedMoney(row.totalPnl, row.curr) }}</div>
              <div class="metric-sub" :class="valueClass(row.totalPnlRate)">{{ formatPct(row.totalPnlRate) }}</div>
            </div>
          </div>
        </div>

        <div class="action-row">
          <button class="action-btn buy" type="button" @click="openTrade('buy')">加仓</button>
          <button class="action-btn sell" type="button" @click="openTrade('sell')">减仓</button>
          <button class="action-btn adjust" type="button" @click="openTrade('adjust')">修正</button>
        </div>

        <div class="tx-card">
          <div class="tx-head">交易记录</div>

          <div v-if="txLoading" class="tx-empty">正在加载交易记录…</div>
          <div v-else-if="txList.length === 0" class="tx-empty">暂无交易记录</div>
          <div v-else class="tx-list">
            <div class="tx-row tx-row-head">
              <div class="tx-col tx-col-head time">时间</div>
              <div class="tx-col tx-col-head type">类型</div>
              <div class="tx-col tx-col-head qty">数量</div>
              <div class="tx-col tx-col-head price">单价</div>
              <div class="tx-col tx-col-head pnl">盈亏</div>
            </div>
            <div v-for="item in txList" :key="String(item.id || `${item.time || item.date}-${item.type}-${item.qty}`)" class="tx-row">
              <div class="tx-col time">{{ formatDateTime(item.time || item.date || item.created_at) }}</div>
              <div class="tx-col type">{{ tradeTypeLabel(item) }}</div>
              <div class="tx-col qty">{{ tradeQtyLabel(item) }}</div>
              <div class="tx-col price">{{ tradePriceLabel(item) }}</div>
              <div class="tx-col pnl" :class="valueClass(item.pnl)">{{ item.pnl == null ? '-' : formatSignedMoney(item.pnl, row.curr) }}</div>
            </div>
          </div>
        </div>
      </template>

      <InvestTradeModal
        v-model:show="showTradeModal"
        :asset="row"
        :mode="tradeMode"
        @success="onTradeSuccess"
      />
    </div>
  </AppShell>
</template>

<style>
.asset-detail-page {
  max-width: 880px;
  margin: 0 auto;
  padding: 18px 16px 26px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.back-btn,
.refresh-btn {
  height: 36px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--surface-soft);
  color: var(--text);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.16s ease;
}

.back-btn:hover,
.refresh-btn:hover {
  border-color: var(--border-b);
  transform: translateY(-1px);
}

.refresh-btn {
  background: rgba(91, 141, 239, 0.12);
  border-color: rgba(91, 141, 239, 0.32);
  color: var(--blue);
}

.detail-card,
.tx-card {
  border: 1px solid var(--border);
  border-radius: 20px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--s1) 96%, #ffffff 4%), var(--s1));
  padding: 18px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
}

.asset-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
}

.asset-main {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.asset-logo-wrap {
  width: 64px;
  height: 64px;
  flex-shrink: 0;
  border-radius: 16px;
  overflow: hidden;
}

.asset-title-wrap {
  min-width: 0;
}

.asset-name {
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.asset-meta {
  margin-top: 8px;
  display: flex;
  gap: 10px;
  align-items: center;
  color: var(--sub);
  font-size: 13px;
  flex-wrap: wrap;
}

.asset-tag {
  border-radius: 999px;
  padding: 3px 9px;
  background: rgba(91, 141, 239, 0.14);
  color: var(--blue);
  font-size: 11px;
  font-weight: 700;
}

.asset-mv {
  font-family: 'JetBrains Mono', monospace;
  font-size: 28px;
  font-weight: 800;
  color: var(--text);
  text-align: right;
  flex-shrink: 0;
  letter-spacing: -0.03em;
}

.metric-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.metric-item {
  border: 1px solid var(--surface-divider);
  border-radius: 14px;
  padding: 12px;
  background: color-mix(in srgb, var(--surface-soft) 82%, transparent);
}

.metric-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
}

.metric-value {
  margin-top: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 19px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
}

.metric-sub {
  margin-top: 5px;
  font-size: 12px;
  color: var(--sub);
}

.action-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.action-btn {
  height: 44px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--panel-muted, #1a1d25);
  color: var(--sub);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.16s ease;
}

.action-btn:hover {
  border-color: color-mix(in srgb, var(--blue) 35%, var(--border));
  color: var(--text);
  transform: translateY(-1px);
}

.action-btn.buy {
  background: linear-gradient(135deg, rgba(91, 141, 239, 0.16), rgba(74, 123, 224, 0.08));
  border-color: color-mix(in srgb, var(--blue) 35%, var(--border));
  color: var(--blue);
  box-shadow: 0 6px 16px rgba(91, 141, 239, 0.12);
}

.action-btn.sell,
.action-btn.adjust {
  background: var(--panel-muted, #1a1d25);
  color: var(--sub);
}

.action-btn.adjust {
  letter-spacing: 0.02em;
}

.tx-head {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 12px;
}

.tx-list {
  display: flex;
  flex-direction: column;
}

.tx-row:first-child {
  border-top: 1px solid var(--surface-divider);
}

.tx-row {
  display: grid;
  grid-template-columns: 1.7fr 0.75fr 0.85fr 0.95fr 1.1fr;
  gap: 12px;
  padding: 11px 0;
  border-bottom: 1px solid var(--surface-divider);
  align-items: center;
}

.tx-row-head {
  padding: 9px 0 10px;
  border-top: 1px solid var(--surface-divider);
  background: color-mix(in srgb, var(--surface-soft) 55%, transparent);
}

.tx-col {
  font-size: 12.5px;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tx-col.time {
  color: var(--sub);
}

.tx-col.qty,
.tx-col.price,
.tx-col.pnl {
  font-family: 'JetBrains Mono', monospace;
  text-align: right;
  font-size: 13px;
}

.tx-col-head {
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.detail-empty,
.tx-empty,
.detail-error {
  padding: 18px 14px;
  border-radius: 12px;
  border: 1px dashed var(--border);
  color: var(--sub);
  font-size: 13px;
  text-align: center;
}

.detail-error {
  color: var(--red);
}

.up {
  color: var(--red);
}

.dn {
  color: var(--green);
}

.flat {
  color: var(--sub);
}

@media (max-width: 768px) {
  .asset-detail-page {
    padding: 12px 10px 20px;
  }

  .asset-name {
    font-size: 20px;
  }

  .asset-mv {
    font-size: 20px;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }

  .asset-logo-wrap {
    width: 52px;
    height: 52px;
  }

  .tx-row {
    grid-template-columns: 1fr 1fr;
    gap: 7px 10px;
    padding: 10px 0;
  }

  .tx-col.type,
  .tx-col.qty,
  .tx-col.price,
  .tx-col.pnl {
    text-align: left;
  }
}
</style>
