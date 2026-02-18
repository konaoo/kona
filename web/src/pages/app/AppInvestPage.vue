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
          <thead>
            <tr>
              <th>资产代码</th>
              <th>资产名称</th>
              <th>持有数量</th>
              <th>成本/现价</th>
              <th>持有金额</th>
              <th>当日盈亏</th>
              <th>累计盈亏</th>
              <th style="text-align:right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredRows" :key="row.code">
              <td class="code-cell">{{ displayCode(row.code) }}</td>
              <td class="name-cell">{{ row.name || '-' }}</td>
              <td>{{ toNumber(row.qty).toFixed(3) }}</td>
              <td class="price-cell">
                <span>{{ formatMoney(row.costPrice, row.curr || 'CNY') }}</span>
                <span>{{ formatMoney(row.currentPrice, row.curr || 'CNY') }}</span>
              </td>
              <td>{{ formatCny(toCny(row.value, row.curr)) }}</td>
              <td class="pnl-cell" :class="valueClass(toCny(row.dayPnl, row.curr))">
                <span>{{ formatSignedCny(toCny(row.dayPnl, row.curr)) }}</span>
                <span>{{ formatPct(toNumber(row.dayPnlRate)) }}</span>
              </td>
              <td class="pnl-cell" :class="valueClass(toCny(row.totalPnl, row.curr))">
                <span>{{ formatSignedCny(toCny(row.totalPnl, row.curr)) }}</span>
                <span>{{ formatPct(toNumber(row.totalPnlRate)) }}</span>
              </td>
              <td class="actions">
                <button class="action-btn" @click="openModal('buy', row)">买入</button>
                <button class="action-btn" @click="openModal('sell', row)">卖出</button>
                <button class="action-btn" @click="openModal('edit', row)">修正</button>
                <button class="action-btn danger" @click="remove(row.code)">删</button>
              </td>
            </tr>
            <tr v-if="!filteredRows.length">
              <td colspan="8" class="empty">暂无持仓</td>
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
            <input v-model.number="form.qty" type="number" step="0.0001" class="modal-input" required />
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
import { computed, onMounted, reactive, ref } from 'vue'
import LegacyAppShell from '../../layouts/LegacyAppShell.vue'
import { api } from '../../shared/http'
import { money, toNumber } from '../../shared/format'
import { useKonaStore } from '../../shared/store'

type TabKey = 'all' | 'a' | 'fund' | 'us' | 'hk'
type ModalType = 'add' | 'buy' | 'sell' | 'edit'

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

const form = reactive({
  code: '',
  name: '',
  qty: 0,
  price: 0,
  curr: 'CNY',
  adjustment: 0,
})

function rateToCny(curr?: string): number {
  const code = String(curr || 'CNY').toUpperCase()
  return toNumber(rates.value[code], 1) || 1
}

function toCny(amount: unknown, curr?: string): number {
  return toNumber(amount) * rateToCny(curr)
}

function formatMoney(value: number, curr: string): string {
  return money(toNumber(value), curr)
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

function valueClass(value: number): 'up' | 'down' {
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
    dayPnl += toNumber(row.dayPnl) * rate
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
  return `修正 ${modal.code}`
})

function openModal(type: ModalType, row?: Record<string, unknown>) {
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

function closeModal() {
  modal.visible = false
}

async function submitModal() {
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
  await refresh()
}

async function remove(code: string) {
  if (!confirm(`确认删除 ${code} ？`)) return
  await api.post('/api/portfolio/delete', { code })
  await refresh()
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

async function refresh() {
  await Promise.all([store.refreshAll(), loadIndexes()])
}

onMounted(refresh)
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
  font-size: 14px;
  color: var(--legacy-text-secondary);
}

.idx-value {
  font-size: 30px;
  font-weight: 700;
}

.idx-change {
  font-size: 14px;
  margin-top: 4px;
}

.up { color: var(--legacy-red); }
.down { color: var(--legacy-green); }

.assets-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 28px;
}

.total-mv-label {
  font-size: 14px;
  color: var(--legacy-text-secondary);
  margin-bottom: 12px;
}

.main-mv {
  font-size: 52px;
  font-weight: 700;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.pnl-stats {
  display: flex;
  gap: 12px;
}

.pnl-stat-item {
  background: var(--legacy-bg-tertiary);
  border-radius: var(--legacy-radius-sm);
  padding: 14px 16px;
  border: 2px solid var(--legacy-border);
  min-width: 170px;
}

.pnl-label {
  font-size: 12px;
  color: var(--legacy-text-secondary);
}

.pnl-value {
  margin-top: 8px;
  font-size: 18px;
  font-weight: 700;
}

.pnl-rate {
  margin-top: 4px;
  font-size: 13px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--legacy-border);
}

.table-header h2 {
  font-size: 22px;
  margin: 0;
}

.category-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  padding: 4px;
  background: var(--legacy-bg-tertiary);
  border-radius: 12px;
  border: 1px solid var(--legacy-border);
}

.tab-item {
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
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
}

.table-legacy {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.table-legacy th {
  font-size: 13px;
  color: var(--legacy-text-secondary);
  padding: 14px;
  text-align: left;
  border-bottom: 1px solid var(--legacy-border);
  background: var(--legacy-bg-tertiary);
}

.table-legacy td {
  padding: 14px;
  border-bottom: 1px solid var(--legacy-border);
}

.code-cell {
  color: var(--legacy-blue);
  font-weight: 700;
}

.name-cell {
  max-width: 140px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.price-cell,
.pnl-cell {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.actions {
  text-align: right;
  white-space: nowrap;
}

.action-btn {
  border: none;
  background: transparent;
  color: var(--legacy-text-secondary);
  cursor: pointer;
  margin-left: 8px;
}

.action-btn:hover {
  color: var(--legacy-text-primary);
}

.action-btn.danger:hover {
  color: #ff9ca8;
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
  padding: 30px;
  width: 420px;
  border: 1px solid var(--legacy-border);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.close-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--legacy-bg-tertiary);
  color: #fff;
  cursor: pointer;
  font-size: 24px;
}

.input-group { margin-bottom: 14px; }
.input-label {
  display: block;
  color: var(--legacy-text-secondary);
  font-size: 13px;
  margin-bottom: 8px;
}
.modal-input {
  width: 100%;
  background: #0f172a;
  border: 1px solid var(--legacy-border);
  border-radius: 12px;
  color: #fff;
  padding: 12px;
}
.btn-primary.full {
  width: 100%;
  height: 44px;
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
</style>
