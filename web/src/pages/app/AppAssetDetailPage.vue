<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/shared/http'
import { toNumber } from '@/shared/format'
import {
  formatLatestNavDateText,
  isFundAsset,
  isStaleFund,
  readLatestNavDate,
  shouldShowFundNavMeta
} from '@/shared/assetDisplay'
import { useKonaStore } from '@/stores/composables'
import AppShell from '@/layouts/AppShell.vue'
import AssetLogo from '@/components/base/AssetLogo.vue'
import { InvestTradeModal, Modal } from '@/components'

type TradeMode = 'buy' | 'sell' | 'adjust'

const route = useRoute()
const router = useRouter()
const store = useKonaStore()

const loading = ref(false)
const txLoading = ref(false)
const pageError = ref('')
const txList = ref<Record<string, any>[]>([])

const showTradeModal = ref(false)
const showDeleteModal = ref(false)
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
    store.rows.value.find(
      item =>
        String(item.code || '')
          .trim()
          .toLowerCase() === target
    ) || null
  )
})

const marketLabel = computed(() => {
  if (isFundAsset(row.value)) return '基金'
  const market = String(row.value?.category || row.value?.market || '').toLowerCase()
  if (market === 'hk') return '港股'
  if (market === 'us') return '美股'
  return 'A股'
})

function formatDisplayCode(raw: unknown): string {
  const codeText = String(raw || '').trim()
  if (!codeText) return '--'
  if (codeText === 'ft_LU1116320737') return 'BLK'
  if (codeText.toLowerCase().startsWith('gb_')) return codeText.slice(3).toUpperCase()
  if (codeText.toLowerCase().startsWith('f_')) return codeText.slice(2)
  if (codeText.toLowerCase().startsWith('ft_')) return codeText.slice(3)
  if (
    codeText.toLowerCase().startsWith('sh') ||
    codeText.toLowerCase().startsWith('sz') ||
    codeText.toLowerCase().startsWith('bj')
  ) {
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
    maximumFractionDigits: digits
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

function normalizeTradeType(item: Record<string, any>): string {
  const text = String(item.type || item.action || '')
    .trim()
    .toLowerCase()
  if (text === 'buy') return '买入'
  if (text === 'sell') return '卖出'
  if (text === 'modify') return '修正'
  if (text === 'dividend') return '分红'
  if (text === 'fee') return '手续费'
  if (text === 'tax') return '税金'
  const raw = String(item.type || item.action || '').trim()
  if (raw === '手动调整') {
    const note = String(item.note || '').trim()
    if (note.includes('成本')) return '成本修正'
    if (note.includes('数量')) return '数量修正'
  }
  return raw || '-'
}

function tradeTypeLabel(item: Record<string, any>): string {
  return normalizeTradeType(item)
}

function formatQty(value: unknown): string {
  const qty = toNumber(value)
  if (!Number.isFinite(qty)) return '-'
  return qty.toLocaleString('zh-CN')
}

function formatPricePlain(value: unknown): string {
  const price = toNumber(value)
  if (!Number.isFinite(price) || price <= 0) return '-'
  return price.toLocaleString('zh-CN', {
    minimumFractionDigits: price < 10 ? 3 : 2,
    maximumFractionDigits: 4
  })
}

function tradeDetailLabel(item: Record<string, any>): string {
  const type = normalizeTradeType(item)
  const note = String(item.note || '').trim()
  if (type === '买入' || type === '加仓' || type === '卖出' || type === '减仓') {
    const price = formatPricePlain(item.price)
    const qty = formatQty(item.qty)
    const parts = [`${price} × ${qty}股`]
    const pnl = toNumber(item.pnl)
    if ((type === '卖出' || type === '减仓') && Number.isFinite(pnl) && pnl !== 0) {
      parts.push(`盈亏 ${formatSignedMoney(pnl, row.value?.curr)}`)
    }
    return parts.join(' · ')
  }

  if (type === '成本修正') {
    const before = formatPricePlain(item.before_price)
    const after = formatPricePlain(item.after_price)
    const base = before !== '-' || after !== '-' ? `成本价 ${before} -> ${after}` : ''
    return [base, note].filter(Boolean).join(' · ') || '成本价已修正'
  }

  if (type === '数量修正') {
    const before = formatQty(item.before_qty)
    const after = formatQty(item.after_qty)
    const base = before !== '-' || after !== '-' ? `持仓数量 ${before}股 -> ${after}股` : ''
    return [base, note].filter(Boolean).join(' · ') || '持仓数量已修正'
  }

  if (type === '持仓修正' || type === '初始持仓') {
    const parts: string[] = []
    const beforePrice = formatPricePlain(item.before_price)
    const afterPrice = formatPricePlain(item.after_price)
    const beforeQty = formatQty(item.before_qty)
    const afterQty = formatQty(item.after_qty)
    if (beforePrice !== '-' || afterPrice !== '-') {
      parts.push(`成本价 ${beforePrice} -> ${afterPrice}`)
    }
    if (beforeQty !== '-' || afterQty !== '-') {
      parts.push(`持仓数量 ${beforeQty}股 -> ${afterQty}股`)
    }
    if (note) parts.push(note)
    return parts.join(' · ') || '持仓信息已修正'
  }

  return note || '-'
}

function tradeAmountLabel(item: Record<string, any>): string {
  const type = normalizeTradeType(item)
  const amount = toNumber(item.amount)
  if (!Number.isFinite(amount) || amount === 0) {
    return ['成本修正', '数量修正', '持仓修正', '初始持仓', '手动调整'].includes(type)
      ? '--'
      : formatSignedMoney(0, row.value?.curr)
  }
  if (type === '卖出' || type === '减仓' || type === '手续费' || type === '税金') {
    return formatSignedMoney(-Math.abs(amount), row.value?.curr)
  }
  if (type === '买入' || type === '加仓' || type === '分红') {
    return formatSignedMoney(Math.abs(amount), row.value?.curr)
  }
  return formatSignedMoney(amount, row.value?.curr)
}

function tradeAmountClass(item: Record<string, any>): 'up' | 'dn' | 'flat' {
  const type = normalizeTradeType(item)
  if (type === '买入' || type === '加仓' || type === '分红') return 'up'
  if (type === '卖出' || type === '减仓') return 'dn'
  const amount = toNumber(item.amount)
  return valueClass(amount)
}

function truncateAssetName(name: string): string {
  if (!name) return ''
  const limit = 20
  if (name.length <= limit) return name
  return name.slice(0, limit) + '...'
}

async function loadTransactions() {
  txLoading.value = true
  try {
    const targetCode = String(row.value?.code || code.value).trim()
    if (!targetCode) {
      txList.value = []
      return
    }
    const params = new URLSearchParams({ code: targetCode })
    const ledgerId = row.value?.ledger_id
    if (ledgerId != null && Number.isFinite(Number(ledgerId))) {
      params.set('ledger_id', String(ledgerId))
    }
    const payload = await api.get<{ records?: Record<string, any>[] }>(
      `/api/portfolio/transactions?${params.toString()}`
    )
    txList.value = Array.isArray(payload?.records) ? payload.records : []
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

async function handleDeleteHolding() {
  showDeleteModal.value = true
}

async function confirmDeleteAction() {
  if (!row.value) return

  loading.value = true
  showDeleteModal.value = false
  try {
    const assetCode = row.value.code
    const ledgerId = row.value.ledger_id
    await api.post('/api/portfolio/delete', {
      code: assetCode,
      ledger_id: ledgerId
    })
    // 刷新全局状态并返回
    await store.refreshAll()
    router.replace('/app/invest')
  } catch (error) {
    console.error('Failed to delete holding', error)
    alert('删除失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

function openTrade(mode: TradeMode) {
  console.log('[DEBUG Detail] openTrade called, mode:', mode, 'row:', row.value)
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
        <button class="delete-btn" type="button" :disabled="loading" @click="handleDeleteHolding">
          删除
        </button>
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
                <div class="asset-name">
                  {{ truncateAssetName(row.name || formatDisplayCode(row.code)) }}
                </div>
                <div class="asset-meta">
                  <span class="asset-tag">{{ marketLabel }}</span>
                  <span>{{ formatDisplayCode(row.code) }}</span>
                </div>
              </div>
            </div>
            <div class="asset-right-info">
              <div class="asset-mv">{{ formatMoney(row.mv ?? row.value, row.curr) }}</div>
              <div class="asset-qty-right">
                {{ Number(row.qty || 0).toLocaleString('zh-CN')
                }}{{ row.unit || (isFundAsset(row) ? '份' : '股') }}
              </div>
            </div>
          </div>

          <div class="metric-grid">
            <div class="metric-item">
              <div class="metric-label">
                {{ shouldShowFundNavMeta(row) ? '最新净值' : '最新价格' }}
              </div>
              <div class="metric-value">{{ formatPrice({ ...row, price: row.currentPrice }) }}</div>
              <div v-if="shouldShowFundNavMeta(row)" class="metric-sub">
                {{
                  formatLatestNavDateText(readLatestNavDate(row))
                    ? `最新净值 (${formatLatestNavDateText(readLatestNavDate(row))})`
                    : '最新净值'
                }}
              </div>
            </div>

            <div class="metric-item">
              <div class="metric-label">成本价</div>
              <div class="metric-value">{{ formatPrice({ ...row, price: row.costPrice }) }}</div>
            </div>

            <div class="metric-item">
              <div class="metric-label">当日盈亏</div>
              <div
                class="metric-value"
                :class="isStaleFund(row) ? 'text-muted' : valueClass(row.dayPnl)"
              >
                {{ isStaleFund(row) ? '--' : formatSignedMoney(row.dayPnl, row.curr) }}
              </div>
              <div
                class="metric-sub"
                :class="isStaleFund(row) ? 'text-muted' : valueClass(row.dayPnlRate)"
              >
                {{ isStaleFund(row) ? '--' : formatPct(row.dayPnlRate) }}
              </div>
            </div>

            <div class="metric-item">
              <div class="metric-label">累计盈亏</div>
              <div class="metric-value" :class="valueClass(row.totalPnl)">
                {{ formatSignedMoney(row.totalPnl, row.curr) }}
              </div>
              <div class="metric-sub" :class="valueClass(row.totalPnlRate)">
                {{ formatPct(row.totalPnlRate) }}
              </div>
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
            <div
              v-for="item in txList"
              :key="String(item.id || `${item.time || item.date}-${item.type}-${item.qty}`)"
              class="tx-item"
            >
              <span class="tx-dot" :class="tradeAmountClass(item)"></span>
              <div class="tx-body">
                <div class="tx-line-main">
                  <div class="tx-type">{{ tradeTypeLabel(item) }}</div>
                  <div class="tx-amount" :class="tradeAmountClass(item)">
                    {{ tradeAmountLabel(item) }}
                  </div>
                </div>
                <div class="tx-line-sub">
                  <div class="tx-detail">{{ tradeDetailLabel(item) }}</div>
                  <div class="tx-time">
                    {{ formatDateTime(item.time || item.date || item.created_at) }}
                  </div>
                </div>
              </div>
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

      <!-- 自定义风格的删除确认弹窗 -->
      <Modal v-model:show="showDeleteModal" title="确认删除持仓" :width="400">
        <div class="delete-confirm-content">
          <div class="confirm-icon">⚠️</div>
          <p>
            确定要彻底删除
            <strong>{{ row?.name || formatDisplayCode(row?.code) }}</strong>
            的全部持仓和历史记录吗？
          </p>
          <span class="confirm-hint">此操作将同时删除相关的交易流水，且不可撤销。</span>
        </div>
        <template #footer>
          <div class="delete-modal-footer">
            <button class="modal-btn cancel" @click="showDeleteModal = false">取消</button>
            <button class="modal-btn delete" @click="confirmDeleteAction">确认删除</button>
          </div>
        </template>
      </Modal>
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
.delete-btn {
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
.delete-btn:hover {
  border-color: var(--border-b);
  transform: translateY(-1px);
}

.delete-btn {
  background: rgba(244, 63, 94, 0.12);
  border-color: rgba(244, 63, 94, 0.32);
  color: #f43f5e;
}

.delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
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
  align-items: center;
  gap: 14px;
  min-width: 0;
  flex: 1;
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
  margin-top: 6px;
  display: flex;
  gap: 10px;
  align-items: center;
  color: var(--sub);
  font-size: 13px;
}

.asset-right-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  text-align: right;
  gap: 4px;
}

.asset-qty-right {
  font-size: 14px;
  font-weight: 500;
  color: var(--sub);
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

.tx-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--surface-divider);
  align-items: flex-start;
}

.tx-item:first-child {
  border-top: 1px solid var(--surface-divider);
}

.tx-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: var(--sub);
  margin-top: 7px;
  flex-shrink: 0;
}

.tx-dot.up {
  background: var(--red);
}

.tx-dot.dn {
  background: var(--green);
}

.tx-dot.flat {
  background: var(--sub);
}

.tx-body {
  min-width: 0;
  flex: 1;
}

.tx-line-main,
.tx-line-sub {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

.tx-line-sub {
  margin-top: 4px;
}

.tx-type {
  min-width: 0;
  color: var(--text);
  font-size: 13px;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tx-amount {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 800;
  white-space: nowrap;
}

.tx-detail {
  min-width: 0;
  color: var(--sub);
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tx-time {
  color: var(--muted);
  font-size: 11.5px;
  white-space: nowrap;
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

/* ───────────────────────────────────────────────────────────────
   DELETE MODAL CUSTOM STYLES
   ─────────────────────────────────────────────────────────────── */

.delete-confirm-content {
  text-align: center;
  padding: 10px 0;
}

.confirm-icon {
  font-size: 40px;
  margin-bottom: 16px;
}

.delete-confirm-content p {
  font-size: 15px;
  color: var(--text);
  line-height: 1.6;
  margin-bottom: 12px;
}

.confirm-hint {
  font-size: 13px;
  color: var(--muted);
  display: block;
}

.delete-modal-footer {
  display: flex;
  gap: 12px;
  width: 100%;
}

.modal-btn {
  flex: 1;
  height: 42px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.modal-btn.cancel {
  background: var(--surface-soft);
  color: var(--sub);
  border: 1px solid var(--border);
}

.modal-btn.cancel:hover {
  background: var(--surface-divider);
  color: var(--text);
}

.modal-btn.delete {
  background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(244, 63, 94, 0.25);
}

.modal-btn.delete:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.modal-btn.delete:active {
  transform: translateY(0);
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

  .tx-line-main,
  .tx-line-sub {
    align-items: flex-start;
  }

  .tx-line-sub {
    flex-direction: column;
    gap: 3px;
  }

  .tx-time {
    font-size: 11px;
  }
}
</style>
